"""
spell_checker.py — ระบบตรวจสะกดคำ (Spell Checking Engine)

ไฟล์นี้รวมฟังก์ชันตรวจสะกดคำทั้งภาษาอังกฤษและภาษาไทย:

1. ตรวจว่าคำอยู่ใน dictionary (word_in_dict)
   - english_word_exists() → ใช้ LanguageTool ตรวจ
   - thai_word_exists()    → ใช้ PyThaiNLP corpus + spell check

2. หาคำแนะนำ (suggestions)
   - english_suggestions() → แนะนำคำที่ถูกต้องสำหรับภาษาอังกฤษ
   - thai_suggestions()    → แนะนำคำที่ถูกต้องสำหรับภาษาไทย

3. Helper
   - safe_get_issue_type() → อ่านประเภทปัญหาจาก LanguageTool Match อย่างปลอดภัย
   - get_spell_suggestions_sync() → wrapper สำหรับเรียกจาก async code
"""

import re
from typing import List

from pythainlp.spell import correct as thai_correct, spell as thai_spell

from cache_manager import word_check_cache, spell_check_cache, en_word_cache
import language_loader


# =============================================================================
# Helper: อ่านประเภทปัญหาจาก LanguageTool Match
# =============================================================================

def safe_get_issue_type(match) -> str:
    """
    ดึงประเภทปัญหา (issue type) จาก LanguageTool Match object อย่างปลอดภัย
    
    LanguageTool มีหลาย version ที่ใช้ attribute ต่างกัน:
      - match.ruleIssueType (camelCase)
      - match.rule_issue_type (snake_case)
      - match.ruleId (fallback — ดูจาก rule name)
    
    Returns:
        "misspelling" | "grammar" | "" (empty string ถ้าไม่รู้จัก)
    """
    try:
        # ลอง attribute โดยตรง (รองรับทั้ง camelCase และ snake_case)
        issue_type = (
            getattr(match, 'ruleIssueType', None) or
            getattr(match, 'rule_issue_type', None)
        )
        if issue_type:
            return issue_type

        # Fallback: ดูจาก ruleId
        rule_id = (
            getattr(match, 'ruleId', None) or
            getattr(match, 'rule_id', '') or ''
        )
        if 'MORFOLOGIK' in rule_id or 'SPELL' in rule_id or 'TYPOS' in rule_id:
            return 'misspelling'
        if 'GRAMMAR' in rule_id:
            return 'grammar'

        return ''
    except Exception:
        return ''


# =============================================================================
# Word Existence Check (ตรวจว่าคำอยู่ใน dictionary หรือไม่)
# =============================================================================

def english_word_exists(word: str) -> bool:
    """
    ตรวจว่าคำภาษาอังกฤษเป็นคำจริงหรือไม่
    
    วิธีการ: ส่งคำไปให้ LanguageTool ตรวจ
             ถ้าไม่มี spelling error = คำนี้มีอยู่จริง
    
    Args:
        word: คำที่ต้องการตรวจ (เช่น "hello", "teh")
    
    Returns:
        True ถ้าเป็นคำจริง, False ถ้าไม่ใช่
    """
    if not word or not language_loader.lt_en:
        return False

    word_clean = word.lower().strip()

    # ตรวจ cache ก่อน (เร็วกว่า LanguageTool มาก)
    cached = en_word_cache.get(word_clean)
    if cached is not None:
        return cached

    # ต้องเป็นตัวอักษรอังกฤษเท่านั้น (และ hyphen/apostrophe)
    if not re.match(r"^[a-zA-Z\-']+$", word_clean):
        en_word_cache.set(word_clean, False)
        return False

    try:
        matches = language_loader.lt_en.check(word_clean)
        # ไม่มี spelling error = คำนี้ถูกต้อง
        has_spelling_error = any(
            safe_get_issue_type(m) == "misspelling" for m in matches
        )
        result = not has_spelling_error
        en_word_cache.set(word_clean, result)
        return result
    except Exception as e:
        print(f"[EN] Error checking word '{word}': {e}")
        return False


def thai_word_exists(word: str) -> bool:
    """
    ตรวจว่าคำภาษาไทยเป็นคำจริงหรือไม่
    
    วิธีการ (ตามลำดับ):
      1. ตรวจใน corpus (set ของคำไทยทั้งหมด)
      2. ใช้ PyThaiNLP spell check เป็น backup
      3. ลองใช้ thai_correct() สำหรับคำประสม
    """
    word_clean = word.strip()
    if not word_clean:
        return False

    # ต้องมีตัวอักษรไทย
    if not re.search(r'[\u0E00-\u0E7F]', word_clean):
        return False

    # 1. ตรวจใน corpus (เร็วที่สุด ลบส่วน spell_check แบบเก่าที่ช้ามากออกไป)
    if word_clean in language_loader.thai_words:
        return True

    return False


def word_in_dict(word: str, language: str) -> bool:
    """
    ตรวจว่าคำอยู่ใน dictionary ของภาษาที่ระบุ (พร้อม cache)
    
    Args:
        word:     คำที่ต้องการตรวจ
        language: "en" หรือ "th"
    """
    word_clean = word.strip()
    cache_key = f"{word_clean}:{language}"

    # ตรวจ cache
    cached = word_check_cache.get(cache_key)
    if cached is not None:
        return cached

    # ตรวจตามภาษา
    if language == "th":
        result = thai_word_exists(word_clean)
    elif language == "en":
        result = english_word_exists(word_clean)
    else:
        result = False

    word_check_cache.set(cache_key, result)
    return result


# =============================================================================
# Spell Suggestions (หาคำแนะนำ)
# =============================================================================

def english_suggestions(text: str) -> dict:
    """
    ตรวจสะกดภาษาอังกฤษ — คืนคำแนะนำที่ถูกต้อง
    
    ใช้ LanguageTool ตรวจแล้วดึง replacements ออกมา
    จำกัดสูงสุด 8 คำแนะนำ
    
    Returns:
        {"correction": None, "suggestions": ["word1", "word2", ...]}
    """
    if language_loader.lt_en is None:
        return {"correction": None, "suggestions": []}

    # ตรวจ cache
    cached = spell_check_cache.get(text)
    if cached is not None:
        if isinstance(cached, dict) and "suggestions" in cached:
            return {"correction": None, "suggestions": cached["suggestions"]}
        elif isinstance(cached, list):
            return {"correction": None, "suggestions": cached}

    suggestions: List[str] = []
    try:
        matches = language_loader.lt_en.check(text)
        if matches:
            print(f"[EN] Found {len(matches)} issues in '{text}'")

        for match in matches:
            issue_type = safe_get_issue_type(match)
            if issue_type not in ("misspelling", "grammar"):
                continue

            if match.replacements:
                for replacement in match.replacements[:2]:
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

    result = {"suggestions": suggestions[:8]}
    spell_check_cache.set(text, result)
    return {"correction": None, "suggestions": suggestions[:8]}


def thai_suggestions(text: str) -> dict:
    """
    ตรวจสะกดภาษาไทย — คืนคำแก้ไขและคำแนะนำ
    
    ใช้ PyThaiNLP:
      - thai_correct() → คำที่ถูกต้องที่สุด
      - thai_spell()   → รายการคำที่คล้ายกัน
    
    Returns:
        {"correction": "คำที่ถูก", "suggestions": ["คำ1", "คำ2", ...]}
    """
    # ตรวจ cache
    cached = spell_check_cache.get(text)
    if cached is not None:
        if isinstance(cached, dict):
            return cached
        else:
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

    result = {"correction": correction, "suggestions": suggestions}
    spell_check_cache.set(text, result)
    return result


def get_spell_suggestions_sync(word: str, language: str) -> List[str]:
    """
    Wrapper สำหรับเรียก spell suggestions แบบ synchronous
    (ใช้กับ asyncio.run_in_executor)
    
    Args:
        word:     คำที่ต้องการตรวจ
        language: "en" หรือ "th"
    
    Returns:
        รายการคำแนะนำ (list of strings)
    """
    if language == "en":
        result = english_suggestions(word)
    else:
        result = thai_suggestions(word)
    return result.get("suggestions", [])
