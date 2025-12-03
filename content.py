from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QListWidgetItem, 
    QListWidget, QListView, QAbstractItemView, QMenu
)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QFontMetrics, QPainterPath


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

def applyRoundedImage(label, path, radius=16):

    pm = QPixmap(path).scaled(
        label.width(),
        label.height(),
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation
    )

    rounded = QPixmap(label.size())
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)

    path = QPainterPath()
    path.addRoundedRect(0, 0, label.width(), label.height(), radius, radius)

    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pm)
    painter.end()

    label.setPixmap(rounded)



class PlaylistCard(QWidget):

    def __init__(self, title: str, subtitle: str = "",
                 thumbnail_path: str = None, parent=None):
        super().__init__(parent)
        self.title_text = title
        self._active = False

        self.width = 282
        self.height = 290#220

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(self.width, self.height)
        self.setStyleSheet("border: none; background-color: red;")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(6)


        self.thumb_width = self.width
        self.thumb_height = 158#self.height - 40


        self.thumb_container = QFrame()
        self.thumb_container.setFixedSize(self.thumb_width, self.thumb_height)
        self.thumb_container.setFrameShape(QFrame.NoFrame)
        self.thumb_container.setAttribute(Qt.WA_StyledBackground, True) #333333

        self.thumb_container.setStyleSheet("""
            QFrame {
                border: none;
                background-color: blue;
                border-radius: 14px;
            }
        """)

        self.thumb_container.setStyleSheet("border: none; background: green;")
        # self.thumb_container.enterEvent = self.on_enter
        # self.thumb_container.leaveEvent = self.on_leave

        thumb_layout = QVBoxLayout(self.thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(0)


        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(self.thumb_width, self.thumb_height)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        applyRoundedImage(self.thumb_label, "img/2.png", radius=14)

        self.thumb_label.setStyleSheet(f"""
            QLabel {{
                border: none;
                padding: 0;
                border-radius: 14px;
            }}
        """)


        thumb_layout.addWidget(self.thumb_label)


        # Overlay
        self.overlay = QWidget(self.thumb_container)
        self.overlay.setGeometry(0, 0, self.thumb_width, self.thumb_height)
        self.overlay.setAttribute(Qt.WA_StyledBackground, True)
        self.overlay.setStyleSheet("""
            QWidget {
                border: none;
                background-color: rgba(0,0,0,0.45);
                border-radius: 14px;
            }
        """)

        self.overlay.setStyleSheet("background-color: yellow;")

        ov = QVBoxLayout(self.overlay)
        ov.setContentsMargins(8, 8, 8, 8)
        ov.setSpacing(0)

        # top-right 3-dots
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
                font-size: 14px;
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

        # center play
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
        # self.play_btn.clicked.connect(self._on_play_clicked)
        ov.addWidget(self.play_btn, 0, Qt.AlignHCenter)
        ov.addStretch(2)

        self.overlay.hide()

        main.addWidget(self.thumb_container, 0, Qt.AlignTop)

        # ---------- Text ----------
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

            
        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 13))
        self.title_lbl.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                padding: 0;
                font-weight: 600;
            }
        """)

        self.title_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.title_lbl.setWordWrap(False)

        # # Limit to 2 lines:
        # metrics = QFontMetrics(self.title_lbl.font())
        # line_height = metrics.lineSpacing()
        # max_height = line_height * 2   # for 2 lines
        # self.title_lbl.setFixedHeight(max_height)
        # self.title_lbl.setSizePolicy(self.title_lbl.sizePolicy().horizontalPolicy(), 0)


        # ----- Subtitle -----
        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setFont(QFont("Segoe UI", 11))
        self.subtitle_lbl.setStyleSheet("""
            QLabel {
                color: #bebfbd;
                background: transparent;
                padding: 0;
                font-weight: 600;
            }
        """)
        self.subtitle_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.subtitle_lbl.setWordWrap(True)

        metrics = QFontMetrics(self.subtitle_lbl.font())
        line_height = metrics.lineSpacing()
        max_height = line_height * 2   # for 2 lines
        self.subtitle_lbl.setFixedHeight(max_height)
        self.subtitle_lbl.setSizePolicy(self.subtitle_lbl.sizePolicy().horizontalPolicy(), 0)

        # Add to layout
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.subtitle_lbl)
        text_layout.addStretch(1)  # keeps everything pinned to top 
        main.addLayout(text_layout)

        # active vs normal
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
                border: none;
            }
        """
        self._apply_style()

        # menu
        self.menu = QMenu(self)
        self.menu.addAction("Play next",
                            lambda: print(f"[MENU] Play next: {self.title_text}"))
        self.menu.addAction("Add to queue",
                            lambda: print(f"[MENU] Add to queue: {self.title_text}"))
        self.menu.addSeparator()
        self.menu.addAction("Remove playlist",
                            lambda: print(f"[MENU] Remove: {self.title_text}"))

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(self._active_style)
        else:
            self.setStyleSheet(self._normal_style)

    def on_enter(self, event):
        self.overlay.show()
        # self.thumb_container.enterEvent(event)

    def on_leave(self, event):
        self.overlay.hide()
        self._apply_style()
        # self.thumb_container.leaveEvent(event)

    def _on_play_clicked(self):
        print(f"[UI] play playlist: {self.title_text}")

    def _on_menu_clicked(self):
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight())
        self.menu.exec_(pos)


class PlaylistGrid(QListWidget):
    """
    Wrapping grid of PlaylistTile cards.

    IMPORTANT: scrollbars are disabled.
    Height is auto-adjusted so the
    *outer* page scroll area handles scrolling.
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

        # 🔒 disable internal scrollbars
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # drag & drop reorder still works
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        self.itemClicked.connect(self._on_item_clicked)

    def add_playlist(self, title, subtitle="", thumb=None):
        item = QListWidgetItem()
        tile = PlaylistCard(title, subtitle, thumbnail_path=thumb)
        item.setSizeHint(tile.size())
        self.addItem(item)
        self.setItemWidget(item, tile)
        self._update_height_for_content()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_height_for_content()

    def _update_height_for_content(self):
        """Resize the list widget vertically so all rows are visible."""
        if self.count() == 0:
            self.setFixedHeight(0)
            return

        # last item rect gives us bottom of content
        last_item = self.item(self.count() - 1)
        rect = self.visualItemRect(last_item)
        content_bottom = rect.bottom() + self.spacing()

        # some padding
        self.setFixedHeight(content_bottom + 4)

    def _on_item_clicked(self, item):
        clicked_tile = self.itemWidget(item)
        print(f"[UI] open playlist: {clicked_tile.title_text}")

        for i in range(self.count()):
            it = self.item(i)
            tile = self.itemWidget(it)
            tile.set_active(tile is clicked_tile)


class PlaylistSection(QWidget):
    """
    One section like:
        "From your library"
        [PlaylistGrid here]

    Vertical layout: title on top, grid below.
    No scrollbars inside; grid height grows.
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        # self.setStyleSheet("background-color: red;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 24)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 24,  QFont.Black))
        self.title_label.setStyleSheet("color: #ffffff;")

        layout.addWidget(self.title_label)

        self.grid = PlaylistGrid()
        layout.addWidget(self.grid)

    def add_playlist(self, title, subtitle="", thumb=None):
        self.grid.add_playlist(title, subtitle, thumb)



class ContentArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # outer layout sits on ContentArea itself
        outer = QVBoxLayout(self)
        outer.setContentsMargins(50, 5, 2, 5)
        outer.setSpacing(0)

        # Scroll area (only vertical)
        scroll = ScrollArea()
        outer.addWidget(scroll, 1)

        # inner content widget that actually holds all sections
        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, True)
        content.setStyleSheet("background-color: #000000;")
        scroll.setWidget(content)

        # this layout belongs to *content*, NOT self
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(24, 12, 24, 24)
        main_layout.setSpacing(32)

        # Section 1
        self.section_library = PlaylistSection("From your library")
        main_layout.addWidget(self.section_library)

        # Section 2
        self.section_featured = PlaylistSection("Featured playlists for you")
        main_layout.addWidget(self.section_featured)

        # keep sections pinned to top if there are few
        main_layout.addStretch(1)

        # sample data  #Dhun (Movie: Saiyaara)
        self._populate_demo()

    def _populate_demo(self):
        self.section_library.add_playlist(
            "Dhun (Movie: Saiyaara)", "Song • Arijit Singh & Mithoon 251M plays", thumb="img/2.png"
        )
        # self.section_library.add_playlist(
        #     "threee", "Aditya Mukhiya • 4 tracks", thumb="img/2.png"
        # )
        # self.section_library.add_playlist(
        #     "EngFav", "Aditya Mukhiya • 7 tracks", thumb="img/1.png"
        # )

        # self.section_featured.add_playlist(
        #     "Band Baaja Baraat", "Wedding • Mix", thumb="img/2.png"
        # )
        # self.section_featured.add_playlist(
        #     "Night Chill", "AURIX • 30 tracks", thumb="img/1.png"
        # )
