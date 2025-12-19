from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog,
    QLabel, QLineEdit, QPushButton, QComboBox, 
    QHBoxLayout, QVBoxLayout
)

from PyQt5.QtGui import QFont, QColor, QPalette


class CreatePlaylistPopup(QDialog):
    requestCreatePlaylist = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(630, 500)

        # Context-menu like behavior
        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint
        )

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._build_ui()

    def _build_ui(self):
        # Outer layout (for rounded corners)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName("container")
        outer.addWidget(container)

        #1e1e1e
        container.setStyleSheet("""
            QWidget#container {
                background-color: #282828;
                border-radius: 12px;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
                                
            }
                                
            QLineEdit, QComboBox {
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-bottom: 1px solid #444;
                padding: 6px;
                font-size: 22px;
                font-weight: 600px;
            }
                                
            QLineEdit:focus {
                border-bottom: 1px solid #1db954;
            }
                                
                                                
            QComboBox:focus {
                border-bottom: 1px solid #1db954;
            }
                                
            QComboBox QAbstractItemView {
                color: #BEBEBE;
                background-color: #1e1e1e;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #1db954;
                color: #000000;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #333;
                color: #ffffff;
            }

                                
            QPushButton {
                padding: 10px 24px;
                border-radius: 20px;
            }
                                
            QPushButton#cancelBtn {
                background: transparent;
                color: #bbb;
            }
            QPushButton#cancelBtn:hover {
                color: white;
                background: #393939;
            }
                                
            QPushButton#createBtn {
                background-color: #0f79c0;
                color: white;
            }
            QPushButton#createBtn:hover {
                background-color: #086cae;
            }

        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(45, 30, 45, 22)

        # Title
        title = QLabel("New playlist")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        layout.addWidget(title)
        layout.addSpacing(42)


        # Inputs
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Title")
        
        pal = self.title_edit.palette()
        pal.setColor(QPalette.PlaceholderText, QColor("#BEBEBE"))
        self.title_edit.setPalette(pal)
        layout.addWidget(self.title_edit)
        layout.addSpacing(38)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Description")
        
        pal = self.desc_edit.palette()
        pal.setColor(QPalette.PlaceholderText, QColor("#BEBEBE"))
        self.desc_edit.setPalette(pal)

        layout.addWidget(self.desc_edit)
        layout.addSpacing(38)


        # Privacy
        privacy_label = QLabel(" Privacy")
        privacy_label.setStyleSheet("color: #BEBEBE; font-size: 20px;")
        layout.addWidget(privacy_label)

        self.privacy_combo = QComboBox()
        self.privacy_combo.addItems([
            "Private",
            "Public"
        ])

        self.privacy_combo.setFixedWidth(240)
        self.privacy_combo.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.privacy_combo)


        layout.addStretch()

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()

        font = QFont("Helvatica", 11)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setFont(font)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.close)

        create_btn = QPushButton("Create")
        create_btn.setObjectName("createBtn")
        create_btn.setFont(font)
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.clicked.connect(self._create)

        btns.addWidget(cancel_btn)
        btns.addSpacing(20)
        btns.addWidget(create_btn)
        layout.addLayout(btns)
        layout.addSpacing(15)


    def focusOutEvent(self, event):
        self.close()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if not self.geometry().contains(event.globalPos()):
                self.close()
                return True
        return False

    def closeEvent(self, event):
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)

    def _create(self):
        self.requestCreatePlaylist.emit(
            self.title_edit.text(),
            self.desc_edit.text(),
            self.privacy_combo.currentText(),
        )

        self.close()
