/**
 * shortcut.js — ระบบปุ่มลัด (Keyboard Shortcut Matching)
 *
 * ไฟล์นี้จัดการการจับคู่ปุ่มลัดที่ผู้ใช้ตั้งไว้กับปุ่มที่กดจริง
 *
 * ปัญหาที่แก้:
 *   เมื่อ keyboard layout เป็นภาษาไทย ปุ่ม "=" จะแสดงเป็น "ช"
 *   แต่ตำแหน่งหนึ่งทาง (physical position) ยังเป็น "Equal" เหมือนเดิม
 *   → ดังนั้นต้องใช้ e.code (ตำแหน่งกายภาพ) แทน e.key (ตัวอักษรที่ได้)
 *
 * ฟังก์ชันที่ export (global):
 *   - matchesShortcut() : ตรวจว่าปุ่มที่กดตรงกับ shortcut ที่ตั้งไว้หรือไม่
 */

// =============================================================================
// Physical Key Code Map
// =============================================================================

/**
 * แปลง e.code (ตำแหน่งกายภาพ) → ชื่อปุ่มที่อ่านง่าย
 * เช่น "KeyA" → "a", "Digit5" → "5", "NumpadAdd" → "plus"
 */
const CODE_MAP = {
  // ─── ตัวอักษร A-Z ───
  KeyA: "a", KeyB: "b", KeyC: "c", KeyD: "d", KeyE: "e",
  KeyF: "f", KeyG: "g", KeyH: "h", KeyI: "i", KeyJ: "j",
  KeyK: "k", KeyL: "l", KeyM: "m", KeyN: "n", KeyO: "o",
  KeyP: "p", KeyQ: "q", KeyR: "r", KeyS: "s", KeyT: "t",
  KeyU: "u", KeyV: "v", KeyW: "w", KeyX: "x", KeyY: "y", KeyZ: "z",

  // ─── ตัวเลข 0-9 ───
  Digit0: "0", Digit1: "1", Digit2: "2", Digit3: "3", Digit4: "4",
  Digit5: "5", Digit6: "6", Digit7: "7", Digit8: "8", Digit9: "9",

  // ─── สัญลักษณ์พิเศษ ───
  Equal: "=", Minus: "-",
  BracketLeft: "[", BracketRight: "]",
  Semicolon: ";", Quote: "'",
  Comma: ",", Period: ".", Slash: "/",
  Backslash: "\\",
  NumpadAdd: "plus",
  Space: "space",
};


// =============================================================================
// Key Normalization
// =============================================================================

/**
 * แปลง keyboard event code เป็นชื่อปุ่มที่ normalize แล้ว
 *
 * @param {KeyboardEvent} e - keyboard event
 * @returns {string} ชื่อปุ่มที่ normalize แล้ว (lowercase)
 */
function getNormalizedPressed(e) {
  if (e.code === "NumpadAdd") return "plus";
  if (e.code.startsWith("Digit")) return e.code.replace("Digit", "");
  if (e.code === "Equal") return "=";
  if (e.code === "Minus") return "-";
  if (e.code === "Space") return "space";
  return CODE_MAP[e.code] || e.code.toLowerCase();
}

/**
 * Normalize ชื่อปุ่มจาก settings ให้ตรงกับ getNormalizedPressed
 *
 * ตัวอย่าง:
 *   "Plus" → "plus"
 *   "+"    → "plus"
 *   "Space" → "space"
 *   "A"    → "a"
 *
 * @param {string} k - ชื่อปุ่มจาก settings
 * @returns {string} ชื่อปุ่มที่ normalize แล้ว
 */
function normalizeKey(k) {
  const v = k.toLowerCase();
  if (["+", "plus", "equal"].includes(v)) return "plus";
  if (["space", "spacebar"].includes(v)) return "space";
  return v;
}


// =============================================================================
// Shortcut Matching
// =============================================================================

/**
 * ตรวจว่า keyboard event ตรงกับ shortcut ที่ผู้ใช้ตั้งไว้หรือไม่
 *
 * ตัวอย่าง: ถ้าตั้งไว้ "Alt+Plus"
 *   → e.altKey ต้องเป็น true
 *   → ปุ่มที่กดต้องเป็น "plus" (ตำแหน่ง Equal หรือ NumpadAdd)
 *
 * @param {KeyboardEvent} e - keyboard event
 * @returns {boolean} true ถ้าตรงกับ shortcut
 */
function matchesShortcut(e) {
  // ถ้าปิดปุ่มลัด → ไม่ match เลย
  if (!shortcutEnabled) return false;

  // แยกส่วนของ shortcut (เช่น "Alt+Plus" → ["Alt", "Plus"])
  const parts = activeShortcut.split("+").map(p => p.trim());

  // ตรวจ modifier keys
  const needCtrl = parts.some(p => /^ctrl|control$/i.test(p));
  const needShift = parts.some(p => /^shift$/i.test(p));
  const needAlt = parts.some(p => /^alt$/i.test(p));

  // หาปุ่มหลัก (ปุ่มที่ไม่ใช่ modifier)
  const key = parts.find(p => !/^(ctrl|control|shift|alt)$/i.test(p));

  // ตรวจ modifier keys
  if (needCtrl && !e.ctrlKey) return false;
  if (needShift && !e.shiftKey) return false;
  if (needAlt && !e.altKey) return false;

  // ตรวจปุ่มหลัก (เทียบแบบ physical position)
  return normalizeKey(getNormalizedPressed(e)) === normalizeKey(key);
}
