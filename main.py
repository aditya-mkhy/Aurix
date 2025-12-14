import os
import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QApplication, QStackedWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSignal

# project import
from sidebar import Sidebar
from topbar import Topbar
from bottom_bar import BottomBar
from content import ContentArea
from util import dark_title_bar, get_music_path, MediaKeys, is_mp3
from yt_music import YtScreen
from player import PlayerEngine
from databse import DataBase
from typing import List


class LoadFiles(QThread):
    config_one = pyqtSignal(str, str, str, object)
    addOneSong = pyqtSignal(int, str, str, str, str)
    finished = pyqtSignal(bool)

    def __init__(self, dataBase: DataBase = None, parent = None):
        super().__init__(parent)

        self.dataBase = dataBase

        # list of id's of the song wich does not exists anymore
        # so to remove later add here
        self._to_delete: List[int] = []

        self.sleep_on_count = 10
        self.count = 0


    def run(self):
        all_songs = self.dataBase.get_song()

        for song in all_songs:
            if not os.path.exists(song['path']):
                print(f"PathNotFound => {song['path']}")
                # add to delete later
                self._to_delete.append(song['id'])
                continue

            if not os.path.exists(song['cover_path']):
                # if cover path not found... 
                # add logic later
                pass

            self.addOneSong.emit(song['id'], song['title'], song['subtitle'], song['path'], song['cover_path'])

        self.finished.emit(True)



class MusicMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurix - Music Player")
        self.resize(1520, 880)
        self.setStyleSheet("background-color: #000000;")

        music_dirs = get_music_path()

        # DataBase
        self.dataBase = DataBase()

        # init player engine
        self.playerEngine = PlayerEngine(parent=self)

        self.playlist_paths = []
        self.current_index = -1

        # Media Keys
        self.media_keys = MediaKeys(parent=self)
        self.media_keys.onPlayPause.connect(self.playerEngine.play_toggled)
        self.media_keys.onPlayNext.connect(self.playerEngine.next_track)
        self.media_keys.onPlayPrevious.connect(self.playerEngine.prevoius_track)
        QTimer.singleShot(0, self.media_keys.register)


        central = QWidget()
        self.setCentralWidget(central)

        # OUTER LAYOUT (TOP, MIDDLE, BOTTOM)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Topbar - logo and searchbox
        self.top_bar = Topbar(parent=self, search_callback=self.search_call)
        outer.addWidget(self.top_bar)

        # MIDDLE (sidebar + main content)
        middle_frame = QWidget()

        middle_layout = QHBoxLayout(middle_frame)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        # middle_frame.setStyleSheet("background-color: green;")

        # sidebar
        self.sidebar = Sidebar(parent=self, nav_call=self._nav_call)
        middle_layout.addWidget(self.sidebar)

        # HOME SCREEN
        self.home_screen = ContentArea(music_dirs=music_dirs)
        self.home_screen.playRequested.connect(self._play_requested)
        self.home_screen.playToggleRequested.connect(self.playerEngine.play_toggled)


        #LIBRARAY SCREEN
        self.library_screen = ContentArea()

        # TY SCREEN
        self.yt_screen = YtScreen(parent=self)
        # call when yt want to all item to home screen and play
        self.yt_screen.addItemHomeRequested.connect(self.add_item_home_requested)
        self.yt_screen.playRequested.connect(self._play_requested)
        self.yt_screen.addSongToDB.connect(self.add_song_to_db)


        outer.addWidget(middle_frame, 1)

        self.content_area = QStackedWidget()
        self.content_area.addWidget(self.home_screen)      # index 0
        self.content_area.addWidget(self.library_screen)   # index 1
        self.content_area.addWidget(self.yt_screen)   # index 2

        middle_layout.addWidget(self.content_area, 1)
        self.content_area.setCurrentIndex(0)

        # bottombar
        self.bottom_bar = BottomBar(parent=self)
        outer.addWidget(self.bottom_bar)

        # connect bottom_bar signal
        self.bottom_bar.seekRequested.connect(self.playerEngine.set_seek)
        self.bottom_bar.volumeChanged.connect(self.playerEngine.set_volume)
        self.bottom_bar.playToggled.connect(self.playerEngine.play_toggled)
        self.bottom_bar.repeatModeChanged.connect(self.playerEngine.set_repeat_mode)
        self.bottom_bar.previousClicked.connect(self.playerEngine.prevoius_track)
        self.bottom_bar.nextClicked.connect(self.playerEngine.next_track)
        self.bottom_bar.shuffleToggled.connect(self.set_shuffle)

        # connect PlayerEngine signal
        self.playerEngine.setTrackInfo.connect(self.bottom_bar.set_track)
        self.playerEngine.setPlaying.connect(self.bottom_bar.set_playing)
        self.playerEngine.setSeekPos.connect(self.bottom_bar.set_position)
        self.playerEngine.setRepeatMode.connect(self.set_repeat_mode)
        self.playerEngine.broadcastMsg.connect(self.broadcast_msg)

        self.is_setting = False
        self.is_suffle = False

        # Thread to add files...
        self.loader = LoadFiles(dataBase=self.dataBase, parent=self)
        self.loader.addOneSong.connect(self.home_screen.add_item)

        QTimer.singleShot(0, self.load_basic_settings)

    def on_finish_loader(self, status):
        if status:
            print(f"All Local Files added sucessfully")
        else:
            print("Maybe some Error in loading local files..")

        self.loader.deleteLater()


    def add_song_to_db(self, title: str, subtitle: str, artist: str, vid: str, path: str, cover_path: str, duration: int, play = False):
        self.dataBase.add_song(title, subtitle, artist, vid, duration, 0, 0, 0, path, cover_path)
        # get song_id
        song_id = self.dataBase.get_song_id(path=path)

        self.home_screen.add_item(song_id, title, subtitle, path, cover_path, play=play)
        print(f"Song : {path} saved with id : {song_id}")


    def load_basic_settings(self):
        basic_info = self.dataBase.get_basic()
        
        self.is_setting = True

        prev_song = None

        for key, value in basic_info.items():
            
            # setting the repeat mode as prev
            if key == "repeat":
                self.playerEngine.set_repeat_mode(int(value))

            elif key == "suffle":
                value =  True if int(value) else False
                self.set_shuffle(value)

            elif key == "current_song":
                if not os.path.exists(value):
                    # save file doesn't exists anymore
                    continue
                
                if not is_mp3(value): # save file is not and mp3
                    continue
                
                # saving it to play after all settings done
                prev_song = value

        # loading the last played song
        if prev_song is not None:
            self.playerEngine.init_play(prev_song)

        self.is_setting = False


    def set_shuffle(self, value: bool):
        self.bottom_bar.set_shuffle(value)

        if not self.is_setting:
            value = 1 if value else 0
            self.dataBase.add_basic(key="suffle", value=value)

    def set_repeat_mode(self, value: int):
        self.bottom_bar.set_repeat_mode(value)
        if not self.is_setting:
            self.dataBase.add_basic(key="repeat", value=value)


    def broadcast_msg(self, type: str, item_id: str, value: bool):
        # print(f"Boradcast[main] => {type} | {item_id} | {value}")
        self.yt_screen.set_broadcast(type, item_id, value)
        self.home_screen.set_broadcast(type, item_id, value)

        if type == "active" and value == True and not self.is_setting:
            # saving the current playing song path
            # if type is active and value is True -> means it's playing broadcast
            # is not self.is_setting -> means it's not called at the time of loading settings
            self.dataBase.add_basic("current_song", item_id)


    def play_song(self, file_path: str):
        self.playerEngine.play(path=file_path)

    def _play_requested(self, file_path: str):
        print(f"PlayingByPlayer : {file_path}")
        self.play_song(file_path=file_path)


    def add_item_home_requested(self, title, subtitle, path, cover_path, play):
        self.home_screen.add_item(title, subtitle, path, cover_path, play = play)


    def search_call(self, query: str):
        print(f"Search Query : {query}")
        self.yt_screen.search_call(query)


    # call this fun when nav button clicked...
    def _nav_call(self, name: str):
        print(f"Navigation clicked : {name}")

        if name == "home":
            self.content_area.setCurrentIndex(0)

        elif name == "library":
            self.content_area.setCurrentIndex(1)

        elif name == "yt":
            self.content_area.setCurrentIndex(2)

    def nativeEvent(self, eventType, message):
        return self.media_keys.nativeEvent(eventType, message)
    
    def closeEvent(self, event):
        self.media_keys.unregister()
        super().closeEvent(event)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    win = MusicMainWindow()
    win.show()
    dark_title_bar(win)   # make Windows title bar dark
    sys.exit(app.exec_())