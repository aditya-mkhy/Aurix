import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QScrollArea,
    QPushButton, QFrame, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal


from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap, QFont

import os
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QScrollArea
from PyQt5.QtGui import QIcon, QFont
from helper import round_pix_form_path

class PlaylistItemWidget(QWidget):
    clicked = pyqtSignal(int)  # playlist_id

    def __init__(self, playlist_id: int, name: str, count: int, cover_path: str = None):
        super().__init__()
        self.playlist_id = playlist_id
        self.setFixedHeight(72)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QWidget:hover {
                background: #2a2a2a;
                border-radius: 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Cover
        cover_lbl = QLabel()
        cover_lbl.setFixedSize(56, 56)
        cover_lbl.setStyleSheet("background:#444; border-radius:6px;")

        if cover_path:
            cover_lbl.setPixmap()

        # Text
        text_layout = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_lbl.setStyleSheet("color:white;")

        count_lbl = QLabel(f"{count} songs")
        count_lbl.setStyleSheet("color:#aaaaaa; font-size:10px;")

        text_layout.addWidget(name_lbl)
        text_layout.addWidget(count_lbl)

        layout.addWidget(cover_lbl)
        layout.addLayout(text_layout)
        layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.playlist_id)


class PlaylistPickerMenu(QWidget):
    playlistSelected = pyqtSignal(int)
    newPlaylistRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(420)
        self.setFixedWidth(400)
        ##181818
        self.setStyleSheet("""
            QWidget {
                background: red;
                border-radius: 18px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(35, 16, 16, 16)
        root.setSpacing(14)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("Save to playlist")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color:white;")

        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.PointingHandCursor)

        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                color:white;
                background: transparent;
                font-size: 25px;
                font-weight: 600;
            }
            QPushButton:hover {
                background:#2a2a2a;
                border-radius: 20px;
            }
        """)
        close_btn.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        root.addLayout(header)

        # --- Scroll Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollArea > QWidget > QWidget {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: #000;
                width: 10px;
                border: none;
                margin: 0;
                padding: 0;
            }

            QScrollBar::handle:vertical {
                background: #b3b3b3;
                border-radius: 4px;
                border: none;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: transparent;
                height: 10px;
                border: none;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: #171717;
                border: none;
                border-radius: 4px;
            }

            QScrollBar::up-arrow:vertical {
                border-bottom: 6px solid #b3b3b3;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                background: transparent;
            }

            QScrollBar::down-arrow:vertical {
                border-top: 6px solid #b3b3b3;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                background: transparent;
            }

            *:focus {
                outline: none;
            }
        """)


        content = QWidget()
        self.list_layout = QVBoxLayout(content)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

        # --- New Playlist Button ---

        new_btn = QPushButton(" New Playlist")       
        new_btn.setFixedHeight(44)

        new_btn.setFont(QFont("Segoe UI", 12, QFont.Black))
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setIcon(QIcon("./res/plus_black.png"))
        new_btn.setIconSize(QSize(18, 18))


        # new_btn = QPushButton("+  New playlist")
        # new_btn.setFixedHeight(44)
        new_btn.setStyleSheet("""
            QPushButton {
                background:white;
                color: black;
                border-radius: 22px;
                font-size: 20px;
                font-weight: 600;
                margin-right: 20px;
            }
            QPushButton:hover {
                background:#e6e6e6;
            }
        """)
        new_btn.clicked.connect(self.newPlaylistRequested)

        root.addWidget(new_btn)

    # ---- API to add playlists ----
    def add_playlist(self, playlist_widget: PlaylistItemWidget):
        playlist_widget.clicked.connect(self.playlistSelected)
        self.list_layout.insertWidget(self.list_layout.count() - 1, playlist_widget)


class DummyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Aurix • Playlist Picker Test")
        self.resize(820, 720)
        self.setStyleSheet("background:#0f0f0f;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        info = QLabel("Click the button to open Playlist Picker")
        info.setStyleSheet("color:#aaaaaa;")
        layout.addWidget(info)

        layout.addStretch()

        open_btn = QPushButton("Open Playlist Picker")
        open_btn.setFixedHeight(48)
        open_btn.setStyleSheet("""
            QPushButton {
                background:#1db954;
                color:black;
                font-size:14px;
                font-weight:600;
                border-radius:24px;
            }
            QPushButton:hover {
                background:#1ed760;
            }
        """)
        open_btn.clicked.connect(self.show_picker)
        layout.addWidget(open_btn)

        self.picker = None

    def show_picker(self):
        if self.picker:
            self.picker.close()

        self.picker = PlaylistPickerMenu(self)
        self.picker.move(200, (self.height() - self.picker.height()) - 200)

        # ---- dummy playlists ----
        self.picker.add_playlist(PlaylistItemWidget(1, "Liked music", 5))
        self.picker.add_playlist(PlaylistItemWidget(2, "fav", 2))
        self.picker.add_playlist(PlaylistItemWidget(3, "Workout", 18))
        self.picker.add_playlist(PlaylistItemWidget(4, "Chill", 9))

        # ---- signals ----
        self.picker.playlistSelected.connect(self.on_playlist_selected)
        self.picker.newPlaylistRequested.connect(self.on_new_playlist)

        self.picker.show()

    def on_playlist_selected(self, playlist_id):
        print(f"[TEST] Playlist selected → ID: {playlist_id}")
        self.picker.close()

    def on_new_playlist(self):
        print("[TEST] New playlist requested")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DummyWindow()
    w.show()
    sys.exit(app.exec_())
