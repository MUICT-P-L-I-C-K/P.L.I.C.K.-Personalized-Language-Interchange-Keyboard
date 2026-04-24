document.addEventListener("DOMContentLoaded", () => {
  // --- Elements ---
  const shortcutToggle = document.getElementById("shortcutToggle");
  const shortcutKeyInput = document.getElementById("shortcutKey");
  const autoDetectToggle = document.getElementById("autoDetectToggle");
  const correctionToggle = document.getElementById("correctionToggle");
  const soundToggle = document.getElementById("soundToggle");
  const volumeSlider = document.getElementById("volumeSlider");
  const volumeValue = document.getElementById("volumeValue");
  const saveBtn = document.getElementById("savebutton");
  const defaultBtn = document.getElementById("defaultbutton");
  const langToggle = document.getElementById("langToggle");

  // --- Default Settings ---
  const defaultSettings = {
    shortcut: true,
    shortcutKey: "Alt+Plus",
    autoDetect: false,
    correction: false,
    sound: true,
    volume: 50
  };

  const translations = {
    en: {
      title: "P.L.I.C.K. Setting",
      labelShortcut: "Manual Language Switching",
      tipShortcut: "Enable and set a custom keyboard shortcut to quickly toggle the extension.",
      labelSetKey: "Set Key",
      tipSetKey: "Click inside the box and press your preferred shortcut keys.",
      labelAutoDetect: "Automatic Language Switching",
      tipAutoDetect: "Automatically detect typing mistakes while you write.",
      labelCorrection: "Spell Checking",
      tipCorrection: "Show suggested corrections for detected mistakes.",
      labelSound: "Sound Alert",
      tipSound: "Play a sound notification when a mistake is detected or corrected.",
      save: "Confirm",
      reset: "Default Setting"
    },
    th: {
      title: "P.L.I.C.K. Setting",
      labelShortcut: "การสลับภาษาด้วยตนเอง",
      tipShortcut: "เปิด/ปิดการสลับภาษา เลือกข้อความแล้วกดปุ่มลัดเพื่อแปลงจากไทยเป็นอังกฤษ หรือในทางกลับกัน",
      labelSetKey: "เลือกปุ่มลัด",
      tipSetKey: "กดไปที่กล่องแล้วกดปุ่มที่ต้องการเพื่อตั้งปุ่มลัดใหม่",
      labelAutoDetect: "การสลับภาษาอัตโนมัติ",
      tipAutoDetect: "เปิด/ปิดการตรวจจับข้อผิดพลาดในการพิมพ์ขณะที่คุณเขียน",
      labelCorrection: "การตรวจสอบการสะกดคำ",
      tipCorrection: "แสดงข้อแนะนำในการแก้ไขสำหรับคำที่พบข้อผิดพลาด",
      labelSound: "การแจ้งเตือนด้วยเสียง",
      tipSound: "เล่นเสียงเตือนเมื่อมีการตรวจพบข้อผิดพลาดหรือการแก้ไข",
      save: "ยืนยัน",
      reset: "คืนค่าเริ่มต้น"
    }
  };

  // --- Language functions ---
  function setLanguage(lang) {
    const t = translations[lang];
    document.getElementById("title").innerText = t.title;
    document.getElementById("labelShortcut").innerText = t.labelShortcut;
    document.getElementById("tipShortcut").innerText = t.tipShortcut;
    document.getElementById("labelSetKey").innerText = t.labelSetKey;
    document.getElementById("tipSetKey").innerText = t.tipSetKey;
    document.getElementById("labelAutoDetect").innerText = t.labelAutoDetect;
    document.getElementById("tipAutoDetect").innerText = t.tipAutoDetect;
    document.getElementById("labelCorrection").innerText = t.labelCorrection;
    document.getElementById("tipCorrection").innerText = t.tipCorrection;
    document.getElementById("labelSound").innerText = t.labelSound;
    document.getElementById("tipSound").innerText = t.tipSound;
    saveBtn.innerText = t.save;
    defaultBtn.innerText = t.reset;
  }

  function loadLanguage() {
    chrome.storage.local.get(["lang"], (res) => {
      const lang = res.lang || "en";
      setLanguage(lang);
      if (langToggle) {
        langToggle.checked = lang === "th"; // checked = Thai, unchecked = English
      }
    });
  }

  if (langToggle) {
    langToggle.addEventListener("change", (e) => {
      const lang = e.target.checked ? "th" : "en";
      setLanguage(lang);
      chrome.storage.local.set({ lang });
    });
  }

  // --- Shortcut key capture (Physical keyboard based) ---
  shortcutKeyInput.addEventListener("keydown", (e) => {
    e.preventDefault();
    let keys = [];
    if (e.ctrlKey) keys.push("Ctrl");
    if (e.shiftKey) keys.push("Shift");
    if (e.altKey) keys.push("Alt");

    // Use keyboard code (physical position) instead of key value
    // This works regardless of input language (Thai/English)
    const codeMap = {
      "KeyA": "A", "KeyB": "B", "KeyC": "C", "KeyD": "D", "KeyE": "E",
      "KeyF": "F", "KeyG": "G", "KeyH": "H", "KeyI": "I", "KeyJ": "J",
      "KeyK": "K", "KeyL": "L", "KeyM": "M", "KeyN": "N", "KeyO": "O",
      "KeyP": "P", "KeyQ": "Q", "KeyR": "R", "KeyS": "S", "KeyT": "T",
      "KeyU": "U", "KeyV": "V", "KeyW": "W", "KeyX": "X", "KeyY": "Y",
      "KeyZ": "Z",
      "Digit0": "0", "Digit1": "1", "Digit2": "2", "Digit3": "3", "Digit4": "4",
      "Digit5": "5", "Digit6": "6", "Digit7": "7", "Digit8": "8", "Digit9": "9",
      "Equal": "Plus", "Minus": "Minus", "BracketLeft": "[", "BracketRight": "]",
      "Semicolon": ";", "Quote": "'", "Comma": ",", "Period": ".", "Slash": "/",
      "Backslash": "\\", "NumpadAdd": "Plus", "Space": "Space"
    };

    const keyName = codeMap[e.code] || e.code;

    if (!["Control", "Shift", "Alt"].includes(keyName)) {
      keys.push(keyName);
    }
    shortcutKeyInput.value = keys.join("+");
  });

  // --- Load/Save Settings ---
  function loadSettings() {
    chrome.storage.local.get(["settings"], (res) => {
      const s = res.settings || defaultSettings;
      shortcutToggle.checked = s.shortcut ?? defaultSettings.shortcut;
      shortcutKeyInput.value = s.shortcutKey ?? ""; // show blank if null
      autoDetectToggle.checked = s.autoDetect ?? defaultSettings.autoDetect;
      correctionToggle.checked = s.correction ?? defaultSettings.correction;
      soundToggle.checked = s.sound ?? defaultSettings.sound;
      volumeSlider.value = s.volume ?? defaultSettings.volume;
      volumeValue.innerText = volumeSlider.value;
    });
  }

  function saveSettings() {
    const s = {
      shortcut: shortcutToggle.checked,
      shortcutKey: shortcutKeyInput.value.trim() === "" ? null : shortcutKeyInput.value,
      autoDetect: autoDetectToggle.checked,
      correction: correctionToggle.checked,
      sound: soundToggle.checked,
      volume: parseInt(volumeSlider.value, 10)
    };
    chrome.storage.local.set({ settings: s });
  }

  // Volume slider change
  volumeSlider.addEventListener("input", (e) => {
    volumeValue.innerText = e.target.value;
  });

  saveBtn.addEventListener("click", () => {
    saveSettings();
    window.close();
  });

  defaultBtn.addEventListener("click", () => {
    shortcutToggle.checked = defaultSettings.shortcut;
    shortcutKeyInput.value = defaultSettings.shortcutKey;
    autoDetectToggle.checked = defaultSettings.autoDetect;
    correctionToggle.checked = defaultSettings.correction;
    soundToggle.checked = defaultSettings.sound;
    volumeSlider.value = defaultSettings.volume;
    volumeValue.innerText = defaultSettings.volume;
    chrome.storage.local.set({ settings: defaultSettings }); // instantly save defaults
  });

  loadLanguage();
  loadSettings();
});
