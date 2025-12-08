import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QListWidgetItem, QFileDialog, QApplication, QStackedWidget
)

from PyQt5.QtCore import QTimer

# project import
from sidebar import Sidebar
from topbar import Topbar
from bottom_bar import BottomBar
from content import ContentArea
from util import dark_title_bar, get_music_path, MediaKeys
from yt_music import YtScreen
from player import PlayerEngine


class MusicMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurix - Music Player")
        self.resize(1520, 880)
        self.setStyleSheet("background-color: #000000;")

        music_dirs = get_music_path()

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


        #LIBRARAY SCREEN
        self.library_screen = ContentArea()

        # TY SCREEN
        self.yt_screen = YtScreen(parent=self)
        # call when yt want to all item to home screen and play
        self.yt_screen.addItemHomeRequested.connect(self.add_item_home_requested)
        self.yt_screen.playRequested.connect(self._play_requested)


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

        # connect PlayerEngine signal
        self.playerEngine.setTrackInfo.connect(self.bottom_bar.set_track)
        self.playerEngine.setPlaying.connect(self.bottom_bar.set_playing)
        self.playerEngine.setSeekPos.connect(self.bottom_bar.set_position)
        self.playerEngine.setRepeatMode.connect(self.bottom_bar.set_repeat_mode)

        # duration = 3 * 60 + 34
        # self.bottom_bar.set_track(
        #     "Barbaad",
        #     "Jubin Nautiyal • 155M views • 982K likes",
        #     duration_seconds=duration
        # )


    def play_song(self, file_path: str):
        self.playerEngine.play(path=file_path)

    def _play_requested(self, file_path: str):
        print(f"PlayingByPlayer : {file_path}")
        self.play_song(file_path=file_path)


    def add_item_home_requested(self, title, subtitle_text, path, pix, play = False):
        self.home_screen.add_item(title, subtitle_text, path, pix, play = play)

        # ---- connect engine signals ----
        # self.engine.positionChanged.connect(self.on_engine_position)
        # self.engine.durationChanged.connect(self.on_engine_duration)
        # self.engine.stateChanged.connect(self.on_engine_state)

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



    # ===== ENGINE <-> UI HANDLERS (same as before) =====

    def on_engine_position(self, pos_ms: int):
        pass
        # if self.engine.duration() > 0:
        #     self.seek_slider.blockSignals(True)
        #     self.seek_slider.setValue(pos_ms)
        #     self.seek_slider.blockSignals(False)
        # self.lbl_current_time.setText(self.format_time(pos_ms))

    def on_engine_duration(self, dur_ms: int):
        self.seek_slider.setRange(0, dur_ms)
        self.lbl_total_time.setText(self.format_time(dur_ms))

    def on_engine_state(self, state: int):
        from PyQt5.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlayingState:
            self.btn_play.setText("⏸")
        else:
            self.btn_play.setText("▶")

    # ----- playlist / controls -----

    def on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select audio files",
            "",
            "Audio files (*.mp3 *.wav *.ogg *.flac);;All files (*.*)",
        )
        if not files:
            return
        for path in files:
            self.playlist_paths.append(path)
            self.playlist_widget.addItem(QListWidgetItem(os.path.basename(path)))
        if self.current_index == -1 and self.playlist_paths:
            self.play_track_at(0)

    def on_playlist_double_clicked(self, item):
        row = self.playlist_widget.row(item)
        self.play_track_at(row)

    def on_play_clicked(self):
        if self.current_index == -1:
            if self.playlist_paths:
                self.play_track_at(0)
        else:
            self.engine.play_pause()

    def on_prev_clicked(self):
        if not self.playlist_paths:
            return
        new_index = (self.current_index - 1) % len(self.playlist_paths)
        self.play_track_at(new_index)

    def on_next_clicked(self):
        if not self.playlist_paths:
            return
        new_index = (self.current_index + 1) % len(self.playlist_paths)
        self.play_track_at(new_index)

    def play_track_at(self, index: int):
        if not (0 <= index < len(self.playlist_paths)):
            return
        self.current_index = index
        path = self.playlist_paths[index]
        self.engine.load(path)
        self.engine.play()
        self.lbl_title.setText(os.path.basename(path))
        self.lbl_artist.setText("Local file")
        self.playlist_widget.setCurrentRow(index)

    @staticmethod
    def format_time(ms: int) -> str:
        seconds = ms // 1000
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"


# back to PyQt5 

if __name__ == "__main__":

    app = QApplication(sys.argv)
    win = MusicMainWindow()
    win.show()
    dark_title_bar(win)   # make Windows title bar dark
    sys.exit(app.exec_())