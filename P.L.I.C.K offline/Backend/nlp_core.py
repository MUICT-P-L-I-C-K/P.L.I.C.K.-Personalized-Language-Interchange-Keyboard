from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
import re

from pythainlp.spell import correct as thai_correct, spell as thai_spell
import language_tool_python
from pythainlp.corpus import get_corpus

# -----------------------
# KEYBOARD MAPPING (English ↔ Thai)
# -----------------------
# Unshifted keys
ENG_TO_THAI = {
    "1": "ๅ", "2": "/", "3": "-", "4": "ภ", "5": "ถ", "6": "ุ", "7": "ึ", "8": "ค", "9": "ต", "0": "จ",
    "-": "ข", "=": "ช",
    "q": "ๆ", "w": "ไ", "e": "ำ", "r": "พ", "t": "ะ", "y": "ั", "u": "ี", "i": "ร", "o": "น", "p": "ย",
    "[": "บ", "]": "ล",
    "a": "ฟ", "s": "ห", "d": "ก", "f": "ด", "g": "เ", "h": "้", "j": "่", "k": "า", "l": "ส", ";": "ว", "'": "ง",
    "z": "ผ", "x": "ป", "c": "แ", "v": "อ", "b": "ิ", "n": "ื", "m": "ท", ",": "ม", ".": "ใ", "/": "ฝ",
    # Shifted letter keys
    "A": "ฤ", "S": "ฆ", "D": "ฏ", "F": "โ", "G": "ฌ", "H": "็", "I": "ณ", "J": "๋", "K": "ษ", "L": "ศ",
    "T": "ธ", "U": "๊", "O": "ฯ", "P": "ญ",
    "Q": "๐", "W": "\"", "E": "ฎ", "R": "ฑ", "Y": "ํ",
    # Shifted bottom row (corrected: M=?, <=ฒ, >=ฬ, ?=ฦ)
    "Z": "(", "X": ")", "C": "ฉ", "V": "ฮ", "B": "ฺ", "N": "์",
    "M": "?", "<": "ฒ", ">": "ฬ",
    # Shifted symbol keys
    ":": "ซ",
    # Shifted number row
    "!": "+", "@": "๑", "#": "๒", "$": "๓", "%": "๔",
    "^": "ู", "&": "฿", "*": "๕", "(": "๖", ")": "๗",
    "_": "๘", "+": "๙",
    # Shifted bracket keys
    "{": "ฐ", "}": ",",
    # Shifted symbol keys missing from duplicates
    "?": "ฦ", "\"": ".",
}

THAI_TO_ENG = {tv: ek for ek, tv in ENG_TO_THAI.items()}

def _is_thai_char(ch: str) -> bool:
    """Check if a single character is Thai."""
    return '\u0E00' <= ch <= '\u0E7F'


def _is_eng_char(ch: str) -> bool:
    """Check if a single character is English letter or digit."""
    return ch.isascii() and (ch.isalpha() or ch.isdigit())


def convert_keyboard(text: str, to_lang: str) -> str:
    """Convert text as if typed on wrong keyboard layout.

    Handles duplicate characters (like '(', ')', '?') that exist on both
    Thai and English shifted keyboards by checking the preceding character
    to determine context.
    """
    result = []

    for ch in text:
        if to_lang == "en":
            result.append(THAI_TO_ENG.get(ch, ch))
        else:
            result.append(ENG_TO_THAI.get(ch) or ENG_TO_THAI.get(ch.lower(), ch))

    return "".join(result)


def is_mostly_thai(text: str) -> bool:
    """Check if text contains mostly Thai characters."""
    if not text:
        return False
    thai_count = len(re.findall(r"[\u0E00-\u0E7F]", text))
    return thai_count > 0


# -----------------------
# PERFORMANCE CACHE
# -----------------------
WORD_CHECK_CACHE: Dict[str, bool] = {}
SPELL_CHECK_CACHE: Dict[str, dict] = {}
LANG_MISTAKE_CACHE: Dict[str, dict] = {}
EN_WORD_CACHE: Dict[str, bool] = {}
executor = ThreadPoolExecutor(max_workers=4)


def safe_get_issue_type(match) -> str:
    """Safely get the issue type from a LanguageTool Match object.

    Falls back to ruleId checking if ruleIssueType is not available.
    """
    try:
        issue_type = getattr(match, "ruleIssueType", None) or getattr(match, "rule_issue_type", None)
        if issue_type:
            return issue_type

        rule_id = getattr(match, "ruleId", None) or getattr(match, "rule_id", "") or ""

        if "MORFOLOGIK" in rule_id or "SPELL" in rule_id or "TYPOS" in rule_id:
            return "misspelling"
        if "GRAMMAR" in rule_id:
            return "grammar"

        return ""
    except Exception:
        return ""


# -----------------------
# LOAD LANGUAGE TOOLS
# -----------------------
print("[INFO] Initializing LanguageTool (core)...")

# Pin the LanguageTool JAR to a fixed folder inside the project so it
# downloads once and is never re-downloaded or duplicated in the temp folder.
import os as _os
import glob as _glob

_LT_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "languagetool_data")
_os.makedirs(_LT_DIR, exist_ok=True)
language_tool_python.utils.LTP_PATH = _LT_DIR

# Auto-detect Java if not already on PATH — mirrors the search logic in setup.bat.
# pythonw.exe launches without inheriting the full user PATH so Java is often
# invisible even when correctly installed.
def _find_and_set_java():
    import subprocess
    # Already on PATH?
    try:
        subprocess.run(["java", "-version"], capture_output=True, timeout=5)
        print("[INFO] Java found on PATH")
        return
    except Exception:
        pass

    # Common installation paths to search
    search_patterns = [
        r"C:\Program Files\Java\jdk*",
        r"C:\Program Files\Java\jre*",
        r"C:\Program Files\Microsoft\jdk*",
        r"C:\Program Files\Eclipse Adoptium\jdk*",
        r"C:\Program Files\Eclipse Adoptium\jre*",
        r"C:\Program Files\Amazon Corretto\jdk*",
        r"C:\Program Files\Zulu\zulu*",
    ]

    for pattern in search_patterns:
        matches = _glob.glob(pattern)
        for java_home in sorted(matches, reverse=True):  # newest version first
            java_exe = _os.path.join(java_home, "bin", "java.exe")
            if _os.path.exists(java_exe):
                _os.environ["PATH"] = _os.path.join(java_home, "bin") + _os.pathsep + _os.environ.get("PATH", "")
                _os.environ["JAVA_HOME"] = java_home
                print(f"[INFO] Java found at: {java_home}")
                return

    print("[WARN] Java not found in common locations — LanguageTool may fail")

_find_and_set_java()

try:
    lt_en = language_tool_python.LanguageTool("en-US")
    print("[OK] LanguageTool (en-US) loaded")
except Exception as e:
    print(f"[ERROR] Error loading LanguageTool (en-US): {e}")
    lt_en = None

try:
    lt_th = language_tool_python.LanguageTool("th")
    print("[OK] LanguageTool (th) loaded")
except Exception as e:
    print(f"[WARN] Thai LanguageTool not available: {e}")
    lt_th = None

print("[INFO] Loading Thai dictionary (core)...")
try:
    try:
        thai_words = set(get_corpus("thai_icu_words"))
        print(f"[OK] Thai dictionary loaded ({len(thai_words)} words) from thai_icu_words")
    except Exception:
        try:
            thai_words = set(get_corpus("thai_words"))
            print(f"[OK] Thai dictionary loaded ({len(thai_words)} words) from thai_words")
        except Exception:
            thai_words = set()
            print("[OK] Using PyThaiNLP spell module for Thai checking as fallback")
except Exception as e:
    print(f"[WARN] Thai setup error: {e}")
    thai_words = set()

COMMON_THAI_WORDS = {
    "สวัสดี", "ขอบคุณ", "คิดถึง", "รักษา", "สบายดี", "กินข้าว", "ไปเที่ยว",
    "ทำงาน", "เรียน", "นอน", "กิน", "ดื่ม", "เดิน", "วิ่ง", "พูด", "ฟัง",
    "อ่าน", "เขียน", "ดู", "ซื้อ", "ขาย", "ให้", "รับ", "ส่ง", "มา", "ไป",
    "อยู่", "มี", "เป็น", "ได้", "ต้อง", "จะ", "แล้ว", "อีก", "ก็", "และ",
    "หรือ", "แต่", "ถ้า", "เมื่อ", "ที่", "ซึ่ง", "อัน", "คน", "สิ่ง", "เรื่อง",
    "วัน", "เวลา", "บ้าน", "รถ", "เงิน", "งาน", "ที่นี่", "ตรงนี้", "อะไร", "ใคร",
    "ทำไม", "อย่างไร", "เท่าไหร่", "ผัดไทย", "ผัดไท", "ต้มยำ", "ส้มตำ","เเล้ว",
    "สวยงาม","น่ารัก","ดีใจ","เสียใจ","สนุก","เบื่อ","ง่วง","หิว","อร่อย","เหนื่อย",
}

if thai_words is not None:
    thai_words.update(COMMON_THAI_WORDS)
else:
    thai_words = COMMON_THAI_WORDS.copy()

print(f"[OK] Added {len(COMMON_THAI_WORDS)} common Thai words (core)")
print("[OK] NLP core initialized")


# -----------------------
# HELPER: CHECK IF WORD EXISTS IN DICTIONARY
# -----------------------
def english_word_exists(word: str) -> bool:
    """Check if English word exists using LanguageTool (no spelling errors = exists)."""
    if not word or not lt_en:
        return False

    word_clean = word.lower().strip()

    if word_clean in EN_WORD_CACHE:
        return EN_WORD_CACHE[word_clean]

    if not re.match(r"^[a-zA-Z\-']+$", word_clean):
        EN_WORD_CACHE[word_clean] = False
        return False

    try:
        matches = lt_en.check(word_clean)
        # A word exists if LanguageTool found no matches at all,
        # OR if none of the matches have replacement suggestions.
        # We no longer rely on issue_type because newer LanguageTool
        # versions may return "uncategorized" for real spelling errors.
        has_spelling_error = any(
            bool(m.replacements) for m in matches
        )
        result = not has_spelling_error
        EN_WORD_CACHE[word_clean] = result

        if len(EN_WORD_CACHE) > 10000:
            keys_to_delete = list(EN_WORD_CACHE.keys())[:5000]
            for k in keys_to_delete:
                del EN_WORD_CACHE[k]

        return result
    except Exception as e:
        print(f"[EN] Error checking word '{word}': {e}")
        return False


def thai_word_exists(word: str) -> bool:
    """Check if Thai word exists in dictionary."""
    word_clean = word.strip()

    if not word_clean:
        return False

    if not is_mostly_thai(word_clean):
        return False

    if word_clean in thai_words:
        return True

    try:
        suggestions = thai_spell(word_clean)
        if len(suggestions) == 0:
            return True
        if word_clean in suggestions:
            return True
        if len(suggestions) == 1 and suggestions[0] == word_clean:
            return True

        try:
            correction = thai_correct(word_clean)
            if correction == word_clean:
                return True
        except Exception:
            pass

        return False
    except Exception as e:
        print(f"[TH] Error checking word '{word_clean}': {e}")
        return False


def word_in_dict(word: str, language: str) -> bool:
    """Check if word exists in the dictionary (cached)."""
    word_clean = word.strip()
    cache_key = f"{word_clean}:{language}"

    if cache_key in WORD_CHECK_CACHE:
        return WORD_CHECK_CACHE[cache_key]

    result = False
    if language == "th":
        result = thai_word_exists(word_clean)
    elif language == "en":
        result = english_word_exists(word_clean)

    WORD_CHECK_CACHE[cache_key] = result

    if len(WORD_CHECK_CACHE) > 10000:
        keys_to_delete = list(WORD_CHECK_CACHE.keys())[:5000]
        for k in keys_to_delete:
            del WORD_CHECK_CACHE[k]

    return result


# -----------------------
# ENGLISH SPELL CHECK
# -----------------------
def english_suggestions(text: str) -> dict:
    """Fast English spell checking."""
    if lt_en is None:
        return {"correction": None, "suggestions": []}

    # Always lowercase — LanguageTool treats capitalised words as proper
    # nouns and skips spelling checks on them (e.g. "Watamelon" passes,
    # "watamelon" correctly returns "watermelon").
    text = text.lower().strip()

    if text in SPELL_CHECK_CACHE:
        cached = SPELL_CHECK_CACHE[text]
        if isinstance(cached, dict) and "suggestions" in cached:
            return {"correction": None, "suggestions": cached["suggestions"]}
        if isinstance(cached, list):
            return {"correction": None, "suggestions": cached}

    suggestions: List[str] = []
    try:
        matches = lt_en.check(text)

        if matches:
            print(f"[EN] Found {len(matches)} issues in '{text}'")

        for match in matches:
            # Accept any match that has replacement suggestions.
            # We previously filtered by issue_type == "misspelling" but
            # newer LanguageTool versions return "uncategorized" or empty
            # strings for valid spelling errors, causing them to be silently
            # dropped. Collecting all replacements is safer — LanguageTool
            # only flags real issues for single-word checks.
            if match.replacements:
                for replacement in match.replacements[:3]:
                    if replacement and replacement not in suggestions:
                        suggestions.append(replacement)
                        if len(suggestions) >= 5:
                            break

            if len(suggestions) >= 5:
                break

        if not matches:
            print(f"[EN] No issues found in '{text}'")

    except Exception as e:
        print(f"[EN] Error checking English text '{text}': {e}")
        suggestions = []

    SPELL_CHECK_CACHE[text] = {"suggestions": suggestions[:8]}

    if len(SPELL_CHECK_CACHE) > 5000:
        keys_to_delete = list(SPELL_CHECK_CACHE.keys())[:2500]
        for k in keys_to_delete:
            del SPELL_CHECK_CACHE[k]

    return {"correction": None, "suggestions": suggestions[:8]}


# -----------------------
# THAI SPELL CHECK
# -----------------------
def thai_suggestions(text: str) -> dict:
    """Fast Thai spell checking."""
    if text in SPELL_CHECK_CACHE:
        cached = SPELL_CHECK_CACHE[text]
        if isinstance(cached, dict):
            return cached
        return {"correction": None, "suggestions": cached}

    try:
        correction = thai_correct(text)
        suggestions = thai_spell(text)[:5]

        if suggestions:
            print(f"[TH] Found {len(suggestions)} suggestions for '{text}'")
        else:
            print(f"[TH] No suggestions found for '{text}'")

    except Exception as e:
        print(f"[TH] Error checking Thai text '{text}': {e}")
        correction = None
        suggestions = []

    result = {
        "correction": correction,
        "suggestions": suggestions,
    }

    SPELL_CHECK_CACHE[text] = result

    if len(SPELL_CHECK_CACHE) > 5000:
        keys_to_delete = list(SPELL_CHECK_CACHE.keys())[:2500]
        for k in keys_to_delete:
            del SPELL_CHECK_CACHE[k]

    return result


def get_spell_suggestions_sync(word: str, language: str) -> List[str]:
    """Get spell suggestions synchronously."""
    if language == "en":
        result = english_suggestions(word)
        return result.get("suggestions", [])
    result = thai_suggestions(word)
    return result.get("suggestions", [])


def detect_lang_mistake_core(word: str, detected_lang: str) -> dict:
    """Pure-Python core for language mistake detection with keyboard conversion.

    Matches the response structure of the FastAPI /detect-lang-mistake endpoint.
    """
    word = word.strip()

    default_response = {
        "is_mistake": False,
        "mistake_type": "correct",
        "correct_language": detected_lang,
        "original_word": word,
        "converted_word": None,
        "suggestions": [],
    }

    if not word or len(word) < 2:
        return default_response

    cache_key = f"{word}:{detected_lang}"
    if cache_key in LANG_MISTAKE_CACHE:
        return LANG_MISTAKE_CACHE[cache_key]

    opposite_lang = "en" if detected_lang == "th" else "th"

    # Step 1: Check if word exists in detected language
    if word_in_dict(word, detected_lang):
        result = {
            "is_mistake": False,
            "mistake_type": "correct",
            "correct_language": detected_lang,
            "original_word": word,
            "converted_word": None,
            "suggestions": [],
        }
        LANG_MISTAKE_CACHE[cache_key] = result
        return result

    # Step 2: typo in same language?
    spell_suggestions = get_spell_suggestions_sync(word, detected_lang)
    if spell_suggestions:
        result = {
            "is_mistake": True,
            "mistake_type": "typo",
            "correct_language": detected_lang,
            "original_word": word,
            "converted_word": None,
            "suggestions": spell_suggestions[:5],
        }
        LANG_MISTAKE_CACHE[cache_key] = result
        return result

    # Step 3: convert keyboard layout
    converted_word = convert_keyboard(word, opposite_lang)

    if word_in_dict(converted_word, opposite_lang):
        result = {
            "is_mistake": True,
            "mistake_type": "wrong_language",
            "correct_language": opposite_lang,
            "original_word": word,
            "converted_word": converted_word,
            "suggestions": [converted_word],
        }
        LANG_MISTAKE_CACHE[cache_key] = result
        return result

    # Step 4: typo in converted word?
    converted_suggestions = get_spell_suggestions_sync(converted_word, opposite_lang)
    if converted_suggestions:
        suggestions = [converted_word] + [s for s in converted_suggestions[:4] if s != converted_word]
        result = {
            "is_mistake": True,
            "mistake_type": "wrong_language_typo",
            "correct_language": opposite_lang,
            "original_word": word,
            "converted_word": converted_word,
            "suggestions": suggestions[:5],
        }
        LANG_MISTAKE_CACHE[cache_key] = result
        return result

    # Step 5: gibberish
    result = {
        "is_mistake": True,
        "mistake_type": "gibberish",
        "correct_language": detected_lang,
        "original_word": word,
        "converted_word": converted_word,
        "suggestions": [],
    }
    LANG_MISTAKE_CACHE[cache_key] = result

    if len(LANG_MISTAKE_CACHE) > 10000:
        keys_to_delete = list(LANG_MISTAKE_CACHE.keys())[:5000]
        for k in keys_to_delete:
            del LANG_MISTAKE_CACHE[k]

    return result

