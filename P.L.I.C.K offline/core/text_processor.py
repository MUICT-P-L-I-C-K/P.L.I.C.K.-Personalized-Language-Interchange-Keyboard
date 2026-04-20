"""Text processing wrappers that delegate to the existing backend.
"""
from Backend import nlp_core


def convert_text(text: str, to_lang: str) -> str:
    return nlp_core.convert_keyboard(text, to_lang)


def is_mostly_thai(text: str) -> bool:
    return nlp_core.is_mostly_thai(text)


def detect_mistake(word: str, lang: str) -> dict:
    return nlp_core.detect_lang_mistake_core(word, lang)
