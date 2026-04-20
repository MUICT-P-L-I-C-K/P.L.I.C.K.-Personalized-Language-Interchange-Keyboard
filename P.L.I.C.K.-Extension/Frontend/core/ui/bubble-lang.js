/**
 * bubble-lang.js — Language Switch Bubble (กล่องสีแดง)
 * 
 * แจ้งเตือนพิมพ์ผิดภาษาแบบ Auto
 */

/**
 * แสดง bubble สำหรับสลับภาษา (สีแดง gradient)
 * ปรากฏเหนือ input/textarea — กดเพื่อแทนที่คำที่พิมพ์ผิดภาษา
 *
 * @param {string}      convertedWord - คำที่แปลง keyboard layout แล้ว
 * @param {HTMLElement}  input         - input/textarea ที่กำลังพิมพ์
 * @param {string}      originalWord  - คำเดิมที่พิมพ์ (ก่อนแปลง)
 */
function showLanguageSwitchBubble(convertedWord, input, originalWord) {
  if (!convertedWord || !input) return;

  // สร้าง bubble ครั้งแรก (lazy initialization)
  if (!langSwitchBubble) {
    langSwitchBubble = createBubbleElement({
      position: "absolute",
      background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
      padding: "8px 14px",
      borderRadius: "10px",
      display: "flex",
      alignItems: "center",
      gap: "8px",
      zIndex: 10000,
      boxShadow: "0 4px 15px rgba(220, 38, 38, 0.4)",
      cursor: "pointer",
      transition: "transform 0.2s, box-shadow 0.2s",
    });

    // Hover animation
    langSwitchBubble.onmouseover = () => {
      langSwitchBubble.style.transform = "scale(1.05)";
      langSwitchBubble.style.boxShadow =
        "0 6px 20px rgba(220, 38, 38, 0.5)";
    };
    langSwitchBubble.onmouseout = () => {
      langSwitchBubble.style.transform = "scale(1)";
      langSwitchBubble.style.boxShadow =
        "0 4px 15px rgba(220, 38, 38, 0.4)";
    };
  }

  // ใส่ content
  langSwitchBubble.innerHTML = `
    <span style="font-size: 16px;">⇄</span>
    <span style="color: #fff; font-size: 14px; font-weight: 600;">${convertedWord}</span>
  `;

  // กดเพื่อแทนที่คำ
  langSwitchBubble.onclick = e => {
    e.stopPropagation();
    e.preventDefault();
    const cursorPos = input.selectionStart;
    const wordStart = input.value.lastIndexOf(originalWord, cursorPos - 1);
    if (wordStart !== -1) {
      input.setRangeText(
        convertedWord,
        wordStart,
        wordStart + originalWord.length,
        "end"
      );
      input.focus();
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
    langSwitchBubble.style.display = "none";
  };

  // วางตำแหน่งเหนือ input
  const rect = input.getBoundingClientRect();
  langSwitchBubble.style.left = rect.left + window.scrollX + 10 + "px";
  langSwitchBubble.style.top = rect.top + window.scrollY - 45 + "px";
  langSwitchBubble.style.display = "flex";

  // Auto-hide
  clearTimeout(langSwitchTimeout);
  langSwitchTimeout = setTimeout(() => {
    if (langSwitchBubble) langSwitchBubble.style.display = "none";
  }, BUBBLE_AUTO_HIDE);
}
