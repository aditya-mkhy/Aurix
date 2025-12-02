import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QPushButton, QListWidgetItem,
    QScrollArea, QSlider, QFileDialog
)

from PyQt5.QtGui import QPixmap, QPainter, QFont, QBitmap
from sidebar import Sidebar
from topbar import Topbar

class ScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setStyleSheet("""
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

            /* Removes leftover Windows theme artifact */
            *:focus {
                outline: none;
            }
        """)




class Card(QFrame):
    def __init__(self, title, subtitle):
        super().__init__()
        self.setFixedSize(180, 240)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        cover = QFrame()
        cover.setFixedSize(180, 180)
        cover.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border-radius: 12px;
            }
        """)
        layout.addWidget(cover)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        lbl_title.setStyleSheet("color: #ffffff;")
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_sub)


def make_section(section_name, cards_data):
    widget = QWidget()
    v = QVBoxLayout(widget)
    v.setSpacing(12)
    v.setContentsMargins(0, 0, 0, 0)

    title_lbl = QLabel(section_name)
    title_lbl.setFont(QFont("Segoe UI", 20, QFont.Black))
    title_lbl.setStyleSheet("color: #ffffff;")
    v.addWidget(title_lbl)

    row = QWidget()
    h = QHBoxLayout(row)
    h.setSpacing(14)
    h.setContentsMargins(0, 0, 0, 0)

    for t, s in cards_data:
        h.addWidget(Card(t, s))

    h.addStretch()
    v.addWidget(row)
    return widget


class MusicMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurix - Music Player")
        self.resize(1500, 880)

        # ---- engine & playlist state ----
        # self.engine = PlayerEngine(self)
        self.playlist_paths = []
        self.current_index = -1

        central = QWidget()
        self.setCentralWidget(central)

        # OUTER LAYOUT (TOP, MIDDLE, BOTTOM)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Topbar - logo and searchbox
        self.top_bar = Topbar(parent=self)
        outer.addWidget(self.top_bar)

        # -------- MIDDLE (sidebar + main content) --------
        middle_frame = QWidget()
        middle_layout = QHBoxLayout(middle_frame)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        self.sidebar = Sidebar(parent=self)
        middle_layout.addWidget(self.sidebar)

        main_content = self.build_main_area()
        middle_layout.addWidget(main_content, 1)

        outer.addWidget(middle_frame, 1)

        # -------- BOTTOM (player bar, full width) --------
        bottom_bar = self.build_bottom_bar()
        outer.addWidget(bottom_bar)

        self.setStyleSheet("background-color: #000000;")

        # ---- connect engine signals ----
        # self.engine.positionChanged.connect(self.on_engine_position)
        # self.engine.durationChanged.connect(self.on_engine_duration)
        # self.engine.stateChanged.connect(self.on_engine_state)


    def build_main_area(self):
        wrapper = QFrame()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        
        # Scrollable cards
        scroll = ScrollArea()
        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 12, 24, 24)
        layout.setSpacing(32)

        layout.addWidget(make_section("From your library", [
            ("most", "Local playlist · 13 tracks"),
            ("EngFav", "Local playlist · 7 tracks"),
            ("best", "Local playlist · 7 tracks"),
            ("eng", "Local playlist · 12 tracks"),
        ]))

        layout.addWidget(make_section("Featured playlists for you", [
            ("Bridal Entry", "Bollywood · Arijit Singh…"),
            ("Ishq Sufiyana", "Arijit Singh, Pritam…"),
            ("Bollywood Romance", "Romantic Essentials"),
        ]))

        layout.addWidget(make_section("Albums for you", [
            ("Rockstar", "Album · A.R. Rahman"),
            ("MAIN HOON NA", "Album · Various Artists"),
            ("1920", "Album · Adnan Sami"),
        ]))

        layout.addStretch()
        outer.addWidget(scroll, 1)

        return wrapper

    # ========== BOTTOM BAR (player) ==========

    def build_bottom_bar(self):
        bar = QFrame()
        bar.setFixedHeight(96)
        bar.setStyleSheet("background-color: #181818; border-top: 1px solid #262626;")
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(16, 8, 16, 8)
        hb.setSpacing(12)

        # Cover + info
        self.cover_frame = QFrame()
        self.cover_frame.setFixedSize(60, 60)
        self.cover_frame.setStyleSheet("background-color: #333333; border-radius: 4px;")
        hb.addWidget(self.cover_frame)

        info_layout = QVBoxLayout()
        self.lbl_title = QLabel("No track playing")
        self.lbl_title.setStyleSheet("color: white; font-size: 14px;")
        self.lbl_artist = QLabel("Artist")
        self.lbl_artist.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        info_layout.addWidget(self.lbl_title)
        info_layout.addWidget(self.lbl_artist)
        hb.addLayout(info_layout)

        hb.addStretch()

        # center: time + slider
        center_layout = QVBoxLayout()
        time_row = QHBoxLayout()
        self.lbl_current_time = QLabel("00:00")
        self.lbl_current_time.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        time_row.addWidget(self.lbl_current_time)
        time_row.addStretch()
        self.lbl_total_time = QLabel("00:00")
        self.lbl_total_time.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        time_row.addWidget(self.lbl_total_time)
        center_layout.addLayout(time_row)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setFixedWidth(380)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333333;
                height: 5px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #1db954;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #1db954;
                border-radius: 2px;
            }
        """)
        center_layout.addWidget(self.seek_slider)
        hb.addLayout(center_layout)

        # buttons
        btn_layout = QHBoxLayout()
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")

        for b in [self.btn_prev, self.btn_play, self.btn_next]:
            b.setFixedSize(38, 38)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #ffffff;
                    border: none;
                    font-size: 18px;
                }
                QPushButton:hover {
                    color: #1db954;
                }
            """)
            btn_layout.addWidget(b)

        hb.addLayout(btn_layout)
        hb.addStretch()

        # volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333333;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #ffffff;
                border-radius: 2px;
            }
        """)
        hb.addWidget(self.volume_slider)

        # connections
        # self.seek_slider.sliderMoved.connect(self.engine.set_position)
        # self.volume_slider.valueChanged.connect(self.engine.set_volume)
        # self.btn_play.clicked.connect(self.on_play_clicked)
        # self.btn_prev.clicked.connect(self.on_prev_clicked)
        # self.btn_next.clicked.connect(self.on_next_clicked)

        return bar

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


