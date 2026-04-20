"""Refactored desktop app using modular services and strategies.
This module now delegates to core/, external/, and services/ modules.
"""
import sys
from pathlib import Path
import time
from typing import Optional, List, Tuple

from pynput import keyboard
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSystemTrayIcon,
    QMenu,
    QCheckBox,
    QLineEdit,
    QSlider,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QCursor

# Import modular services
from core import text_processor, language_service, suggestion_engine
from external.clipboard_strategy import ClipboardStrategy
from external.uia_strategy import UIAStrategy
from services import settings_service, sound_service

ICON_PATH = Path(__file__).parent / "PLICK_ICON.png"


class HotkeyListener(QThread):
    """Global hotkey listener thread."""
    hotkey_pressed = Signal(str)  # "convert" or "check"
    typed_delimiter = Signal()
    
    def __init__(self):
        super().__init__()
        self.listener = None
        self.suppress = False
    
    def run(self):
        pressed = set()

        def on_press(key):
            try:
                if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    pressed.add('ctrl')
                elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                    pressed.add('shift')
                elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
                    pressed.add('alt')
            except Exception:
                pass

        def on_release(key):
            try:
                if hasattr(key, 'char') and key.char:
                    ch = key.char.lower()
                    if ch == 'c' and 'ctrl' in pressed and 'shift' in pressed:
                        self.hotkey_pressed.emit("convert")
                    elif ch == 'k' and 'ctrl' in pressed and 'shift' in pressed:
                        self.hotkey_pressed.emit("check")

                if not self.suppress:
                    if key == keyboard.Key.space or key == keyboard.Key.enter:
                        self.typed_delimiter.emit()
                    elif hasattr(key, 'char') and key.char:
                        try:
                            if key.char in {',','.', ';',':','!','?','(',')','[',']','{','}','"',"'"}:
                                self.typed_delimiter.emit()
                        except Exception:
                            pass

                if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    pressed.discard('ctrl')
                elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                    pressed.discard('shift')
                elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
                    pressed.discard('alt')
            except Exception:
                pass

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            self.listener = listener
            listener.join()
    
    def stop(self):
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass


class PlainTextEdit(QTextEdit):
    """QTextEdit that always pastes as plain text, stripping all rich formatting."""
    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text())


class SpellCheckWorker(QThread):
    """Runs spell checking in the background so the UI never freezes."""
    progress    = Signal(str)           # status updates while running
    result_item = Signal(object)        # emits each suggestion dict/str as found
    finished    = Signal(list, list)    # all_suggestions, all_statuses when done

    def __init__(self, text: str, detected_lang: str,
                 do_convert: bool, do_spell: bool):
        super().__init__()
        self.text          = text
        self.detected_lang = detected_lang
        self.do_convert    = do_convert
        self.do_spell      = do_spell
        self._cancelled    = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        import re
        from Backend import nlp_core

        all_suggestions = []
        all_statuses    = []
        converted       = None

        # ── Keyboard conversion ───────────────────────────────────────────
        if self.do_convert:
            target_lang = "en" if self.detected_lang == "th" else "th"
            converted = text_processor.convert_text(self.text, target_lang)
            if converted and converted != self.text:
                all_suggestions.append(f"[Converted] {converted}")
                all_statuses.append(f"Converted to {target_lang.upper()}")

        # ── Spell check word by word ──────────────────────────────────────
        if self.do_spell:
            # Split text into Thai and non-Thai segments first, then
            # tokenize each segment appropriately.
            # This handles mixed text like "ผลไม้ Strawberry สายพันธุ์"
            segments = re.split(r'([\u0E00-\u0E7F]+)', self.text)
            tokens = []
            for seg in segments:
                if not seg.strip():
                    continue
                if re.search(r'[\u0E00-\u0E7F]', seg):
                    # Thai segment — use pythainlp tokenizer
                    try:
                        from pythainlp.tokenize import word_tokenize
                        tokens.extend(word_tokenize(seg, engine="newmm",
                                                    keep_whitespace=False))
                    except Exception:
                        tokens.append(seg)
                else:
                    # Non-Thai segment — split on whitespace/punctuation
                    tokens.extend(re.split(r'[\s/\\|,;:]+', seg))

            # Strip edge punctuation and deduplicate
            unique_words = list(dict.fromkeys(
                re.sub(r'^[^\w\u0E00-\u0E7F]+|[^\w\u0E00-\u0E7F]+$', '', w)
                for w in tokens
            ))

            has_issues = False
            for i, clean_word in enumerate(unique_words):
                if self._cancelled:
                    break
                if not clean_word or len(clean_word) < 2:
                    continue

                self.progress.emit(
                    f"Checking word {i+1}/{len(unique_words)}: {clean_word}…"
                )

                # Detect this specific word's language by its script
                word_is_thai = bool(re.search(r'[\u0E00-\u0E7F]', clean_word))
                word_lang = "th" if word_is_thai else "en"

                if word_lang == "en":
                    result = nlp_core.english_suggestions(clean_word.lower())
                else:
                    result = nlp_core.thai_suggestions(clean_word)

                for suggestion in result.get("suggestions", []):
                    item_data = {
                        "source_word": clean_word,
                        "suggestion":  suggestion,
                        "lang":        self.detected_lang,
                    }
                    if item_data not in all_suggestions:
                        all_suggestions.append(item_data)
                        has_issues = True

            if has_issues:
                all_statuses.append(
                    f"Spell check: issues found in {self.detected_lang.upper()}"
                )
            elif not converted:
                all_statuses.append("correct")   # sentinel for "looks correct"

        self.finished.emit(all_suggestions, all_statuses)


class DesktopHelperWindow(QMainWindow):
    """Main desktop helper window using modular services."""

    def _safe_pyperclip_paste(self):
        # Always call from main thread. If not, try to CoInitialize.
        try:
            import pyperclip
            try:
                return pyperclip.paste()
            except Exception as e:
                # Try to CoInitialize if on a worker thread
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    return pyperclip.paste()
                except Exception:
                    print(f"[ERROR] Clipboard paste failed: {e}")
                    return ""
        except Exception as e:
            print(f"[ERROR] pyperclip import failed: {e}")
            return ""

    def _safe_pyperclip_copy(self, text):
        # Always call from main thread. If not, try to CoInitialize.
        try:
            import pyperclip
            try:
                pyperclip.copy(text)
            except Exception as e:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    pyperclip.copy(text)
                except Exception:
                    print(f"[ERROR] Clipboard copy failed: {e}")
        except Exception as e:
            print(f"[ERROR] pyperclip import failed: {e}")

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setWindowTitle("P.L.I.C.K. Personalized Language Interchange Keyboard")
        self.settings = settings_service.load_settings()

        # Setup UI
        self._setup_ui()

        # Connect settings updates
        self._connect_settings_signals()

        # Initialize keyboard controller for auto-detect operations
        self._kb_controller = keyboard.Controller()

        # Suggestion popup reference
        self._suggestion_popup = None

        # Background spell-check worker (replaced on each Check click)
        self._spell_worker = None

        # Start hotkey listener
        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.hotkey_pressed.connect(self.on_hotkey)
        self.hotkey_listener.typed_delimiter.connect(self.on_typed_delimiter)
        self.hotkey_listener.start()

    def _setup_ui(self):
        """Setup UI components."""
        central = QWidget(self)
        self.setCentralWidget(central)

        self.text_edit = PlainTextEdit(self)
        self.text_edit.setPlaceholderText("Type or paste text here...")

        self.status_label = QLabel("Ready | Hotkeys: Ctrl+Shift+C (Convert) | Ctrl+Shift+K (Check)", self)
        self.status_label.setWordWrap(True)

        convert_btn = QPushButton("Convert Language", self)
        check_btn = QPushButton("Check Spelling / Language", self)
        paste_btn = QPushButton("Paste", self)
        copy_btn = QPushButton("Copy", self)
        clear_btn = QPushButton("Clear", self)

        convert_btn.clicked.connect(self.on_convert_clicked)
        check_btn.clicked.connect(self.on_check_clicked)
        paste_btn.clicked.connect(self.on_paste_clicked)
        copy_btn.clicked.connect(self.on_copy_clicked)
        clear_btn.clicked.connect(self.on_clear_clicked)

        # Both features are always enabled — no checkboxes needed.
        # The rest of the code calls .isChecked() on these; a simple lambda wrapper keeps that working.
        class _AlwaysTrue:
            def isChecked(self): return True
        self.spell_check_enabled = _AlwaysTrue()
        self.auto_lang_switch = _AlwaysTrue()

        # Hidden stubs so the rest of the code that references these attributes won't crash
        self.shortcut_enabled = QCheckBox()
        self.shortcut_enabled.setChecked(self.settings.get('shortcut', True))
        self.shortcut_enabled.hide()
        self.shortcut_key_input = QLineEdit(self)
        self.shortcut_key_input.hide()
        self.sound_toggle = QCheckBox()
        self.sound_toggle.setChecked(self.settings.get('sound', True))
        self.sound_toggle.hide()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.settings.get('volume', 50))
        self.volume_slider.hide()
        self.volume_value_label = QLabel(str(self.volume_slider.value()), self)
        self.volume_value_label.hide()

        self.suggestions_list = QListWidget(self)
        self.suggestions_list.itemClicked.connect(self.apply_suggestion)

        # Layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(convert_btn)
        btn_layout.addWidget(check_btn)
        btn_layout.addWidget(paste_btn)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(clear_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("Suggestions:", self))
        layout.addWidget(self.suggestions_list)
        layout.addWidget(self.status_label)

        central.setLayout(layout)

    def _connect_settings_signals(self):
        """Connect UI changes to settings persistence."""
        # spell_check_enabled and auto_lang_switch are always-on stubs, not real widgets.
        self.shortcut_enabled.stateChanged.connect(self._on_settings_changed)
        self.shortcut_key_input.textChanged.connect(self._on_settings_changed)
        self.sound_toggle.stateChanged.connect(self._on_settings_changed)
        self.volume_slider.valueChanged.connect(lambda v: (
            self.volume_value_label.setText(str(v)),
            self._on_settings_changed()
        ))

    def _on_settings_changed(self):
        """Save updated settings."""
        self.settings = {
            'shortcut': self.shortcut_enabled.isChecked(),
            'shortcutKey': self.shortcut_key_input.text() or None,
            'autoLangSwitch': self.auto_lang_switch.isChecked(),
            'spellCheck': self.spell_check_enabled.isChecked(),
            'sound': self.sound_toggle.isChecked(),
            'volume': int(self.volume_slider.value()),
        }
        settings_service.save_settings(self.settings)

    def closeEvent(self, event):
        # Hide to tray instead of closing when user presses X
        event.ignore()
        self.hide()

    def quit_app(self):
        """Actually quit — called only from the tray Quit action."""
        try:
            if hasattr(self, 'hotkey_listener') and self.hotkey_listener:
                self.hotkey_listener.stop()
                self.hotkey_listener.wait(1000)
        except Exception:
            pass
        QApplication.instance().quit()

    def _get_selected_text(self) -> Optional[str]:
        """Get selected text from internal editor."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            return cursor.selectedText()
        text = self.text_edit.toPlainText()
        return text if text.strip() else None

    def _replace_selected_text(self, new_text: str):
        """Replace selected text in internal editor."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.insertText(new_text)
        else:
            self.text_edit.setPlainText(new_text)

    def on_clear_clicked(self):
        """Clear all text in the text box and suggestions list."""
        self.text_edit.clear()
        self.suggestions_list.clear()
        self.status_label.setText("Cleared.")

    def on_paste_clicked(self):
        try:
            import pyperclip
            text = pyperclip.paste()
            self.text_edit.setPlainText(text)
            self.status_label.setText("Pasted from clipboard")
        except Exception as e:
            self.status_label.setText(f"Error pasting: {str(e)}")

    def on_copy_clicked(self):
        try:
            import pyperclip
            text = self.text_edit.toPlainText()
            if text.strip():
                pyperclip.copy(text)
                self.status_label.setText("Copied to clipboard")
            else:
                self.status_label.setText("Nothing to copy")
        except Exception as e:
            self.status_label.setText(f"Error copying: {str(e)}")

    def on_hotkey(self, action: str):
        """Handle global hotkey events."""
        try:
            app = QApplication.instance()
            active = app.activeWindow()
            if active is None or active is not self:
                if action == "convert":
                    self.process_external_convert()
                elif action == "check":
                    self.process_external_check()
                return

            # Fallback: operate on clipboard
            import pyperclip
            text = pyperclip.paste()
            if action == "convert":
                self.on_convert_from_clipboard(text)
            elif action == "check":
                self.on_check_from_clipboard(text)
        except Exception as e:
            self.status_label.setText(f"Hotkey error: {str(e)}")

    def on_convert_from_clipboard(self, text: str):
        """Convert clipboard text."""
        if not text or not text.strip():
            self.status_label.setText("Clipboard is empty")
            return
        
        to_lang = "th" if not language_service.is_mostly_thai(text) else "en"
        converted = text_processor.convert_text(text, to_lang)
        
        import pyperclip
        pyperclip.copy(converted)
        self.status_label.setText(f"✓ Converted & copied to clipboard → {to_lang.upper()}")

    def process_external_convert(self):
        """Process conversion for external app."""
        try:
            import pyperclip
            saved = pyperclip.paste()

            # Try UIA first, fallback to clipboard
            text = self.uia_strategy.get_selected_text()

            if not text:

                text = self.clipboard_strategy.get_selected_text()

            
            if not text or not text.strip():
                self.status_label.setText("No selection to convert.")
                pyperclip.copy(saved)
                return

            to_lang = "th" if not language_service.is_mostly_thai(text) else "en"
            converted = text_processor.convert_text(text, to_lang)

            if self.auto_lang_switch.isChecked():
                def replace_callback(s):
                    ok = self.uia_strategy.replace_selection(s)
                    if not ok:
                        self.clipboard_strategy.replace_selection(s)
                
                self.show_suggestion_popup([converted], external_replace_callback=replace_callback)
                self.status_label.setText(f"Showing conversion suggestion → {to_lang.upper()}")
            else:

                ok = self.uia_strategy.replace_selection(converted)

                if not ok:

                    self.clipboard_strategy.replace_selection(converted)
                self.status_label.setText(f"✓ Converted selection → {to_lang.upper()}")
            
            pyperclip.copy(saved)
        except Exception as e:
            self.status_label.setText(f"External convert error: {str(e)}")

    def on_check_from_clipboard(self, text: str):
        """Check clipboard text."""
        if not text or not text.strip():
            self.status_label.setText("Clipboard is empty")
            return
        
        words = text.split()
        if not words:
            self.status_label.setText("No words to check")
            return
        
        self.suggestions_list.clear()
        current_word = words[-1]
        detected_lang = "th" if language_service.is_mostly_thai(current_word) else "en"
        
        all_suggestions = []
        all_statuses = []
        
        if self.spell_check_enabled.isChecked():
            result = suggestion_engine.get_suggestions(current_word, detected_lang) or []
            for s in result:
                if s not in all_suggestions:
                    all_suggestions.append(s)
            if result:
                all_statuses.append(f"Spell: found issues")
        
        if self.auto_lang_switch.isChecked():
            target_lang = "en" if detected_lang == "th" else "th"
            converted = text_processor.convert_text(current_word, target_lang)
            if converted and converted != current_word:
                if converted not in all_suggestions:
                    all_suggestions.insert(0, f"[Converted] {converted}")
                
                if self.spell_check_enabled.isChecked():
                    result = suggestion_engine.get_suggestions(converted, target_lang) or []
                    for s in result:
                        if s not in all_suggestions:
                            all_suggestions.append(s)
                    if result:
                        all_statuses.append(f"Converted {target_lang.upper()}: found issues")
        
        if not all_suggestions:
            self.status_label.setText("✓ Looks correct")
            return
        
        status_text = " | ".join(all_statuses) if all_statuses else "Showing suggestions"
        self.status_label.setText(status_text)
        
        for suggestion in all_suggestions:
            item = QListWidgetItem(suggestion)
            item.setData(Qt.UserRole, suggestion.replace("[Converted] ", ""))
            self.suggestions_list.addItem(item)

    def process_external_check(self):
        """Process check for external app."""
        try:
            import pyperclip
            saved = pyperclip.paste()

            # Try UIA first, fallback to clipboard
            text = self.uia_strategy.get_selected_text()

            if not text:

                text = self.clipboard_strategy.get_selected_text()

            
            if not text or not text.strip():

                self.status_label.setText("No selection to check.")
                pyperclip.copy(saved)
                return

            words = text.split()
            if not words:
                self.status_label.setText("No words to check")
                pyperclip.copy(saved)
                return

            current_word = words[-1]

            detected_lang = "th" if language_service.is_mostly_thai(current_word) else "en"


            all_suggestions = []
            all_statuses = []

            if self.spell_check_enabled.isChecked():
                result = suggestion_engine.get_suggestions(current_word, detected_lang) or []

                for s in result:
                    if s not in all_suggestions:
                        all_suggestions.append(s)
                if result:
                    all_statuses.append(f"Spell: found issues")

            if self.auto_lang_switch.isChecked():
                target_lang = "en" if detected_lang == "th" else "th"
                converted = text_processor.convert_text(current_word, target_lang)
                if converted and converted != current_word:
                    if converted not in all_suggestions:
                        all_suggestions.insert(0, f"[Converted] {converted}")
                    if self.spell_check_enabled.isChecked():
                        result = suggestion_engine.get_suggestions(converted, target_lang) or []
                        for s in result:
                            if s not in all_suggestions:
                                all_suggestions.append(s)
                        if result:
                            all_statuses.append(f"Converted {target_lang.upper()}: found issues")

            if not all_suggestions:
                self.status_label.setText("✓ Looks correct")
                pyperclip.copy(saved)
                return

            status_text = " | ".join(all_statuses) if all_statuses else "Showing suggestions"
            self.status_label.setText(status_text)

            app = QApplication.instance()
            active = app.activeWindow()

            if active is None or active is not self:

                def replace_callback(s):
                    ok = self.uia_strategy.replace_selection(s)
                    if not ok:
                        self.clipboard_strategy.replace_selection(s)
                    pyperclip.copy(saved)
                
                self.show_suggestion_popup(all_suggestions, external_replace_callback=replace_callback)

                return

            self.suggestions_list.clear()
            for suggestion in all_suggestions:
                item = QListWidgetItem(suggestion)
                item.setData(Qt.UserRole, suggestion.replace("[Converted] ", ""))
                self.suggestions_list.addItem(item)

            pyperclip.copy(saved)
        except Exception as e:
            self.status_label.setText(f"External check error: {str(e)}")

    def on_typed_delimiter(self):
        """Handle auto-detect on delimiter (non-blocking, clipboard safe)."""
        try:
            app = QApplication.instance()
            active = app.activeWindow()

            if active is None or active is not self:

                return

            if not self.auto_lang_switch.isChecked() and not self.spell_check_enabled.isChecked():
                return

            self.hotkey_listener.suppress = True
            saved = self._safe_pyperclip_paste()

            def after_select_word():
                # Copy selection
                try:
                    self._kb_controller.press(keyboard.Key.ctrl)
                    self._kb_controller.press('c')
                    self._kb_controller.release('c')
                    self._kb_controller.release(keyboard.Key.ctrl)
                except Exception:
                    pass

                QTimer.singleShot(80, after_copy_word)

            def after_copy_word():
                try:
                    word = self._safe_pyperclip_paste()
                    if not word or not word.strip():
                        return

                    current_word = word.strip()
                    detected_lang = "th" if language_service.is_mostly_thai(current_word) else "en"

                    if self.spell_check_enabled.isChecked():
                        result = suggestion_engine.get_suggestions(current_word, detected_lang) or []
                        if result:
                            self.suggestions_list.clear()
                            for s in result:
                                item = QListWidgetItem(s)
                                item.setData(Qt.UserRole, s)
                                self.suggestions_list.addItem(item)

                            if self.sound_toggle.isChecked():
                                sound_service.play_beep(self.volume_slider.value())
                        else:
                            pass
                finally:
                    # Always restore clipboard and unhighlight (Right arrow)
                    try:
                        self._safe_pyperclip_copy(saved)
                    except Exception:
                        pass
                    try:
                        self._kb_controller.press(keyboard.Key.right)
                        self._kb_controller.release(keyboard.Key.right)
                    except Exception:
                        pass
                    self.hotkey_listener.suppress = False

            # Select previous word (simulate keypresses)
            try:
                self._kb_controller.press(keyboard.Key.ctrl)
                self._kb_controller.press(keyboard.Key.shift)
                self._kb_controller.press(keyboard.Key.left)
                self._kb_controller.release(keyboard.Key.left)
                self._kb_controller.release(keyboard.Key.shift)
                self._kb_controller.release(keyboard.Key.ctrl)
            except Exception:
                pass

            # Use QTimer to avoid blocking UI
            QTimer.singleShot(60, after_select_word)

        except Exception:
            try:
                self.hotkey_listener.suppress = False
            except Exception:
                pass

    def show_suggestion_popup(self, suggestions: List[str], external_replace_callback=None):
        """Show floating suggestion popup."""
        try:
            if self._suggestion_popup:
                try:
                    self._suggestion_popup.close()
                except Exception:
                    pass

            popup = QWidget(None, Qt.Tool | Qt.FramelessWindowHint)
            popup.setAttribute(Qt.WA_ShowWithoutActivating)
            popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
            popup.setStyleSheet("background:#ffffe0; border:1px solid #888;")

            listw = QListWidget(popup)
            for s in suggestions:
                item = QListWidgetItem(s)
                listw.addItem(item)

            def on_item_clicked(item):
                text = item.text()
                if external_replace_callback:
                    external_replace_callback(text)
                else:
                    cur = self.text_edit.toPlainText()
                    parts = cur.split()
                    if parts:
                        parts[-1] = text
                        self.text_edit.setPlainText(" ".join(parts))
                popup.hide()

            listw.itemClicked.connect(on_item_clicked)
            listw.setFixedWidth(250)
            listw.setFixedHeight(min(150, 24 * listw.count() + 4))

            popup.resize(listw.width(), listw.height())
            pos = QCursor.pos()
            popup.move(pos.x() + 10, pos.y() + 10)
            popup.show()
            self._suggestion_popup = popup
            
            QTimer.singleShot(8000, lambda: popup.hide())
        except Exception:
            pass

    def on_convert_clicked(self):
        """Handle convert button click.
        
        For mixed-language text (e.g. 'ProjectงานProject'), each segment is
        converted independently based on its own script so Thai chars go → EN
        and English chars go → TH, rather than forcing the whole string one way.
        """
        original = self._get_selected_text()
        if not original:
            self.status_label.setText("No text to convert.")
            return

        import re

        def is_thai_char(ch):
            return '\u0e00' <= ch <= '\u0e7f'

        def is_latin_char(ch):
            return ch.isascii() and ch.isalpha()

        # Split into segments of (thai | latin+apostrophe | other) characters.
        # Apostrophe (') is a valid EN->TH keyboard key (maps to ng/ง) so it
        # must be grouped with Latin chars, not treated as pass-through punctuation.
        segments = re.findall(r"[\u0e00-\u0e7f]+|[A-Za-z0-9']+|[^\u0e00-\u0e7fA-Za-z0-9']+", original)

        converted_parts = []
        langs_used = set()
        for seg in segments:
            if re.fullmatch(r'[\u0e00-\u0e7f]+', seg):
                # Pure Thai segment -> convert to EN
                converted_parts.append(text_processor.convert_text(seg, "en"))
                langs_used.add("EN")
            elif re.fullmatch(r"[A-Za-z0-9']+", seg):
                # Pure Latin/digit/apostrophe segment -> convert to TH
                converted_parts.append(text_processor.convert_text(seg, "th"))
                langs_used.add("TH")
            else:
                # Punctuation / spaces / symbols — keep as-is
                converted_parts.append(seg)

        converted = "".join(converted_parts)
        self._replace_selected_text(converted)
        direction = " & ".join(sorted(langs_used)) if langs_used else "?"
        self.status_label.setText(f"Converted using keyboard layout → {direction}")

    def on_check_clicked(self):
        """Handle check button click — runs spell check in background thread."""
        text = self._get_selected_text()
        if not text or not text.strip():
            self.status_label.setText("No text to check.")
            return

        # Cancel any previous check still running
        if self._spell_worker and self._spell_worker.isRunning():
            self._spell_worker.cancel()
            self._spell_worker.quit()
            self._spell_worker.wait(500)

        self.suggestions_list.clear()
        detected_lang = "th" if language_service.is_mostly_thai(text) else "en"

        self._spell_worker = SpellCheckWorker(
            text          = text,
            detected_lang = detected_lang,
            do_convert    = self.auto_lang_switch.isChecked(),
            do_spell      = self.spell_check_enabled.isChecked(),
        )

        # Show live progress in status bar
        self._spell_worker.progress.connect(self.status_label.setText)

        # When done, populate suggestions list
        def on_done(all_suggestions, all_statuses):
            if "correct" in all_statuses and len(all_statuses) == 1:
                self.status_label.setText("✓ Looks correct.")
                return
            if not all_suggestions and not all_statuses:
                self.status_label.setText("✓ Looks correct.")
                return

            status_text = " | ".join(
                s for s in all_statuses if s != "correct"
            ) or "Showing conversion"
            self.status_label.setText(status_text)

            for suggestion_data in all_suggestions:
                if isinstance(suggestion_data, str):
                    item = QListWidgetItem(suggestion_data)
                    item.setData(Qt.UserRole,
                                 suggestion_data.replace("[Converted] ", ""))
                    self.suggestions_list.addItem(item)
                elif isinstance(suggestion_data, dict):
                    item = QListWidgetItem(suggestion_data["suggestion"])
                    item.setData(Qt.UserRole, suggestion_data)
                    self.suggestions_list.addItem(item)

        self._spell_worker.finished.connect(on_done)
        self.status_label.setText("Checking…")
        self._spell_worker.start()
    def apply_suggestion(self, item: QListWidgetItem):
        """Apply selected suggestion."""
        data = item.data(Qt.UserRole)
        if not data:
            return

        text = self.text_edit.toPlainText()
        if not text:
            return

        # Check if data contains source word info
        if isinstance(data, dict) and "source_word" in data:
            source_word = data["source_word"]
            suggestion = data["suggestion"]
            # Replace the first occurrence of the source word
            new_text = text.replace(source_word, suggestion, 1)
        else:
            # Fallback: treat as simple suggestion
            suggestion = data if isinstance(data, str) else str(data)
            
            # Check if it's a converted text suggestion
            if suggestion.startswith("[Converted] "):
                # Extract the converted text (remove the prefix)
                new_text = suggestion.replace("[Converted] ", "", 1)
            else:
                # Replace last word
                words = text.split()
                if not words:
                    return
                words[-1] = suggestion
                new_text = " ".join(words)
        
        self.text_edit.setPlainText(new_text)
        self.status_label.setText(f"Applied suggestion: {suggestion}")


def create_tray(app: QApplication, window: DesktopHelperWindow) -> QSystemTrayIcon:
    """Create system tray icon and menu."""
    if ICON_PATH.exists():
        tray_icon = QIcon(str(ICON_PATH))
    else:
        tray_icon = QIcon()

    tray = QSystemTrayIcon(tray_icon, app)
    tray.setToolTip("P.L.I.C.K. Language Interchange")

    # Right-click menu
    menu = QMenu()
    show_action = QAction("Show Window", menu)
    quit_action = QAction("Quit", menu)

    def show_window():
        window.showNormal()
        window.activateWindow()
        window.raise_()

    show_action.triggered.connect(show_window)
    quit_action.triggered.connect(window.quit_app)

    menu.addAction(show_action)
    menu.addSeparator()
    menu.addAction(quit_action)

    tray.setContextMenu(menu)

    # Left click → show window | Right click → menu (handled automatically by setContextMenu)
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.Trigger:  # left click
            show_window()

    tray.activated.connect(on_tray_activated)
    tray.show()
    return tray


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # keep running in tray when window is closed
    window = DesktopHelperWindow()
    window.show()          # show on desktop at launch
    window.activateWindow()
    tray = create_tray(app, window)
    _ = tray
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
