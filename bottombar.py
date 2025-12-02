from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QSlider
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette


class Bottombar(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent,)
        self.setFixedHeight(96)
        self.setStyleSheet("background-color: #181818; border-top: 1px solid #262626;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Cover + info
        self.cover_frame = QFrame()
        self.cover_frame.setFixedSize(60, 60)
        self.cover_frame.setStyleSheet("background-color: #333333; border-radius: 4px;")
        layout.addWidget(self.cover_frame)

        info_layout = QVBoxLayout()
        self.lbl_title = QLabel("No track playing")
        self.lbl_title.setStyleSheet("color: white; font-size: 14px;")
        self.lbl_artist = QLabel("Artist")
        self.lbl_artist.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        info_layout.addWidget(self.lbl_title)
        info_layout.addWidget(self.lbl_artist)
        layout.addLayout(info_layout)

        layout.addStretch()

        # center: time + slider
        center_layout = QVBoxLayout()
        time_row = QHBoxLayout()
        self.lbl_current_time = QLabel("00:00")
        self.lbl_current_time.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        time_row.addWidget(self.lbl_current_time)
        time_row.addStretch()
        self.lbl_total_time = QLabel("00:00")
        self.lbl_total_time.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        time_row.addWidget(self.lbl_total_time)
        center_layout.addLayout(time_row)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setFixedWidth(380)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333333;
                height: 5px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #1db954;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #1db954;
                border-radius: 2px;
            }
        """)
        center_layout.addWidget(self.seek_slider)
        layout.addLayout(center_layout)

        # buttons
        btn_layout = QHBoxLayout()
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")

        for b in [self.btn_prev, self.btn_play, self.btn_next]:
            b.setFixedSize(38, 38)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #ffffff;
                    border: none;
                    font-size: 18px;
                }
                QPushButton:hover {
                    color: #1db954;
                }
            """)
            btn_layout.addWidget(b)

        layout.addLayout(btn_layout)
        layout.addStretch()

        # volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333333;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #ffffff;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.volume_slider)

        # connections
        # self.seek_slider.sliderMoved.connect(self.engine.set_position)
        # self.volume_slider.valueChanged.connect(self.engine.set_volume)
        # self.btn_play.clicked.connect(self.on_play_clicked)
        # self.btn_prev.clicked.connect(self.on_prev_clicked)
        # self.btn_next.clicked.connect(self.on_next_clicked)

