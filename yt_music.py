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
    playRequest = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        size = 86
        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: blue;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        img_path = "C:\\Users\\freya\\Downloads\\song.jpg"

        px  = QPixmap(img_path)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(size, size)
        self.image_label.setAlignment(Qt.AlignCenter)
        applyRoundedImage(self.image_label, px, size=size, radius=8)
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
        self.play_icon.clicked.connect(self._play_requested)

        self.play_icon.setStyleSheet("color: white;")
        ov_layout.addWidget(self.play_icon)

        layout.addWidget(self.image_label)

    def _play_requested(self):
        print("...PlaySignalOriginated...")
        self.playRequest.emit("This is Fuck")

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
    playRequest = pyqtSignal(str)

    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(108)
        # self.setCursor(Qt.PointingHandCursor)

        main = QHBoxLayout()
        main.setContentsMargins(24, 8, 24, 8)  # left/right padding
        main.setSpacing(16)

        # cover
        self.thumb = HoverThumb(parent=self)
        self.thumb.playRequest.connect(self._play_requested)
        main.addWidget(self.thumb)

        # text block
        text_col = QVBoxLayout()
        text_col.setContentsMargins(5, 6, 0, 20)
        text_col.setSpacing(1)

        self.title_lbl = QLabel(title)
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

        self.subtitle_lbl = QLabel(subtitle)
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

    def _play_requested(self, txt):
        print(f"Recieved [TrackRow] : {txt}")
        self.playRequest.emit(txt)


    def show_menu(self):
        self.menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomRight()))

    def enterEvent(self, event):
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._base_style)
        super().leaveEvent(event)


class SearchResultPage(QWidget):
    """
    Page that mimics the YT Music album + track list layout.
    """
    playRequest = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #000000;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        # Album header
        album_title = QLabel("Tubelight (Original Motion Picture Soundtrack)")
        album_title.setStyleSheet("color: white;")
        album_title.setFont(QFont("Segoe UI", 16, QFont.DemiBold))

        album_meta = QLabel("Album • Pritam • 2017")
        album_meta.setStyleSheet("color: #b3b3b3;")
        album_meta.setFont(QFont("Segoe UI", 11))

        outer.addWidget(album_title)
        outer.addWidget(album_meta)

        # Scrollable track list
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        outer.addWidget(scroll, 1)

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, True)
        content.setStyleSheet("background-color: #000000;")
        scroll.setWidget(content)

        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(0, 16, 0, 16)
        vbox.setSpacing(0)

        # demo data – you will fill this with real search results
        demo_tracks = [
            ("Main Agar (From \"Tubelight\")",
             "Song • Pritam & Atif Aslam • 137M plays"),
            ("Naach Meri Jaan (From \"Tubelight\")",
             "Song • Pritam, Kamaal Khan, Nakash Aziz & Dev Negi • 123M plays"),
            ("Radio (From \"Tubelight\")",
             "Song • Pritam, Kamaal Khan & Amit Mishra • 49M plays"),
            ("Tinka Tinka Dil Mera (From \"Tubelight\")",
             "Song • Pritam & Rahat Fateh Ali Khan • 25M plays"),
            ("Kuch Nahi (From \"Tubelight\")",
             "Song • Pritam • 5M plays"),
        ]

        # add rows
        for title, subtitle in demo_tracks:
            row = TrackRow(title, subtitle)
            row.playRequest.connect(self._play_requested)
            vbox.addWidget(row)

        vbox.addStretch(1)

    def _play_requested(self, txt):
        print(f"Recieved [SearchResultPage] : {txt}")
        self.playRequest.emit(txt)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Music Style List Demo")
        self.resize(900, 600)
        page = SearchResultPage(self)
        page.playRequest.connect(self._play_requested)
        self.setCentralWidget(page)

    def _play_requested(self, txt):
        print(f"Recieved [MainWindow] : {txt}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
