"""Settings persistence service.
Handles reading/writing settings.json in the workspace root.
"""
import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).parent.parent / "settings.json"


def load_settings():
    default = {
        "shortcut": True,
        "shortcutKey": "Ctrl+Shift+C",
        "autoDetect": True,
        "autoLangSwitch": True,
        "correction": False,
        "sound": True,
        "volume": 50,
    }
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                raw = json.load(f)
                if isinstance(raw, dict) and 'settings' in raw:
                    s = raw.get('settings')
                else:
                    s = raw
                out = default.copy()
                if s:
                    out.update(s)
                return out
        except Exception:
            return default
    return default


def save_settings(settings: dict):
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump({'settings': settings}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
