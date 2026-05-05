/**
 * keyboard-map.js — แผนที่ปุ่มกด (Keyboard Layout Mapping)
 *
 * ไฟล์นี้เก็บตาราง mapping ระหว่าง keyboard layout อังกฤษ (QWERTY)
 * กับไทย (Kedmanee) และฟังก์ชันแปลงข้อความ
 *
 * ใช้เมื่อ: ผู้ใช้พิมพ์ผิดภาษา เช่น พิมพ์ "สวัสดี" ตอน layout เป็นอังกฤษ
 *          จะได้ "aw;cofu" → ต้องแปลงกลับเป็น "สวัสดี"
 *
 * ฟังก์ชันที่ export (global):
 *   - engToThai    : object mapping อังกฤษ→ไทย
 *   - thaiToEng    : object mapping ไทย→อังกฤษ
 *   - convertText  : แปลงข้อความเต็ม (ดูตัวอักษรแต่ละตัวว่าเป็นภาษาอะไร)
 *   - normalizeQuotes : ทำให้ quote marks เป็นมาตรฐาน
 *   - isMostlyThai : ตรวจว่าข้อความมีตัวอักษรไทยหรือไม่
 */

// =============================================================================
// Mapping Tables
// =============================================================================

// English → Thai (ปุ่มเดียวกันบน keyboard, layout ต่างกัน)
const engToThai = {
  // ─── แถวตัวเลข (Number row) ───
  "`": "_", "1": "ๅ", "2": "/", "3": "-", "4": "ภ", "5": "ถ",
  "6": "ุ", "7": "ึ", "8": "ค", "9": "ต", "0": "จ",
  "-": "ข", "=": "ช",
  // ─── แถวตัวเลข + Shift ───
  // ตัด ๔, ๖, ๗, ๘, ๙ ออกเพื่อให้เครื่องหมาย % ( ) _ + สลับไปกลับได้แม่นยำขึ้นเมื่อติดกับตัวอักษร
  "~": "%", "!": "+", "@": "๑", "#": "๒", "$": "๓",
  "^": "ู", "&": "฿", "*": "๕",

  // ─── แถวบน (QWERTY) ───
  "q": "ๆ", "w": "ไ", "e": "ำ", "r": "พ", "t": "ะ",
  "y": "ั", "u": "ี", "i": "ร", "o": "น", "p": "ย",
  "[": "บ", "]": "ล", "\\": "ฃ",
  // ─── แถวบน + Shift ───
  "Q": "๐", "W": "\"", "E": "ฎ", "R": "ฑ", "T": "ธ",
  "Y": "ํ", "U": "๊", "I": "ณ", "O": "ฯ", "P": "ญ",
  "{": "ฐ", "}": ",", "|": "ฅ",

  // ─── แถวกลาง (ASDF / Home row) ───
  "a": "ฟ", "s": "ห", "d": "ก", "f": "ด", "g": "เ",
  "h": "้", "j": "่", "k": "า", "l": "ส", ";": "ว", "'": "ง",
  // ─── แถวกลาง + Shift ───
  "A": "ฤ", "S": "ฆ", "D": "ฏ", "F": "โ", "G": "ฌ",
  "H": "็", "J": "๋", "K": "ษ", "L": "ศ", ":": "ซ", "\"": ".",

  // ─── แถวล่าง (ZXCV) ───
  "z": "ผ", "x": "ป", "c": "แ", "v": "อ", "b": "ิ",
  "n": "ื", "m": "ท", ",": "ม", ".": "ใ", "/": "ฝ",
  // ─── แถวล่าง + Shift ───
  // ตัด ฦ ออกเพื่อให้เครื่องหมาย ? สลับไปกลับได้แม่นยำขึ้น
  "Z": "(", "X": ")", "C": "ฉ", "V": "ฮ", "B": "ฺ",
  "N": "์", "M": "?", "<": "ฒ", ">": "ฬ",
};

// Thai → English (reverse ของ engToThai)
const thaiToEng = {};
for (const [eng, thai] of Object.entries(engToThai)) {
  thaiToEng[thai] = eng;
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * ตรวจว่าข้อความมีตัวอักษรไทย (Unicode 0E00-0E7F) หรือไม่
 * ใช้ตัดสินว่าผู้ใช้กำลังพิมพ์ภาษาอะไร
 *
 * @param {string} text - ข้อความที่ต้องการตรวจ
 * @returns {boolean} true ถ้ามีตัวอักษรไทย
 */
function isMostlyThai(text) {
  return text ? /[\u0E00-\u0E7F]/.test(text) : false;
}

/**
 * แปลง smart quotes / fancy quotes ให้เป็น ASCII quotes มาตรฐาน
 * ทำไมต้องทำ: บาง OS/เว็บ จะเปลี่ยน ' เป็น ' หรือ " เป็น " อัตโนมัติ
 * ซึ่งทำให้ mapping table หาไม่เจอ
 *
 * @param {string} text - ข้อความที่อาจมี smart quotes
 * @returns {string} ข้อความที่แปลงเป็น ASCII quotes แล้ว
 */
function normalizeQuotes(text) {
  if (!text) return text;
  return text.replace(/[''‛❛❜＇]/g, "'").replace(/[""‟❝❞〝〞＂]/g, '"');
}

/**
 * แปลงข้อความจาก layout หนึ่งไปอีก layout
 *
 * Logic: ดูตัวอักษรทีละตัว
 *   - ถ้าเป็นภาษาไทย → แปลง Thai→English
 *   - ถ้าเป็นภาษาอังกฤษ → แปลง English→Thai
 *   - ถ้าเป็นสัญลักษณ์ → ใช้บริบทจากตัวอักษรก่อนหน้า
 *
 * @param {string} text - ข้อความต้นฉบับ
 * @returns {string} ข้อความที่แปลงแล้ว
 */
function convertText(text) {
  text = normalizeQuotes(text);
  const chars = [...text];
  const overallThai = isMostlyThai(text);
  let lastLang = null; // ติดตามภาษาของตัวอักษรล่าสุดที่ไม่ใช่สัญลักษณ์

  return chars.map((ch, index) => {
    const isThaiKey = ch in thaiToEng;
    const isEngKey = ch in engToThai;

    // 1) Not in keyboard mapping at all (e.g., spaces, newlines, emojis)
    if (!isThaiKey && !isEngKey) {
      lastLang = null; // Reset context across word boundaries
      return ch;
    }

    // 2) Unambiguously Thai
    if (isThaiKey && !isEngKey) {
      lastLang = "th";
      return thaiToEng[ch];
    }

    // 3) Unambiguously English
    if (isEngKey && !isThaiKey) {
      lastLang = "en";
      return engToThai[ch];
    }

    // 4) Ambiguous keys (e.g., -, _, /, ", ,, ., (, ), ?, %, +)
    let ctx = lastLang;

    // ถ้าไม่รู้ว่าตัวหน้าคืออะไร ให้ดูตัวหลังที่ระบุภาษาได้ชัดเจน
    if (!ctx) {
      for (let i = index + 1; i < chars.length; i++) {
        const nextCh = chars[i];
        const nextIsThai = nextCh in thaiToEng;
        const nextIsEng = nextCh in engToThai;

        if (nextIsThai && !nextIsEng) {
          ctx = "th";
          break;
        }
        if (nextIsEng && !nextIsThai) {
          ctx = "en";
          break;
        }
      }
    }

    // ถ้าหาตัวหน้าและตัวหลังไม่เจอเลย ให้ใช้ overallThai
    ctx = ctx || (overallThai ? "th" : "en");
    lastLang = ctx;

    if (ctx === "th") return thaiToEng[ch];
    return engToThai[ch];
  }).join("");
}
