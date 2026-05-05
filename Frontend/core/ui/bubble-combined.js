/**
 * bubble-combined.js — Combined Bubble (กล่องสีเขียวและแดง)
 * 
 * แสดงรวมแบบ 2 หมวดหมู่ ทั้งคำสะกดผิดและพิมพ์สลับภาษา
 */

/**
 * แสดง bubble รวมที่มีทั้งคำแนะนำสะกดคำ (เขียว) และคำแปลงภาษา (แดง)
 *
 * ใช้เมื่อ detection พบว่ามีทั้งปัญหาสะกดคำและพิมพ์ผิดภาษา
 *
 * @param {Object}      details     - ผลจาก detectLanguageMistake() {original, converted}
 * @param {Object|null} sel         - ข้อมูล selection (สำหรับ contentEditable)
 * @param {HTMLElement|null} input  - input element (สำหรับ input/textarea)
 * @param {string|null} currentWord - คำปัจจุบันที่กำลังพิมพ์
 */
function showCombinedBubble(details, sel, input = null, currentWord = null) {
  if (spellBubble) spellBubble.style.display = "none";

  // ── รวบรวมคำแนะนำจากทั้ง 2 ส่วน ──

  // คำแนะนำสะกดคำ (เขียว) — แสดงเมื่อเปิด correction + คำเดิมไม่อยู่ใน dict
  const originalSuggestions =
    correctionEnabled && details.original && !details.original.exists
      ? details.original.suggestions || []
      : [];

  // คำแปลงภาษา (แดง) — แสดงเมื่อเปิด autoDetect
  const convertedSuggestions = [];
  if (autoDetectEnabled && details.converted) {
    if (details.converted.exists) {
      convertedSuggestions.push(details.converted.word);
    }
    if (details.converted.suggestions) {
      convertedSuggestions.push(...details.converted.suggestions);
    }
  }

  // ลบ duplicates
  const uniqueOriginal = [...new Set(originalSuggestions)].filter(
    w => w && w.toLowerCase() !== (currentWord || "").toLowerCase()
  );
  const uniqueConverted = [...new Set(convertedSuggestions)].filter(
    w => w && w.toLowerCase() !== (currentWord || "").toLowerCase()
  );

  if (uniqueOriginal.length === 0 && uniqueConverted.length === 0) return;

  // ── สร้าง UI ──
  ensureSpellBubble();
  spellBubble.style.flexDirection = "column";
  spellBubble.style.alignItems = "flex-start";
  spellBubble.style.gap = "8px";
  spellBubble.style.padding = "8px";

  /**
   * สร้าง section (กลุ่มปุ่ม) สำหรับ bubble
   * @param {string}   title - ชื่อ section (ปัจจุบันไม่แสดง แต่เก็บไว้สำหรับอนาคต)
   * @param {string[]} words - รายการคำ
   * @param {string}   color - สี background ของปุ่ม
   */
  const createSection = (title, words, color) => {
    const section = document.createElement("div");
    section.style.display = "flex";
    section.style.flexDirection = "column";
    section.style.gap = "4px";

    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.flexWrap = "wrap";
    row.style.gap = "4px";

    words.slice(0, 5).forEach(w => {
      const chip = createSuggestionItem(w, e => {
        e.stopPropagation();
        e.preventDefault();

        // แทนที่คำ — ดูว่าเป็น input หรือ contentEditable
        if (input && currentWord) {
          const start = input.selectionStart;
          const wordStart = input.value.lastIndexOf(currentWord, start - 1);
          if (wordStart !== -1) {
            input.setRangeText(
              w,
              wordStart,
              wordStart + currentWord.length,
              "end"
            );
            input.focus();
            input.dispatchEvent(new Event("input", { bubbles: true }));
          }
        } else if (sel) {
          replaceSelection(sel, w);
        }

        setTimeout(() => hideActionBubbles(), 0);
      });

      // ปรับสีถ้าระบุ
      if (color) {
        chip.style.backgroundColor = color;
        chip.onmouseover = () => (chip.style.background = color);
        chip.onmouseout = () => (chip.style.background = color);
      }
      row.appendChild(chip);
    });

    section.appendChild(row);
    return section;
  };

  // ── เพิ่ม Section: Spell Check (สีเขียว) ──
  if (uniqueOriginal.length > 0) {
    spellBubble.appendChild(
      createSection("Spell Checking", uniqueOriginal, "#22c55e")
    );
  }

  // ── เพิ่ม Section: Language Switch (สีแดง) ──
  if (uniqueConverted.length > 0) {
    // Separator (ถ้ามีทั้ง 2 section)
    if (uniqueOriginal.length > 0) {
      const sep = document.createElement("div");
      sep.style.height = "1px";
      sep.style.width = "100%";
      sep.style.background = "#444";
      spellBubble.appendChild(sep);
    }
    spellBubble.appendChild(
      createSection("Lang Switch", uniqueConverted, "#ef4444")
    );
  }

  // ── วางตำแหน่ง bubble ──
  let rect;
  if (input) {
    const r = input.getBoundingClientRect();
    rect = { left: r.left + 10, bottom: r.bottom };
  } else if (sel) {
    rect = { left: sel.rect.left, bottom: sel.rect.bottom };
  }

  if (rect) {
    spellBubble.style.left = rect.left + window.scrollX + "px";
    spellBubble.style.top = rect.bottom + window.scrollY + 6 + "px";
    spellBubble.style.display = "flex";
  }

  // Auto-hide
  clearTimeout(spellBubbleHideTimeout);
  spellBubbleHideTimeout = setTimeout(() => {
    if (spellBubble) spellBubble.style.display = "none";
  }, BUBBLE_AUTO_HIDE);
}
