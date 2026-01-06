import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QLabel
)

from menu  import CardMenu
import random
from menu import PlaylistPickerMenu

class DummyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Aurix • Playlist Picker Test")
        self.resize(820, 720)
        self.setStyleSheet("background: #0f0f0f;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        info = QLabel("Click the button to open Playlist Picker")
        info.setStyleSheet("color: #aaaaaa;")


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
        self.menu = CardMenu(self)
        self.menu.clickedOn.connect(self.menu_btn_clicked)

        layout.addStretch()

    def menu_btn_clicked(self, btn: str, song_id: int):
        print(f"Button : {btn} |  song_id : {song_id}")

    def show_menu(self):
        song_id = random.randint(1, 300)
        self.menu.show_at_cursor(song_id)

    def show_picker(self):
        if self.picker:
            self.picker.close()

        self.picker = PlaylistPickerMenu(self)
        self.picker.move(200, (self.height() - self.picker.height()) - 200)

        cover_path = "C:\\Users\\sungj\\.aurix\\cvr\\9xer8vedluesck35zaqjhamwzkvc6k.jpg"

        # ---- dummy playlists ----
        self.picker.add_playlist(1, "Liked music", 5, cover_path)
        self.picker.add_playlist(2, "fav", 2, cover_path)
        self.picker.add_playlist(3, "Workout", 18, cover_path)
        self.picker.add_playlist(4, "Chill", 9, cover_path)

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
