import ctypes
import sys

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