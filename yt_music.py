import os
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QMenu, QGraphicsOpacityEffect
)
from helper import CircularProgress, LoadingSpinner, YTSearchThread, ConfigResult, ConvertingSpinner
from tube import Dtube
from helper import get_pixmap, round_pix
from common import ScrollArea
from typing import List
from util import trim_text, MUSIC_DIR_PATH, make_title_path


class HoverThumb(QWidget):
    downloadRequested = pyqtSignal(str)
    playRequested = pyqtSignal(str)

    def __init__(self, pix: QPixmap, parent=None):
        super().__init__(parent)

        size = 86
        self.setFixedSize(size, size)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setPixmap(round_pix(pix, size, size, 6))

        self.image_label.setStyleSheet(f"""
            QLabel {{
                border: none;
                padding: 0;
                border-radius: 14px;
            }}
        """)

        main_layout.addWidget(self.image_label)

        # ----- Overlay -----
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WA_StyledBackground, True)
        self.overlay.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 110);
                border-radius: 4px;
            }
        """)
        self.overlay.setGeometry(self.rect())
        self.overlay.hide()

        ov_layout = QHBoxLayout(self.overlay)
        ov_layout.setContentsMargins(0, 0, 0, 0)
        ov_layout.setAlignment(Qt.AlignCenter)

        # spinner 
        self.spinner = LoadingSpinner(size-16, self.overlay)
        self.spinner.hide()

        # download progress
        self.progress = CircularProgress(size-16, self.overlay)
        self.progress.hide()

        # converting
        self.convering_spinner = ConvertingSpinner(size-16, self.overlay)
        self.convering_spinner.hide()

        # play button---
        self.play_icon = QIcon("res/play-card.png")
        self.down_icon = QIcon("res/downloads.png")


        # download button
        self.download_btn = QPushButton(self.overlay)
        self.download_btn.setFixedSize(size, size)
        self.download_btn.setIcon(self.down_icon)  # or use your icon
        self.download_btn.setIconSize(QSize(30, 30))
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self._download_requested)
        self.download_btn.setStyleSheet("color: white;")
        ov_layout.addWidget(self.download_btn)


        # done checkmark
        self.done_label = QLabel("✓", self.overlay)
        self.done_label.setAlignment(Qt.AlignCenter)
        self.done_label.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.done_label.setStyleSheet("""
            QLabel {
                color: #00E676;
                background: transparent;
            }
        """)
        self.done_label.hide()

        ov_layout.addWidget(self.spinner)
        ov_layout.addWidget(self.convering_spinner)
        ov_layout.addWidget(self.progress)
        ov_layout.addWidget(self.done_label)

        # opacity effect for *finish* animation
        self.overlay_effect = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self.overlay_effect)
        self.overlay_effect.setOpacity(1.0)

        self.fade_anim = QPropertyAnimation(self.overlay_effect, b"opacity", self)
        self.fade_anim.setDuration(400)
        self.fade_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_anim.finished.connect(self._on_fade_finished)

        # internal mode
        self.mode = "idle"


    def _download_requested(self):
        print("...PlaySignalOriginated... Down")
        self.downloadRequested.emit("down")

    def _play_requested(self):
        print("...PlaySignalOriginated... Play")
        self.playRequested.emit("play")


    def setProgress(self, value: int):
        """Call from your yt-dlp progress hook."""
        self.progress.setValue(value)

    # -------- Internal state logic -------- #

    def set_mode(self, mode: str):
        self._set_mode(mode=mode)

    def _set_mode(self, mode: str):
        self.mode = mode

        # reset visibility
        self.progress.hide()
        self.download_btn.hide()
        self.done_label.hide()
        self.fade_anim.stop()
        self.spinner.stop()
        self.convering_spinner.stop()
        self.overlay_effect.setOpacity(1.0)

        if mode == "idle":
            self.overlay.hide()
            self.download_btn.setIcon(self.down_icon)
            self.download_btn.show() # download btn
            self.download_btn.clicked.disconnect(self._play_requested)
            self.download_btn.clicked.connect(self._download_requested)


        elif mode == "loading":
            self.overlay.show()
            self.spinner.start()

        elif mode == "downloading":
            self.overlay.show()
            self.progress.show()

        elif mode == "converting":
            self.overlay.show()
            self.convering_spinner.start()

        elif mode == "done":
            self.overlay.show()
            self.done_label.show()
            QTimer.singleShot(400, self._start_fade_out)

        elif mode == "play":
            self.overlay.hide()
            self.download_btn.show()
            self.download_btn.setIcon(self.play_icon)  # or use your icon
            self.download_btn.clicked.disconnect(self._download_requested)
            self.download_btn.clicked.connect(self._play_requested)



    def _start_fade_out(self):
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def _on_fade_finished(self):
        if self.mode == "done":
            self._set_mode("play")

    # keep overlay resized
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())

    # show overlay only on hover if in loading/downloading/done modes
    def enterEvent(self, event):
        if self.mode in ("idle", "play"):
            self.overlay.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # if still loading/downloading, we can leave overlay visible
        # or hide it – your choice.
        if self.mode in ("idle", "play"):
            self.overlay.hide()
        super().leaveEvent(event)


class TrackRow(QWidget):
    downloadRequested = pyqtSignal(str, str, str, int)
    playRequested = pyqtSignal(str)

    def __init__(self, title: str, subtitle: str, artists: list, vid: str, pix: QPixmap, track_id: int, parent=None):
        super().__init__(parent)
        self.title_txt = title
        self.subtitle_txt = subtitle
        self.artists = artists
        self.vid = vid
        self.track_id = track_id
        self.file_path = None

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(108)
        # self.setCursor(Qt.PointingHandCursor)

        main = QHBoxLayout()
        main.setContentsMargins(0, 8, 24, 8)  # left/right padding
        main.setSpacing(16)

        # cover
        self.thumb = HoverThumb(pix=pix, parent=self)
        self.thumb.downloadRequested.connect(self._download_requested)
        self.thumb.playRequested.connect(self._play_requested)
        main.addWidget(self.thumb)

        # text block
        text_col = QVBoxLayout()
        text_col.setContentsMargins(5, 6, 0, 20)
        text_col.setSpacing(1)
        

        self.title_lbl = QLabel(trim_text(self.title_txt, 62))
        self.title_lbl.setFont(QFont("Segoe UI", 14))
        self.title_lbl.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: white;
                font-weight: 550;
            }
                                    
            QLabel:hover {
                background-color: transparent;
            }
        """)
        self.title_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.subtitle_lbl = QLabel(trim_text(self.subtitle_txt, 80))
        self.subtitle_lbl.setFont(QFont("Segoe UI", 11))
        self.subtitle_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.subtitle_lbl.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: #b3b3b3;
                font-weight: 550;
            }
                                    
            QLabel:hover {
                background-color: transparent;
            }
        """)

        text_col.addWidget(self.title_lbl)
        text_col.addWidget(self.subtitle_lbl)

        main.addLayout(text_col, 1)


        # spacer + menu button
        self.menu_btn = QPushButton(self)
        # self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setIcon(QIcon("res/three-dot-menu.png"))
        self.menu_btn.setFixedSize(48, 48)
        self.menu_btn.setIconSize(QSize(22, 22)) 
        self.menu_btn.setCursor(Qt.PointingHandCursor)

        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 24px;
            }
                                    
            QPushButton:hover {
                background-color:  rgba(255, 255, 255, 0.08);
            }
            QPushButton:pressed {
                background-color:  rgba(255, 255, 255, 0.1);
            }
        """)
        main.addWidget(self.menu_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        # self.menu_btn.hide()

        # underline separator like YT Music
        bottom_line = QFrame(self)
        bottom_line.setStyleSheet("background-color: #262626; margin: 2px")
        bottom_line.setFixedHeight(1)

        bottom_layout = QVBoxLayout(self)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        bottom_layout.addLayout(main)
        bottom_layout.addWidget(bottom_line)

        self.setLayout(bottom_layout)

        # simple menu
        self.menu = QMenu(self)
        self.menu.setObjectName("SearchMenu")
        self.menu.addAction("Play next")
        self.menu.addAction("Add to queue")
        self.menu.addSeparator()
        self.menu.addAction("Go to album")
        self.menu.setStyleSheet("""
            QMenu#SearchMenu {
                background-color: transparent; 
                border: 1px solid #3a3b3d;
                border-radius: 10px;
                padding: 6px 0px;
                color: white;
                font-size: 22px;
                font-family: 'Segoe UI';
            }

            QMenu#SearchMenu::item {
                padding: 10px 16px;
                border-radius: 6px;
                margin: 2px 8px;
            }

            QMenu#SearchMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.08);
            }

            QMenu#SearchMenu::item:pressed {
                background-color: rgba(255, 255, 255, 0.16);
            }

            QMenu#SearchMenu::separator {
                height: 1px;
                margin: 6px 14px;
                background-color: #3a3b3d;
            }
        """)

        self.menu_btn.clicked.connect(self.show_menu)

        # normal + hover style for row background
        self._base_style = """
            QWidget {
                background-color: transparent;
            }
        """
        self._hover_style = """
            QWidget {
                background-color: rgba(255, 255, 255, 0.06);
            }
        """
        self.setStyleSheet(self._base_style)

    def set_mode(self, mode: str):
        print(f"Setting State : {mode}")
        self.thumb.set_mode(mode)

    def get_mode(self):
        return self.thumb.mode
    
    def set_file_path(self, file_path: str):
        self.file_path = file_path

    def setProgress(self, value: int):
        self.thumb.setProgress(value)

    def _download_requested(self, txt):
        print(f"Recieved [TrackRow] : {txt}")
        self.downloadRequested.emit(self.title_txt, self.subtitle_txt, self.artists, self.vid, self.track_id)

    def _play_requested(self, txt):
        print(f"Play Requested : {txt}")
        self.playRequested.emit(self.file_path)


    def show_menu(self):
        self.menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight()))

    def enterEvent(self, event):
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._base_style)
        super().leaveEvent(event)


class YtScreen(QFrame):
    downloadRequested = pyqtSignal(str, str, str)
    addItemHomeRequested = pyqtSignal(str, str, str, QPixmap, bool)
    playRequested = pyqtSignal(str)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #000000;")
            
        outer = QVBoxLayout(self)
        outer.setContentsMargins(80, 10, 2, 5)
        outer.setSpacing(0)

        outer.addSpacing(20)

        # Album header
        header = QLabel("YT MUSIC")
        header.setStyleSheet("color: white; font-weight: 600; margin-left: 10px;")
        header.setFont(QFont("Segoe UI", 15))

        font = header.font()
        font.setUnderline(True)
        header.setFont(font)
        header.setFixedHeight(32)

        outer.addWidget(header)

        line = QFrame()
        line.setStyleSheet("background-color: #262626; margin-right: 35px; margin-top: -10px;")
        line.setFixedHeight(1)
        outer.addWidget(line)

        # Scroll area (only vertical)
        scroll = ScrollArea()
        outer.addWidget(scroll, 1)

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, True)
        content.setStyleSheet("background-color: #000000;")
        scroll.setWidget(content)

        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(24, 16, 24, 24)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.track_list: List[TrackRow] = [] # store all the TrackRow

        # icon_path = "C:\\Users\\freya\\Downloads\\song.jpg"
        # pix  = QPixmap(icon_path)
        # tite = "Naach Meri Jaan (From \"Tubelight\") Aditya Mukhiya and palak Thakur Lve each other and also fuck Each Other".upper()
        # sub = "Song • Pritam, Kamaal Khan, Nakash Aziz & Dev Negi • 123M plays Hellow mahadev ji maaf krdijiye please mahadev ".upper()
        # url = ""
        # self.config_one(tite, sub, url, pix)
        
    def set_broadcast(self, type: str, item_id: str, value: bool):
        pass

    def is_already_downloaded(self, title: str) -> str | None:
        # check if the file is already downloaded 
        # use tite to make a path and then check is it esists
        # if it is.. then change the 'mode' to 'play'
        assume_filename = f"{make_title_path(title)}.mp3"
        assume_path = os.path.join(MUSIC_DIR_PATH, assume_filename)

        if os.path.exists(assume_path):
            return assume_path
             
    

    def clear_results(self):
        self.track_list.clear()
        # remove stretch first
        item = self.main_layout.takeAt(self.main_layout.count() - 1)
        if item:
            del item

        # remove all widget rows
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.setParent(None)
                widget.deleteLater()


    def config_one(self, title: str, subtitle: str, artists: list, vid: str, pix: QPixmap):
        track_id = len(self.track_list)
        
        row = TrackRow(title, subtitle, artists, vid, pix, track_id, parent=self)
        row.downloadRequested.connect(self._download_requested)
        row.playRequested.connect(self._play_requested)
        self.main_layout.addWidget(row)

        # add row in track_list
        self.track_list.append(row)

        # check is the file is already downloaded...
        exists_path = self.is_already_downloaded(title)
        if exists_path:
            # change "mode" to "play"
            row.set_file_path(exists_path)
            row.set_mode("play")

    

    def config_finished(self, status):
        if status:
            print("Config finished...")
        else:
            print("Error in Config..")

        self.main_layout.addStretch(1)


    def config_search(self, result1: list, result2: list):
        print(f"Search Done : TotalResutl => {len(result1) + len(result2)}")
        print(f"Clearing prevois data...")
        self.clear_results()
        print("cleared...")

        config_result = ConfigResult(result=result1, parent=self)
        config_result.add_one.connect(self.config_one)
        config_result.finished.connect(self.config_finished)


        config_result2 = ConfigResult(result=result2, parent=self)
        config_result2.add_one.connect(self.config_one)
        config_result2.finished.connect(self.config_finished)

        # start both
        config_result.start()
        config_result2.start()


        if not hasattr(self, "_config_threads"):
            self._config_threads = []
        self._config_threads.append(config_result)
        self._config_threads.append(config_result2)

        print(f"currentThread -> {self._config_threads}")
    

    def search_call(self, query: str):
        print(f"YTSearch Query : {query}")

        thread = YTSearchThread(query=query, parent=self)
        thread.finished.connect(self.config_search)
        thread.start()
        print(f"start thread_id ==> {thread}")

        if not hasattr(self, "_search_threads"):
            self._search_threads = []
        self._search_threads.append(thread)


    def download_finished(self, title: str = None, subtitle: str = None, path: str = None, track_id: int = None):
        print(f"FileDownloaded : {path}")

        # set the downloaded file path
        if track_id:
            track_obj = self.track_list[track_id]
            track_obj.set_file_path(path)

        play = True
        self.addItemHomeRequested.emit(title, subtitle_text, path,  get_pixmap(path), play)

        thread = self.sender()
        if hasattr(self, "_down_threads") and thread in self._down_threads:
            self._down_threads.remove(thread)

        thread.deleteLater()


    def download_progress(self, track_id, mode, value: int = 0):
        if mode == "error":
            print(f"Error occured during downloading..")
            return
        
        # track object...
        track_obj = self.track_list[track_id]

        if mode != "percentage":
            track_obj.set_mode(mode)
            return

        # set progess value
        track_obj.setProgress(int(value))
    
    def _play_requested(self, file_path: str):
        if not file_path:
            print(f"Can't play an invalid file path")
            return
        
        print(f"sending request to play : {file_path}")
        self.playRequested.emit(file_path)


    def _download_requested(self, title: str, subtitle: str, artists: list, vid: str, track_id: int):
        print(f"Track[{vid}] [download request] => {title}")

        if not vid:
            print(f"===> Path is empty")
            return
        
        thread = Dtube(title, subtitle, artists, vid, track_id, parent=self)
        thread.finished.connect(self.download_finished)
        thread.progress.connect(self.download_progress)
        thread.start()
        print(f"start thread_id ==> {thread}")

        if not hasattr(self, "_down_threads"):
            self._down_threads = []
        self._down_threads.append(thread)