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


def make_section(section_name, cards_data):
    widget = QWidget()
    v = QVBoxLayout(widget)
    v.setSpacing(12)
    v.setContentsMargins(0, 0, 0, 0)

    title_lbl = QLabel(section_name)
    title_lbl.setFont(QFont("Segoe UI", 20, QFont.Black))
    title_lbl.setStyleSheet("color: #ffffff;")
    v.addWidget(title_lbl)

    row = QWidget()
    h = QHBoxLayout(row)
    h.setSpacing(14)
    h.setContentsMargins(0, 0, 0, 0)

    for t, s in cards_data:
        h.addWidget(Card(t, s))

    h.addStretch()
    v.addWidget(row)
    return widget


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

        layout.addWidget(make_section("From your library", [
            ("most", "Local playlist · 13 tracks"),
            ("EngFav", "Local playlist · 7 tracks"),
            ("best", "Local playlist · 7 tracks"),
            ("eng", "Local playlist · 12 tracks"),
        ]))

        layout.addWidget(make_section("Featured playlists for you", [
            ("Bridal Entry", "Bollywood · Arijit Singh…"),
            ("Ishq Sufiyana", "Arijit Singh, Pritam…"),
            ("Bollywood Romance", "Romantic Essentials"),
        ]))

        layout.addWidget(make_section("Albums for you", [
            ("Rockstar", "Album · A.R. Rahman"),
            ("MAIN HOON NA", "Album · Various Artists"),
            ("1920", "Album · Adnan Sami"),
        ]))

        layout.addStretch()
        outer.addWidget(scroll, 1)