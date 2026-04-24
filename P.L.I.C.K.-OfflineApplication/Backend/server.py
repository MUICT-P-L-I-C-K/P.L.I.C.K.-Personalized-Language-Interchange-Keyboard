from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import asyncio

from nlp_core import (
    executor,
    english_suggestions,
    thai_suggestions,
    word_in_dict,
    detect_lang_mistake_core,
)

# -----------------------
# APP
# -----------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------
# REQUEST MODELS
# ---------
class SpellCheckRequest(BaseModel):
    text: str
    language: str

class DictCheckRequest(BaseModel):
    word: str
    language: str

#
# All NLP / dictionary helpers now live in nlp_core and are imported above.

# ---------
# API ENDPOINTS
# ---------

@app.get("/")
async def health():
    """Health check"""
    return {"status": "ok"}

@app.post("/spell-check")
async def spell_check(req: SpellCheckRequest):
    """Fast spell checking with caching"""
    text = req.text.strip()

    if not text:
        return {"correction": text, "suggestions": []}

    loop = asyncio.get_event_loop()
    
    if req.language == "th":
        return await loop.run_in_executor(executor, thai_suggestions, text)
    elif req.language == "en":
        return await loop.run_in_executor(executor, english_suggestions, text)

    return {"correction": text, "suggestions": []}

# -----------------------
# API: DETECT LANGUAGE SWITCHING ERROR (Full detection with keyboard conversion)
# -----------------------
def get_spell_suggestions_sync(word: str, language: str) -> List[str]:
    """Get spell suggestions synchronously"""
    if language == "en":
        result = english_suggestions(word)
        return result.get("suggestions", [])
    else:
        result = thai_suggestions(word)
        return result.get("suggestions", [])

@app.post("/detect-lang-mistake")
async def detect_lang_mistake(req: DictCheckRequest):
    """
    Full language mistake detection with keyboard conversion:
    
    Flow:
    1. Check if word exists in detected language dict
       - If found → word is correct (mistake_type: "correct")
    2. If not found → get spell suggestions for detected language
       - If similar words found → it's a typo (mistake_type: "typo")
    3. If no similar → convert keyboard layout & check opposite language
       - If converted word found → wrong language (mistake_type: "wrong_language")
    4. If converted not found → get spell suggestions for converted word
       - If similar found → wrong language + typo (mistake_type: "wrong_language_typo")
    5. If nothing found → gibberish (mistake_type: "gibberish")
    
    Returns:
    {
        "is_mistake": bool,
        "mistake_type": "correct" | "typo" | "wrong_language" | "wrong_language_typo" | "gibberish",
        "correct_language": "en" | "th",
        "original_word": str,
        "converted_word": str | None,
        "suggestions": list[str]
    }
    """
    # Delegate to shared core logic so extension and desktop app stay in sync.
    return detect_lang_mistake_core(req.word, req.language)

# -----------------------
# API: CHECK WORD IN SPECIFIC DICTIONARY
# -----------------------
@app.post("/check-word-in-dict")
async def check_word_dict(req: DictCheckRequest):
    """Check if a word exists in a specific language dictionary (cached)"""
    word = req.word.strip()
    
    loop = asyncio.get_event_loop()
    exists = await loop.run_in_executor(executor, word_in_dict, word, req.language)
    
    return {"word": word, "language": req.language, "exists": exists}



# -----------------------
# RUN SERVER
# -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
