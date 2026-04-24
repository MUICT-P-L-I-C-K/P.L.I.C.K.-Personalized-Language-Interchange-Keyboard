/**
 * background.js — Background Service Worker
 *
 * ไฟล์นี้ทำงานเป็น proxy ระหว่าง content script กับ backend server
 *
 * ทำไมต้องมี?
 *   Chrome Extension บน HTTPS pages ไม่สามารถ fetch HTTP localhost ได้โดยตรง
 *   (Mixed Content Policy) แต่ service worker ไม่มีข้อจำกัดนี้
 *   ดังนั้น: content script → background.js → localhost:8000
 *
 * Actions ที่รองรับ:
 *   - "detectLanguageMistake" → POST /detect-lang-mistake
 *   - "spellCheck"            → POST /spell-check
 */

// =============================================================================
// Configuration
// =============================================================================

/** URL ของ backend server */
const SERVER_BASE_URL = "http://localhost:8000";

/** Mapping: action name → API endpoint */
const API_ENDPOINTS = {
  detectLanguageMistake: "/detect-lang-mistake",
  spellCheck: "/spell-check",
};


// =============================================================================
// API Request Handler (ใช้ร่วมกันทุก action)
// =============================================================================

/**
 * ส่ง POST request ไปยัง backend server
 *
 * @param {string} endpoint - API path (เช่น "/spell-check")
 * @param {Object} data     - ข้อมูลที่จะส่ง (JSON body)
 * @returns {Promise<Object>} response data จาก server
 * @throws {Error} ถ้า HTTP status ไม่ใช่ 2xx
 */
async function postToServer(endpoint, data) {
  const response = await fetch(`${SERVER_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}


// =============================================================================
// Message Listener (รับ message จาก content script)
// =============================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const endpoint = API_ENDPOINTS[message.action];

  // ไม่รู้จัก action → ไม่ตอบ
  if (!endpoint) return;

  // ส่ง request ไป server แล้วตอบกลับ content script
  postToServer(endpoint, message.data)
    .then(data => sendResponse({ success: true, data }))
    .catch(error => sendResponse({ success: false, error: error.message }));

  // return true → บอก Chrome ว่าจะตอบแบบ asynchronous
  return true;
});
