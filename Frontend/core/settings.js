/**
 * settings.js — การตั้งค่า Extension (Settings Manager)
 *
 * ไฟล์นี้จัดการ settings ทั้งหมดของ extension:
 *   - โหลด settings จาก chrome.storage.local
 *   - อัพเดท settings เมื่อผู้ใช้เปลี่ยนค่าจาก popup
 *   - เก็บค่า settings เป็น global variables ให้ไฟล์อื่นใช้ได้
 *
 * ตัวแปร Global ที่ export:
 *   - shortcutEnabled   : เปิด/ปิดปุ่มลัด
 *   - soundEnabled      : เปิด/ปิดเสียงเตือน
 *   - soundVolume       : ระดับเสียง (0-100)
 *   - activeShortcut    : ปุ่มลัดที่ใช้อยู่ (เช่น "Alt+Plus")
 *   - correctionEnabled : เปิด/ปิดการแนะนำคำสะกด
 *   - autoDetectEnabled : เปิด/ปิดการตรวจจับภาษาอัตโนมัติ
 */

// =============================================================================
// Constants (ค่าคงที่สำหรับ timing ต่างๆ)
// =============================================================================

/** หน่วง delay หลังหยุดพิมพ์ก่อนเริ่มตรวจ (ms) */
const DEBOUNCE_DELAY = 600;

/** ระยะเวลาขั้นต่ำระหว่างเสียงเตือน (ms) — ป้องกันเสียงถี่เกิน */
const SOUND_COOLDOWN = 3000;

/** ความยาวขั้นต่ำของคำก่อนเริ่มตรวจ (characters) */
const MIN_WORD_LENGTH = 4;

/** เวลาที่ bubble จะซ่อนตัวอัตโนมัติ (ms) */
const BUBBLE_AUTO_HIDE = 5000;

/** จำนวนคำแนะนำสูงสุดที่แสดงใน popup */
const MAX_SUGGESTIONS = 5;


// =============================================================================
// Settings State (ค่าปัจจุบันที่ใช้อยู่)
// =============================================================================

let shortcutEnabled = true;       // เปิดการใช้ปุ่มลัด
let soundEnabled = true;          // เปิดเสียงเตือน
let soundVolume = 50;             // ระดับเสียง (0-100)
let activeShortcut = "Alt+Plus";  // ปุ่มลัดที่ตั้งไว้
let correctionEnabled = false;    // เปิดการตรวจสะกดคำ
let autoDetectEnabled = false;    // เปิดการตรวจจับภาษาอัตโนมัติ


// =============================================================================
// Settings Functions
// =============================================================================

/**
 * อัพเดทค่า settings จาก object ที่ได้มา
 * ใช้ nullish coalescing (??) เพื่อ fallback เป็นค่า default ถ้าไม่มี
 *
 * @param {Object} s - object settings จาก chrome.storage
 */
function applySettings(s) {
  shortcutEnabled = s.shortcut ?? true;
  soundEnabled = s.sound ?? true;
  soundVolume = s.volume ?? 50;
  correctionEnabled = s.correction ?? false;
  autoDetectEnabled = s.autoDetect ?? false;
  activeShortcut = s.shortcutKey?.trim() || "Alt+Plus";
}

/**
 * โหลด settings จาก chrome.storage.local
 * เรียกตอน content script เริ่มทำงาน
 *
 * @param {Function} callback - function ที่จะเรียกหลังโหลดเสร็จ
 */
function loadSettings(callback) {
  chrome.storage.local.get(["settings"], (res) => {
    applySettings(res?.settings || {});
    if (callback) callback();
  });
}

// ── Listen สำหรับ settings เปลี่ยน (เมื่อผู้ใช้บันทึกค่าใหม่จาก popup) ──
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.settings?.newValue) {
    applySettings(changes.settings.newValue);
  }
});
