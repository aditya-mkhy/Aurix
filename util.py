import ctypes
import sys
import os

def format_time(seconds: int) -> str:
    seconds = int(seconds)
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)

    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def trim_text(text: str, max_length: int = 25) -> str:
    if len(text) <= max_length:
        return text

    cut = text[:max_length - 3]

    # try to avoid cutting mid-word
    if " " in cut:
        cut = cut[:cut.rfind(" ")]

    return cut + "..."


def is_mp3(path: str):
    return os.path.splitext(path)[1].lower() == ".mp3"

def dark_title_bar(window):
    """Enable immersive dark mode title bar on Windows 10+."""
    if sys.platform != "win32":
        return  # only works on Windows

    hwnd = int(window.winId())  # get native window handle

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20   # for newer builds
    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19  # for older builds

    value = ctypes.c_int(1)

    # try attribute 20 first, if it fails then try 19
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
    except Exception:
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except Exception:
            # silently ignore if OS doesn't support it
            pass


if __name__ == "__main__":
    print(format_time(4000))