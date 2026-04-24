/**
 * sound.js — ระบบเสียงเตือน (Sound Alert System)
 *
 * ไฟล์นี้จัดการเสียงเตือนเมื่อตรวจพบข้อผิดพลาด
 *
 * มีระบบ cooldown: เสียงจะไม่ดังถี่กว่า SOUND_COOLDOWN (3 วินาที)
 * เพื่อไม่ให้รำคาญผู้ใช้เมื่อพิมพ์ผิดต่อเนื่อง
 *
 * ฟังก์ชันที่ export (global):
 *   - playErrorSound() : เล่นเสียงเตือน (ถ้าเปิดอยู่ + ไม่อยู่ใน cooldown)
 */

// =============================================================================
// Audio Setup
// =============================================================================

/** เสียงเตือน (โหลดจากไฟล์ notify.mp3 ใน extension) */
const notifyAudio = new Audio(chrome.runtime.getURL("sound/notify.mp3"));

/** เวลาที่เล่นเสียงครั้งล่าสุด (timestamp) — ใช้คำนวณ cooldown */
let lastSoundTime = 0;


// =============================================================================
// Sound Function
// =============================================================================

/**
 * เล่นเสียงเตือน
 *
 * เงื่อนไข:
 *   1. soundEnabled ต้องเป็น true (ผู้ใช้เปิดเสียง)
 *   2. ต้องผ่าน cooldown (ไม่เล่นถี่กว่า SOUND_COOLDOWN)
 *
 * การทำงาน:
 *   - ตั้งระดับเสียงตาม soundVolume (0-100 → 0.0-1.0)
 *   - reset เสียงไปเริ่มต้น (currentTime = 0)
 *   - เล่นเสียง (catch error เงียบๆ ถ้าเล่นไม่ได้)
 */
function playErrorSound() {
  // ตรวจว่าเปิดเสียงอยู่ (soundEnabled มาจาก settings.js)
  if (!soundEnabled) return;

  // ตรวจ cooldown — ป้องกันเสียงดังถี่เกินไป
  const now = Date.now();
  if (now - lastSoundTime < SOUND_COOLDOWN) return;

  // ตั้งค่าและเล่นเสียง
  notifyAudio.volume = soundVolume / 100;
  notifyAudio.currentTime = 0;
  notifyAudio.play().catch(() => {
    // เสียงอาจเล่นไม่ได้ (เช่น autoplay policy) — ไม่ต้องทำอะไร
  });

  lastSoundTime = now;
}
