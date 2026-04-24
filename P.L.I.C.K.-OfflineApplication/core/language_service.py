"""Small language helper wrappers."""
from Backend import nlp_core


def is_mostly_thai(text: str) -> bool:
    return nlp_core.is_mostly_thai(text)
