import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QLineEdit, QScrollArea, QSlider, QFileDialog
)

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

# from player import PlayerEngine


class NavButton(QPushButton):
    def __init__(self, text, icon):
        super().__init__(f"   {text}")
        self.icon_path = icon
        self.setFixedHeight(66)


        self.setFont(QFont("Segoe UI", 13, QFont.Black))
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(QIcon(self.icon_path))
        self.setIconSize(QSize(30, 30))


        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                color: #ffffff;
                background-color: transparent;
                font-weight: 500;
                border: none;
                border-radius: 12px;
                padding-left: 28px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #1f1f1f;
            }
        """)


    def activate(self):
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                color: #ffffff;
                background-color: #262626;
                border: none;
                border-radius: 12px;
                padding-left: 28px;
            }
        """)

        active_icon_path = f"{os.path.dirname(self.icon_path)}/active-{os.path.basename(self.icon_path)}"
        if os.path.exists(active_icon_path):
            self.setIcon(QIcon(active_icon_path))




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

        # -------- TOP (logo + search bar etc. full width) --------
        top_bar = self.build_top_bar()
        outer.addWidget(top_bar)

        # -------- MIDDLE (sidebar + main content) --------
        middle_frame = QWidget()
        middle_layout = QHBoxLayout(middle_frame)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        sidebar = self.build_sidebar()
        middle_layout.addWidget(sidebar)

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

    # ========== TOP BAR ==========

    def build_top_bar(self):
        top = QFrame()
        top.setFixedHeight(90)
        top.setStyleSheet("background-color: #000000; border-bottom: 1px solid #262626;")

        h = QHBoxLayout(top)
        h.setContentsMargins(18, 10, 18, 10)
        h.setSpacing(20)

        h.addSpacing(10)


        # close sidebar button
        sidebar_btn = QPushButton()
        sidebar_btn.setIcon(QIcon("./res/menu.png"))
        sidebar_btn.setIconSize(QSize(34, 34))
        sidebar_btn.setFixedSize(56, 56)
        sidebar_btn.setCursor(Qt.PointingHandCursor)

        sidebar_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 28px;
            }
            QPushButton:hover {
                background-color: #1f1f1f;
                border-radius: 28px;
            }
            QPushButton:pressed {
                background-color: #262626;
                border-radius: 28px;
            }
        """)

   
        h.addWidget(sidebar_btn)



        # Left: logo (AURIX + pulse icon could go here)

        logo_btn = QPushButton("AURIX")  # <-- text added here
        logo_btn.setFont(QFont("Segoe UI", 20, QFont.Black))
        logo_btn.setIcon(QIcon("./res/pulse.png"))
        logo_btn.setIconSize(QSize(52, 52))
        logo_btn.setFixedSize(176, 56)  # wider now to fit both
        logo_btn.setCursor(Qt.PointingHandCursor)

        logo_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                color: white; 
                letter-spacing: 2px;
            }
        """)

        logo_btn.setLayoutDirection(Qt.RightToLeft)  # Ensures icon left, text right

        h.addWidget(logo_btn)

        # h.addSpacing(20)

        # Center: search bar
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search songs, albums, artists...")
        self.search_box.setFixedHeight(38)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #202020;
                border-radius: 20px;
                border: 1px solid #3a3a3a;
                padding-left: 16px;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #ffffff;
            }
        """)
        h.addWidget(self.search_box, 1)

        # Right: dummy icons (cast + profile)
        cast = QLabel("📡")
        cast.setStyleSheet("font-size: 18px; color: #f1f1f1;")
        h.addWidget(cast)

        profile = QFrame()
        profile.setFixedSize(32, 32)
        profile.setStyleSheet("background-color: #444444; border-radius: 16px;")
        h.addWidget(profile)

        return top

    # ========== SIDEBAR (left) ==========

    def build_sidebar(self):
        side = QFrame()
        side.setFixedWidth(320) #0f0f0f
        side.setStyleSheet("background-color: #000000; border-right: 1px solid #262626;")

        layout = QVBoxLayout(side)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(1)

        # ("Explore", False), ("Library", False), ("Upgrade", False)

    
        home_nav_btn = NavButton(text="Home", icon="./res/home.png")
        layout.addWidget(home_nav_btn)
        # home_nav_btn.activate()

        explore_nav_btn = NavButton(text="Explore", icon="./res/explore.png")
        layout.addWidget(explore_nav_btn)

        library_nav_btn = NavButton(text="Library", icon="./res/library.png")
        layout.addWidget(library_nav_btn)
        library_nav_btn.activate()

        layout.addSpacing(30)

        line = QFrame()
        line.setStyleSheet("background-color: #262626; margin: 16px")
        line.setFixedHeight(1)
        layout.addWidget(line)

        layout.addSpacing(20)


        # Add files button
        self.btn_add_files = QPushButton("+  Add audio files")
        self.btn_add_files.setCursor(Qt.PointingHandCursor)
        self.btn_add_files.setFixedHeight(32)
        self.btn_add_files.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border-radius: 16px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f1f1f1;
            }
        """)
        layout.addWidget(self.btn_add_files)
        layout.addSpacing(12)

        # Playlist list
        lbl = QLabel("Your Tracks")
        lbl.setStyleSheet("color: #b3b3b3; font-size: 13px;")
        layout.addWidget(lbl)

        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: #e0e0e0;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 0px;
            }
            QListWidget::item:selected {
                background: #262626;
            }
        """)
        layout.addWidget(self.playlist_widget, 1)

        # connections
        self.btn_add_files.clicked.connect(self.on_add_files)
        self.playlist_widget.itemDoubleClicked.connect(self.on_playlist_double_clicked)

        return side

    # ========== MAIN AREA (right) ==========

    def build_main_area(self):
        wrapper = QFrame()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Category pills row
        pill_row = QFrame()
        pr = QHBoxLayout(pill_row)
        pr.setContentsMargins(24, 8, 24, 8)
        pr.setSpacing(10)
        for txt in ["Podcasts", "Feel good", "Romance", "Relax", "Energize",
                    "Party", "Workout", "Commute", "Sad", "Focus", "Sleep"]:
            btn = QPushButton(txt)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 18px;
                    border-radius: 18px;
                    background-color: #2a2a2a;
                    color: #f1f1f1;
                    border: none;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                }
            """)
            pr.addWidget(btn)
        pr.addStretch()
        outer.addWidget(pill_row)

        # Scrollable cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
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
