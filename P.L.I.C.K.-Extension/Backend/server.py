"""
server.py — P.L.I.C.K. Backend API Server

ไฟล์นี้เป็น entry point ของ backend server
หน้าที่หลัก: รับ HTTP requests จาก Chrome Extension แล้วส่งไปให้ modules ประมวลผล

API Endpoints:
  GET  /                  → Health check (ตรวจว่า server ทำงานอยู่)
  POST /spell-check       → ตรวจสะกดคำ (English/Thai)
  POST /detect-lang-mistake → ตรวจว่าพิมพ์ผิดภาษาหรือไม่
  POST /check-word-in-dict → ตรวจว่าคำอยู่ใน dictionary หรือไม่

Modules ที่ใช้:
  - keyboard_map.py    : แปลง keyboard layout
  - cache_manager.py   : จัดการ cache (thread-safe)
  - language_loader.py : โหลด LanguageTool + Thai dictionary
  - spell_checker.py   : ตรวจสะกดคำ + หา suggestions
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import asyncio

# ── Import จาก modules ภายใน ──
from keyboard_map import convert_keyboard, normalize_quotes
from cache_manager import lang_mistake_cache, start_periodic_cleanup
from language_loader import initialize_all, get_health_status
from spell_checker import (
    word_in_dict,
    english_suggestions,
    thai_suggestions,
    get_spell_suggestions_sync,
)


# =============================================================================
# App Setup
# =============================================================================

app = FastAPI(title="P.L.I.C.K. Server", version="3.3")

# อนุญาต CORS ทุก origin (เพราะ extension เรียกมาจาก background script)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool สำหรับ run blocking functions (LanguageTool, PyThaiNLP)
executor = ThreadPoolExecutor(max_workers=4)


# =============================================================================
# Request Models (โครงสร้างข้อมูลที่ client ส่งมา)
# =============================================================================

class SpellCheckRequest(BaseModel):
    """สำหรับ /spell-check — ส่งข้อความ + ภาษาที่ต้องการตรวจ"""
    text: str
    language: str  # "en" หรือ "th"


class DictCheckRequest(BaseModel):
    """สำหรับ /detect-lang-mistake และ /check-word-in-dict"""
    word: str
    language: str  # "en" หรือ "th"


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def health():
    """
    Health Check — ตรวจว่า server ทำงานอยู่
    คืนสถานะของ language tools ทั้งหมด
    """
    return {"status": "ok", **get_health_status()}


@app.post("/spell-check")
async def spell_check(req: SpellCheckRequest):
    """
    ตรวจสะกดคำ — รับข้อความ + ภาษา แล้วคืนคำแนะนำ
    
    ใช้ ThreadPoolExecutor เพราะ LanguageTool เป็น blocking call
    """
    text = normalize_quotes(req.text.strip())
    if not text:
        return {"correction": text, "suggestions": []}

    loop = asyncio.get_event_loop()

    if req.language == "th":
        return await loop.run_in_executor(executor, thai_suggestions, text)
    elif req.language == "en":
        return await loop.run_in_executor(executor, english_suggestions, text)

    return {"correction": text, "suggestions": []}


@app.post("/detect-lang-mistake")
async def detect_lang_mistake(req: DictCheckRequest):
    """
    ตรวจว่าผู้ใช้พิมพ์ผิดภาษาหรือไม่ (Full detection)
    
    ขั้นตอน:
      1. ตรวจว่าคำเดิมอยู่ใน dictionary ของภาษาที่ตรวจพบ
      2. แปลง keyboard layout ไปภาษาตรงข้าม
      3. ตรวจว่าคำที่แปลงแล้วอยู่ใน dictionary หรือไม่
      4. หาคำแนะนำสำหรับทั้ง 2 ฝั่ง
    
    Returns:
        {
            "is_mistake": bool,
            "mistake_type": "combined",
            "original":  { word, language, exists, suggestions },
            "converted": { word, language, exists, suggestions }
        }
    """
    raw_word = req.word.strip()
    word = normalize_quotes(raw_word)
    detected_lang = req.language

    # ── Default response (ถ้าคำสั้นเกินหรือว่างเปล่า) ──
    default_response = {
        "is_mistake": False,
        "mistake_type": "correct",
        "correct_language": detected_lang,
        "original_word": raw_word,
        "converted_word": None,
        "suggestions": [],
    }

    if not word or len(word) < 2:
        return default_response

    # ── ตรวจ cache ก่อน ──
    cache_key = f"{word}:{detected_lang}"
    cached = lang_mistake_cache.get(cache_key)
    if cached is not None:
        result = cached.copy()
        if "original" in result:
            result["original"] = result["original"].copy()
            result["original"]["word"] = raw_word
        return result

    opposite_lang = "en" if detected_lang == "th" else "th"
    loop = asyncio.get_event_loop()

    # ── Step 1: ตรวจคำเดิมในภาษาที่ตรวจพบ ──
    original_exists = await loop.run_in_executor(
        executor, word_in_dict, word, detected_lang
    )
    original_suggestions = []
    if not original_exists:
        original_suggestions = await loop.run_in_executor(
            executor, get_spell_suggestions_sync, word, detected_lang
        )

    # ── Step 2: แปลง keyboard layout + ตรวจภาษาตรงข้าม ──
    converted_word = convert_keyboard(word, opposite_lang)
    converted_exists = await loop.run_in_executor(
        executor, word_in_dict, converted_word, opposite_lang
    )

    # ── Step 3: หาคำแนะนำสำหรับคำที่แปลงแล้ว ──
    converted_suggestions = await loop.run_in_executor(
        executor, get_spell_suggestions_sync, converted_word, opposite_lang
    )

    # ── สร้าง response ──
    response = {
        "is_mistake": (
            (not original_exists) or
            converted_exists or
            (len(converted_suggestions) > 0)
        ),
        "mistake_type": "combined",
        "original": {
            "word": raw_word,
            "language": detected_lang,
            "exists": original_exists,
            "suggestions": original_suggestions[:5],
        },
        "converted": {
            "word": converted_word,
            "language": opposite_lang,
            "exists": converted_exists,
            "suggestions": converted_suggestions[:5],
        },
    }

    # ── บันทึก cache ──
    lang_mistake_cache.set(cache_key, response.copy())
    return response


@app.post("/check-word-in-dict")
async def check_word_dict(req: DictCheckRequest):
    """ตรวจว่าคำอยู่ใน dictionary ของภาษาที่ระบุ"""
    word = req.word.strip()
    loop = asyncio.get_event_loop()
    exists = await loop.run_in_executor(executor, word_in_dict, word, req.language)
    return {"word": word, "language": req.language, "exists": exists}


# =============================================================================
# Startup
# =============================================================================

# โหลด language tools + dictionary ตอน import
initialize_all()

# เริ่ม cache cleanup ทุก 3 นาที
start_periodic_cleanup(interval_seconds=180)


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
