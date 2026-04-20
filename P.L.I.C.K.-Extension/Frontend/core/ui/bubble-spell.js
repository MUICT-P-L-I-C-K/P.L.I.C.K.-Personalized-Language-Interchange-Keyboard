/**
 * bubble-spell.js — Spell Bubble (กล่องสีเขียว)
 * 
 * แสดงคำแนะนำเวลาสะกดผิด
 */

/**
 * เตรียม spellBubble element (สร้างใหม่ถ้ายังไม่มี, ล้าง content ถ้ามีแล้ว)
 */
function ensureSpellBubble() {
  if (!spellBubble) {
    spellBubble = createBubbleElement({
      position: "absolute",
      background: "#222",
      padding: "6px",
      borderRadius: "10px",
      display: "flex",
      gap: "6px",
      zIndex: 9999,
      maxWidth: "400px",
      flexWrap: "wrap",
      boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
    });
  }
  spellBubble.innerHTML = "";
}

/**
 * แสดง bubble คำแนะนำสะกดคำ (สีเขียว)
 * ปรากฏใต้ข้อความที่เลือก
 *
 * @param {string[]} words - รายการคำแนะนำ
 * @param {Object}   sel   - ข้อมูล selection
 */
function showSpellBubble(words, sel) {
  if (spellBubble) spellBubble.style.display = "none";
  if (!words?.length || !sel) return;
  ensureSpellBubble();

  // สร้างปุ่มสำหรับแต่ละคำแนะนำ
  words.slice(0, MAX_SUGGESTIONS).forEach(w => {
    spellBubble.appendChild(
      createSuggestionItem(w, e => {
        e.stopPropagation();
        e.preventDefault();
        replaceSelection(sel, w);
        setTimeout(() => hideActionBubbles(), 0);
      })
    );
  });

  // วางตำแหน่งใต้ข้อความ
  spellBubble.style.left = sel.rect.left + window.scrollX + "px";
  spellBubble.style.top = sel.rect.bottom + window.scrollY + 6 + "px";
  spellBubble.style.display = "flex";

  // Auto-hide หลังจากเวลาที่กำหนด
  clearTimeout(spellBubbleHideTimeout);
  spellBubbleHideTimeout = setTimeout(() => {
    if (spellBubble) spellBubble.style.display = "none";
  }, BUBBLE_AUTO_HIDE);
}
