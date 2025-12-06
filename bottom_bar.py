# bottom_bar.py
# Aurix bottom player bar - YouTube web style with animated inline volume slider
import os
import sys
from PyQt5.QtCore import (
    Qt, QSize, QRectF, QPoint, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QToolButton, QMainWindow, QSlider
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QPixmap, QFont, QIcon
)

from helper import get_pixmap, applyRoundedImage


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(BASE_DIR, "res")


def icon(name: str) -> QIcon:
    return QIcon(os.path.join(RES_DIR, name))


# ===================== SEEK BAR (click + drag) ===================== #
class SeekBar(QWidget):
    seekRequested = pyqtSignal(int)         # final seek (mouse release) in seconds
    positionPreview = pyqtSignal(int)       # while dragging, preview pos (seconds)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0         # seconds
        self._position = 0         # seconds
        self._dragging = False

        self._bar_height = 4
        self._knob_radius = 7

        self._bg_top = QColor(0, 0, 0)          # top (page) color
        self._bg_bottom = QColor(31, 31, 31)    # bottom bar color
        self._track_bg = QColor(80, 80, 80)     # grey track
        self._track_fill = QColor(242, 0, 0)   # pink bar
        self._knob_color = QColor(255, 0, 96)
        self._knob_border = QColor(30, 30, 30)

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

        # Shadow
        p.setBrush(QColor(0, 0, 0, 110))
        p.drawEllipse(QPoint(int(knob_x), int(knob_y) + 1),
                    self._knob_radius + 1, self._knob_radius + 1)

        # Knob
        p.setBrush(self._knob_color)
        p.setPen(QPen(self._knob_border, 2))
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


# ===================== MAIN BOTTOM BAR ===================== #
class BottomBar(QWidget):
    seekRequested = pyqtSignal(int)
    volumeChanged = pyqtSignal(float)
    playToggled = pyqtSignal(bool)
    previousClicked = pyqtSignal()
    nextClicked = pyqtSignal()
    likeToggled = pyqtSignal(bool)
    dislikeToggled = pyqtSignal(bool)
    shuffleToggled = pyqtSignal(bool)
    repeatModeChanged = pyqtSignal(int)  # 0=off,1=all,2=one

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomBar")
        self.setMinimumHeight(125)

        # internal state
        self._duration = 0
        self._position = 0
        self._playing = False
        self._volume = 0.7
        self._liked = False
        self._disliked = False
        self._shuffle = False
        self._repeat_mode = 0  # 0 off, 1 all, 2 one

        # ========== SEEK BAR ==========
        self.seekbar = SeekBar(self)
        self.seekbar.seekRequested.connect(self._on_seek)
        self.seekbar.positionPreview.connect(self._on_preview)

        # ========== CONTROLS ROW ==========
        controls = QWidget(self)
        controls.setObjectName("ControlsRow")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(10)

        # ----- Left (prev / play / next / time) -----
        left_w = QWidget(controls)
        left_l = QHBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(8)

        self.prev_btn = self._make_btn(icon("previous.png"))
        self.play_btn = self._make_btn(icon("play-card.png"))
        self.play_btn.setCheckable(True)
        self.next_btn = self._make_btn(icon("next.png"))

        self.time_label = QLabel("0:00 / 0:00", left_w)
        self.time_label.setFont(QFont("Segoe UI", 9))
        self.time_label.setStyleSheet("color: #bdbdbd;")

        left_l.addWidget(self.prev_btn)
        left_l.addWidget(self.play_btn)
        left_l.addWidget(self.next_btn)
        left_l.addWidget(self.time_label)
        left_l.addStretch(1)

        # ----- Center (cover + title/meta + like/dislike/more) -----
        center_w = QWidget(controls)
        center_l = QHBoxLayout(center_w)
        center_l.setContentsMargins(0, 0, 0, 0)
        center_l.setSpacing(10)

        # cover...
        path = "C:\\Users\\freya\\Music\\Barbaad.mp3"
        pix  = get_pixmap(path)

        size = 48

        self.cover = QLabel(center_w)
        # self.image_label.setAlignment(Qt.AlignCenter)
        self.cover.setFixedSize(size, size)
        self.cover.setScaledContents(True)
        applyRoundedImage(self.cover, pix, size=size, radius=8)
        self.cover.setStyleSheet(f"""
            QLabel {{
                border: none;
                padding: 0;
                border-radius: 8px;
            }}
        """)


        text_wrap = QWidget(center_w)
        text_v = QVBoxLayout(text_wrap)
        text_v.setContentsMargins(0, 0, 0, 0)
        text_v.setSpacing(2)

        self.title_label = QLabel("Track Title", text_wrap)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.meta_label = QLabel("Artist • Album • 2018", text_wrap)
        self.meta_label.setFont(QFont("Segoe UI", 9))
        self.meta_label.setStyleSheet("color: #bdbdbd;")

        text_v.addWidget(self.title_label)
        text_v.addWidget(self.meta_label)

        self.dislike_btn = self._make_btn(icon("dislike.png"))
        self.like_btn = self._make_btn(icon("like.png"))
        self.more_btn = self._make_btn(QIcon())  # placeholder
        self.more_btn.setText("⋯")

        center_l.addWidget(self.cover)
        center_l.addWidget(text_wrap)
        center_l.addWidget(self.dislike_btn)
        center_l.addWidget(self.like_btn)
        center_l.addWidget(self.more_btn)
        center_l.addStretch(1)

        # ----- Right (animated volume slider + shuffle + repeat) -----
        right_w = QWidget(controls)
        right_l = QHBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(6)

        right_l.addStretch(1)

        # volume slider (animated)
        self.volume_slider = QSlider(Qt.Horizontal, right_w)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self._volume * 100))
        self.volume_slider.setFixedHeight(16)
        self.volume_slider.setMinimumWidth(0)
        self.volume_slider.setMaximumWidth(0)  # start hidden (width=0)
        self.volume_slider.valueChanged.connect(self._on_volume_slider)

        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255,255,255,8%);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: #ff0060;
                border-radius: 2px;
            }
        """)

        # speaker button
        self.volume_btn = self._make_btn(icon("volume.png"))
        self.volume_btn.clicked.connect(self._on_volume_btn_clicked)

        # add in order: slider (left) then button
        right_l.addWidget(self.volume_slider)
        right_l.addWidget(self.volume_btn)

        self.shuffle_btn = self._make_btn(icon("shuffle-off.png"))
        self.repeat_btn = self._make_btn(icon("repeat-off.png"))

        right_l.addWidget(self.shuffle_btn)
        right_l.addWidget(self.repeat_btn)

        # assemble controls row
        controls_layout.addWidget(left_w, 0)
        controls_layout.addWidget(center_w, 1)
        controls_layout.addWidget(right_w, 0)

        # ========== main layout ==========
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.seekbar)
        vbox.addWidget(controls)

        # styling
        self.setStyleSheet("""
        QWidget#BottomBar {
            background-color: #1f1f1f;
            border-top: 1px solid #2a2a2a;
        }
        QWidget#ControlsRow {
            background-color: #1f1f1f;
        }
        QToolButton {
            border: none;
            padding: 4px;
        }
        QToolButton:hover {
            background-color: rgba(255,255,255,6%);
            border-radius: 4px;
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

    # -------------- helpers & API -------------- #
    def _make_btn(self, ic: QIcon) -> QToolButton:
        btn = QToolButton(self)
        btn.setIcon(ic)
        btn.setIconSize(QSize(24, 24))  # your PNGs are 64px; scaled down
        btn.setCursor(Qt.PointingHandCursor)
        btn.setAutoRaise(True)
        return btn

    def set_track(self, title: str, meta: str, duration_seconds: int, cover: QPixmap = None):
        self.title_label.setText(title)
        self.meta_label.setText(meta)
        self._duration = max(0, int(duration_seconds))
        self._position = 0
        self.seekbar.setDuration(self._duration)
        self.seekbar.setPosition(0)
        self._update_time()
        if cover:
            self.cover.setPixmap(
                cover.scaled(self.cover.size(),
                             Qt.KeepAspectRatioByExpanding,
                             Qt.SmoothTransformation)
            )

    def set_position(self, seconds: int):
        self._position = max(0, min(int(seconds), self._duration or int(seconds)))
        self.seekbar.setPosition(self._position)
        self._update_time()

    def set_playing(self, playing: bool):
        self._playing = bool(playing)
        self.play_btn.setChecked(self._playing)
        if self._playing:
            self.play_btn.setIcon(icon("pause.png"))
        else:
            self.play_btn.setIcon(icon("play-card.png"))
        self.playToggled.emit(self._playing)


    def set_volume(self, volume: float):
        volume = max(0.0, min(1.0, float(volume)))
        self._volume = volume
        self.volume_slider.setValue(int(volume * 100))
        self._update_volume_icon()
        self.volumeChanged.emit(volume)

    # -------------- internal handlers -------------- #
    def _format_time(self, secs: int) -> str:
        m = secs // 60
        s = secs % 60
        return f"{m}:{s:02d}"

    def _update_time(self):
        self.time_label.setText(
            f"{self._format_time(self._position)} / {self._format_time(self._duration)}"
        )

    def _on_seek(self, seconds: int):
        self._position = seconds
        self._update_time()
        self.seekRequested.emit(seconds)

    def _on_preview(self, seconds: int):
        self._position = seconds
        self._update_time()

    def _on_play_clicked(self):
        self.set_playing(not self._playing)

    # ---- volume slider + animation ---- #
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
            self.volume_btn.setIcon(icon("volume-mute.png"))
        else:
            self.volume_btn.setIcon(icon("volume.png"))

    # ---- like / dislike / shuffle / repeat ---- #
    def _on_like_clicked(self):
        self._liked = not self._liked
        if self._liked:
            self.like_btn.setIcon(icon("like-on.png"))
            if self._disliked:
                self._disliked = False
                self.dislike_btn.setIcon(icon("dislike.png"))
        else:
            self.like_btn.setIcon(icon("like.png"))
        self.likeToggled.emit(self._liked)

    def _on_dislike_clicked(self):
        self._disliked = not self._disliked
        if self._disliked:
            self.dislike_btn.setIcon(icon("dislike-on.png"))
            if self._liked:
                self._liked = False
                self.like_btn.setIcon(icon("like.png"))
        else:
            self.dislike_btn.setIcon(icon("dislike.png"))
        self.dislikeToggled.emit(self._disliked)

    def _on_shuffle_clicked(self):
        self._shuffle = not self._shuffle
        self.shuffle_btn.setIcon(icon("shuffle-on.png" if self._shuffle else "shuffle-off.png"))
        self.shuffleToggled.emit(self._shuffle)

    def _on_repeat_clicked(self):
        # 0 -> 1 -> 2 -> 0
        self._repeat_mode = (self._repeat_mode + 1) % 3
        if self._repeat_mode == 0:
            ic = "repeat-off.png"
        elif self._repeat_mode == 1:
            ic = "repeat-all.png"
        else:
            ic = "repeat-one.png"
        self.repeat_btn.setIcon(icon(ic))
        self.repeatModeChanged.emit(self._repeat_mode)


# ===================== DEMO (optional) ===================== #
class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurix Bottom Bar Demo")
        self.resize(1500, 880)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)

        self.bottom = BottomBar(self)
        layout.addWidget(self.bottom)
        self.setCentralWidget(central)

        duration = 3 * 60 + 34
        self.bottom.set_track(
            "Baarish Lete Aana",
            "Darshan Raval • Baarish Lete Aana • 2018",
            duration_seconds=duration
        )

        # demo timer to move progress
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._advance)

        self.bottom.playToggled.connect(self._toggle_timer)
        self.bottom.seekRequested.connect(self._seek)

    def _toggle_timer(self, playing: bool):
        if playing:
            self._timer.start()
        else:
            self._timer.stop()

    def _advance(self):
        if self.bottom._position < self.bottom._duration:
            self.bottom.set_position(self.bottom._position + 1)
        else:
            self._timer.stop()
            self.bottom.set_playing(False)

    def _seek(self, secs: int):
        self.bottom.set_position(secs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QMainWindow { background-color: #000; }")
    win = DemoWindow()
    win.show()
    sys.exit(app.exec_())
