/**
 * detection.js — ลอจิกการตัดสินใจว่าจะแสดงการเตือนหรือแจ้งให้เปลี่ยนภาษา
 *
 * เรียกใช้งานร่วมกันทั้งใน input ปกติและแบบ contentEditable
 */

/**
 * ประมวลผลการตรวจคำผิดแบบรวม (spell check + language detection)
 *
 * Logic:
 *   1. ส่งคำไป backend ตรวจ
 *   2. ตัดสินว่าต้องเล่นเสียงหรือไม่
 *   3. ตัดสินว่าต้องแสดง popup หรือไม่
 *   4. เรียก callback เพื่อแสดง UI
 *
 * @param {string} currentWord - คำที่ผู้ใช้พิมพ์อยู่
 * @param {Object} options     - options.onCombinedMistake(result) — callback เมื่อพบข้อผิดพลาด
 */
async function handleMistakeDetection(currentWord, options) {
  // ต้องเปิดอย่างน้อย 1 ฟีเจอร์ ถึงจะทำงาน
  if (!(autoDetectEnabled || correctionEnabled || soundEnabled)) return;

  // ส่งคำไป backend ตรวจ
  const result = await detectLanguageMistake(currentWord);

  // ตรวจว่าคำที่แปลงแล้วมีความหมาย (อยู่ใน dictionary หรือมีคำแนะนำ)
  const convertedHasMeaning =
    result.converted &&
    (result.converted.exists || result.converted.suggestions?.length > 0);

  // ── SOUND: เล่นเสียงเตือน ──
  if (soundEnabled) {
    // พิมพ์ผิดภาษา: คำที่แปลงแล้วต้องมีอยู่จริงใน dictionary
    const isWrongLanguage = convertedHasMeaning && result.converted.exists;

    if (isWrongLanguage) {
      playErrorSound();
    }
  }

  // ── POPUP: ตัดสินว่าต้องแสดง popup หรือไม่ ──
  const isOriginalCorrect = result.original && result.original.exists;

  // แสดงคำแนะนำสะกดคำ (เมื่อเปิด correction + คำเดิมไม่ถูก + มี suggestions)
  const showOriginal =
    correctionEnabled &&
    !isOriginalCorrect &&
    result.original.suggestions?.length > 0;

  // แสดงคำแปลงภาษา (เมื่อเปิด autoDetect + คำเดิมไม่ถูก + คำแปลงมีความหมาย)
  const showConverted =
    autoDetectEnabled && !isOriginalCorrect && convertedHasMeaning;

  if (!showOriginal && !showConverted) return;

  // เรียก callback เพื่อแสดง UI
  if (options.onCombinedMistake) {
    options.onCombinedMistake(result);
  }
}
