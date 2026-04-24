/**
 * input-handler.js — จัดการ Event ของ Input และ Textarea ปกติ
 */

/**
 * เพิ่ม event listeners ให้ input/textarea
 *
 * Events ที่จัดการ:
 *   - input: ตรวจคำทุกครั้งที่พิมพ์ (debounced)
 *   - keydown: จับ shortcut เพื่อแปลงข้อความที่เลือก
 *
 * @param {HTMLElement} input - input หรือ textarea element
 */
function attach(input) {
  // ── ตรวจคำขณะพิมพ์ ──
  input.addEventListener("input", () => {
    hideActionBubbles();
    if (input.selectionStart === undefined) return;

    // หาคำที่กำลังพิมพ์ (คำสุดท้ายก่อน cursor)
    const beforeCursor = input.value.substring(0, input.selectionStart);
    const wordMatch = beforeCursor.match(/\S+$/);
    const currentWord = wordMatch ? wordMatch[0] : "";

    // ตรวจเมื่อคำยาวพอ
    if (currentWord.length >= MIN_WORD_LENGTH) {
      debounced(() =>
        handleMistakeDetection(currentWord, {
          onCombinedMistake: (result) => {
            showCombinedBubble(result, null, input, currentWord);
          },
        })
      );
    }
  });

  // ── จับ shortcut เพื่อแปลงข้อความ ──
  input.addEventListener("keydown", async (e) => {
    if (!matchesShortcut(e)) return;
    e.preventDefault();

    const sel = getSelectionInfo(input);
    if (!sel) return;

    // แปลงข้อความที่เลือก
    const converted = convertText(sel.text);
    replaceSelection(sel, converted);

    // ตรวจสะกดคำหลังแปลง
    if (correctionEnabled) {
      const suggestions = await smartSpellCheck(converted);
      if (suggestions.length > 0) {
        setTimeout(() => showSpellBubble(suggestions, sel), 50);
      }
    }
  });
}
