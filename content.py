from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QSpacerItem, 
    QLineEdit, QSizePolicy, QToolButton
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette

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


class Section(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)

        self.vb_layout = QVBoxLayout(self)
        self.vb_layout.setSpacing(12)
        self.vb_layout.setContentsMargins(0, 0, 0, 0)

        self.title_lbl = QLabel(name)
        self.title_lbl.setFont(QFont("Segoe UI", 20, QFont.Black))
        self.title_lbl.setStyleSheet("color: #ffffff;")
        self.vb_layout.addWidget(self.title_lbl)

        self.row = QWidget()
        self.hb_layout = QHBoxLayout(self.row)
        self.hb_layout.setSpacing(14)
        self.hb_layout.setContentsMargins(0, 0, 0, 0)
        self.hb_layout.addWidget(self.row)


    def add_item(self, name, dis):
        self.hb_layout.addWidget(Card(name, dis))


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

        from_lib_sec = Section("From your library")

        from_lib_sec.add_item("most", "Local playlist · 13 tracks")
        from_lib_sec.add_item("EngFav", "Local playlist · 7 tracks")
        from_lib_sec.add_item("best", "Local playlist · 7 tracks")
        from_lib_sec.add_item("eng", "Local playlist · 12 tracks")

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