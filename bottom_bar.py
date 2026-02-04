import os
import sys
from PyQt5.QtCore import Qt, QSize, QRectF, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QToolButton, QMainWindow, QSlider
)
from PyQt5.QtGui import QPainter, QColor, QPixmap, QFont, QIcon

from util import format_time, trim_text, resource_path
from helper import round_pix_form_path


class SeekBar(QWidget):
    seekRequested = pyqtSignal(int)         # final seek (mouse release) in seconds
    positionPreview = pyqtSignal(int)       # while dragging, preview pos (seconds)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: pink;")
        self.setFixedHeight(30)

        self._duration = 0         # seconds
        self._position = 0         # seconds
        self._dragging = False

        self._bar_height = 4
        self._knob_radius = 10

        self._bg_top = QColor(0, 0, 0)         # top (page) color
        self._bg_bottom = QColor(31, 31, 31)   # bottom bar color
        self._track_bg = QColor(80, 80, 80)     # grey track
        self._track_fill = QColor(242, 0, 0)   # red bar
        self._knob_color = QColor(242, 0, 0)

        self.setMouseTracking(True)
        self.setMinimumHeight(20)

    # ---------- external control ---------- #
    def setDuration(self, seconds: int):
        self._duration = max(0, int(seconds))
        if self._position > self._duration:
            self._position = self._duration
        self.update()

    def setPosition(self, seconds: int):
        # ignore external updates when user dragging
        if self._dragging:
            return
        self._position = max(0, min(int(seconds), self._duration or int(seconds)))
        self.update()

    # ---------- drawing ---------- #
    def paintEvent(self, event):
        w = self.width()
        h = self.height()

        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        mid_y = h // 2

        p.fillRect(0, 0, w, mid_y, self._bg_top)
        p.fillRect(0, mid_y, w, h - mid_y, self._bg_bottom)

        # ---- No margins version ----
        track_x = 0
        track_w = w
        track_y = mid_y - self._bar_height // 2

        # Background bar
        p.setPen(Qt.NoPen)
        p.setBrush(self._track_bg)
        p.drawRoundedRect(QRectF(track_x, track_y, track_w, self._bar_height), 2, 2)

        # Filled position
        frac = self._position / self._duration if self._duration > 0 else 0.0
        fill_w = int(track_w * frac)
        if fill_w > 0:
            p.setBrush(self._track_fill)
            p.drawRoundedRect(QRectF(track_x, track_y, fill_w, self._bar_height), 2, 2)

        # Knob position covers edge cleanly
        knob_x = fill_w
        knob_y = mid_y

        # # Shadow
        # p.setBrush(QColor(0, 0, 0, 110))
        # p.drawEllipse(QPoint(int(knob_x), int(knob_y) + 1),
        #             self._knob_radius + 1, self._knob_radius + 1)

        # Knob
        p.setBrush(self._knob_color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPoint(int(knob_x), int(knob_y)), self._knob_radius, self._knob_radius)


        p.end()

    # ---------- mouse handling ---------- #
    def _position_from_x(self, x: int) -> int:
        w = self.width()
        margin = self._knob_radius + 2
        track_x = margin
        track_w = max(4, w - 2 * margin)
        rel = (x - track_x) / float(track_w)
        rel = max(0.0, min(1.0, rel))
        if self._duration <= 0:
            return 0
        return int(round(rel * self._duration))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            secs = self._position_from_x(event.x())
            self._position = secs
            self.positionPreview.emit(secs)
            self.update()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            secs = self._position_from_x(event.x())
            self._position = secs
            self.positionPreview.emit(secs)
            self.update()
            event.accept()
        else:
            self.setCursor(Qt.PointingHandCursor)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.LeftButton:
            self._dragging = False
            secs = self._position_from_x(event.x())
            self._position = secs
            self.seekRequested.emit(secs)
            self.update()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)


class BottomBar(QWidget):
    seekRequested = pyqtSignal(int)
    volumeChanged = pyqtSignal(float)
    playToggled = pyqtSignal()
    previousClicked = pyqtSignal()
    nextClicked = pyqtSignal()
    likeDislikeToggled = pyqtSignal(int, int)
    shuffleToggled = pyqtSignal(bool)
    repeatModeChanged = pyqtSignal(int)  # 0=off,1=all,2=one

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomBar")
        self.setFixedHeight(120)

        # internal state
        self._song_id = None # id of current playing song
        self._duration = 0
        self._position = 0
        self._playing = False
        self._volume = 0
        self._liked = 0
        self._shuffle = False
        self._repeat_mode = 0  # 0 off, 1 all, 2 one

        self.setStyleSheet("background: #1f1f1f;")

        # SEEK BAR
        self.seekbar = SeekBar(self)
        self.seekbar.seekRequested.connect(self._on_seek)
        self.seekbar.positionPreview.connect(self._on_preview)

        # CONTROLS ROW 
        controls = QWidget(self)
        controls.setObjectName("ControlsRow")
        # controls.setFixedHeight(100)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        controls_layout.addSpacing(30)

        # -> Left 
        left_w = QWidget(controls)
        left_w.setStyleSheet("background: transparent;")
        left_l = QHBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 0, 10)
        left_l.setSpacing(15)

        self.prev_btn = self._make_btn(resource_path("res/previous.png"), size=34)
        self.play_btn = self._make_btn(resource_path("res/play-card.png"), size=44)
        self.play_btn.setCheckable(True)
        self.next_btn = self._make_btn(resource_path("res/next.png"), size=34)

        self.time_label = QLabel("0:00 / 0:00", left_w)
        self.time_label.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        self.time_label.setFixedWidth(160)
        self.time_label.setStyleSheet("color: #bdbdbd;")

        left_l.addWidget(self.prev_btn)
        left_l.addWidget(self.play_btn)
        left_l.addWidget(self.next_btn)
        left_l.addWidget(self.time_label)
        left_l.addStretch(1)

        # -> Center
        center_w = QWidget(controls)
        center_w.setStyleSheet("background: transparent;")
        center_l = QHBoxLayout(center_w)
        center_l.setContentsMargins(0, 0, 0, 10)
        center_l.setSpacing(10)
        center_l.setAlignment(Qt.AlignCenter) 

        # cover..
        size = 80

        self.cover = QLabel(center_w)
        # self.image_label.setAlignment(Qt.AlignCenter)
        self.cover.setFixedSize(size, size)
        self.cover.setScaledContents(True)
        self.cover.setStyleSheet(f"""
            QLabel {{
                border: none;
                padding: 0;
                border-radius: 8px;
            }}
        """)


        text_wrap = QWidget(center_w)
        text_wrap.setStyleSheet("background: transparent;")
        text_wrap.setFixedHeight(60)
        text_v = QVBoxLayout(text_wrap)
        text_v.setContentsMargins(0, 0, 0, 0)
        text_v.setSpacing(0)

        self.title_label = QLabel("", text_wrap)
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.meta_label = QLabel("", text_wrap)
        self.meta_label.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.meta_label.setStyleSheet("color: #bdbdbd;")

        text_v.addWidget(self.title_label)
        text_v.addWidget(self.meta_label)

        self.dislike_btn = self._make_btn(resource_path("res/dislike.png"), size=33)
        self.like_btn = self._make_btn(resource_path("res/like.png"), size=33)
        # self.more_btn = self._make_btn(QIcon())  # placeholder
        # self.more_btn.setText("⋯")

        center_l.addStretch()
        center_l.addWidget(self.cover)
        center_l.addSpacing(10)

        center_l.addWidget(text_wrap)
        center_l.addSpacing(10)
        center_l.addWidget(self.dislike_btn)
        center_l.addSpacing(10)
        center_l.addWidget(self.like_btn)
        # center_l.addWidget(self.more_btn)
        center_l.addStretch()


        # -> Right
        right_w = QWidget(controls)
        right_w.setStyleSheet("background: transparent;")
        right_w.setFixedWidth(330)
        right_l = QHBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 10)
        right_l.setSpacing(10)

        right_l.addStretch(1)

        # volume slider (animated)
        self.volume_slider = QSlider(Qt.Horizontal, right_w)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self._volume * 100))
        self.volume_slider.setFixedHeight(20)
        self.volume_slider.setMinimumWidth(0)
        self.volume_slider.setMaximumWidth(0)  # start hidden (width=0)
        self.volume_slider.valueChanged.connect(self._on_volume_slider)

        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 8%);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #ff0060;
                border-radius: 2px;
            }
        """)

        # speaker button
        self.volume_btn = self._make_btn(resource_path("res/volume.png"), size=33)
        self.volume_btn.clicked.connect(self._on_volume_btn_clicked)

    
        right_l.addWidget(self.volume_slider)
        right_l.addWidget(self.volume_btn)
        right_l.addSpacing(15)

        self.shuffle_btn = self._make_btn(resource_path("res/shuffle-off.png"), size=33)
        self.repeat_btn = self._make_btn(resource_path("res/repeat-off.png"), size=33)

        right_l.addWidget(self.shuffle_btn)
        right_l.addSpacing(15)
        right_l.addWidget(self.repeat_btn)
        right_l.addSpacing(45)

        # assemble controls row
        controls_layout.addWidget(left_w, 0)
        controls_layout.addWidget(center_w, 1)
        controls_layout.addWidget(right_w, 0)

        # main layout
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.seekbar)
        vbox.addWidget(controls)

        # styling #1f1f1f
        self.setStyleSheet("""
        QWidget#BottomBar {
            background-color: #1f1f1f;
            border-top: 1px solid #2a2a2a;
        }
        QWidget#ControlsRow {
            background-color: #1f1f1f;
        }
        """)

        # connections
        self.prev_btn.clicked.connect(self.previousClicked)
        self.next_btn.clicked.connect(self.nextClicked)
        self.play_btn.clicked.connect(self._on_play_clicked)
        self.like_btn.clicked.connect(self._on_like_clicked)
        self.dislike_btn.clicked.connect(self._on_dislike_clicked)
        self.shuffle_btn.clicked.connect(self._on_shuffle_clicked)
        self.repeat_btn.clicked.connect(self._on_repeat_clicked)

        # volume animation
        self._volume_anim = QPropertyAnimation(self.volume_slider, b"maximumWidth", self)
        self._volume_anim.setDuration(160)
        self._volume_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._volume_target_width = 120

    # helpers & API
    def _make_btn(self, ic: str, size:int = 24) -> QToolButton:
        btn = QToolButton(self)
        btn.setIcon(QIcon(ic))
        btn.setIconSize(QSize(size, size))  # your PNGs are 64px; scaled down
        btn.setCursor(Qt.PointingHandCursor)
        btn.setAutoRaise(True)

        btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                padding: 10px;
            }}
            QToolButton:hover {{
                background-color: rgba(255,255,255, 5%);
                border-radius: {(size + 20)// 2}px;
            }}
        """)
        return btn

    def set_track(self, song_id: int, title: str, subtitle: str, liked: int, cover_path: str, duration_seconds: int):
        self._song_id = song_id # current playing song

        self.title_label.setText(trim_text(title, max_length=33))
        self.meta_label.setText(trim_text(subtitle, max_length=38))
        self._duration = duration_seconds
        self._position = 0
        self.seekbar.setDuration(self._duration * 1000)
        self.seekbar.setPosition(0)
        self._update_time() 

        # set cover image
        self.cover.setPixmap(round_pix_form_path(cover_path, 80, 80, 6))

        # update - like-dislike
        self.set_like_dislike(value=liked, is_emmit=False)


    def set_position(self, seconds: int):
        self._position = seconds // 1000
        self.seekbar.setPosition(seconds)
        self._update_time()

    def set_playing(self, playing: bool):
        self._playing = bool(playing)

        self.play_btn.setChecked(self._playing)
        if self._playing:
            self.play_btn.setIcon(QIcon(resource_path("res/pause.png")))

        else:
            self.play_btn.setIcon(QIcon(resource_path("res/play-card.png")))


    def set_volume(self, volume: float):
        volume = max(0.0, min(1.0, float(volume)))
        self._volume = volume
        self.volume_slider.setValue(int(volume * 100))
        self._update_volume_icon()
        self.volumeChanged.emit(volume)


    def _update_time(self):
        self.time_label.setText(
            f"{format_time(self._position)} / {format_time(self._duration)}"
        )

    def _on_seek(self, seconds: int):
        self._position = seconds // 1000
        self._update_time()
        self.seekRequested.emit(seconds // 1000)

    def _on_preview(self, seconds: int):
        self._position = seconds // 1000 # ms -> sec
        self._update_time()

    def _on_play_clicked(self):
        self.playToggled.emit()

    # volume slider + animation 
    def _on_volume_btn_clicked(self):
        # animate show/hide by changing maximumWidth
        self._volume_anim.stop()
        current = self.volume_slider.maximumWidth()
        if current == 0:
            # open
            self._volume_anim.setStartValue(0)
            self._volume_anim.setEndValue(self._volume_target_width)
        else:
            # close
            self._volume_anim.setStartValue(current)
            self._volume_anim.setEndValue(0)
        self._volume_anim.start()

    def _on_volume_slider(self, value: int):
        self._volume = value / 100.0
        self._update_volume_icon()
        self.volumeChanged.emit(self._volume)

    def _update_volume_icon(self):
        if self._volume <= 0.01:
            self.volume_btn.setIcon(QIcon(resource_path("res/volume-mute.png")))
        else:
            self.volume_btn.setIcon(QIcon(resource_path("res/volume.png")))

    def set_like_dislike(self, value: int = 0, is_emmit = True):
        self._liked = value

        print(f"settin the value ==> {value}")

        if value == 0:
            self.dislike_btn.setIcon(QIcon(resource_path("res/dislike.png")))
            self.like_btn.setIcon(QIcon(resource_path("res/like.png")))

        elif value == 1:
            self.dislike_btn.setIcon(QIcon(resource_path("res/dislike.png")))
            self.like_btn.setIcon(QIcon(resource_path("res/like-on.png")))

        elif value == 2:
            self.like_btn.setIcon(QIcon(resource_path("res/like.png")))
            self.dislike_btn.setIcon(QIcon(resource_path("res/dislike-on.png")))

        else:
            print(f"Error : Invalid value for like -> {value}")

        if is_emmit:
            self.likeDislikeToggled.emit(self._song_id, value)

    # like / dislike / shuffle / repeat
    def _on_like_clicked(self):
        if self._liked == 1:
            value = 0
        else:
            value = 1

        self.set_like_dislike(value)


    def _on_dislike_clicked(self):
        if self._liked == 2:
            value = 0
        else:
            value = 2

        self.set_like_dislike(value)

    def set_shuffle(self, value: bool):
        self._shuffle = value
        self.shuffle_btn.setIcon(QIcon(resource_path("res/shuffle-on.png") if self._shuffle else resource_path("res/shuffle-off.png")))


    def _on_shuffle_clicked(self):
        self.shuffleToggled.emit(not self._shuffle)

    def _on_repeat_clicked(self):
        # 0 -> 1 -> 2 -> 0
        change_mode = (self._repeat_mode + 1) % 3
        self.repeatModeChanged.emit(change_mode)

    def set_repeat_mode(self, value: int):
        self._repeat_mode = value

        if self._repeat_mode == 0:
            ic = "res/repeat-off.png"
        elif self._repeat_mode == 1:
            ic = "res/repeat-all.png"
        else:
            ic = "res/repeat-one.png"
        self.repeat_btn.setIcon(QIcon(resource_path(ic)))

