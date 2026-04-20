"""Adapter exposing the existing DesktopHelperWindow implementation.
This file keeps a thin wrapper around the legacy `desktop_app.py` window
so the rest of the refactor can import from a clean module path.
"""

from desktop_app import DesktopHelperWindow as DesktopHelperWindow  # re-export

__all__ = ["DesktopHelperWindow"]
