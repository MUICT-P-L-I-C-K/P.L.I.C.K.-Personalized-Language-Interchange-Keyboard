/**
 * utils.js — ฟังก์ชันอำนวยความสะดวกทั่วไป
 */

/**
 * Debounce — หน่วง callback ให้ทำงานหลังหยุดเรียกไประยะหนึ่ง
 * ใช้กับ spell check เพื่อไม่ให้ตรวจทุกครั้งที่กดปุ่ม
 *
 * @param {Function} callback - function ที่จะเรียกหลังหน่วง
 */
function debounced(callback) {
  clearTimeout(spellCheckTimeout);
  spellCheckTimeout = setTimeout(callback, DEBOUNCE_DELAY);
}
