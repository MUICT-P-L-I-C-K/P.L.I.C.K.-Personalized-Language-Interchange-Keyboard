/**
 * selection.js — ระบบจัดการข้อความที่ผู้ใช้เลือกในหน้าเว็บ (Selection Management)
 */

/**
 * ดึงข้อมูลข้อความที่ผู้ใช้เลือกอยู่ (selection)
 *
 * @param {HTMLElement|null} input - element ถ้าเป็น input/textarea, null ถ้าเป็น contentEditable
 * @returns {Object|null} ข้อมูล selection หรือ null ถ้าไม่มีการเลือก
 */
function getSelectionInfo(input = null) {
  // กรณี input/textarea
  if (input && input.selectionStart !== undefined) {
    const { selectionStart: start, selectionEnd: end } = input;
    if (start === end) return null; // ไม่มีข้อความถูกเลือก
    return {
      type: "input",
      input,
      start,
      end,
      text: input.value.slice(start, end),
      rect: input.getBoundingClientRect(),
    };
  }

  // กรณี contentEditable / หน้าเว็บทั่วไป
  const sel = window.getSelection();
  if (!sel || !sel.rangeCount) return null;
  const range = sel.getRangeAt(0);
  const text = sel.toString();
  if (!text) return null;
  return { type: "ce", range, text, rect: range.getBoundingClientRect() };
}

/**
 * แทนที่ข้อความที่เลือกด้วยข้อความใหม่
 *
 * @param {Object} sel  - ข้อมูล selection จาก getSelectionInfo()
 * @param {string} text - ข้อความใหม่ที่จะแทนที่
 */
function replaceSelection(sel, text) {
  if (sel.type === "input") {
    // input/textarea → ใช้ setRangeText
    sel.input.setRangeText(text, sel.start, sel.end, "end");
  } else {
    // contentEditable → ลบ content เดิม แล้วแทรก text node ใหม่
    sel.range.deleteContents();
    sel.range.insertNode(document.createTextNode(text));
    const newRange = document.createRange();
    newRange.selectNodeContents(sel.range.endContainer);
    newRange.collapse(false);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(newRange);
  }
}
