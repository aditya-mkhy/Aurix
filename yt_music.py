import sys
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QMenu
)


from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QListWidgetItem, 
    QListWidget, QListView, QAbstractItemView, QMenu, 
    QSizePolicy, 
)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QFontMetrics, QPainterPath, QIcon

from player import MusicPlayer
from helper import LocalFilesLoader

from ytmusicapi import YTMusic
from PyQt5.QtGui import QPixmap
import requests
from tube import Dtube
from helper import get_pixmap
from common import ScrollArea
from helper import YTSearchThread, ConfigResult
# ---------- Small helpers ----------

def make_placeholder_cover(size=64, color=QColor("#444")):
    """Create a simple square pixmap placeholder for album art."""
    pm = QPixmap(size, size)
    pm.fill(color)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#666"))
    painter.drawRect(0, 0, size, size)
    painter.end()
    return pm


def applyRoundedImage(label, pix: QPixmap, size: int = 90, radius: int = 16):

    pm = pix.scaled(
        size,
        size,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation
    )

    rounded = QPixmap(QSize(size, size))
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)

    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)

    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pm)
    painter.end()
    label.setPixmap(rounded)


class HoverThumb(QWidget):
    downloadRequested = pyqtSignal(str)

    def __init__(self, pix: QPixmap, parent=None):
        super().__init__(parent)

        size = 86
        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: blue;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(size, size)
        self.image_label.setAlignment(Qt.AlignCenter)
        applyRoundedImage(self.image_label, pix, size=size, radius=8)
        # self.image_label.setScaledContents(True)

        self.image_label.setStyleSheet(f"""
            QLabel {{
                border: none;
                padding: 0;
                border-radius: 14px;
            }}
        """)


        # overlay play icon
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WA_StyledBackground, True)#rgba(0, 0, 0, 110)
        # self.overlay.setCursor(Qt.PointingHandCursor)
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

        self.play_icon = QPushButton(self.overlay)
        self.play_icon.setFixedSize(size, size)
        self.play_icon.setIcon(QIcon("res/downloads.png"))  # or use your icon
        self.play_icon.setIconSize(QSize(30, 30))
        self.play_icon.setCursor(Qt.PointingHandCursor)
        self.play_icon.clicked.connect(self._download_requested)

        self.play_icon.setStyleSheet("color: white;")
        ov_layout.addWidget(self.play_icon)

        layout.addWidget(self.image_label)

    def _download_requested(self):
        print("...PlaySignalOriginated...")
        self.downloadRequested.emit("down")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())

    def enterEvent(self, event):
        self.overlay.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.overlay.hide()
        super().leaveEvent(event)


class TrackRow(QWidget):
    downloadRequested = pyqtSignal(str, str, str)

    def __init__(self, title: str, subtitle: str, url: str, pix: QPixmap, parent=None):
        super().__init__(parent)
        self.title_txt = title
        self.subtitle_txt = subtitle
        self.url = url

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(108)
        # self.setCursor(Qt.PointingHandCursor)

        main = QHBoxLayout()
        main.setContentsMargins(0, 8, 24, 8)  # left/right padding
        main.setSpacing(16)

        # cover
        self.thumb = HoverThumb(pix=pix, parent=self)
        self.thumb.downloadRequested.connect(self._download_requested)
        main.addWidget(self.thumb)

        # text block
        text_col = QVBoxLayout()
        text_col.setContentsMargins(5, 6, 0, 20)
        text_col.setSpacing(1)

        self.title_lbl = QLabel(self.title_txt)
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

        self.subtitle_lbl = QLabel(self.subtitle_txt)
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

    def _download_requested(self, txt):
        print(f"Recieved [TrackRow] : {txt}")
        self.downloadRequested.emit(self.title_txt, self.subtitle_txt, self.url)



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

    
        # add rows
        # for title, subtitle in demo_tracks:
        #     row = TrackRow(title, subtitle)
        #     row.downloadRequested.connect(self._download_requested)
        #     self.main_layout.addWidget(row)

        # self.main_layout.addStretch(1)



    def clear_results(self):
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


    def config_one(self, title: str, subtitle: str, url: str, pix: QPixmap):
        row = TrackRow(title, subtitle, url, pix)
        row.downloadRequested.connect(self._download_requested)
        self.main_layout.addWidget(row)

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


    def download_finished(self, title: str = None, subtitle_text: str = None, path: str = None):
        print(f"FileDownloaded : {path}")
        self._add_home_callback(title, subtitle_text, path, get_pixmap(path), play = True)

        thread = self.sender()
        if hasattr(self, "_down_threads") and thread in self._down_threads:
            self._down_threads.remove(thread)

        thread.deleteLater()


    def _download_requested(self, title: str = None, subtitle_text: str = None, url: str = None):

        if not url:
            print(f"Path is empty")
            return
        
        print(f" Downloading Song : {title}  =>  {url}")
        thread = Dtube(title=title, subtitle_text=subtitle_text, url=url, parent=self)
        thread.finished.connect(self.download_finished)
        thread.start()
        print(f"start thread_id ==> {thread}")

        if not hasattr(self, "_down_threads"):
            self._down_threads = []
        self._down_threads.append(thread)
