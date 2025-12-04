import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QScrollArea
from PyQt5.QtGui import QIcon, QFont


class PlaylistArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 8, 0)
        self.layout.setSpacing(0)

        self.setWidget(self.container)

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




    def add_playlist(self, item_widget):
        self.layout.addWidget(item_widget)



class PlaylistItem(QWidget):
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.setCursor(Qt.PointingHandCursor)

        self.setFixedHeight(70)
        self.setAttribute(Qt.WA_StyledBackground, True)  # so bg color works

        main = QHBoxLayout(self)
        main.setContentsMargins(20, 8, 20, 8)
        main.setSpacing(10)

        # ---- Left side: title + subtitle ----
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        text_box.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 11))
        title_lbl.setStyleSheet("color: #FFFFFF; font-weight: 800; ")

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setFont(QFont("Segoe UI", 9))
        subtitle_lbl.setStyleSheet("color: #b3b3b3;")

        text_box.addWidget(title_lbl)
        text_box.addWidget(subtitle_lbl)

        main.addLayout(text_box, 1)

        # ---- Right side: circular play button ----
        self.play_btn = QPushButton()
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setFixedSize(34, 34)
        self.play_btn.setIcon(QIcon("res/play.png"))  # or use your icon
        self.play_btn.setIconSize(QSize(20, 20))
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
        # initially hidden
        self.play_btn.hide()
        self.play_btn.clicked.connect(self._on_play_clicked)

        main.addWidget(self.play_btn, 0, Qt.AlignVCenter)

        # ---- Card background ----
        self.normal_style = """
            QWidget {
                background-color: transparent;
                border-radius: 12px;
                border-color: transparent;
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
        self.play_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.normal_style)
        self.play_btn.hide()
        super().leaveEvent(event)


class NavButton(QPushButton):
    def __init__(self, text, icon):
        super().__init__(f"   {text}")
        self.icon_path = icon
        self.setFixedHeight(66)

        self.setFont(QFont("Segoe UI", 13, QFont.Black))
        self.setCursor(Qt.PointingHandCursor)

        # icons
        self.normal_icon = QIcon(self.icon_path)
        self.setIcon(self.normal_icon)

        # active icon
        active_icon_path = f"{os.path.dirname(self.icon_path)}/active-{os.path.basename(self.icon_path)}"
        if os.path.exists(active_icon_path):
            self.active_icon = QIcon(active_icon_path)

        else:
            self.active_icon = self.normal_icon

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
                margin-right: 4px;
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
                margin-right: 4px;
            }
        """)

        self.setIcon(self.active_icon)

    def de_activate(self):
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                color: #ffffff;
                background-color: transparent;
                font-weight: 500;
                border: none;
                border-radius: 12px;
                padding-left: 28px;
                margin-right: 4px;
            }
        """)
        self.setIcon(self.normal_icon)


class Sidebar(QFrame):
    def __init__(self, parent = None, nav_call = None):
        super().__init__(parent)

        # fucntions call
        self.nav_call = nav_call

        self.setFixedWidth(320)
        self.setStyleSheet("background-color: #000000; border-right: 1px solid #262626;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(1)

        # ("Explore", False), ("Library", False), ("Upgrade", False)

    
        self.home_nav_btn = NavButton(text="Home", icon="./res/home.png")
        layout.addWidget(self.home_nav_btn)
        self.home_nav_btn.activate()
        self.home_nav_btn.clicked.connect(self.show_home)

        self.explore_nav_btn = NavButton(text="Explore", icon="./res/explore.png")
        layout.addWidget(self.explore_nav_btn)
        self.explore_nav_btn.clicked.connect(self.show_explore)

        self.library_nav_btn = NavButton(text="Library", icon="./res/library.png")
        layout.addWidget(self.library_nav_btn)
        self.library_nav_btn.clicked.connect(self.show_library)

        layout.addSpacing(30)

        line = QFrame()
        line.setStyleSheet("background-color: #262626; margin: 16px")
        line.setFixedHeight(1)
        layout.addWidget(line)

        layout.addSpacing(20)


        # New Playlist button
        add_playlist = QPushButton(" New Playlist")       
        add_playlist.setFixedHeight(55)

        add_playlist.setFont(QFont("Segoe UI", 12, QFont.Black))
        add_playlist.setCursor(Qt.PointingHandCursor)
        add_playlist.setIcon(QIcon("./res/plus.png"))
        add_playlist.setIconSize(QSize(22, 22))


        add_playlist.setStyleSheet("""
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

        layout.addWidget(add_playlist)


        layout.addSpacing(20)

        playlist_scroll = PlaylistArea()
        layout.addWidget(playlist_scroll)


        playlist_scroll.add_playlist(PlaylistItem("Liked Music", "Auto playlist"))
        playlist_scroll.add_playlist(PlaylistItem("EngFav", "Aditya Mukhiya"))
        playlist_scroll.add_playlist(PlaylistItem("Mahadev songs", "Aditya Mukhiya"))
        playlist_scroll.add_playlist(PlaylistItem("hindi songs", "Palak Thakur"))
        playlist_scroll.add_playlist(PlaylistItem("Eng Love", "Aditya Mukhiya"))
        playlist_scroll.add_playlist(PlaylistItem("Best songs", "Aditya Mukhiya"))
        playlist_scroll.add_playlist(PlaylistItem("sleep", "Aditya Mukhiya"))

    def show_home(self):
        self.explore_nav_btn.de_activate()
        self.library_nav_btn.de_activate()
        self.home_nav_btn.activate()
        self.nav_call("home")
        

    def show_library(self):
        self.explore_nav_btn.de_activate()
        self.home_nav_btn.de_activate()
        self.library_nav_btn.activate()
        self.nav_call("library")

    def show_explore(self):
        self.home_nav_btn.de_activate()
        self.library_nav_btn.de_activate()
        self.explore_nav_btn.activate()
        self.nav_call("yt")

    
        
