"""Clipboard-based strategy: safe fallback that uses copy/paste to read and replace selection."""
import time
import pyperclip
from pynput import keyboard
from .text_access_strategy import TextAccessStrategy


class ClipboardStrategy(TextAccessStrategy):
    def __init__(self):
        self._kb = keyboard.Controller()

    def get_selected_text(self) -> str:
        saved = pyperclip.paste()
        try:
            # simulate copy
            self._kb.press(keyboard.Key.ctrl)
            self._kb.press('c')
            self._kb.release('c')
            self._kb.release(keyboard.Key.ctrl)
            time.sleep(0.12)
            return pyperclip.paste()
        finally:
            pyperclip.copy(saved)

    def replace_selection(self, replacement: str) -> bool:
        # Use clipboard to paste replacement; non-atomic and potentially destructive for IME
        saved = pyperclip.paste()
        try:
            pyperclip.copy(replacement)
            time.sleep(0.05)
            self._kb.press(keyboard.Key.ctrl)
            self._kb.press('v')
            self._kb.release('v')
            self._kb.release(keyboard.Key.ctrl)
            time.sleep(0.05)
            return True
        finally:
            pyperclip.copy(saved)
