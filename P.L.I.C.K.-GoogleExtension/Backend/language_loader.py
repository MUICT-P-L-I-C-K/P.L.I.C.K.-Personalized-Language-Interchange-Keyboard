"""
language_loader.py — โหลด Language Tools (ตัวตรวจภาษา)

ไฟล์นี้รับผิดชอบการโหลด tools ที่ใช้ตรวจสอบภาษา:
  1. LanguageTool (en-US) — ตรวจสะกดภาษาอังกฤษ
  2. LanguageTool (th)    — ตรวจสะกดภาษาไทย (ถ้ามี)
  3. Thai Dictionary      — คลังคำภาษาไทยจาก PyThaiNLP

การโหลดจะทำครั้งเดียวตอนเริ่ม server (startup)
ถ้าโหลดไม่สำเร็จจะ fallback อย่างปลอดภัย (graceful degradation)
"""

import language_tool_python
from pythainlp.corpus import get_corpus
from pythainlp.corpus.common import thai_words as get_thai_words


# =============================================================================
# LanguageTool Instances
# =============================================================================

# LanguageTool สำหรับภาษาอังกฤษ (ใช้ตรวจ spelling + grammar)
lt_en = None

# LanguageTool สำหรับภาษาไทย (อาจไม่มี — ไม่ใช่ทุก version รองรับ)
lt_th = None


def load_language_tools() -> None:
    """
    โหลด LanguageTool instances สำหรับทั้ง 2 ภาษา
    ถ้าโหลดไม่ได้จะ set เป็น None (ไม่ crash)
    """
    global lt_en, lt_th

    print("[INFO] Initializing LanguageTool...")

    # โหลด English LanguageTool
    try:
        lt_en = language_tool_python.LanguageTool('en-US')
        print("[OK] LanguageTool (en-US) loaded")
    except Exception as e:
        print(f"[ERROR] Error loading LanguageTool (en-US): {e}")
        lt_en = None

    # โหลด Thai LanguageTool (optional — อาจไม่รองรับ)
    try:
        lt_th = language_tool_python.LanguageTool('th')
        print("[OK] LanguageTool (th) loaded")
    except Exception as e:
        print(f"[WARN] Thai LanguageTool not available: {e}")
        lt_th = None


# =============================================================================
# Thai Dictionary (คลังคำภาษาไทย)
# =============================================================================

# set ของคำไทยทั้งหมดที่รู้จัก (ใช้ตรวจว่าคำอยู่ใน dictionary หรือไม่)
thai_words: set = set()


def load_thai_dictionary() -> None:
    """
    โหลดคลังคำภาษาไทยจาก PyThaiNLP corpus
    ลองหลาย corpus name เพราะ version ต่างกันอาจใช้ชื่อต่างกัน
    
    ลำดับการลอง:
      1. "thai_icu_words" (corpus ใหญ่)
      2. "thai_words" (corpus สำรอง)
      3. ใช้ spell module เป็น fallback
    """
    global thai_words

    print("[INFO] Loading Thai dictionary...")

    try:
        # วิธีหลัก: ใช้ thai_words() function (เสถียรที่สุด)
        thai_words = set(get_thai_words())
        print(f"[OK] Thai dictionary loaded ({len(thai_words)} words)")
    except Exception:
        try:
            # Fallback 1: ลอง corpus ไฟล์
            thai_words = set(get_corpus("thai_icu_words"))
            print(f"[OK] Thai dictionary loaded via corpus ({len(thai_words)} words)")
        except Exception:
            try:
                thai_words = set(get_corpus("thai_words"))
                print(f"[OK] Thai dictionary loaded via corpus ({len(thai_words)} words)")
            except Exception:
                thai_words = set()
                print("[WARN] Thai dictionary could not be loaded")

    # เพิ่มคำที่ใช้บ่อยแต่อาจไม่อยู่ใน corpus
    _add_common_thai_words()


# คำไทยที่ใช้บ่อยมาก — เพิ่มเข้าไปเผื่อ corpus ไม่ครบ
COMMON_THAI_WORDS = {
    "สวัสดี", "ขอบคุณ", "คิดถึง", "รักษา", "สบายดี", "กินข้าว", "ไปเที่ยว",
    "ทำงาน", "เรียน", "นอน", "กิน", "ดื่ม", "เดิน", "วิ่ง", "พูด", "ฟัง",
    "อ่าน", "เขียน", "ดู", "ซื้อ", "ขาย", "ให้", "รับ", "ส่ง", "มา", "ไป",
    "อยู่", "มี", "เป็น", "ได้", "ต้อง", "จะ", "แล้ว", "อีก", "ก็", "และ",
    "หรือ", "แต่", "ถ้า", "เมื่อ", "ที่", "ซึ่ง", "อัน", "คน", "สิ่ง", "เรื่อง",
    "วัน", "เวลา", "บ้าน", "รถ", "เงิน", "งาน", "ที่นี่", "ตรงนี้", "อะไร", "ใคร",
    "ทำไม", "อย่างไร", "เท่าไหร่", "ผัดไทย", "ผัดไท", "ต้มยำ", "ส้มตำ",
}


def _add_common_thai_words() -> None:
    """เพิ่มคำไทยที่ใช้บ่อยเข้า dictionary"""
    global thai_words
    if thai_words is not None:
        thai_words.update(COMMON_THAI_WORDS)
    else:
        thai_words = COMMON_THAI_WORDS.copy()
    print(f"[OK] Added {len(COMMON_THAI_WORDS)} common Thai words")


# =============================================================================
# Initialization (โหลดทุกอย่างทีเดียว)
# =============================================================================

def initialize_all() -> None:
    """
    เรียกตอน server เริ่มต้น — โหลด LanguageTool + Thai dictionary
    """
    load_language_tools()
    load_thai_dictionary()
    print("[OK] Server initialized")


def get_health_status() -> dict:
    """
    ตรวจสถานะของ language tools ทั้งหมด
    ใช้สำหรับ health check endpoint
    """
    return {
        "language_tool_en": lt_en is not None,
        "language_tool_th": lt_th is not None,
        "thai_dictionary_size": len(thai_words) if thai_words else 0,
    }
