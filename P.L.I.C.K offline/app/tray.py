"""Tray creation wrapper.
"""
from desktop_app import create_tray as _create_tray


def create_tray(app, window):
    return _create_tray(app, window)
