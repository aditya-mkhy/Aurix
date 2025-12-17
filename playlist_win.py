import sys
from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QListWidget, QListWidgetItem,
    QHBoxLayout, QVBoxLayout, QFrame,
    QMenu
)
from helper import round_pix_form_path

from helper import round_pix
from common import ScrollArea
from typing import List
from util import trim_text
from common import ScrollArea


class HoverThumb(QWidget):
    playRequested = pyqtSignal()
    playToggleRequested = pyqtSignal()


    def __init__(self, cover_path: str, parent=None):
        super().__init__(parent)

        size = 78
        self.setFixedSize(size, size)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setPixmap(round_pix_form_path(cover_path, size, size, 5))

        self.image_label.setStyleSheet(f"""
            QLabel {{
                border: none;
                padding: 0;
                border-radius: 14px;
            }}
        """)

        main_layout.addWidget(self.image_label)

        # ----- Overlay -----
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WA_StyledBackground, True)
        self.overlay.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 110);
                border-radius: 4px;
            }
        """)
        self.overlay.setGeometry(self.rect())
        self.overlay.hide()

        ov_layout = QHBoxLayout(self.overlay)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.setAlignment(Qt.AlignCenter)


        # play button---
        self.play_icon = QIcon("res/play-card.png")
        self.pause_icon = QIcon("res/pause.png")


        # download button
        self.play_btn = QPushButton(self.overlay)
        self.play_btn.setFixedSize(size, size)
        self.play_btn.setIcon(self.play_icon)  # or use your icon
        self.play_btn.setIconSize(QSize(30, 30))
        self.play_btn.setCursor(Qt.PointingHandCursor)

        self.play_btn.clicked.connect(self._play_requested)

        self.play_btn.setStyleSheet("color: white;")
        ov_layout.addWidget(self.play_btn)

        # internal mode
        self.mode = "idle"


    def set_mode(self, mode: str):
        self.mode = mode

        if mode == "idle":
            self.overlay.hide()
            try:
                self.play_btn.clicked.disconnect(self._play_toggle_request)
            except:
                pass

            self.play_btn.clicked.connect(self._play_requested)
            self.play_btn.setIcon(self.play_icon)


        if mode == "active":
            self.overlay.show()
            self.play_btn.show()
            try:
                self.play_btn.clicked.disconnect(self._play_requested)
            except:
                pass

            self.play_btn.clicked.connect(self._play_toggle_request)
            print(f"SettingValue[Ative] for => {self}")

    def _play_requested(self):
        self.playRequested.emit()


    def set_active(self, value):
        # setactive staus if this song is playing
        if value:
            self.set_mode("active")

        else:
            self.set_mode("idle")


    def _play_toggle_request(self):
        self.playToggleRequested.emit()

    def set_play(self, value):
        if value:
            self.play_btn.setIcon(self.pause_icon)

        else:
            self.play_btn.setIcon(self.play_icon)

    # keep overlay resized
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())

    # show overlay only on hover if in loading/downloading/done modes
    def enterEvent(self, event):
        if self.mode  == "idle":
            self.overlay.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # if still loading/downloading, we can leave overlay visible
        # or hide it – your choice.
        if self.mode  == "idle":
            self.overlay.hide()
        super().leaveEvent(event)

    
class SongRow(QWidget):
    playRequested = pyqtSignal(int)
    playToggleRequested = pyqtSignal()


    def __init__(
            self, song_id: int, title: str, subtitle: str, 
            duration: str, cover_path: str, parent=None
        ):
        super().__init__(parent)
        self.title_txt = title
        self.subtitle_txt = subtitle
        self.song_id = song_id
        self.duration = duration

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(98)
        # self.setCursor(Qt.PointingHandCursor)

        main = QHBoxLayout()
        main.setContentsMargins(10, 6, 24, 4)  # left/right padding
        main.setSpacing(16)

        # cover
        self.thumb = HoverThumb(cover_path, parent=self)
        self.thumb.playRequested.connect(self._play_requested)
        self.thumb.playToggleRequested.connect(self.playToggleRequested.emit)
        main.addWidget(self.thumb)

        # text block
        text_col = QVBoxLayout()
        text_col.setContentsMargins(5, 10, 0, 15)
        text_col.setSpacing(1)
        

        self.title_lbl = QLabel(trim_text(self.title_txt, 62))
        self.title_lbl.setFont(QFont("Segoe UI", 13))
        self.title_lbl.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: white;
                font-weight: 550;
            }
                                    
            QLabel:hover {
                background-color: transparent;
            }
        """)
        self.title_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.subtitle_lbl = QLabel(trim_text(self.subtitle_txt, 80))
        self.subtitle_lbl.setFont(QFont("Segoe UI", 11))
        self.subtitle_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.subtitle_lbl.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: #b3b3b3;
                font-weight: 500;
            }
                                    
            QLabel:hover {
                background-color: transparent;
            }
        """)

        text_col.addWidget(self.title_lbl)
        text_col.addWidget(self.subtitle_lbl)

        main.addLayout(text_col, 1)


        # spacer + menu button
        self.menu_btn = QPushButton(self)
        # self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setIcon(QIcon("res/three-dot-menu.png"))
        self.menu_btn.setFixedSize(48, 48)
        self.menu_btn.setIconSize(QSize(22, 22)) 
        self.menu_btn.setCursor(Qt.PointingHandCursor)

        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 24px;
            }
                                    
            QPushButton:hover {
                background-color:  rgba(255, 255, 255, 0.08);
            }
            QPushButton:pressed {
                background-color:  rgba(255, 255, 255, 0.1);
            }
        """)
        main.addWidget(self.menu_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        # self.menu_btn.hide()

        # underline separator like YT Music
        bottom_line = QFrame(self)
        bottom_line.setStyleSheet("background-color: #262626; margin: 2px")
        bottom_line.setFixedHeight(1)

        bottom_layout = QVBoxLayout(self)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        bottom_layout.addLayout(main)
        bottom_layout.addWidget(bottom_line)

        self.setLayout(bottom_layout)

        # simple menu
        self.menu = QMenu(self)
        self.menu.setObjectName("SearchMenu")
        self.menu.addAction("Play next")
        self.menu.addAction("Add to queue")
        self.menu.addSeparator()
        self.menu.addAction("Go to album")
        self.menu.setStyleSheet("""
            QMenu#SearchMenu {
                background-color: transparent; 
                border: 1px solid #3a3b3d;
                border-radius: 10px;
                padding: 6px 0px;
                color: white;
                font-size: 22px;
                font-family: 'Segoe UI';
            }

            QMenu#SearchMenu::item {
                padding: 10px 16px;
                border-radius: 6px;
                margin: 2px 8px;
            }

            QMenu#SearchMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.08);
            }

            QMenu#SearchMenu::item:pressed {
                background-color: rgba(255, 255, 255, 0.16);
            }

            QMenu#SearchMenu::separator {
                height: 1px;
                margin: 6px 14px;
                background-color: #3a3b3d;
            }
        """)

        self.menu_btn.clicked.connect(self.show_menu)

        # normal + hover style for row background
        self._base_style = """
            QWidget {
                background-color: transparent;
            }
        """
        self._hover_style = """
            QWidget {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """
        self.setStyleSheet(self._base_style)


    def set_broadcast(self, type: str, value: bool):
        print(f"[atTrackRow] [broadcast] => type : {type}, value : {value}")

        if type == "active":
            self.thumb.set_active(value)

        elif type == "playing":
            self.thumb.set_play(value)

        else:
            print(f"[yt-screen][trackrow][broadcast] => not implemented for type : {type}")


    def set_mode(self, mode: str):
        print(f"Setting State : {mode}")
        self.thumb.set_mode(mode)

    def get_mode(self):
        return self.thumb.mode

    def _play_requested(self):
        print(f"Request Play : {self.song_id}")
        self.playRequested.emit(self.song_id)


    def show_menu(self):
        self.menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight()))

    def enterEvent(self, event):
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._base_style)
        super().leaveEvent(event)


class PlaylistPlayerWindow(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent=parent)
        self.setWindowTitle("Aurix – Playlist Player")
        self.resize(1200, 700)

        self.setStyleSheet("""
            QWidget { background: #000000; color: white; }
            QLabel { color: white; }
        """)

        self.current_index = None
        self.song_widgets: List[SongRow] = []  # list of SongRow objects
        self.last_hovered_idx = None

        main = QHBoxLayout(self)
        main.setContentsMargins(0, 10, 0, 10)
        main.setSpacing(65)

        # LEFT: playlist big artwork + meta + buttons

        left_panel = QWidget()
        left_panel.setMaximumWidth(500)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(76, 40, 0, 14)
        left_layout.setSpacing(0)
        left_layout.addSpacing(20)

        # collage / big cover
        self.big_cover = QLabel()

        self.cover_size = 340
        self.cover_radius = 18

        self.big_cover.setFixedHeight(self.cover_size)
        self.big_cover.setStyleSheet(f"border-radius: {self.cover_radius}px; background-color: transparent; width: 100%;")
        self.big_cover.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.big_cover)

        left_layout.addSpacing(18)


        self.playlist_title = QLabel()
        self.playlist_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.playlist_title.setStyleSheet("background-color: transparent;")
        self.playlist_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.playlist_title)

        left_layout.addSpacing(2)


        self.playlist_desc = QLabel()
        self.playlist_desc.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        self.playlist_desc.setStyleSheet("color: #b3b3b3; background-color: transparent;")

        self.playlist_desc.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.playlist_desc)

        left_layout.addSpacing(20)

        self.meta = QLabel()
        self.meta.setStyleSheet("color: #cdcdcd; font-size: 20px; font-weight: 450;")
        self.meta.setAlignment(Qt.AlignCenter)

        left_layout.addWidget(self.meta)

        left_layout.addSpacing(40)

        # control buttons row
        ctrl = QHBoxLayout()
        ctrl.addStretch()


        edit_btn = QPushButton()
        edit_btn.setFixedSize(54, 54)
        edit_btn.setIcon(QIcon("res/edit.png"))  
        edit_btn.setIconSize(QSize(32, 32))
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border-radius: 27px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
            QPushButton:pressed {
                background-color: #141414;
            }
        """)
        ctrl.addWidget(edit_btn)
        ctrl.addSpacing(40)


        play_btn_big = QPushButton()
        play_btn_big.setFixedSize(84, 84)
        play_btn_big.setIcon(QIcon("res/play.png"))  
        play_btn_big.setIconSize(QSize(50, 50))
        play_btn_big.setCursor(Qt.PointingHandCursor)
        play_btn_big.setStyleSheet("""
            QPushButton {
                background: white; color: black; border-radius: 42px; padding-left: 8px;
            }
            QPushButton:hover { background: #efefef; }
        """)
        ctrl.addWidget(play_btn_big)
        ctrl.addSpacing(40)


        more_btn = QPushButton()
        more_btn.setFixedSize(54, 54)
        more_btn.setIcon(QIcon("res/three-dot-menu.png"))  
        more_btn.setIconSize(QSize(26, 26))
        more_btn.setCursor(Qt.PointingHandCursor)

        more_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border-radius: 27px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
            QPushButton:pressed {
                background-color: #141414;
            }
        """)

        ctrl.addWidget(more_btn)
        ctrl.addStretch()


        left_layout.addLayout(ctrl)
        left_layout.addStretch()

        main.addWidget(left_panel, 1)

        # RIGHT: song list
        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        


        # Scroll area (only vertical)
        scroll = ScrollArea()
        right_layout.addWidget(scroll, 2)

        container = QWidget()

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(76, 40, 50, 50)  # 👈 margins
        container_layout.setSpacing(0)


        self.list = QListWidget()
        self.list.setContentsMargins(76, 40, 0, 14)
        self.list.setSpacing(0)
        self.list.setFrameShape(QFrame.NoFrame)

        # Optional but recommended
        self.list.setSelectionMode(QListWidget.NoSelection)

        self.list.setStyleSheet("""
            QListWidget {
                background: transparent;
            }

            QListWidget::viewport {
                padding: 40px 0 14px 76px;
            }

            QListWidget::item {
                background: transparent;
            }

            QListWidget::item:hover {
                background: transparent;
            }

            QListWidget::item:selected {
                background: transparent;
            }

            QListWidget::item:selected:!active {
                background: transparent;
            }
        """)


        scroll.setWidget(self.list)

        main.addLayout(right_layout, 2)

        play_btn_big.clicked.connect(lambda: self.play_song(0))

        self.is_playing = True
        self.song_id = None

    def init_playlist(self, playlist_id: int, title: str, desc: str, meta: str, cover_path: str):
        self.playlist_id = playlist_id
        
        self.playlist_title.setText(title)
        self.playlist_desc.setText(desc)
        self.meta.setText(meta)

        # set playlist cover img
        big_pix = round_pix_form_path(
            path=cover_path, 
            width=self.cover_size, 
            height=self.cover_size, 
            radius=self.cover_radius
        )

        self.big_cover.setPixmap(big_pix)

        # clear_list
        self.clear_list()

        # add space at top
        top_spacer = QListWidgetItem()
        top_spacer.setSizeHint(QSize(0, 50))
        top_spacer.setFlags(Qt.NoItemFlags)
        self.list.addItem(top_spacer)

    def add_song(self, song_id: int, title: str, subtitle: str, duration: str, cover_path: str):
        item = QListWidgetItem()
        row = SongRow(song_id, title,subtitle,  duration, cover_path, self)
        item.setSizeHint(row.size())
        # connects
        row.playRequested.connect(self.request_play)
        row.playToggleRequested.connect(self.play_toogle)

        self.song_widgets.append(row)
        self.list.addItem(item)
        self.list.setItemWidget(item, row)


    def clear_list(self):
        while self.list.count():
            item = self.list.takeItem(0)
            widget = self.list.itemWidget(item)
            if widget:
                widget.deleteLater()
            del item


    def request_play(self, song_id: int):
        print(f"Playing song with id : {song_id}")

        if self.song_id is not None: # previus id
            prev_row_obj = self.song_widgets[self.song_id]
            prev_row_obj.set_broadcast("active", value=False) 

        row_obj = self.song_widgets[song_id]
        row_obj.set_broadcast("active", value=True)
        self.song_id = song_id
        
        # on pause state...
        QTimer.singleShot(200, lambda row = row_obj : row.set_broadcast("playing", value=True))

    def play_toogle(self):
        if self.song_id is None:
            return
        
        self.is_playing = not self.is_playing
        row_obj = self.song_widgets[self.song_id]
        row_obj.set_broadcast("playing", value=self.is_playing)


    def play_song(self, index: int):
        print("Request play song:", index)
        self.on_song_play_requested(index)


    # cleanup
    def closeEvent(self, event):
        try:
            self.list.viewport().removeEventFilter(self)
        except Exception:
            pass
        super().closeEvent(event)


songs = [
    ("Meri Banogi Kya", "Rito Riba & Rajat Nagpal • Meri Banogi Kya", "3:36"),
    ("SAWARE", "ARJIT SINGH, PRITAM & AMITABH BHATTACHARYA • PHANTOM", "5:22"),
    ("Tera Fitoor", "Arijit Singh • Genius (Original Motion Picture Soundtrack)", "5:10"),
    ("Saiyaara (Movie: Saiyaara)", "Faheem Abdullah, Arslan Nizami & Irshad Kamil • SAIYAARA", "6:11"),
    ("Iktara", "Amit Trivedi, Kavita Seth & Amit • Wake Up Sid", "4:14"),
    ("Halka Halka", "Rahat Fateh Ali Khan • Halka Halka", "4:34"),
    ("Bad Liar", "Imagine Dragons", "4:21"),
    ("Bad Liar", "Imagine Dragons", "4:21"),
    ("Bad Liar", "Imagine Dragons", "4:21"),
    ("Bad Liar", "Imagine Dragons", "4:21"),
    ("Bad Liar", "Imagine Dragons", "4:21"),
    ("Bad Liar", "Imagine Dragons", "4:21"),
]



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlaylistPlayerWindow()

    playlist_id = 1
    title = "Bath Song"
    desc = "uset to listen while bating"
    meta = "Playlist • Private • 2025\n123 views • 13 tracks • 55 minutes"
    cover_path = "./res/cover1.jpg"
    w.init_playlist(playlist_id, title, desc, meta, cover_path)
    
    cover_path = "./res/cover2.jpg"

    for index, (title, subtitle, duration) in enumerate(songs):
        w.add_song(index, title, subtitle, duration, cover_path)

    w.show()
    sys.exit(app.exec_())
