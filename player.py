import os
from pygame import mixer
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QListWidgetItem, 
    QListWidget, QListView, QAbstractItemView, QMenu, 
    QSizePolicy, 
)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QFontMetrics, QPainterPath, QIcon

from helper import LocalFilesLoader, get_mp3_metadata
from util import is_mp3
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize


class PlayerEngine:
    # (title, subtitle, total_time, )
    setTrackInfo = pyqtSignal(str)

    def __init__(self):
        self._current_path = None
        self._is_paused = False
        self._channels = None
        self._freq = None
        self._out_dev = None
        self._volume = 0.8

        self._init_mixer(freq=48000, channels=2, out_dev="default")


    def _init_mixer(self, freq=48000, channels=2, out_dev="default"):
        if not (freq != self._freq or channels != self._channels or out_dev != self._out_dev):
            # everything is same as previous init.. pass
            return
        
        mixer.quit() # remove prev init
        self._freq = freq
        self._channels = channels
        self._out_dev = out_dev

        if out_dev != "default":
            mixer.init(devicename=self._out_dev, frequency=self._freq, channels = self._channels)

        else:
            mixer.init(frequency=freq, channels=channels)

        # set the prevous or default volume
        mixer.music.set_volume(self._volume)



    def play(self, path:str, out_dev = None):
        if not os.path.isfile(path):
            raise ValueError(f"Path not exists or it's a directory.")
        
        if not is_mp3(path):
            raise ValueError(f"Path must be a mp3 file path not this : {path}")

        meta = get_mp3_metadata(path)
        channels = meta["channels"]
        freq = meta["sample_rate"]
        duration = meta["duration"]

        title = meta["title"] 
        publisher = meta["publisher"] 
        artist = meta["artist"]
        album = meta["album"]

        # init mixer according to the file
        if out_dev is None:
            out_dev = self._out_dev

        self._init_mixer(freq=freq, channels=channels, out_dev=out_dev)

        # load music
        self._current_path = path
        mixer.music.load(path)

        # emit setTrackInfo
        self.setTrackInfo.emit(title, publisher, duration, meta["cover"])

        # play...
        mixer.music.play(loops=-1)
        self._is_paused = False


    def pause(self):
        if not self._is_paused:
            mixer.music.pause()
            self._is_paused = True
        else:
            mixer.music.unpause()
            self._is_paused = False


    def stop(self):
        mixer.music.stop()
        self._is_paused = False

    def set_volume(self, vol: float):
        vol = max(0.0, min(1.0, float(vol)))
        mixer.music.set_volume(vol)
        self._volume = vol # to re-init

    def is_playing(self) -> bool:
        return mixer.music.get_busy() and not self._is_paused


if __name__ == "__main__":
    pl = PlayerEngine()
