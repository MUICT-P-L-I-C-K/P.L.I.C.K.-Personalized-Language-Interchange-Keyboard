/**
 * core.js — State และ ฟังก์ชันจัดการภาพรวมของ Pop-up Bubbles
 *
 * เก็บตัวแปร Global สำหรับอ้างอิงถึง Bubble elements และ Timer ต่างๆ
 */

// =============================================================================
// Timers (ตัวจับเวลาสำหรับ auto-hide)
// =============================================================================
let spellCheckTimeout;      // timer สำหรับ debounce spell check
let spellBubbleHideTimeout; // timer สำหรับ auto-hide spell bubble
let langSwitchTimeout;      // timer สำหรับ auto-hide lang switch bubble

// =============================================================================
// UI Elements
// =============================================================================
let convertBubble;     // bubble สำหรับแปลงข้อความ (สีเทาดำ)
let spellBubble;       // bubble สำหรับแสดงคำแนะนำ (สีเขียว)
let langSwitchBubble;  // bubble สำหรับแสดงคำแปลงภาษา (สีแดง)

// =============================================================================
// Global Actions
// =============================================================================
/**
 * ซ่อน bubble ทั้งหมด — เรียกเมื่อคลิกที่อื่น หรือเริ่มพิมพ์ใหม่
 */
function hideActionBubbles() {
  if (convertBubble) convertBubble.style.display = "none";
  if (spellBubble) spellBubble.style.display = "none";
  if (langSwitchBubble) langSwitchBubble.style.display = "none";

  // ซ่อน conversion bubble เก่า (ถ้ามี)
  const oldBubble = document.getElementById("conversion-bubble");
  if (oldBubble) oldBubble.style.opacity = "0";
}
