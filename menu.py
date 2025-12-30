from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QCursor


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
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color: white;")

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
        self.remove = MenuItem("Remove playlist")

        layout.addWidget(self.play_next)
        layout.addWidget(self.add_queue)
        layout.addWidget(MenuSeparator())
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


    def show_at_cursor(self):
        self.container.adjustSize()
        self.adjustSize()

        pos = QCursor.pos()
        self.move(pos + QPoint(-self.width() + 12, 12))
        self.show()