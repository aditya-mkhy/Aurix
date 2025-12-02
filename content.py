from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QSpacerItem, 
    QLineEdit, QSizePolicy, QToolButton
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette


from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon

from PyQt5.QtWidgets import QListWidget, QListView, QAbstractItemView
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem, QListView,
    QAbstractItemView, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
import sys


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

from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem, QListView,
    QAbstractItemView, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
import sys


# ---------------------- Playlist Tile ---------------------- #
class PlaylistTile(QWidget):
    """
    YouTube Music style playlist card:

      [ big rounded square thumbnail ]
      most
      Aditya Mukhiya • 13 tracks

    - On hover: semi-transparent overlay on thumbnail with:
        ▶ round play button (center)
        ⋮ 3-dots menu (top-right)
    - Active state: thin colored border around the whole card
    - Card size is approx like screenshot; adjust if you want
    """

    def __init__(self, title: str, subtitle: str = "",
                 thumbnail_path: str = None, parent=None):
        super().__init__(parent)
        self.title_text = title
        self._active = False

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(200, 240)   # card size (approx YouTube Music)

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(6)

        # ---------- Thumbnail container (top) ----------
        self.thumb_size = 180  # square
        thumb_container = QFrame()
        thumb_container.setFixedSize(self.thumb_size, self.thumb_size)
        thumb_container.setFrameShape(QFrame.NoFrame)
        thumb_container.setAttribute(Qt.WA_StyledBackground, True)
        thumb_container.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border-radius: 16px;
            }
        """)

        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(0)

        # actual image
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(self.thumb_size, self.thumb_size)
        self.thumb_label.setAlignment(Qt.AlignCenter)

        if thumbnail_path:
            pm = QPixmap(thumbnail_path)
            if not pm.isNull():
                pm = pm.scaled(self.thumb_size, self.thumb_size,
                               Qt.KeepAspectRatioByExpanding,
                               Qt.SmoothTransformation)
                self.thumb_label.setPixmap(pm)
        thumb_layout.addWidget(self.thumb_label)

        # --- overlay on top of thumbnail (hidden by default) ---
        self.overlay = QWidget(thumb_container)
        self.overlay.setGeometry(0, 0, self.thumb_size, self.thumb_size)
        self.overlay.setAttribute(Qt.WA_StyledBackground, True)
        self.overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0,0,0,0.45);
                border-radius: 16px;
            }
        """)
        ov = QVBoxLayout(self.overlay)
        ov.setContentsMargins(8, 8, 8, 8)
        ov.setSpacing(0)

        # top row: spacer + 3-dots
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)
        top_row.addStretch(1)

        self.menu_btn = QPushButton("⋮", self.overlay)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setFixedSize(26, 26)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #f5f5f5;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.16);
                border-radius: 13px;
            }
            QPushButton:pressed {
                background-color: rgba(255,255,255,0.26);
            }
        """)
        self.menu_btn.clicked.connect(self._on_menu_clicked)
        top_row.addWidget(self.menu_btn, 0, Qt.AlignRight)

        ov.addLayout(top_row)
        ov.addStretch(1)

        # center play button
        self.play_btn = QPushButton("▶", self.overlay)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setFixedSize(46, 46)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border-radius: 23px;
                border: none;
                color: #000000;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #dedede;
            }
        """)
        self.play_btn.clicked.connect(self._on_play_clicked)
        ov.addWidget(self.play_btn, 0, Qt.AlignHCenter)
        ov.addStretch(2)

        self.overlay.hide()  # only visible on hover

        main.addWidget(thumb_container, 0, Qt.AlignHCenter)

        # ---------- Text area (bottom) ----------
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(4, 0, 4, 0)
        text_layout.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        self.title_lbl.setStyleSheet("color: #ffffff;")
        self.title_lbl.setWordWrap(False)

        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setFont(QFont("Segoe UI", 9))
        self.subtitle_lbl.setStyleSheet("color: #b3b3b3;")
        self.subtitle_lbl.setWordWrap(False)

        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.subtitle_lbl)
        main.addLayout(text_layout)

        # ---------- styles: normal / active ----------
        self._normal_style = """
            QWidget {
                background-color: transparent;
                border-radius: 16px;
            }
        """
        self._active_style = """
            QWidget {
                background-color: transparent;
                border-radius: 16px;
                border: 1px solid #b36bff;   /* AURIX highlight */
            }
        """
        self._apply_style()

        # menu for dots
        self.menu = QMenu(self)
        self.menu.addAction("Play next",
                            lambda: print(f"[MENU] Play next: {self.title_text}"))
        self.menu.addAction("Add to queue",
                            lambda: print(f"[MENU] Add to queue: {self.title_text}"))
        self.menu.addSeparator()
        self.menu.addAction("Remove playlist",
                            lambda: print(f"[MENU] Remove: {self.title_text}"))

    # ----- public API -----
    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    # ----- internal helpers -----
    def _apply_style(self):
        if self._active:
            self.setStyleSheet(self._active_style)
        else:
            self.setStyleSheet(self._normal_style)

    # ----- events -----
    def enterEvent(self, event):
        self.overlay.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.overlay.hide()
        self._apply_style()
        super().leaveEvent(event)

    def _on_play_clicked(self):
        print(f"[UI] play playlist: {self.title_text}")

    def _on_menu_clicked(self):
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight())
        self.menu.exec_(pos)


# ---------------------- Playlist Grid ---------------------- #
class PlaylistGrid(QListWidget):
    """
    Wrapping grid of PlaylistTile cards:
    - Left-to-right, wraps to new line
    - Drag & drop reorder
    - Clicking item sets it active (highlight)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)

        self.setSpacing(18)
        self.setMovement(QListView.Snap)

        self.setFrameShape(self.NoFrame)
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")

        # drag & drop reorder
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        self.itemClicked.connect(self._on_item_clicked)

    def add_playlist(self, title, subtitle="", thumb=None):
        item = QListWidgetItem()
        tile = PlaylistTile(title, subtitle, thumbnail_path=thumb)
        item.setSizeHint(tile.size())
        self.addItem(item)
        self.setItemWidget(item, tile)

    def _on_item_clicked(self, item):
        clicked_tile = self.itemWidget(item)
        print(f"[UI] open playlist: {clicked_tile.title_text}")

        for i in range(self.count()):
            it = self.item(i)
            tile = self.itemWidget(it)
            tile.set_active(tile is clicked_tile)

class ContentArea(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)
    
        outer = QVBoxLayout(self)
        outer.setContentsMargins(50, 5, 2, 5)
        outer.setSpacing(0)

        
        # Scrollable cards
        scroll = ScrollArea()
        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 12, 24, 24)
        layout.setSpacing(32)

        self.playlist_grid = PlaylistGrid()
        some_layout.addWidget(self.playlist_grid)

        add_playlist_tile(self.playlist_grid,
                        "Om Namah Shivaye: Hindi",
                        "Playlist • YouTube Music",
                        thumb="res/thumb1.jpg")

        add_playlist_tile(self.playlist_grid,
                        "Mahakaal",
                        "Song • B Praak • 112M plays",
                        thumb="res/thumb2.jpg")

        # layout.addWidget(make_section("Featured playlists for you", [
        #     ("Bridal Entry", "Bollywood · Arijit Singh…"),
        #     ("Ishq Sufiyana", "Arijit Singh, Pritam…"),
        #     ("Bollywood Romance", "Romantic Essentials"),
        # ]))

        # layout.addWidget(make_section("Albums for you", [
        #     ("Rockstar", "Album · A.R. Rahman"),
        #     ("MAIN HOON NA", "Album · Various Artists"),
        #     ("1920", "Album · Adnan Sami"),
        # ]))

        layout.addStretch()
        outer.addWidget(scroll, 1)