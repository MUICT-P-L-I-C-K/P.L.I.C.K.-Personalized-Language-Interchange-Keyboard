/**
 * bubble-convert.js — Convert Bubble (กล่องสีเทา)
 * 
 * แสดงเมื่อผู้ใช้เลือกข้อความ กดเพื่อแปลงภาษาไปอีกฝั่ง
 */

/**
 * แสดง bubble สำหรับแปลงข้อความ (สีเทาดำ)
 * ปรากฏเหนือข้อความที่เลือก — กดเพื่อแปลงเป็นภาษาตรงข้าม
 *
 * @param {string} text - ข้อความที่แปลงแล้ว (preview)
 * @param {Object} sel  - ข้อมูล selection
 */
function showConvertBubble(text, sel) {
  if (convertBubble) convertBubble.style.display = "none";
  if (!text || !sel) return;

  // สร้าง bubble ครั้งแรก (lazy initialization)
  if (!convertBubble) {
    convertBubble = createBubbleElement({
      position: "absolute",
      background: "#333",
      color: "#fff",
      padding: "6px 12px",
      borderRadius: "12px",
      fontSize: "14px",
      cursor: "pointer",
      zIndex: 9999,
      whiteSpace: "nowrap",
    });
  }

  convertBubble.textContent = `⇄ ${text}`;
  const originalText = sel.text;

  // คลิกเพื่อแปลง
  convertBubble.onclick = async (e) => {
    e.stopPropagation();
    removeUnderlineSpans();
    replaceSelection(sel, text);
    hideActionBubbles();

    // ตรวจสะกดคำหลังแปลง (ถ้าเปิดฟีเจอร์ไว้)
    if (correctionEnabled || autoDetectEnabled) {
      const suggestions = await smartSpellCheck(text);
      const filtered = (suggestions || [])
        .filter(
          s =>
            s !== text &&
            s !== originalText &&
            s.toLowerCase() !== text.toLowerCase() &&
            s.toLowerCase() !== originalText.toLowerCase()
        )
        .slice(0, MAX_SUGGESTIONS);

      if (filtered.length > 0) {
        setTimeout(() => showSpellBubble(filtered, sel), 100);
      }
    }
  };

  // วางตำแหน่ง bubble เหนือข้อความ
  convertBubble.style.left = sel.rect.left + window.scrollX + "px";
  convertBubble.style.top = sel.rect.top + window.scrollY - 38 + "px";
  convertBubble.style.display = "block";
}
