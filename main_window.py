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
from search import SearchBox
from PyQt5.QtWidgets import QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QRegion, QBitmap


# from player import PlayerEngine

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize, Qt

from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class PlaylistArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #1d1d1d;
                width: 8px;
                margin: 6px 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
            QScrollBar::add-line,
            QScrollBar::sub-line {
                background: none;
                height: 0px;
            }
        """)

        self.setWidgetResizable(True)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        # IMPORTANT → align items at top
        self.layout.setAlignment(Qt.AlignTop)

        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        self.setWidget(self.container)

    def add_playlist(self, item_widget):
        self.layout.addWidget(item_widget)



class PlaylistItem(QWidget):
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.title_text = title

        self.setFixedHeight(68)
        self.setAttribute(Qt.WA_StyledBackground, True)  # so bg color works

        main = QHBoxLayout(self)
        main.setContentsMargins(14, 8, 14, 8)
        main.setSpacing(10)

        # ---- Left side: title + subtitle ----
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        text_box.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        title_lbl.setStyleSheet("color: #FFFFFF;")

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setFont(QFont("Segoe UI", 10))
        subtitle_lbl.setStyleSheet("color: #b3b3b3;")

        text_box.addWidget(title_lbl)
        text_box.addWidget(subtitle_lbl)

        main.addLayout(text_box, 1)

        # ---- Right side: circular play button ----
        self.play_btn = QPushButton()
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setFixedSize(34, 34)
        self.play_btn.setIcon(QIcon("res/play_filled.png"))  # or use your icon
        self.play_btn.setIconSize(QSize(18, 18))
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border-radius: 17px;
                border: none;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:pressed {
                background-color: #d1d1d1;
            }
        """)
        self.play_btn.clicked.connect(self._on_play_clicked)

        main.addWidget(self.play_btn, 0, Qt.AlignVCenter)

        # ---- Card background ----
        self.normal_style = """
            QWidget {
                background-color: #212121;
                border-radius: 12px;
            }
        """
        self.hover_style = """
            QWidget {
                background-color: #2a2a2a;
                border-radius: 12px;
            }
        """
        self.setStyleSheet(self.normal_style)

    # ---------- interactions ----------
    def mousePressEvent(self, event):
        # click on card area (excluding play button) = open playlist
        if event.button() == Qt.LeftButton:
            # if click NOT inside play button
            if not self.play_btn.geometry().contains(event.pos()):
                print(f"[UI] open playlist: {self.title_text}")
        super().mousePressEvent(event)

    def _on_play_clicked(self):
        print(f"[UI] play playlist: {self.title_text}")

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.normal_style)
        super().leaveEvent(event)


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
        logo_btn.setFixedSize(180, 56)  # wider now to fit both
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

        h.addSpacing(80)

        # Center: search bar
        self.search_box = SearchBox()
        h.addWidget(self.search_box)

        # Add spacer before the profile button
        h.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))


        profile_btn = QPushButton()
        profile_btn.setObjectName("profileButton")
        profile_btn.setFixedSize(40, 40)
        profile_btn.setCursor(Qt.PointingHandCursor)

        profile_btn.setStyleSheet("""
            QPushButton#profileButton {
                border: none;
                padding: 0;
                border-radius: 20px;
                background-color: transparent;
                border-image: url("res/profile.png") 0 fill;
            }
        """)

        h.addWidget(profile_btn)

        profile_btn.clicked.connect(lambda: print("Profile button clicked!"))

        h.addSpacing(80)
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
        home_nav_btn.activate()

        explore_nav_btn = NavButton(text="Explore", icon="./res/explore.png")
        layout.addWidget(explore_nav_btn)

        library_nav_btn = NavButton(text="Library", icon="./res/library.png")
        layout.addWidget(library_nav_btn)

        layout.addSpacing(30)

        line = QFrame()
        line.setStyleSheet("background-color: #262626; margin: 16px")
        line.setFixedHeight(1)
        layout.addWidget(line)

        layout.addSpacing(20)


        # close sidebar button
        self.add_playlist = QPushButton(" New Playlist")       
        self.add_playlist.setFixedHeight(55)

        self.add_playlist.setFont(QFont("Segoe UI", 12, QFont.Black))
        self.add_playlist.setCursor(Qt.PointingHandCursor)
        self.add_playlist.setIcon(QIcon("./res/plus.png"))
        self.add_playlist.setIconSize(QSize(22, 22))


        self.add_playlist.setStyleSheet("""
            QPushButton {
                text-align: left;
                color: #ffffff;
                background-color: #151515;
                font-weight: 500;
                border: none;
                border-radius: 25px;
                padding-left: 40px;
                margin-left: 20px;
                margin-right: 20px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #1f1f1f;
            }
        """)

        layout.addWidget(self.add_playlist)


        layout.addSpacing(12)

        playlist_scroll = PlaylistArea()
        layout.addWidget(playlist_scroll)


        playlist_scroll.add_playlist(PlaylistItem("Eng Fav", "Aditya Mukhiya"))
        # playlist_scroll.add_playlist(PlaylistItem("Eng Fav", "Aditya Mukhiya"))
        # playlist_scroll.add_playlist(PlaylistItem("Eng Fav", "Aditya Mukhiya"))
        # playlist_scroll.add_playlist(PlaylistItem("Eng Fav", "Aditya Mukhiya"))
        # playlist_scroll.add_playlist(PlaylistItem("Eng Fav", "Aditya Mukhiya"))


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
    
    def create_circle_image(self, path, size=36):
        """Returns a circular masked pixmap from image path"""
        img = QPixmap(path).scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        mask = QBitmap(size, size)
        mask.fill(Qt.color0)

        painter = QPainter(mask)
        painter.setBrush(Qt.color1)
        painter.drawEllipse(0, 0, size, size)
        painter.end()

        img.setMask(mask)
        return img

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
