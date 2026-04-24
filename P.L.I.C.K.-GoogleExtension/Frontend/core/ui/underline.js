/**
 * underline.js — ระบบขีดเส้นใต้คำผิดใน contentEditable
 */

/**
 * ลบเส้นขีดสีแดง (wavy underline) ทั้งหมดที่เพิ่มไว้
 */
function removeUnderlineSpans() {
    document.querySelectorAll(".plick-underline").forEach(span => {
      const parent = span.parentNode;
      while (span.firstChild) parent.insertBefore(span.firstChild, span);
      parent.removeChild(span);
      parent.normalize();
    });
  }
  
  /**
   * เพิ่มเส้นขีด wavy ใต้คำที่ผิดใน contentEditable
   *
   * @param {HTMLElement} div         - contentEditable element
   * @param {string}      word        - คำที่ต้องการขีดเส้น
   * @param {string}      mistakeType - ประเภทข้อผิดพลาด ("wrong_language", "wrong_language_typo", "typo")
   */
  function addUnderlineForContentEditable(div, word, mistakeType) {
    const colors = {
      wrong_language: "#ef4444",
      wrong_language_typo: "#ef4444",
      typo: "#f97316",
    };
    const color = colors[mistakeType];
    if (!color) return;
  
    // บันทึกตำแหน่ง cursor ก่อน
    const sel = window.getSelection();
    let savedRange =
      sel && sel.rangeCount > 0 ? sel.getRangeAt(0).cloneRange() : null;
  
    // หาตำแหน่งคำใน DOM
    const walker = document.createTreeWalker(div, NodeFilter.SHOW_TEXT, null);
    let node;
    while ((node = walker.nextNode())) {
      const idx = node.textContent.lastIndexOf(word);
      if (idx === -1) continue;
      if (node.parentElement?.classList.contains("plick-underline")) continue;
  
      // สร้าง range ครอบคำ
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + word.length);
  
      // ครอบด้วย span ที่มีเส้นขีด wavy
      const span = document.createElement("span");
      span.className = "plick-underline";
      Object.assign(span.style, {
        textDecorationLine: "underline",
        textDecorationStyle: "wavy",
        textDecorationColor: color,
        textDecorationThickness: "2px",
        textUnderlineOffset: "3px",
      });
      range.surroundContents(span);
  
      // คืน cursor กลับตำแหน่งเดิม
      try {
        const textNode = span.firstChild;
        if (textNode && sel) {
          const restoreRange = document.createRange();
          restoreRange.setStart(textNode, textNode.length);
          restoreRange.collapse(true);
          sel.removeAllRanges();
          sel.addRange(restoreRange);
        }
      } catch (_) {
        if (savedRange && sel) {
          try {
            sel.removeAllRanges();
            sel.addRange(savedRange);
          } catch (__) {
            // ไม่สามารถ restore cursor ได้ — ไม่เป็นไร
          }
        }
      }
  
      // ลบเส้นขีดอัตโนมัติหลังเวลาที่กำหนด
      setTimeout(() => {
        if (span.parentNode) {
          const parent = span.parentNode;
          while (span.firstChild) parent.insertBefore(span.firstChild, span);
          parent.removeChild(span);
          parent.normalize();
        }
      }, BUBBLE_AUTO_HIDE);
  
      break; // ขีดเฉพาะตำแหน่งล่าสุดที่เจอ
    }
  }
