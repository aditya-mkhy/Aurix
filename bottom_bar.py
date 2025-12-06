# bottom_web_player_seek_volume.py
# PyQt5 implementation with clickable/draggable progress indicator and hover volume slider.
import os
import sys
from PyQt5.QtCore import Qt, QSize, QRectF, QPoint, QTimer, pyqtSignal, QPropertyAnimation
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QToolButton,
    QStyle, QMainWindow, QSlider
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QFont, QIcon

# Use your screenshot path if available
DEFAULT_COVER = "/mnt/data/Screenshot 2025-12-05 210901.png"


# ------------------ Clickable / Draggable Progress Bar ------------------ #
class SeekBar(QWidget):
    """Clickable & draggable progress strip with circular indicator like YT Music."""
    seekRequested = pyqtSignal(int)         # seconds (requested when user clicks/drags)
    positionChangedByUser = pyqtSignal(int) # during drag (optional)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0        # seconds
        self._position = 0        # seconds
        self._dragging = False
        self.setMinimumHeight(20)  # gives space for the knob
        self.setMouseTracking(True)

        # Styling
        self._bar_height = 4
        self._knob_radius = 8     # knob circle radius
        self._bg_color = QColor(50, 50, 50)
        self._fill_color = QColor(255, 43, 111)  # hot pink
        self._knob_color = QColor(255, 43, 111)
        self._knob_border = QColor(30, 30, 30)

    def setDuration(self, seconds: int):
        self._duration = max(0, int(seconds))
        if self._position > self._duration:
            self._position = self._duration
        self.update()

    def setPosition(self, seconds: int):
        if not self._dragging:
            self._position = max(0, min(int(seconds), self._duration or int(seconds)))
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # Calculate bar geometry
        bar_y = int((h - self._bar_height) / 2)
        bar_x = self._knob_radius
        bar_w = max(4, w - 2 * self._knob_radius)

        # ---- Background bar ----
        p.setPen(Qt.NoPen)
        p.setBrush(self._bg_color)

        # using QRectF to avoid type mismatch errors
        bg_rect = QRectF(bar_x, bar_y, bar_w, self._bar_height)
        p.drawRoundedRect(bg_rect, 2, 2)

        # ---- Filled bar ----
        frac = self._position / self._duration if self._duration > 0 else 0
        fill_w = int(bar_w * frac)

        if fill_w > 0:
            p.setBrush(self._fill_color)
            fill_rect = QRectF(bar_x, bar_y, fill_w, self._bar_height)
            p.drawRoundedRect(fill_rect, 2, 2)

        # ---- Knob ----
        knob_x = bar_x + fill_w
        knob_y = h // 2

        # Shadow
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawEllipse(QPoint(int(knob_x), int(knob_y + 1)), self._knob_radius + 1, self._knob_radius + 1)

        # Knob circle
        p.setBrush(self._knob_color)
        p.setPen(QPen(self._knob_border, 2))
        p.drawEllipse(QPoint(int(knob_x), int(knob_y)), self._knob_radius, self._knob_radius)

        p.end()


    def _pos_from_x(self, x: int) -> int:
        w = self.width()
        bar_x = self._knob_radius
        bar_w = max(4, w - 2 * self._knob_radius)
        rel = (x - bar_x) / bar_w
        rel = max(0.0, min(1.0, rel))
        secs = int(round(rel * self._duration)) if self._duration else 0
        return secs

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            secs = self._pos_from_x(event.x())
            self._position = secs
            self.positionChangedByUser.emit(secs)
            self.update()
            # don't immediately emit final seek; allow mouseRelease or continuous drag to emit
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            secs = self._pos_from_x(event.x())
            self._position = secs
            self.positionChangedByUser.emit(secs)
            self.update()
            event.accept()
        else:
            # change cursor when hovering over knob region or bar
            # we simply set pointing hand for experience
            self.setCursor(Qt.PointingHandCursor)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.LeftButton:
            self._dragging = False
            secs = self._pos_from_x(event.x())
            self._position = secs
            self.seekRequested.emit(secs)
            self.update()
            event.accept()

    def leaveEvent(self, event):
        # restore cursor
        self.unsetCursor()
        super().leaveEvent(event)


# ------------------ Hover volume popup ------------------ #
class VolumePopup(QWidget):
    """A small popup widget with a vertical slider that appears above the speaker."""
    volumeChanged = pyqtSignal(float)  # 0.0 .. 1.0

    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setFixedSize(56, 120)

        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(70)
        self.slider.setInvertedAppearance(False)  # higher at top
        self.slider.setGeometry(16, 8, 24, 104)
        self.slider.valueChanged.connect(self._on_value_changed)

        # style
        self.setStyleSheet("""
            QWidget {
                background: rgba(30,30,30,240);
                border: 1px solid rgba(255,255,255,6%);
                border-radius: 8px;
            }
            QSlider::groove:vertical {
                background: rgba(255,255,255,6%);
                width: 6px;
                border-radius: 3px;
            }
            QSlider::handle:vertical {
                height: 12px;
                width: 14px;
                margin: -6px 0;
                border-radius: 7px;
                background: white;
            }
            QSlider::sub-page:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff2b6f, stop:1 #ff2b6f);
                border-radius: 3px;
                width: 6px;
            }
        """)

        # hide timer to avoid flicker when moving between speaker and popup
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(250)
        self._hide_timer.timeout.connect(self.hide)

    def _on_value_changed(self, value: int):
        v = value / 100.0
        self.volumeChanged.emit(v)

    def show_above_widget(self, widget):
        # position popup above the widget (speaker), centered horizontally
        global_pos = widget.mapToGlobal(widget.rect().topLeft())
        w = widget.width()
        popup_w = self.width()
        x = global_pos.x() + (w // 2) - (popup_w // 2)
        y = global_pos.y() - self.height() - 8
        self.move(max(8, x), max(8, y))
        self.show()
        self.raise_()
        self._hide_timer.stop()

    def enterEvent(self, event):
        # cancel hide when mouse moves into popup
        self._hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # start delayed hide to allow small gap movement
        self._hide_timer.start()
        super().leaveEvent(event)


# ------------------ Main Bottom Web Player (integrates SeekBar & Volume) ------------------ #
class BottomWebPlayer(QWidget):
    seekRequested = pyqtSignal(int)    # seconds
    volumeChanged = pyqtSignal(float)  # 0.0..1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomWebPlayer")
        self.setMinimumHeight(76)

        # SeekBar (thin with knob)
        self.seekbar = SeekBar(self)
        self.seekbar.setFixedHeight(28)

        # Left controls (prev/play/next + time)
        style = self.style()
        prev_icon = style.standardIcon(QStyle.SP_MediaSkipBackward)
        play_icon = style.standardIcon(QStyle.SP_MediaPlay)
        pause_icon = style.standardIcon(QStyle.SP_MediaPause)
        next_icon = style.standardIcon(QStyle.SP_MediaSkipForward)
        vol_icon = style.standardIcon(QStyle.SP_MediaVolume)

        self.prev_btn = QToolButton()
        self.prev_btn.setIcon(prev_icon)
        self.prev_btn.setAutoRaise(True)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn = QToolButton()
        self.play_btn.setIcon(play_icon)
        self.play_btn.setCheckable(True)
        self.play_btn.setAutoRaise(True)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn = QToolButton()
        self.next_btn.setIcon(next_icon)
        self.next_btn.setAutoRaise(True)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #bdbdbd;")
        self.time_label.setFont(QFont("Segoe UI", 9))

        # Center track info
        self.cover = QLabel()
        self.cover.setFixedSize(48, 48)
        self.cover.setScaledContents(True)
        self.cover.setStyleSheet("border-radius:4px; background: #222;")
        self.title_label = QLabel("Track Title")
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.meta_label = QLabel("Artist • Album • 2018")
        self.meta_label.setStyleSheet("color: #bdbdbd;")
        self.meta_label.setFont(QFont("Segoe UI", 9))

        # small action icons
        self.dislike_btn = QToolButton()
        self.like_btn = QToolButton()
        self.more_btn = QToolButton()
        self.dislike_btn.setAutoRaise(True)
        self.like_btn.setAutoRaise(True)
        self.more_btn.setAutoRaise(True)
        self.dislike_btn.setCursor(Qt.PointingHandCursor)
        self.like_btn.setCursor(Qt.PointingHandCursor)
        self.more_btn.setCursor(Qt.PointingHandCursor)
        self.dislike_btn.setText("👎") if QIcon() else None
        self.like_btn.setText("👍") if QIcon() else None
        self.more_btn.setText("⋯") if QIcon() else None

        # Volume button + popup
        self.volume_btn = QToolButton()
        self.volume_btn.setIcon(vol_icon)
        self.volume_btn.setAutoRaise(True)
        self.volume_btn.setCursor(Qt.PointingHandCursor)
        self.volume_popup = VolumePopup(self)
        self.volume_popup.volumeChanged.connect(self._on_volume_changed)

        # connect hover behavior: show popup on enter of speaker; hide when leaving both
        self.volume_btn.installEventFilter(self)

        # layout composition
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(8, 0, 8, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self.prev_btn)
        left_layout.addWidget(self.play_btn)
        left_layout.addWidget(self.next_btn)
        left_layout.addWidget(self.time_label)
        left_layout.addStretch(1)

        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)
        center_layout.addWidget(self.cover)
        txt_v = QVBoxLayout()
        txt_v.setSpacing(2)
        txt_v.setContentsMargins(0, 0, 0, 0)
        txt_v.addWidget(self.title_label)
        txt_v.addWidget(self.meta_label)
        center_layout.addLayout(txt_v)
        center_layout.addWidget(self.dislike_btn)
        center_layout.addWidget(self.like_btn)
        center_layout.addWidget(self.more_btn)
        center_layout.addStretch(1)

        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 8, 0)
        right_layout.setSpacing(6)
        right_layout.addStretch(1)
        right_layout.addWidget(self.volume_btn)
        # (repeat/shuffle icons could be added here)

        # overall layout (vertical stacked: seekbar on top, controls row below)
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.seekbar)
        controls = QWidget()
        controls.setStyleSheet("background-color: #1f1f1f; border-top: 1px solid #2a2a2a;")
        c_layout = QHBoxLayout(controls)
        c_layout.setContentsMargins(12, 8, 12, 8)
        c_layout.setSpacing(8)
        c_layout.addLayout(left_layout, 0)
        c_layout.addLayout(center_layout, 1)
        c_layout.addLayout(right_layout, 0)
        vbox.addWidget(controls)

        # default states
        self._duration = 0
        self._position = 0
        self._playing = False
        self._volume = 0.7
        self.volume_popup.slider.setValue(int(self._volume * 100))

        # connect seek signals
        self.seekbar.seekRequested.connect(self._on_seek_requested)
        self.seekbar.positionChangedByUser.connect(self._on_position_drag)

        # connect play toggling
        self.play_btn.clicked.connect(self._on_play_clicked)

        # load cover if available
        if os.path.exists(DEFAULT_COVER):
            pix = QPixmap(DEFAULT_COVER).scaled(self.cover.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.cover.setPixmap(pix)

    # --------------- API methods --------------- #
    def set_track(self, title: str, meta: str, duration_seconds: int = 0, cover_pixmap: QPixmap = None):
        self.title_label.setText(title)
        self.meta_label.setText(meta)
        self._duration = max(0, int(duration_seconds))
        self._position = 0
        self._update_time_label()
        self.seekbar.setDuration(self._duration)
        self.seekbar.setPosition(0)
        if cover_pixmap:
            self.cover.setPixmap(cover_pixmap.scaled(self.cover.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

    def set_position(self, seconds: int):
        self._position = max(0, min(int(seconds), self._duration or int(seconds)))
        self.seekbar.setPosition(self._position)
        self._update_time_label()

    def set_playing(self, playing: bool):
        self._playing = bool(playing)
        if self._playing:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.play_btn.setChecked(True)
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.play_btn.setChecked(False)

    def set_volume(self, v: float):
        v = max(0.0, min(1.0, float(v)))
        self._volume = v
        self.volume_popup.slider.setValue(int(v * 100))
        self.volumeChanged.emit(v)

    # --------------- internal handlers --------------- #
    def _on_seek_requested(self, seconds: int):
        # emit externally so main player can handle actual seeking
        self._position = seconds
        self.seekRequested.emit(seconds)
        self._update_time_label()

    def _on_position_drag(self, seconds: int):
        # while dragging — update label for immediate feedback
        self._position = seconds
        self._update_time_label()

    def _update_time_label(self):
        total = self._duration or 0
        self.time_label.setText(f"{self._format_time(self._position)} / {self._format_time(total)}")

    def _format_time(self, seconds: int):
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"

    def _on_play_clicked(self):
        self.set_playing(not self._playing)
        # user will connect to this toggle or use our played state externally

    def _on_volume_changed(self, v: float):
        self._volume = v
        self.volumeChanged.emit(v)

    # ---------------- event filter for volume hover ---------------- #
    def eventFilter(self, watched, event):
        # watch volume_btn enter/leave to show/hide popup with small tolerance
        if watched is self.volume_btn:
            if event.type() == event.Enter:
                # show popup anchored to button
                self.volume_popup.show_above_widget(self.volume_btn)
                return True
            elif event.type() == event.Leave:
                # start hide timer on popup (itself handles its timer)
                # if mouse goes to popup, it cancels the hide
                # we don't hide immediately to allow small cursor movement
                self.volume_popup._hide_timer.start()
                return True
        return super().eventFilter(watched, event)


# ------------------ Demo usage ------------------ #
class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurix — Bottom Player (Seek + Hover Volume) Demo")
        self.resize(1000, 180)
        widget = QWidget()
        v = QVBoxLayout(widget)
        v.addStretch(1)

        self.player = BottomWebPlayer(self)
        v.addWidget(self.player)

        self.setCentralWidget(widget)

        # demo track
        duration = 3 * 60 + 34
        self.player.set_track("Baarish Lete Aana", "Darshan Raval • Baarish Lete Aana • 2018", duration_seconds=duration)

        # connect signals
        self.player.seekRequested.connect(self.on_seek_requested)
        self.player.volumeChanged.connect(lambda vol: print(f"Volume -> {vol:.2f}"))
        self.player.play_btn.clicked.connect(self._toggle_demo_timer)

        # demo timer for playback progress
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._advance)

    def _toggle_demo_timer(self):
        if self._timer.isActive():
            self._timer.stop()
            self.player.set_playing(False)
        else:
            self._timer.start()
            self.player.set_playing(True)

    def _advance(self):
        if self.player._position < self.player._duration:
            self.player.set_position(self.player._position + 1)
        else:
            self._timer.stop()
            self.player.set_playing(False)

    def on_seek_requested(self, seconds: int):
        print("User requested seek to:", seconds)
        # for demo, set position directly (in real use you'd command your player backend)
        self.player.set_position(seconds)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QMainWindow{ background-color: #111; }")
    w = DemoWindow()
    w.show()
    sys.exit(app.exec_())
