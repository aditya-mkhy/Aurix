import os
import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QApplication, QStackedWidget
from PyQt5.QtCore import QTimer, pyqtSignal, QObject

# project import
from sidebar import Sidebar
from topbar import Topbar
from bottom_bar import BottomBar
from content import ContentArea
from util import dark_title_bar, get_music_path, MediaKeys, format_duration, COVER_DIR_PATH
from yt_music import YtScreen
from player import PlayerEngine
from databse import DataBase
from typing import List
from playlist_win import PlaylistPlayerWindow
from playlist import CreatePlaylistPopup
from menu import CardMenu

class LoadFiles(QObject):
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
        self.batch_size = 10

        self.all_songs = []

    def add_song_batch(self, start_index: int):
        end_index = start_index + self.batch_size

        for song in self.all_songs[start_index : end_index]:
            if not os.path.exists(song['path']):
                print(f"PathNotFound => {song['path']}")
                # add to delete later
                self._to_delete.append(song['id'])
                continue


            cover_path = os.path.join(COVER_DIR_PATH, song['cover_path'])
            if not os.path.exists(cover_path):
                # if cover path not found... 
                # add logic later
                pass

            self.addOneSong.emit(song['id'], song['title'], song['subtitle'], song['path'], cover_path)

        if end_index < len(self.all_songs):
            QTimer.singleShot(300, lambda idx=end_index: self.add_song_batch(idx))

        else:
            self.finished.emit(True)


    def run(self):
        self.all_songs = self.dataBase.get_song()
        self.add_song_batch(0)



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
        self.sidebar = Sidebar(parent=self)
        self.sidebar.requestCreatePlaylist.connect(self.save_playlist)
        self.sidebar.navCall.connect(self._nav_call)
        self.sidebar.openPlaylistRequested.connect(self.open_playlist)
        self.sidebar.playToggleRequested.connect(self.playerEngine.play_toggled)

        middle_layout.addWidget(self.sidebar)


        # HOME SCREEN
        self.home_screen = ContentArea(music_dirs=music_dirs)
        self.home_screen.playRequested.connect(self._play_requested)
        self.home_screen.playToggleRequested.connect(self.playerEngine.play_toggled)
        self.home_screen.showMenuRequested.connect(self.show_song_card_menu)


        #LIBRARAY SCREEN
        self.library_screen = ContentArea()

        # TY SCREEN
        self.yt_screen = YtScreen(parent=self)
        # call when yt want to all item to home screen and play
        self.yt_screen.playRequested.connect(self._play_requested)
        self.yt_screen.addSongToDBandHome.connect(self.add_song_to_db_and_home)
        self.yt_screen.checkForExistance.connect(self.check_for_song_existance)
        self.yt_screen.playToggleRequested.connect(self.playerEngine.play_toggled)

        # playlist player window...
        self.playlistPlayerWin = PlaylistPlayerWindow(parent=self)
        self.playlistPlayerWin.playRequested.connect(self._play_requested)
        self.playlistPlayerWin.playToggleRequested.connect(self.playerEngine.play_toggled)
        self.playlistPlayerWin.navbarPlaylistBroadcast.connect(self.sidebar.set_navbar_playlist_status)

        outer.addWidget(middle_frame, 1)

        self.content_area = QStackedWidget()
        self.content_area.addWidget(self.home_screen)      # index 0
        self.content_area.addWidget(self.library_screen)   # index 1
        self.content_area.addWidget(self.yt_screen)   # index 2
        self.content_area.addWidget(self.playlistPlayerWin) # 3

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
        self.bottom_bar.likeDislikeToggled.connect(self.save_like_dislike_song)

        # connect PlayerEngine signal
        self.playerEngine.setTrackInfo.connect(self.bottom_bar.set_track)
        self.playerEngine.setPlaying.connect(self.bottom_bar.set_playing)
        self.playerEngine.setSeekPos.connect(self.bottom_bar.set_position)
        self.playerEngine.setRepeatMode.connect(self.set_repeat_mode)
        self.playerEngine.broadcastMsg.connect(self.broadcast_msg)
        self.playerEngine.infoPlayingStatus.connect(self.commit_song_info_status)

        # -> play track signals
        self.playerEngine.askForNext.connect(self.play_next_track)
        self.playerEngine.askForPreviuos.connect(self.play_prevoius_track)

        # songCard popup Menu
        self.card_menu = CardMenu(self)
        self.card_menu.clickedOn.connect(self.card_menu_btn_clicked)

        self.is_setting = False
        self.is_suffle = False


        # Thread to add files...
        self.loader = LoadFiles(dataBase=self.dataBase, parent=self)
        self.loader.addOneSong.connect(self.home_screen.add_item)
        self.loader.finished.connect(self.on_finish_loader)
        # self.loader.start()

        # all song_id list for playing song....
        self.all_song_list = self.dataBase.get_all_song_id()


        QTimer.singleShot(10, self.load_basic_settings)

    def show_song_card_menu(self, song_id):
        print(f"Show SongCard menu for song : {song_id}")
        self.card_menu.show_at_cursor(song_id)

    def card_menu_btn_clicked(self, btn: str, song_id: int):
        print(f"Button : {btn} |  song_id : {song_id}")

        if btn == "next":
            current_song_id = self.playerEngine.song_id # playing song_id
            try:
                index = self.all_song_list.index(current_song_id)
            except Exception as e:
                print("UnknownError : Song must be the song list... please check..")
                print(f"Error --> {e}")
                return
            
            next_index = index + 1
            # add song_id next to the current playing song
            self.all_song_list.insert(next_index, song_id)

        elif btn == "queue":
            if song_id in self.all_song_list:
                print("Song already in queue")
                # later add ui to confirm that user still want it to add alt last
                return

            self.all_song_list.append(song_id)
            print(f"Song {song_id} added to queue")

        elif btn == "playlist":
            print(f"Opening playlist popup to add song : {song_id}")



    def commit_song_info_status(self, song_id: str, type: str):
        print(f"Recv status form player for song : {song_id}  and type : {type}")

        if type == "finished":
            # song is finished...
            # increasing play count.. in db
            self.dataBase.increament_play_count(song_id=song_id)

    def open_playlist(self, playlist_id: int):
        print(f"Confuring PlayList with ID : {playlist_id}")

        info = self.dataBase.get_playlist(playlist_id=playlist_id)

        meta = f"Playlist • Private • 2025\n{info['plays']} views • {info['count']} tracks • {format_duration(info['duration'])}"

        # init the playlist
        cover_path = info['cover_path']
        if playlist_id == 1:
            cover_path = os.path.join("./res", cover_path)

        self.playlistPlayerWin.init_playlist(playlist_id, info['title'], info['subtitle'], meta, cover_path)

        # add songs in the playlist UI
        song_list = self.dataBase.get_playlist_song(playlist_id, detailed=True)
        self.playlistPlayerWin.add_in_batch(song_list, playlist_id, 4)

        
    def save_playlist(self, title: str, desc: str, privacy: str):

        playlist_id = self.dataBase.add_playlist(
            title=title,
            subtitle=desc,
            author= "Aditya Mukhiya",
            count=0,
            duration=0,
            plays = 0,
            cover_path=""
        )

        if playlist_id is None:
            print(f"Failed to create Playlist : {title}")

            # playlist is not create
            # maybe it already exists..
            playlist_id = self.dataBase.get_playlist_id_by_title(title=title)

            if playlist_id is None: # not found
                print(f"Unknow Error while checking for existance for playlist : {title}")
                return
            
            # found... then open that playlist.....
            # logic will be added later
            return
        
        # create playlist on sidebar
        self.sidebar.create_playlist(playlist_id, title, desc)


    def save_like_dislike_song(self, song_id: int, value: int):
        self.dataBase.update_song(song_id, liked = value)

        if value == 1:
            # add into liked playlist
            # liked_playlist id = 1
            self.dataBase.add_playlist_song(1, song_id)

        else:
            # remove song from liked playlist
            self.dataBase.remove_playlist_song(1, song_id)
    

        if value == 2:
            # this means user dislike the song.. 
            # so skip this one and play next from all_song_list
            self.play_next_track(song_id=song_id)

    def check_for_song_existance(self, item_id: int, vid: str):
        song_id = self.dataBase.get_songid_by_vid(vid)
        if song_id is None:
            return
        
        self.yt_screen.songAlreadyexists(item_id, song_id)


    def _get_track(self, song_id: int = None, is_back: bool = False):
        # retrun the next or previous song_id 
        if song_id is None:
            return self.all_song_list[0] # first song from list
        
        try:
            index = self.all_song_list.index(song_id)
        except:
            index = -1

        if is_back:
            index -= 1
        else:
            index += 1

        if index < 0 or index >= len(self.all_song_list):
            index = 0

        return self.all_song_list[index]

    def play_next_track(self, song_id: int = None):
        next_song_id = self._get_track(song_id=song_id)
        self.play_song(song_id=next_song_id) # play next track


    def play_prevoius_track(self, song_id: int = None):
        prev_song_id = self._get_track(song_id=song_id, is_back=True)
        self.play_song(song_id=prev_song_id) # play prev track

    def on_finish_loader(self, status):
        if status:
            print(f"All Local Files added sucessfully")
        else:
            print("Maybe some Error in loading local files..")

        self.loader.deleteLater()


    def add_song_to_db_and_home(
            self, title: str, subtitle: str, artist: str, 
            vid: str, path: str, cover_path: str, duration: int, 
            track_id: int = None
    ):
        # add song to database
        self.dataBase.add_song(title, subtitle, artist, vid, duration, 0, 0, 0, path, cover_path)
        # get song_id
        song_id = self.dataBase.get_song_id(path=path)

        # add this to all_song_list at 0
        self.all_song_list.insert(0, song_id)

        # set play status in yt_screen for TrackRow
        if track_id is not None:
            # do not change mode to play.. as it already in play mode set after downloading
            self.yt_screen.songAlreadyexists(track_id, song_id, change_mode=False)

        self.home_screen.add_item(song_id, title, subtitle, path, cover_path, play=True)
        self.play_song(song_id=song_id) # play song


    def load_basic_settings(self):
        basic_info = self.dataBase.get_basic()
        
        self.is_setting = True

        prev_song_id = None

        for key, value in basic_info.items():
            
            # setting the repeat mode as prev
            if key == "repeat":
                self.playerEngine.set_repeat_mode(int(value))

            elif key == "suffle":
                value =  True if int(value) else False
                self.set_shuffle(value)

            elif key == "current_song":
                # saving it to play after all settings done
                try:
                    # convert into integer song_id
                    prev_song_id = int(value)
                except:
                    prev_song_id = None

        # loading the last played song
        if prev_song_id is not None:
            song_info = self.dataBase.get_song(song_id=prev_song_id)
            QTimer.singleShot(10, lambda info = song_info: self.playerEngine.init_play(info))

        self.is_setting = False

        # load playlist. on sidebar...
        playlists = self.dataBase.get_playlist()
        for playlist in playlists:
            self.sidebar.create_playlist(playlist['id'], playlist['title'], playlist['subtitle'])

        # loading data..
        self.loader.run()


    def set_shuffle(self, value: bool):
        self.bottom_bar.set_shuffle(value)

        if not self.is_setting:
            value = 1 if value else 0
            self.dataBase.add_basic(key="suffle", value=value)

    def set_repeat_mode(self, value: int):
        self.bottom_bar.set_repeat_mode(value)
        if not self.is_setting:
            self.dataBase.add_basic(key="repeat", value=value)


    def broadcast_msg(self, type: str, song_id: int, value: bool):
        # print(f"Boradcast[main] => {type} | {item_id} | {value}")
        self.yt_screen.set_broadcast(type, song_id, value)
        self.home_screen.set_broadcast(type, song_id, value)
        self.playlistPlayerWin.set_broadcast(type, song_id, value)

        if type == "active" and value == True and not self.is_setting:
            # saving the current playing song path
            # if type is active and value is True -> means it's playing broadcast
            # is not self.is_setting -> means it's not called at the time of loading settings
            self.dataBase.add_basic("current_song", song_id)

    def play_song(self, song_id: int):
        song_info = self.dataBase.get_song(song_id=song_id)
        if song_info is None:
            print(f"***************************")
            print(f"Could't find the song with id : {song_id}")
            print("****************************")
            return
        
        self.playerEngine.play(song_info)

    def _play_requested(self, song_id: int):
        self.play_song(song_id=song_id)


    def search_call(self, query: str):
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

        elif name == "playlist":
            self.content_area.setCurrentIndex(3)


    def nativeEvent(self, eventType, message):
        return self.media_keys.nativeEvent(eventType, message)
    
    def closeEvent(self, event):
        self.media_keys.unregister()
        super().closeEvent(event)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    win = MusicMainWindow()
    win.show()
    dark_title_bar(win) # make Windows title_bar dark
    sys.exit(app.exec())