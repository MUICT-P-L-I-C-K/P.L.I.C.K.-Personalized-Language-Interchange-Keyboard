/**
 * global-events.js — ดักจับเหตุการณ์ Global ในระดับหน้าเว็บ
 */

// ── คลิกที่อื่น → ซ่อน bubbles ──
document.addEventListener("click", (e) => {
  if (convertBubble?.contains(e.target) || spellBubble?.contains(e.target)) {
    return;
  }
  hideActionBubbles();
});

// ── เลือกข้อความด้วย mouse → แสดง convert bubble ──
document.addEventListener("mouseup", async () => {
  if (!shortcutEnabled) {
    hideActionBubbles();
    return;
  }

  const sel = getSelectionInfo();
  if (!sel || !sel.text.trim()) {
    hideActionBubbles();
    return;
  }

  setTimeout(() => {
    showConvertBubble(convertText(sel.text), sel);
    if (correctionEnabled) {
      smartSpellCheck(sel.text).then(suggestions => {
        if (suggestions.length) showSpellBubble(suggestions, sel);
      });
    }
  }, 0);
});

// ── เลือกข้อความด้วย keyboard (Shift+Arrow) → แสดง convert bubble ──
let _selectionKeyTimer = null;

document.addEventListener("keyup", (e) => {
  // ตอบสนองเฉพาะปุ่มนำทาง
  const navKeys = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"];
  if (!navKeys.includes(e.key)) return;
  if (!shortcutEnabled) return;

  // หน่วงเล็กน้อยเพื่อให้ browser อัพเดท selection ก่อน
  clearTimeout(_selectionKeyTimer);
  _selectionKeyTimer = setTimeout(() => {
    const activeEl = document.activeElement;
    let sel = null;

    // input/textarea
    if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA")) {
      if (activeEl.selectionStart !== activeEl.selectionEnd) {
        sel = getSelectionInfo(activeEl);
      }
    } else {
      // contentEditable / page
      const winSel = window.getSelection();
      if (winSel && winSel.toString().trim()) {
        sel = getSelectionInfo();
      }
    }

    if (!sel || !sel.text.trim()) return;

    showConvertBubble(convertText(sel.text), sel);
    if (correctionEnabled) {
      smartSpellCheck(sel.text).then(suggestions => {
        if (suggestions.length) showSpellBubble(suggestions, sel);
      });
    }
  }, 80);
});
