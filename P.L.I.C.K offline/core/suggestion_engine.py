"""Suggestion engine wrappers around backend suggestion logic."""
from Backend import nlp_core


def get_suggestions(word: str, lang: str):
    return nlp_core.detect_lang_mistake_core(word, lang).get('suggestions', [])
