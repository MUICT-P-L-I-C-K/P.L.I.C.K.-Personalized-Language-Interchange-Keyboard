import sys
import os
import atexit
from pathlib import Path
import ctypes

# Add workspace root to path for imports
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Set Qt environment variables
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_SCALE_FACTOR", "1")
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.window=false")

from PySide6.QtCore import Qt, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from desktop_app import DesktopHelperWindow, create_tray

# Prefer ICO for taskbar (Windows renders it sharper), fall back to PNG
ICON_ICO = ROOT / "PLICK_ICON.ico"
ICON_PNG = ROOT / "PLICK_ICON.png"
ICON_PATH = ICON_ICO if ICON_ICO.exists() else ICON_PNG


def set_taskbar_icon():
    """Tell Windows to associate this process with our App User Model ID
    so the taskbar shows the correct PLICK icon instead of the Python icon."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PLICK.App")
    except Exception:
        pass


def main():
    set_taskbar_icon()

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))

    window = DesktopHelperWindow()

    # Keep window always on top of all other applications
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
    window.show()
    window.raise_()
    window.activateWindow()

    tray = create_tray(app, window)
    _ = tray
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
