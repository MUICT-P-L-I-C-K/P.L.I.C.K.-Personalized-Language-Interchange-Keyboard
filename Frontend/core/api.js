/**
 * api.js — การสื่อสารกับ Backend Server (API Communication)
 *
 * ไฟล์นี้จัดการการสื่อสารระหว่าง content script กับ background script → backend server
 *
 * ทำไมต้องผ่าน background script?
 *   Chrome Extension บน HTTPS pages ไม่สามารถ fetch HTTP localhost ได้โดยตรง
 *   (Mixed Content Policy) → ต้องส่งผ่าน background.js ซึ่งไม่มีข้อจำกัดนี้
 *
 * ฟังก์ชันที่ export (global):
 *   - sendToBackground()      : ส่ง message ไป background script (low-level)
 *   - smartSpellCheck()       : ตรวจสะกดคำ (retry ได้)
 *   - detectLanguageMistake() : ตรวจว่าพิมพ์ผิดภาษาหรือไม่ (retry ได้)
 */

// =============================================================================
// Core Communication
// =============================================================================

/**
 * ส่ง message ไปยัง background script แล้วรอ response
 * ใช้ Promise wrapper สำหรับ chrome.runtime.sendMessage
 *
 * @param {string} action - ชื่อ action (เช่น "spellCheck", "detectLanguageMistake")
 * @param {Object} data   - ข้อมูลที่จะส่งไป (เช่น {text, language})
 * @returns {Promise<Object>} ข้อมูลที่ server ส่งกลับมา
 * @throws {Error} ถ้า background script ตอบ error หรือ connection ขาด
 */
function sendToBackground(action, data) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ action, data }, (res) => {
      if (chrome.runtime.lastError) {
        return reject(chrome.runtime.lastError);
      }
      if (res?.success) {
        resolve(res.data);
      } else {
        reject(new Error(res?.error || "Unknown error"));
      }
    });
  });
}


// =============================================================================
// API Functions (High-Level)
// =============================================================================

/**
 * ตรวจสะกดคำ — ส่งคำไป backend แล้วได้คำแนะนำกลับมา
 *
 * มี retry logic: ถ้าครั้งแรกล้มเหลว จะลองอีก (default 1 ครั้ง)
 * ทำไมต้อง retry: LanguageTool อาจโหลดไม่ทัน หรือ connection ช้า
 *
 * @param {string} text    - ข้อความที่ต้องการตรวจ
 * @param {number} retries - จำนวนครั้งที่จะ retry (default: 1)
 * @returns {Promise<string[]>} รายการคำแนะนำ (อาจเป็น [] ถ้าไม่มี)
 */
async function smartSpellCheck(text, retries = 1) {
  const language = isMostlyThai(text) ? "th" : "en";

  for (let i = 0; i <= retries; i++) {
    try {
      const response = await sendToBackground("spellCheck", { text, language });

      // ตรวจว่า response ถูกต้อง
      if (!response || typeof response !== "object") {
        throw new Error("Invalid response");
      }
      return response.suggestions || [];
    } catch (e) {
      // ถ้าเป็นรอบสุดท้าย → แสดง warning แล้ว return []
      if (i === retries) {
        console.warn("Spell check error:", e.message);
        return [];
      }
      // รอสักครู่ก่อน retry
      await new Promise(r => setTimeout(r, 50));
    }
  }
  return [];
}

/**
 * ตรวจว่าคำที่พิมพ์เป็นการพิมพ์ผิดภาษาหรือไม่
 *
 * ส่งคำไป backend → backend จะ:
 *   1. ตรวจว่าคำอยู่ใน dictionary ภาษาเดิม
 *   2. แปลง keyboard layout แล้วตรวจภาษาตรงข้าม
 *   3. หาคำแนะนำสำหรับทั้ง 2 ฝั่ง
 *
 * @param {string} word    - คำที่ต้องการตรวจ
 * @param {number} retries - จำนวนครั้งที่จะ retry (default: 1)
 * @returns {Promise<Object>} ผลการตรวจ {is_mistake, original, converted}
 */
async function detectLanguageMistake(word, retries = 1) {
  const defaultResult = {
    is_mistake: false,
    mistake_type: "correct",
    original: {},
    converted: {},
  };

  // คำสั้นเกินไม่ตรวจ (อาจเป็นแค่สัญลักษณ์)
  if (!word || word.length < 2) return defaultResult;

  const language = isMostlyThai(word) ? "th" : "en";

  for (let i = 0; i <= retries; i++) {
    try {
      const data = await sendToBackground("detectLanguageMistake", {
        word,
        language,
      });
      return data;
    } catch (e) {
      if (i === retries) {
        console.warn("Language detection error:", e.message);
        return defaultResult;
      }
      await new Promise(r => setTimeout(r, 100));
    }
  }
  return defaultResult;
}
