"""UI Automation strategy that attempts to read/replace text via pywinauto (safer for many apps).
Returns None if UIA cannot access the control.
"""
import threading
import win32gui
from pywinauto import Desktop
from .text_access_strategy import TextAccessStrategy


class UIAStrategy(TextAccessStrategy):
    def __init__(self):
        self._desktop = None
        self._lock = threading.Lock()

    def _get_desktop(self):
        """Lazy-load desktop with thread-safe access."""
        try:
            return Desktop(backend="uia")
        except Exception:
            return None

    def get_selected_text(self) -> str:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            desktop = self._get_desktop()
            if not desktop:
                return None
            win = desktop.window(handle=hwnd)
            for ctrl_type in ("Edit", "Document", "Pane", "Text"):
                try:
                    elems = win.descendants(control_type=ctrl_type)
                    if elems:
                        w = elems[0]
                        try:
                            val = w.get_value()
                            if val is not None:
                                return val
                        except Exception:
                            try:
                                texts = w.texts()
                                if texts:
                                    return texts[0]
                            except Exception:
                                pass
                except Exception:
                    continue
            return win.window_text()
        except Exception:
            return None

    def replace_selection(self, replacement: str) -> bool:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            desktop = self._get_desktop()
            if not desktop:
                return False
            win = desktop.window(handle=hwnd)
            for ctrl_type in ("Edit", "Document", "Pane", "Text"):
                try:
                    elems = win.descendants(control_type=ctrl_type)
                    if elems:
                        w = elems[0]
                        try:
                            w.set_edit_text(replacement)
                            return True
                        except Exception:
                            try:
                                # as fallback try typing paste (may not succeed)
                                w.type_keys('^v')
                            except Exception:
                                pass
                except Exception:
                    continue
            return False
        except Exception:
            return False
