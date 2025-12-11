import ctypes
import sys
import os
from pathlib import Path
from ctypes import wintypes
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMainWindow
import secrets
import string



MUSIC_DIR_PATH = default_music_path = os.path.join(Path.home(), "Music")

AURIX_DIR_PATH = os.path.join(Path.home(), ".aurix")
COVER_DIR_PATH = os.path.join(AURIX_DIR_PATH, "cvr")
DATABASE_PATH = os.path.join(AURIX_DIR_PATH, "aurix.db")


os.makedirs(COVER_DIR_PATH, exist_ok=True)

def gen_unique_id(existing_ids, length=12):
    chars = string.ascii_letters + string.digits
    
    while True:
        new_id = ''.join(secrets.choice(chars) for _ in range(length))
        if new_id not in existing_ids:
            return new_id


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",     wintypes.HWND),
        ("message",  wintypes.UINT),
        ("wParam",   wintypes.WPARAM),
        ("lParam",   wintypes.LPARAM),
        ("time",     wintypes.DWORD),
        ("pt",       wintypes.POINT),
    ]


class MediaKeys(QObject):
    onPlayPause = pyqtSignal()
    onPlayNext = pyqtSignal()
    onPlayPrevious = pyqtSignal()

    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)

        self.parent_obj = parent

        self.user32 = ctypes.windll.user32

        self.WM_HOTKEY = 0x0312

        # Virtual-Key codes for media keys
        self.VK_MEDIA_NEXT_TRACK  = 0xB0
        self.VK_MEDIA_PREV_TRACK  = 0xB1
        self.VK_MEDIA_PLAY_PAUSE  = 0xB3
        self.MOD_NOREPEAT = 0x4000


    def register(self):
        hwnd = int(self.parent_obj.winId())
        self._hwnd = hwnd
       
        if not self.user32.RegisterHotKey(hwnd, 100, self.MOD_NOREPEAT, self.VK_MEDIA_PLAY_PAUSE):
            print("Failed to register PLAY/PAUSE hotkey")

        if not self.user32.RegisterHotKey(hwnd, 101, self.MOD_NOREPEAT, self.VK_MEDIA_NEXT_TRACK):
            print("Failed to register NEXT hotkey")

        if not self.user32.RegisterHotKey(hwnd, 102, self.MOD_NOREPEAT, self.VK_MEDIA_PREV_TRACK):
            print("Failed to register PREV hotkey")


    def nativeEvent(self, eventType, message):

        if eventType == "windows_generic_MSG":
            # message can be sip.voidptr / int / whatever → get address
            msg = MSG.from_address(int(message))

            if msg.message == self.WM_HOTKEY:
                hotkey_id = msg.wParam

                if hotkey_id == 100:
                    self.onPlayPause.emit()

                elif hotkey_id == 101:
                    self.onPlayNext.emit()

                elif hotkey_id == 102:
                    self.onPlayPrevious.emit()

        # must return (handled: bool, result: int)
        return False, 0



    def unregister(self):
        # Must match ids used above
        self.user32.UnregisterHotKey(self._hwnd, 100)
        self.user32.UnregisterHotKey(self._hwnd, 101)
        self.user32.UnregisterHotKey(self._hwnd, 102)


def get_music_path(paths: list = []):
    paths.append(MUSIC_DIR_PATH)
    return paths

def make_title_path(title: str = None) -> str:
    if title is None:
        raise ValueError("Title can't have \"None\" Value. It must a \"str\"")
    
    not_include = ' <>:"/\\|?*'+"'"
    title_path = ""

    for w in title:
        if w in not_include:
            if title_path[-1:] != " ":
                title_path += " "
        else:
            title_path += w

    return title_path

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

def format_views(count: int) -> str:
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    elif count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    else:
        return str(count)


if __name__ == "__main__":
    print(format_views(477126150))