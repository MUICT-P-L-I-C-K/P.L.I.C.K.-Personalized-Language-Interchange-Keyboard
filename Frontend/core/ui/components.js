/**
 * components.js — ส่วนประกอบพื้นฐานของ UI
 */

/**
 * สร้าง bubble element ใหม่แล้วเพิ่มเข้า parent body
 * @param {Object} styles - CSS styles สำหรับ element
 * @returns {HTMLElement}
 */
function createBubbleElement(styles) {
  const el = document.createElement("div");
  Object.assign(el.style, styles);
  document.body.appendChild(el);
  return el;
}

/**
 * สร้างปุ่มคำแนะนำ 1 ปุ่ม (chip สีต่างๆ)
 *
 * @param {string}   word    - คำที่จะแสดง
 * @param {Function} onClick - callback เมื่อกดปุ่ม
 * @returns {HTMLElement} span element
 */
function createSuggestionItem(word, onClick) {
  const item = document.createElement("span");
  item.textContent = word;
  Object.assign(item.style, {
    background: "#22c55e",
    color: "#fff",
    padding: "4px 10px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "12px",
    fontWeight: "500",
    userSelect: "none",
    transition: "background 0.2s",
  });
  item.onmouseover = () => (item.style.background = "#16a34a");
  item.onmouseout = () => (item.style.background = "#22c55e");
  item.onclick = onClick;
  return item;
}
