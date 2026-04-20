"""Simple sound service wrapper."""
import winsound


def play_beep(volume: int = 50, freq: int = 800, duration_ms: int = 120):
    # winsound doesn't accept volume; keep freq/duration configurable
    try:
        winsound.Beep(freq, duration_ms)
    except Exception:
        pass
