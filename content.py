from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QListWidgetItem, 
    QListWidget, QListView, QMenu, QSizePolicy, 
)
from PyQt5.QtGui import QFont, QPixmap, QFontMetrics, QIcon
from helper import LocalFilesLoader
from helper import round_pix, round_pix_form_path

class HoverButton(QPushButton):
    def __init__(self, *args, size: int = 76, icon_size: int = 38, transform_scale = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = size

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
                border-radius: { self._size//2 }px;
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

    def set_padding(self, value):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.55);
                border-radius: { self._size//2 }px;
                border: none;
                color: #000000;
                padding-left: {value}px;        
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


class SongCard(QWidget):
    playRequested = pyqtSignal(int)
    playToggleRequested = pyqtSignal()

    def __init__(self, song_id: int, title: str, subtitle: str, path: str, cover_path: str, parent=None):
        super().__init__(parent)
        # song id
        self.song_id = song_id
        self.title_text = title
        self.subtitle_text = subtitle
        self.mp3_path = path
        self.cover_path = cover_path

        self._active = False
        self._width  = 240  # 260
        self._height = 292  #220

        self.thumb_width = self._width

        add_thum_height = 85 #105
        self.thumb_height = 158 + add_thum_height #self.height - 40
        self._height += add_thum_height


        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(self._width, self._height)
        self.setStyleSheet("border: none;  background: green; margin: 20px;")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(6)

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
        self.thumb_label.setPixmap(
            round_pix_form_path(cover_path, self.thumb_width, self.thumb_height, 8)
        )


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
        self.play_icon = QIcon("res/play-card.png")
        self.pause_icon = QIcon("res/pause.png")
        
        self.play_btn = HoverButton(parent=self.overlay, size=76, icon_size=38, transform_scale=6)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setIcon(self.play_icon)  # or use your icon

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
        self.title_lbl.setFont(QFont("Segoe UI", 14))
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
                color: #b1b2b1;
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
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 16px;
                border: none;
            }
        """)
        

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
        if active:
            self.play_btn.clicked.disconnect()
            self.play_btn.clicked.connect(self.playToggleRequested.emit)
            self._active = True
            self.overlay.show()


        else:
            self.play_btn.clicked.disconnect()
            self.play_btn.clicked.connect(self._on_play_clicked)
            self._active = False
            self.set_play(False)
            self.overlay.hide()


    def set_play(self, value: bool):
        if value:
            self.play_btn.setIcon(self.pause_icon)
            self.play_btn.set_padding(0)

        else:
            self.play_btn.setIcon(self.play_icon)
            self.play_btn.set_padding(0)

    def on_enter(self):
        if not self._active:
            self.overlay.show()

    def on_leave(self):
        if not self._active:
            self.overlay.hide()

    def _on_play_clicked(self):
        self.playRequested.emit(self.song_id)
        

    def _on_clicked(self):
        print(f"[UI] open playlist: {self.title_text}")

    def _on_menu_clicked(self):
        pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight())
        self.menu.exec_(pos)



class PlaylistSection(QWidget):
    playRequested = pyqtSignal(int)
    playToggleRequested = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.items: dict[str, SongCard] = {}

        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # --- Section title ---
        self.title_label = QLabel(title, self)
        self.title_label.setFont(QFont("Segoe UI", 24, QFont.Black))
        self.title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.title_label)

        # --- Internal list acting as grid ---
        self._list = QListWidget(self)

        self._list.setViewMode(QListView.IconMode)
        self._list.setFlow(QListView.LeftToRight)
        self._list.setWrapping(True)
        self._list.setResizeMode(QListView.Adjust)

        self._list.setMovement(QListView.Snap)
        self._list.setFrameShape(QListWidget.NoFrame)
        self._list.setStyleSheet("QListWidget { background: transparent; border: none; }")

        # disable scrollbars; outer scroll area will handle scrolling
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # enable drag & drop reordering
        self._list.setDragEnabled(False)
        self._list.setAcceptDrops(False)
        self._list.setDropIndicatorShown(False)
        # self._list.setDragDropMode(QAbstractItemView.InternalMove)

        layout.addWidget(self._list)


    def set_broadcast(self, type: str, song_id: int, value: bool):
        card_obj = self.items.get(song_id)
        if not card_obj:
            return
        
        if type == "active":
            card_obj.set_active(value)

        elif type == "playing":
            card_obj.set_play(value)

        else:
            print(f"[PlaylistSection][broadcast] => not implemented for type : {type}")


    def request_play(self, song_id: int):
        self.playRequested.emit(song_id)

    def add_song(self, song_id: int, title: str, subtitle: str, path: str, cover_path: str, play = False):
        """
        Add a PlaylistCard title to this section.
        If top=True, inserts at top; otherwise appends at the end.
        """
        item = QListWidgetItem(self._list)

        song_card = SongCard(song_id, title, subtitle, path, cover_path)
        song_card.playRequested.connect(self.request_play)
        song_card.playToggleRequested.connect(self.playToggleRequested.emit)
        
        # add song_card object to items dict with path as key..
        self.items[song_id] = song_card

        # give each title some breathing room
        item.setSizeHint(song_card.size() + QSize(30, 30))

        if play:
            self._list.insertItem(0, item)
        else:
            self._list.addItem(item)

        self._list.setItemWidget(item, song_card)
        self._update_height_for_content()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_height_for_content()

    def _update_height_for_content(self):
        """
        Resize the internal QListWidget vertically so all rows are visible.
        The outer page scroll area will then scroll the whole section.
        """
        count = self._list.count()
        if count == 0:
            self._list.setFixedHeight(0)
            return

        last_item = self._list.item(count - 1)
        rect = self._list.visualItemRect(last_item)
        content_bottom = rect.bottom() + self._list.spacing()

        # Add a few extra pixels padding
        self._list.setFixedHeight(content_bottom + 4)

    def _on_item_clicked(self, item: QListWidgetItem):
        clicked_title = self._list.itemWidget(item)
        print(f"[UI] open playlist: {clicked_title.title_text}")

        # # mark only one as active
        # for i in range(self._list.count()):
        #     it = self._list.item(i)
        #     title = self._list.itemWidget(it)
        #     title.set_active(title is clicked_title)


class ContentArea(QFrame):
    playRequested = pyqtSignal(int)
    playToggleRequested = pyqtSignal()

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
        self.section_library.playRequested.connect(self.play_requested)
        self.section_library.playToggleRequested.connect(self.playToggleRequested.emit)

        main_layout.addWidget(self.section_library)

        # # Section 2
        # self.section_featured = PlaylistSection("Featured playlists for you")
        # main_layout.addWidget(self.section_featured)

        # keep sections pinned to top if there are few
        main_layout.addStretch(1)


        # load local mp3 files....
        # self.local_file_loader = LocalFilesLoader(music_dirs, parent=self)
        # self.local_file_loader.config_one.connect(self.add_item)
        # self.local_file_loader.finished.connect(self._finish_adding_loc_files)
        # self.local_file_loader.start()

    def set_broadcast(self, type: str, song_id: int, value: bool):
        # print(f"Boradcast[Content] => {type} | {song_id} | {value}")
        self.section_library.set_broadcast(type, song_id, value)
        

    def play_requested(self, song_id: int):
        if song_id is None:
            print(f"Song id not found..")
            return
        
        print(f"Playing SongId : {song_id}")
        self.playRequested.emit(song_id)
        


    def add_item(self, song_id: int, title: str, subtitle: str, path: str, cover_path: str, play=False):
        # is play then add on top
        self.section_library.add_song(song_id, title, subtitle, path, cover_path, play=play)

        if play:
            self.play_requested(path)

