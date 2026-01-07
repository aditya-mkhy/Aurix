from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont, QCursor, QIcon
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QScrollArea, QFrame, QPushButton
from helper import round_pix_form_path

class MenuItem(QWidget):
    clicked = pyqtSignal()

    def __init__(self, text: str):
        super().__init__()

        self.setFixedHeight(42)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        label = QLabel(text) 
        label.setFont(QFont("Segoe UI", 12))
        label.setStyleSheet("color: white; background: transparent;")

        layout.addWidget(label)

        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border-radius: 6px;
            }
            QWidget:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QWidget:pressed {
                background: rgba(255, 255, 255, 0.16);
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()


class MenuSeparator(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(1)
        self.setStyleSheet("background: #3a3b3d; margin: 6px 12px;")


class CardMenu(QWidget):
    clickedOn = pyqtSignal(str, int)
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.container = QWidget(self)
        self.container.setObjectName("Container")

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.play_next = MenuItem("Play next")
        self.add_queue = MenuItem("Add to queue")
        self.add_playlist = MenuItem("Save to playlist")
        self.remove = MenuItem("Remove song")

        # ---- Close on click ----
        self.play_next.clicked.connect(lambda: self._emit_clicked("next"))
        self.add_queue.clicked.connect(lambda: self._emit_clicked("queue"))
        self.add_playlist.clicked.connect(lambda: self._emit_clicked("playlist"))
        self.remove.clicked.connect(lambda: self._emit_clicked("remove"))

        layout.addWidget(self.play_next)
        layout.addWidget(self.add_queue)
        layout.addWidget(self.add_playlist)
        layout.addWidget(self.remove)

        self.container.setStyleSheet("""
            QWidget#Container {
                background: #181818;
                border-radius: 12px;
                border: 1px solid #3a3b3d;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)

        # ✅ LET QT CALCULATE SIZE
        self.container.adjustSize()
        self.adjustSize()

        # song_id
        self.song_id = None

    def _emit_clicked(self, btn: str):
        self.close()
        if self.song_id:
            self.clickedOn.emit(btn, self.song_id)
        self.song_id = None


    def show_at_cursor(self, song_id: int):
        self.song_id = song_id
        self.container.adjustSize()
        self.adjustSize()

        pos = QCursor.pos()
        self.move(pos + QPoint(12, 12))
        self.show()






class PlaylistItemWidget(QWidget):
    clicked = pyqtSignal(int)  # playlist_id

    def __init__(self, playlist_id: int, name: str, count: int, cover_path: str = None):
        super().__init__()
        self.playlist_id = playlist_id
        self.setFixedHeight(72)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("PlaylistItem")
        self.setAttribute(Qt.WA_Hover, True)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_StyledBackground, True)


        self.setStyleSheet("""
            QWidget#PlaylistItem {
                background: transparent;
                border-radius: 6px;
            }

            QWidget#PlaylistItem:hover {
                background: #2a2a2a;
            }
        """)


        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Cover
        cover_lbl = QLabel()
        cover_lbl.setFixedSize(56, 56)
        cover_lbl.setStyleSheet("background: #444; border-radius: 6px;")

        if cover_path:
            cover_lbl.setPixmap(round_pix_form_path(cover_path, 56, 56, 6))

        # Text
        text_layout = QVBoxLayout()
        text_layout.addStretch()

        text_layout.setContentsMargins(0, 3, 0, 7)
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_lbl.setStyleSheet("color: white;  background: transparent;")
        name_lbl.setFixedHeight(25)

        count_lbl = QLabel(f"{count} songs")
        count_lbl.setStyleSheet("color: #aaaaaa; font-size: 14px; font-weight: 450; background: transparent;")

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

    def __init__(self, song_id: int, parent=None):
        super().__init__(parent)
        self.song_id = song_id
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(450)
        self.setFixedWidth(400)
        ##181818
        self.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-radius: 18px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(35, 20, 16, 20)
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
    def add_playlist(self, playlist_id: int, name: str, count: int, cover_path: str = None):
        playlist_widget = PlaylistItemWidget(playlist_id, name, count, cover_path)

        playlist_widget.clicked.connect(self.playlistSelected)
        self.list_layout.insertWidget(self.list_layout.count() - 1, playlist_widget)
        