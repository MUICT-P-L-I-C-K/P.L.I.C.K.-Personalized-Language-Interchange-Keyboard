/**
 * editable-handler.js — จัดการ Event ของ ContentEditable Elements 
 * (เช่นช่องพิมพ์ใน Google Docs หรือ Facebook)
 */

/**
 * เพิ่ม event listeners ให้ contentEditable elements
 *
 * @param {HTMLElement} div - contentEditable element
 */
function attachContentEditable(div) {
  // ── ตรวจคำขณะพิมพ์ ──
  div.addEventListener("input", () => {
    hideActionBubbles();

    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return;

    // คำนวณข้อความก่อน cursor
    const range = sel.getRangeAt(0);
    const preCaretRange = range.cloneRange();
    preCaretRange.selectNodeContents(div);
    preCaretRange.setEnd(range.endContainer, range.endOffset);
    const text = preCaretRange.toString();

    // หาคำที่กำลังพิมพ์
    const wordMatch = text.match(/\S+$/);
    const currentWord = wordMatch ? wordMatch[0] : "";

    if (currentWord.length >= MIN_WORD_LENGTH) {
      debounced(() => {
        // สร้าง range ที่ครอบคำสำหรับ replacement
        const wordRange = document.createRange();
        try {
          wordRange.setStart(
            range.endContainer,
            Math.max(0, range.endOffset - currentWord.length)
          );
          wordRange.setEnd(range.endContainer, range.endOffset);
        } catch (_) {
          wordRange.setStart(range.startContainer, range.startOffset);
          wordRange.setEnd(range.endContainer, range.endOffset);
        }

        const ceSelection = {
          type: "ce",
          range: wordRange,
          text: currentWord,
          rect: wordRange.getBoundingClientRect(),
        };

        handleMistakeDetection(currentWord, {
          onCombinedMistake: (result) => {
            showCombinedBubble(result, ceSelection);
          },
        });
      });
    }
  });

  // ── จับ shortcut เพื่อแปลงข้อความ ──
  div.addEventListener("keydown", async (e) => {
    if (!matchesShortcut(e)) return;
    e.preventDefault();

    const sel = getSelectionInfo();
    if (!sel) return;

    const converted = convertText(sel.text);
    replaceSelection(sel, converted);

    if (correctionEnabled) {
      const suggestions = await smartSpellCheck(converted);
      if (suggestions.length > 0) {
        setTimeout(() => showSpellBubble(suggestions, sel), 50);
      }
    }
  });
}
