from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QListWidgetItem, 
    QListWidget, QListView, QAbstractItemView, QMenu, 
    QSizePolicy, 
)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QFontMetrics, QPainterPath, QIcon

from helper import LocalFilesLoader

class HoverButton(QPushButton):
    def __init__(self, *args, size: int = 76, icon_size: int = 38, transform_scale = 5, **kwargs):
        super().__init__(*args, **kwargs)

        self.transform_scale = transform_scale

        # store sizes
        self.normal_size = QSize(size, size)
        self.hover_size = QSize(size + self.transform_scale, size + self.transform_scale)   # a bit bigger
        self.normal_icon_size = QSize(icon_size, icon_size)
        self.hover_icon_size = QSize(icon_size + (self.transform_scale - 2), icon_size + (self.transform_scale -2))

        self.setFixedSize(self.normal_size)
        self.setIconSize(self.normal_icon_size)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.55);
                border-radius: { size//2 }px;
                border: none;
                color: #000000;
                padding-left: 12px;        
            }}
            QPushButton:hover {{
                background-color:  rgba(0, 0, 0, 0.85);
                border-radius: { (size + self.transform_scale) //2 }px;
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 1);
                border-radius: { (size + self.transform_scale) //2 }px;

            }}
        """)


        
    def enterEvent(self, event):
        self.setFixedSize(self.hover_size)
        self.setIconSize(self.hover_icon_size)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setFixedSize(self.normal_size)
        self.setIconSize(self.normal_icon_size)
        super().leaveEvent(event)



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

def applyRoundedImage(label, pix: QPixmap, radius=16):

    pm = pix.scaled(
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


class HoverFrame(QFrame):
    def __init__(self, enter_event, leave_event, parent=None):
        super().__init__(parent)
        self.enter_event_call = enter_event
        self.leave_event_call = leave_event

    def enterEvent(self, event):
        self.enter_event_call()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.leave_event_call()
        super().leaveEvent(event)



class ClickableOverlay(QWidget):
    clicked = pyqtSignal()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class PlaylistCard(QWidget):

    def __init__(self, title: str, subtitle_text: str, path: str, pix: QPixmap, play_callback=None, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.subtitle_text = subtitle_text
        self._active = False
        self.mp3_path = path
        self.play_callback = play_callback

        self.width = 282
        self.height = 292#220

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(self.width, self.height)
        self.setStyleSheet("border: none;  background: green; margin: 20px;")


        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(6)


        self.thumb_width = self.width
        self.thumb_height = 158#self.height - 40


        self.thumb_container = HoverFrame(enter_event=self.on_enter, leave_event=self.on_leave)
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

        thumb_layout = QVBoxLayout(self.thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(0)


        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(self.thumb_width, self.thumb_height)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        applyRoundedImage(self.thumb_label, pix, radius=14)

        self.thumb_label.setStyleSheet(f"""
            QLabel {{
                border: none;
                padding: 0;
                border-radius: 14px;
            }}
        """)


        thumb_layout.addWidget(self.thumb_label)


        # Overlay
        self.overlay = ClickableOverlay(self.thumb_container)
        self.overlay.setGeometry(0, 0, self.thumb_width, self.thumb_height)
        self.overlay.setAttribute(Qt.WA_StyledBackground, True)
        self.overlay.setCursor(Qt.PointingHandCursor)
        self.overlay.clicked.connect(self._on_clicked)
        self.overlay.setStyleSheet("""
            QWidget {
                border: none;
                background-color: rgba(0, 0, 0, 0.30);
                border-radius: 14px;
            }
        """)

        # self.overlay.setStyleSheet("background-color: yellow;")

        ov = QVBoxLayout(self.overlay)
        ov.setContentsMargins(8, 8, 8, 8)
        ov.setSpacing(0)

        # top-right 3-dots
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)
        top_row.addStretch(1)


        self.menu_btn = QPushButton(self.overlay)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setIcon(QIcon("res/three-dot-menu.png"))  
        self.menu_btn.setFixedSize(46, 46)
        self.menu_btn.setIconSize(QSize(26, 26))

        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 23px;
            }
                                    
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.40);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.50);
            }
        """)
        self.menu_btn.clicked.connect(self._on_menu_clicked)
        top_row.addWidget(self.menu_btn, 0, Qt.AlignRight)
        ov.addLayout(top_row)

        ov.addStretch(1)

        # center play
        self.play_btn = HoverButton(parent=self.overlay, size=76, icon_size=38, transform_scale=6)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setIcon(QIcon("res/play-card.png"))  # or use your icon

        self.play_btn.clicked.connect(self._on_play_clicked)
        ov.addWidget(self.play_btn, 0, Qt.AlignHCenter)
        ov.addStretch(2)

        self.overlay.hide()

        main.addWidget(self.thumb_container, 0, Qt.AlignTop)

        # ---------- Text ----------
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

            
        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 15))
        self.title_lbl.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                padding: 0;
                font-weight: 550;
            }
        """)
        self.title_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.title_lbl.setWordWrap(True)

        # limit to 2 lines
        fm = QFontMetrics(self.title_lbl.font())
        line_height = fm.lineSpacing()
        max_height = line_height * 2

        self.title_lbl.setMaximumHeight(max_height)
        self.title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


        # ----- Subtitle -----
        self.subtitle_lbl = QLabel(self.subtitle_text)
        self.subtitle_lbl.setFont(QFont("Segoe UI", 10))
        self.subtitle_lbl.setStyleSheet("""
            QLabel {
                color: #bebfbd;
                background: transparent;
                padding: 0;
                font-weight: 550;
            }
        """)
        self.subtitle_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.subtitle_lbl.setWordWrap(True)

        # limit to 2 lines
        fm = QFontMetrics(self.subtitle_lbl.font())
        line_height = fm.lineSpacing()
        max_height = line_height * 2

        self.subtitle_lbl.setMaximumHeight(max_height)
        self.subtitle_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

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
                border: none;
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
        self.menu.setObjectName("playlistMenu")

        self.menu.addAction("Play next", lambda: print(f"[MENU] Play next: {self.title_text}"))
        self.menu.addAction("Add to queue", lambda: print(f"[MENU] Add to queue: {self.title_text}"))
        self.menu.addSeparator()
        self.menu.addAction("Remove playlist", lambda: print(f"[MENU] Remove: {self.title_text}"))
        self.menu.setCursor(Qt.PointingHandCursor)

        self.menu.setStyleSheet("""
            QMenu#playlistMenu {
                background-color: transparent; 
                border: 1px solid #3a3b3d;
                border-radius: 10px;
                padding: 6px 0px;
                color: white;
                font-size: 26px;
                font-family: 'Segoe UI';
            }

            QMenu#playlistMenu::item {
                padding: 10px 16px;
                border-radius: 6px;
                margin: 2px 8px;
            }

            QMenu#playlistMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.08);
            }

            QMenu#playlistMenu::item:pressed {
                background-color: rgba(255, 255, 255, 0.16);
            }

            QMenu#playlistMenu::separator {
                height: 1px;
                margin: 6px 14px;
                background-color: #3a3b3d;
            }
        """)


                

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(self._active_style)
        else:
            self.setStyleSheet(self._normal_style)

    def on_enter(self):
        self.overlay.show()

    def on_leave(self):
        self.overlay.hide()
        self._apply_style()

    def _on_play_clicked(self):
        if not self.play_callback:
            print(f"[UI] play playlist: {self.title_text}")
            return
        
        if self.play_callback:
            self.play_callback(self.mp3_path)

    def _on_clicked(self):
        print(f"[UI] open playlist: {self.title_text}")

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

        # self.setSpacing(30)
        # self.setContentsMargins(0, 0, 0, 0)
        # self.setViewportMargins(0, 0, 30, 40)
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

        # self.itemClicked.connect(self._on_item_clicked)

    def add_playlist(self, title, subtitle_text, path, pix, play_callback=None, top=False):
        item = QListWidgetItem()
        tile = PlaylistCard(title, subtitle_text, path, pix,
                            play_callback=play_callback, parent=self)
        item.setSizeHint(tile.size() + QSize(30, 30))

        if top:
            # insert at index 0 → pushes previous items down
            self.insertItem(0, item)
        else:
            # normal behavior → add at end
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 24,  QFont.Black))
        self.title_label.setStyleSheet("color: #ffffff;")

        layout.addWidget(self.title_label)

        self.grid = PlaylistGrid()
        layout.addWidget(self.grid)

    def add_playlist(self, title, subtitle_text, path, pix, play_callback=None, top = False):
        self.grid.add_playlist(title, subtitle_text, path, pix, play_callback = play_callback, top=top)



class ContentArea(QFrame):
    playRequested = pyqtSignal(str)

    def __init__(self, parent = None, music_dirs: list = None):
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


        # load local mp3 files....
        self.local_file_loader = LocalFilesLoader(music_dirs, parent=self)
        self.local_file_loader.config_one.connect(self.add_item)
        self.local_file_loader.finished.connect(self._finish_adding_loc_files)
        self.local_file_loader.start()

    def play_song(self, path: str = None):
        if not path:
            print(f"Path is empty")
            return
        
        print(f"playRequested : {path}")
        self.playRequested.emit(path)
        

    def _finish_adding_loc_files(self, status):
        if status:
            print(f"All Local Files added sucessfully")
        else:
            print("Maybe some Error in loading local files..")

        self.local_file_loader.deleteLater()


    def add_item(self, title, subtitle_text, path, pix, play = False):
        # is play then add on top
        self.section_library.add_playlist(title, subtitle_text, path, pix, play_callback=self.play_song, top=play)

        if play:
            self.play_song(path)

