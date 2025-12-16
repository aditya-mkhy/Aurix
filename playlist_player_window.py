import sys
from PyQt5.QtCore import Qt, QSize, QEvent, QPoint
from PyQt5.QtGui import QPixmap, QFont, QCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QListWidget, QListWidgetItem,
    QHBoxLayout, QVBoxLayout, QFrame, QStackedLayout
)
from helper import round_pix_form_path

class SongRow(QWidget):
    """
    Reusable single row widget for a song.
    -> cover image with overlay play button
    -> title + artist
    -> duration right aligned
    Methods:
      set_active(bool)
      show_play_overlay(bool)
    """
    def __init__(self, title, artist, duration, index):
        super().__init__()
        self.index = index
        self.active = False

        self.setFixedHeight(72)
        self.setStyleSheet("""
            QWidget { background: transparent; }
            QWidget:hover { background-color: rgba(255,255,255,0.02); }
        """)

        main = QHBoxLayout(self)
        main.setContentsMargins(10, 6, 10, 6)
        main.setSpacing(12)

        # cover container with stacked layout for overlay button
        self.cover_container = QWidget()
        self.cover_container.setFixedSize(56, 56)
        self.cover_container.setStyleSheet("border-radius: 6px;")
        stacked = QStackedLayout(self.cover_container)
        stacked.setStackingMode(QStackedLayout.StackAll)

        self.cover = QLabel()
        try:
            pix = QPixmap("./res/cover2.jpg").scaled(
                56, 56, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
        except Exception:
            pix = QPixmap().scaled(56, 56)
        
        size = 56
        radius = 4

        self.cover.setPixmap(round_pix_form_path(
            path="./res/cover2.jpg",
            width=size,
            height=size,
            radius=radius
        ))
        self.cover.setFixedSize(size, size)
        self.cover.setStyleSheet(f"border-radius: {radius}px;")
        stacked.addWidget(self.cover)

        # overlay play button (initially hidden)
        self.play_btn = QPushButton()
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setFixedSize(56, 56)
        # style as translucent circle with triangle
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,120);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,170);
            }
        """)
        self.play_btn.setText("▶")
        stacked.addWidget(self.play_btn)

        main.addWidget(self.cover_container)

        # text area
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(3)
        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.title_lbl.setStyleSheet("color: white;")
        self.artist_lbl = QLabel(artist)
        self.artist_lbl.setStyleSheet("color: #bdbdbd; font-size: 11px;")
        text.addWidget(self.title_lbl)
        text.addWidget(self.artist_lbl)
        main.addLayout(text)

        main.addStretch()

        self.duration_lbl = QLabel(duration)
        self.duration_lbl.setStyleSheet("color: #bdbdbd;")
        self.duration_lbl.setFixedWidth(60)
        self.duration_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        main.addWidget(self.duration_lbl)

        # default state
        self.play_btn.hide()

        # connect play click
        self.play_btn.clicked.connect(self._on_play_clicked)

    def _on_play_clicked(self):
        # emit via parent later; here we call parent's handler if available
        parent = self.parent()
        # find PlaylistPlayerWindow by climbing up to top-level widget
        w = self.window()
        if hasattr(w, "on_song_play_requested"):
            w.on_song_play_requested(self.index)

    def set_active(self, active: bool):
        """Mark this row as active (currently playing)."""
        self.active = active
        if active:
            # green title color like spotify
            self.title_lbl.setStyleSheet("color: #1db954;")
            self.play_btn.show()
        else:
            self.title_lbl.setStyleSheet("color: white;")
            self.play_btn.hide()

    def show_play_overlay(self, show: bool):
        """Show/hide the overlay play button (used for hover)."""
        if show:
            self.play_btn.show()
        else:
            if not self.active:
                self.play_btn.hide()


class PlaylistPlayerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurix – Playlist Player")
        self.resize(1200, 700)

        self.setStyleSheet("""
            QWidget { background: #000000; color: white; }
            QLabel { color: white; }
        """)

        self.current_index = None
        self.song_widgets = []  # list of SongRow objects
        self.last_hovered_idx = None

        main = QHBoxLayout(self)
        main.setContentsMargins(76, 50, 60, 24)
        main.setSpacing(65)

        # LEFT: playlist big artwork + meta + buttons
        left_layout = QVBoxLayout()
        left_layout.setSpacing(18)

        # collage / big cover
        big_cover = QLabel()

        size = 340
        radius=18

        big_pix = round_pix_form_path(path="./res/cover1.jpg", width=size, height=size, radius=radius)
        big_cover.setPixmap(big_pix)
        big_cover.setFixedSize(size, size)
        big_cover.setStyleSheet(f"border-radius: {radius}px;")
        left_layout.addWidget(big_cover)

        playlist_title = QLabel("most")
        playlist_title.setFont(QFont("Segoe UI", 26, QFont.Bold))
        playlist_title.setStyleSheet("margin-top: 8px;")
        left_layout.addWidget(playlist_title)

        meta = QLabel("Aditya Mukhiya\nPlaylist • Public • 2025\n123 views • 13 tracks • 55 minutes")
        meta.setStyleSheet("color: #bdbdbd; margin-top: 6px;")
        left_layout.addWidget(meta)

        # control buttons row
        ctrl = QHBoxLayout()
        play_btn_big = QPushButton("▶")
        play_btn_big.setFixedSize(72, 72)
        play_btn_big.setStyleSheet("""
            QPushButton {
                background: white; color: black; border-radius: 36px; font-size: 26px;
            }
            QPushButton:hover { background: #efefef; }
        """)
        ctrl.addWidget(play_btn_big)

        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(42, 42)
        edit_btn.setStyleSheet("color: #ddd; border: none; font-size: 18px;")
        ctrl.addWidget(edit_btn)

        more_btn = QPushButton("⋯")
        more_btn.setFixedSize(42, 42)
        more_btn.setStyleSheet("color: #ddd; border: none; font-size: 20px;")
        ctrl.addWidget(more_btn)

        ctrl.addStretch()
        left_layout.addLayout(ctrl)
        left_layout.addStretch()

        main.addLayout(left_layout, 1)

        # RIGHT: song list
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)

        self.list = QListWidget()
        self.list.setSpacing(4)
        self.list.setFrameShape(QFrame.NoFrame)
        self.list.setStyleSheet("""
            QListWidget { background: transparent; }
            QListWidget::item:selected { background: rgba(255,255,255,0.03); }
        """)
        right_layout.addWidget(self.list)
        main.addLayout(right_layout, 2)

        # sample songs
        songs = [
            ("Meri Banogi Kya", "Rito Riba & Rajat Nagpal • Meri Banogi Kya", "3:36"),
            ("SAWARE", "ARJIT SINGH, PRITAM & AMITABH BHATTACHARYA • PHANTOM", "5:22"),
            ("Tera Fitoor", "Arijit Singh • Genius (Original Motion Picture Soundtrack)", "5:10"),
            ("Saiyaara (Movie: Saiyaara)", "Faheem Abdullah, Arslan Nizami & Irshad Kamil • SAIYAARA", "6:11"),
            ("Iktara", "Amit Trivedi, Kavita Seth & Amit • Wake Up Sid", "4:14"),
            ("Halka Halka", "Rahat Fateh Ali Khan • Halka Halka", "4:34"),
            ("Bad Liar", "Imagine Dragons", "4:21"),
        ]

        for idx, (t, a, d) in enumerate(songs):
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 72))
            row = SongRow(t, a, d, idx)
            self.song_widgets.append(row)
            self.list.addItem(item)
            self.list.setItemWidget(item, row)

        # enable mouse tracking so viewport sends MouseMove events
        self.list.setMouseTracking(True)
        self.list.viewport().setMouseTracking(True)

        # install event filter on viewport to watch mouse movement & clicks
        self.list.viewport().installEventFilter(self)

        # clicking the big play should start first song (example)
        play_btn_big.clicked.connect(lambda: self.play_song(0))

    def eventFilter(self, obj, event):
        # viewport mouse move -> manage hover overlay
        if obj is self.list.viewport():
            if event.type() == QEvent.MouseMove:
                pos = event.pos()
                item = self.list.itemAt(pos)
                if item:
                    idx = self.list.row(item)
                    if idx != self.last_hovered_idx:
                        self._set_hovered_index(idx)
                else:
                    # moved outside any item
                    self._set_hovered_index(None)
            elif event.type() == QEvent.MouseButtonPress:
                # if clicked inside list, convert to item click
                mouse_pos = event.pos()
                item = self.list.itemAt(mouse_pos)
                if item:
                    idx = self.list.row(item)
                    # If user clicked on item area (not play button), treat as play
                    # but we let the play button handle its own clicks
                    # Here map global position to widget coords to inspect if clicked inside play_btn,
                    # if not, we treat row click as play
                    widget = self.list.itemWidget(item)
                    if widget:
                        # map pos to the widget local coords
                        global_point = self.list.viewport().mapToGlobal(mouse_pos)
                        local_point = widget.mapFromGlobal(global_point)
                        # if click not inside play button rect -> play the song
                        if not widget.play_btn.geometry().contains(local_point):
                            # play the clicked song
                            self.play_song(idx)
                            return True
            elif event.type() == QEvent.Leave:
                # mouse left the viewport entirely
                self._set_hovered_index(None)
        return super().eventFilter(obj, event)

    def _set_hovered_index(self, idx):
        # hide previous hovered unless it's active
        if self.last_hovered_idx is not None and 0 <= self.last_hovered_idx < len(self.song_widgets):
            prev = self.song_widgets[self.last_hovered_idx]
            if not prev.active:
                prev.show_play_overlay(False)

        self.last_hovered_idx = idx

        if idx is None:
            return

        w = self.song_widgets[idx]
        w.show_play_overlay(True)

    def play_song(self, index: int):
        # central audio-starting handler. for now we just update UI state.
        print("Request play song:", index)
        self.on_song_play_requested(index)

    def on_song_play_requested(self, index: int):
        # update UI: mark selected active and unmark previous
        if self.current_index is not None and 0 <= self.current_index < len(self.song_widgets):
            self.song_widgets[self.current_index].set_active(False)

        self.current_index = index
        if 0 <= index < len(self.song_widgets):
            self.song_widgets[index].set_active(True)
            # ensure the active song is visible and scrolled to center-ish
            item = self.list.item(index)
            self.list.scrollToItem(item, hint=QListWidget.PositionAtCenter)

        # connect actual playback engine here

    # cleanup
    def closeEvent(self, event):
        try:
            self.list.viewport().removeEventFilter(self)
        except Exception:
            pass
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlaylistPlayerWindow()
    w.show()
    sys.exit(app.exec_())
