import os
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from helper import get_mp3_metadata
from util import is_mp3, MUSIC_DIR_PATH, COVER_DIR_PATH

MIXER = None #

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
    setTrackInfo = pyqtSignal(int, str, str, int, str, int)
    setPlaying = pyqtSignal(bool)
    setSeekPos = pyqtSignal(int)
    setRepeatMode = pyqtSignal(int)
    broadcastMsg = pyqtSignal(str, int, bool)

    askForNext = pyqtSignal(int)
    askForPreviuos = pyqtSignal(int)
    infoPlayingStatus = pyqtSignal(int, str)

    def __init__(self, parent = None):
        super().__init__(parent)

        # store the current song info
        self.song_info: dict = None
        self.song_id: int = None # previous playing song id

        # variables
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


    def init(self):
        global MIXER
    
        if MIXER is not None:
            return
        
        from pygame import mixer
        MIXER = mixer
        self._init_mixer(freq=48000, channels=2, out_dev="default")
        
    def init_play(self, song_info: dict, out_dev = None):
        self.init() # init pygame..
        self.play(song_info=song_info, out_dev=out_dev)
        self.play_toggled()

    def _init_mixer(self, freq=48000, channels=2, out_dev="default"):
        if not (freq != self._freq or channels != self._channels or out_dev != self._out_dev):
            # everything is same as previous init.. pass
            return
        
        if not MIXER:
            # means pygame is not init...
            self.init()

        MIXER.quit() # remove prev init
        self._freq = freq
        self._channels = channels
        self._out_dev = out_dev

        if out_dev != "default":
            MIXER.init(devicename=self._out_dev, frequency=self._freq, channels = self._channels)

        else:
            MIXER.init(frequency=freq, channels=channels)

        # set the prevous or default volume
        MIXER.music.set_volume(self._volume)


     
    def play(self, song_info: dict, out_dev = None):
        self.song_info = song_info # song info
        
        path = song_info['path']

        if not os.path.isfile(path):
            raise ValueError(f"Path not exists or it's a directory.")
        
        
        # stop prevoius timer..
        self._timer.stop()

        meta = get_mp3_metadata(path)
        channels = meta["channels"]
        freq = meta["sample_rate"]
        duration = meta["duration"]

        title = song_info["title"] 
        subtitle = song_info["subtitle"]
        liked = song_info["liked"]

        cover_path = os.path.join(COVER_DIR_PATH, song_info["cover_path"])

        # init mixer according to the file
        if out_dev is None:
            out_dev = self._out_dev

        self._init_mixer(freq=freq, channels=channels, out_dev=out_dev)

        # load music
        prev_song_id = self.song_id # to broadcast de-active status
        self.song_id = self.song_info['id'] # current song id
        
        self.duration = int(duration) * 1000
        MIXER.music.load(path)

        # emit setTrackInfo
        self.setTrackInfo.emit(self.song_id, title, subtitle, liked, cover_path, duration)

        # play...
        MIXER.music.play()
        self.elapsed_sec = 0
        self._timer.start()

        self._is_paused = False
        self.setPlaying.emit(self.is_playing())
        # to set prevoius Active -> False

        if prev_song_id:
            # to deactive prevoius song card
            self.broadcastMsg.emit("active", prev_song_id, False)

        # to active current song card
        self.broadcastMsg.emit("active", self.song_id, True)

        # to set playing status to song card
        self.broadcastMsg.emit("playing", self.song_id, self.is_playing())


    def set_seek(self, sec: int):    
        try:
            MIXER.music.set_pos(sec)
        except:
            MIXER.music.play(1, sec)

        self.elapsed_sec = (sec * 1000)


    def set_repeat_mode(self, value: int):
        if value not in (0, 1, 2):
            return

        self._repeat_mode = value
        self.setRepeatMode.emit(self._repeat_mode)


    def next_track(self):
        self.askForNext.emit(self.song_id)

    def prevoius_track(self):
        if (self.elapsed_sec //1000) >= 5:
            # Restart current track from beginning
            self.setSeekPos.emit(0) # set the seekbar to 0 pos for smothness
            self.set_seek(0)
            return
        
        self.askForPreviuos.emit(self.song_id)

    def _after_stop(self):
        if self._repeat_mode == 2:
            # repeat one song...
            if not self.song_id:
                # can't repeat with empty path
                return
            
            self.play(self.song_info)
            return
        
        if self._repeat_mode == 1:
            self.next_track()
            

    def stop(self):
        self._timer.stop()
        MIXER.music.stop()
        self.setPlaying.emit(False)
        self.broadcastMsg.emit("active", self.song_id, False)
        
        self._is_paused = False
        self._after_stop()


    def play_toggled(self):
        if self.is_playing(): # playing -> paused
            MIXER.music.pause()
            self._is_paused = True

        elif self._is_paused: # paused -> resuming
            MIXER.music.unpause()
            self._is_paused = False

        else: # song ended...
            # if there is current path.. then play it... again
            # as resume is clicked...
            if self.song_id:
                self.play(self.song_info)
                # not emmiting the play signal.. as self.play fun gonna do it
                return 

            
        # set the play or pause button 
        self.setPlaying.emit(self.is_playing())
        self.broadcastMsg.emit("playing", self.song_id, self.is_playing())


    def set_volume(self, vol: float):
        vol = max(0.0, min(1.0, float(vol)))
        MIXER.music.set_volume(vol)
        self._volume = vol # to re-init

    def is_playing(self) -> bool:
        return MIXER.music.get_busy() and not self._is_paused
    

    def _update_position(self):
        if self._is_paused:
            return
        
        if not MIXER.music.get_busy():
            self.setSeekPos.emit(self.duration)

            # emit song finish status..
            # to increase the song play count
            if self.song_id:
                print(f"Adding play count for song_id : {self.song_id}")
                self.infoPlayingStatus.emit(self.song_id, "finished")
            self.stop()
            return

        self.elapsed_sec = min(self.elapsed_sec + 100, self.duration)
        self.setSeekPos.emit(self.elapsed_sec)