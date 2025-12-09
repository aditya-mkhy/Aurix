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
from util import is_mp3, MUSIC_DIR_PATH
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt5.QtCore import QObject, pyqtSignal

def get_files():
    music_files = []
    for file in os.listdir(MUSIC_DIR_PATH):
        path = os.path.join(MUSIC_DIR_PATH, file)
        if is_mp3(path):
            music_files.append(path)

    return music_files

def get_track_file(files: list, current_file: str = None, is_back: bool = False):
    if current_file is None:
        return files[0]
    
    try:
        index = files.index(current_file)
    except:
        index = -1

    if is_back:
        index -= 1
    else:
        index += 1

    if index < 0 or index >= len(files):
        index = 0
    
    return files[index]
    

class PlayerEngine(QObject):
    # (title, subtitle, total_time, )
    setTrackInfo = pyqtSignal(str, str, int, QPixmap)
    setPlaying = pyqtSignal(bool)
    setSeekPos = pyqtSignal(int)
    setRepeatMode = pyqtSignal(int)
    broadcastMsg = pyqtSignal(str, str, bool)

    def __init__(self, parent = None):
        super().__init__(parent)

        # variables
        self._current_path = None
        self._is_paused = False
        self._channels = None
        self._freq = None
        self._out_dev = None
        self._volume = 0.8
        self._repeat_mode = 0 # 0=off,1=all,2=one

        # time
        self._timer = QTimer(self)
        self._timer.setInterval(100)   # ~60 FPS (16 ms)
        self._timer.timeout.connect(self._update_position)
        self.elapsed_sec = 0
        self.duration = 0

        self._music_files = get_files()

        self._init_mixer(freq=48000, channels=2, out_dev="default")
        
        QTimer.singleShot(0, self._init_play)


    def _init_play(self):
        self.play(self._music_files[0])
        self.play_toggled()


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

    def set_seek(self, sec: int):
        print(f"Sec --> {sec}")

        # mixer.music.play(1, sec)
        
        try:
            mixer.music.set_pos(sec)
        except:
            mixer.music.play(1, sec)

        self.elapsed_sec = sec * 1000

    def set_repeat_mode(self, value: int):
        if value not in (0, 1, 2):
            return
        print(f"RepeatModeChanged : {value}")
        self._repeat_mode = value
        self.setRepeatMode.emit(self._repeat_mode)

    def next_track(self):
        print("Next track is not implemented...")
        next_file = get_track_file(self._music_files, current_file=self._current_path)
        self.play(next_file)

    def prevoius_track(self):
        print("Prevoius button is clicked...")

        if (self.elapsed_sec //1000) >= 5:
            # Restart current track from beginning
            self.setSeekPos.emit(0) # set the seekbar to 0 pos for smothness
            self.set_seek(0)
            return
        
        prev_file = get_track_file(self._music_files, current_file=self._current_path, is_back=True)
        self.play(prev_file)

     
    def play(self, path:str, out_dev = None):
        if not os.path.isfile(path):
            raise ValueError(f"Path not exists or it's a directory.")
        
        if not is_mp3(path):
            raise ValueError(f"Path must be a mp3 file path not this : {path}")
        
        # stop prevoius timer..
        self._timer.stop()

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
        self.duration = int(duration) * 1000
        mixer.music.load(path)

        # emit setTrackInfo
        self.setTrackInfo.emit(title, publisher, duration, meta["cover"])

        # play...
        mixer.music.play()
        self.elapsed_sec = 0
        self._timer.start()

        self._is_paused = False
        self.setPlaying.emit(self.is_playing())

    def _after_stop(self):
        if self._repeat_mode == 2:
            # repeat one song...
            if not self._current_path:
                # can't repeat with empty path
                return
            
            self.play(path=self._current_path)
            return
        
        if self._repeat_mode == 1:
            self.next_track()
            

    def stop(self):
        self.setPlaying.emit(False)
        self._timer.stop()
        mixer.music.stop()
        self._is_paused = False
        self._after_stop()


    def play_toggled(self):
        if self.is_playing(): # playing -> paused
            mixer.music.pause()
            self._is_paused = True

        elif self._is_paused: # paused -> resuming
            mixer.music.unpause()
            self._is_paused = False

        else: # song ended...
            # if there is current path.. then play it... again
            # as resume is clicked...
            if self._current_path:
                self.play(self._current_path)
                # not emmiting the play signal.. as self.play fun gonna do it
                return 
            
            

            
        # set the play or pause button 
        self.setPlaying.emit(self.is_playing())

    def set_volume(self, vol: float):
        vol = max(0.0, min(1.0, float(vol)))
        mixer.music.set_volume(vol)
        self._volume = vol # to re-init

    def is_playing(self) -> bool:
        return mixer.music.get_busy() and not self._is_paused
    

    def _update_position(self):
        if self._is_paused:
            return
        
        if not mixer.music.get_busy():
            self.setSeekPos.emit(self.duration)
            self.stop()
            return

        self.elapsed_sec = min(self.elapsed_sec + 100, self.duration)
        self.setSeekPos.emit(self.elapsed_sec)