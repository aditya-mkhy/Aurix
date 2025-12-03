from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QScrollArea, QSpacerItem,
    QLineEdit, QSizePolicy, QToolButton
)
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QPalette


class SearchSuggestionItem(QWidget):
    """Single suggestion row widget."""
    def __init__(self, info: dict, query: str = ""):
        super().__init__()
        self.info = info
        self.query = query or ""
        self.setFixedHeight(72)
        self.setStyleSheet("background: transparent;")

        h = QHBoxLayout(self)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(12)

        # Thumbnail
        thumb = QLabel()
        thumb.setFixedSize(56, 56)

        pix = None
        if info.get("thumbnail"):
            try:
                pix = QPixmap(info["thumbnail"]).scaled(
                    56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            except Exception:
                pix = None

        if pix is None:
            pix = QPixmap(56, 56)
            pix.fill(QColor("#333333"))

        thumb.setPixmap(pix)
        thumb.setStyleSheet("border-radius:6px;")
        h.addWidget(thumb)

        # Text
        v = QVBoxLayout()
        v.setSpacing(2)
        v.setContentsMargins(0, 6, 0, 6)

        title_lbl = QLabel()
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        title_lbl.setStyleSheet("color: #FFFFFF;")
        title_lbl.setText(self._highlight_title(info.get("title", ""), self.query))
        title_lbl.setTextFormat(Qt.RichText)
        v.addWidget(title_lbl)

        subtitle_lbl = QLabel(info.get("subtitle", ""))
        subtitle_lbl.setFont(QFont("Segoe UI", 10))
        subtitle_lbl.setStyleSheet("color: #b3b3b3;")
        v.addWidget(subtitle_lbl)

        h.addLayout(v, 1)

        # Play button
        play_btn = QPushButton()
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.setFixedSize(36, 36)
        play_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        play_btn.setIconSize(QSize(18, 18))
        play_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 18px;
                background: transparent;
                color: #fff;
            }
            QPushButton:hover { background: rgba(255,255,255,0.06); }
        """)
        play_btn.clicked.connect(self._on_play_clicked)
        h.addWidget(play_btn)

        # hover effect
        self.setStyleSheet("""
            QWidget { background: transparent; }
            QWidget:hover { background: #0f0f0f; }
        """)

    def _highlight_title(self, title: str, query: str) -> str:
        if not query:
            return title
        low = title.lower()
        q = query.lower()
        idx = low.find(q)

        if idx == -1:
            return title

        before = title[:idx]
        match = title[idx:idx+len(query)]
        after = title[idx+len(query):]

        return f'{before}<span style="color:#FFFFFF; font-weight:700;">{match}</span>{after}'

    def mousePressEvent(self, event):
        self.parent().parent().parent().suggestion_selected(self.info)
        return super().mousePressEvent(event)

    def _on_play_clicked(self):
        self.parent().parent().parent().play_requested(self.info)


class SearchBox(QWidget):
    suggestionActivated = Signal(dict)
    playRequested = Signal(dict)
    searchTriggered = Signal(str)
    queryChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.container = QVBoxLayout(self)
        self.container.setContentsMargins(0, 0, 0, 0)
        self.container.setSpacing(6)

        # Search container
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setFixedWidth(700)
        bar.setStyleSheet("""
            QFrame { 
                background-color: #282828; 
                border-radius: 10px; 
                border: 1px solid #484848;
            }
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 6, 6, 6)
        h.setSpacing(8)

        # Search icon
        self.search_icon = QLabel()
        self.search_pixmap = QPixmap("res/search.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.active_search_pixmap = QPixmap("res/active-search.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.search_icon.setPixmap(self.search_pixmap)
        self.search_icon.setFixedSize(40, 40)
        h.addWidget(self.search_icon)

        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search songs, albums, artists, playlist")
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #ffffff;
                font-weight: 500;
                font-size: 20px;
            }
        """)

        pal = self.input.palette()
        pal.setColor(QPalette.PlaceholderText, QColor("#949494"))
        self.input.setPalette(pal)

        self.input.returnPressed.connect(self._on_return)
        self.input.textChanged.connect(self._on_text_changed)

        # override focus event behavior
        self._orig_focus_in = self.input.focusInEvent
        self._orig_focus_out = self.input.focusOutEvent

        self.input.focusInEvent = self._on_focus_in
        self.input.focusOutEvent = self._on_focus_out

        h.addWidget(self.input, 1)

        # Clear button
        self.clear_btn = QToolButton()
        self.clear_btn.setIcon(QIcon.fromTheme("edit-clear") or QIcon())
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.setVisible(False)
        self.clear_btn.clicked.connect(self.clear)

        h.addWidget(self.clear_btn)
        self.container.addWidget(bar)

        # Suggestion Dropdown
        self.suggestions_frame = QFrame()
        self.suggestions_frame.setStyleSheet("""
            QFrame {
                background-color: #0b0b0b;
                border: 1px solid #232323;
                border-radius: 8px;
            }
        """)
        self.suggestions_frame.setVisible(False)

        sv_layout = QVBoxLayout(self.suggestions_frame)
        sv_layout.setContentsMargins(6, 6, 6, 6)
        sv_layout.setSpacing(0)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.suggestions_container = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll.setWidget(self.suggestions_container)
        sv_layout.addWidget(self.scroll)
        self.container.addWidget(self.suggestions_frame)

        self._current_suggestions = []
        self.suggestions_frame.setMaximumHeight(360)

    def _on_focus_in(self, event):
        self.search_icon.setPixmap(self.active_search_pixmap)
        return self._orig_focus_in(event)

    def _on_focus_out(self, event):
        self.search_icon.setPixmap(self.search_pixmap)
        return self._orig_focus_out(event)

    def set_suggestions(self, suggestions: list, query=""):
        while self.suggestions_layout.count():
            item = self.suggestions_layout.takeAt(0).widget()
            if item:
                item.deleteLater()

        if not suggestions:
            self.suggestions_frame.hide()
            return

        for info in suggestions:
            item = SearchSuggestionItem(info, query)
            self.suggestions_layout.addWidget(item)

            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background-color: #1f1f1f; margin-left: 10px; margin-right: 6px;")
            self.suggestions_layout.addWidget(div)

        self.suggestions_layout.addStretch()
        self.suggestions_frame.show()

    def clear(self):
        self.input.clear()
        self.suggestions_frame.hide()
        self.clear_btn.setVisible(False)

    def _on_return(self):
        q = self.input.text().strip()
        if q:
            self.searchTriggered.emit(q)

    def _on_text_changed(self, text):
        self.queryChanged.emit(text)
        self.clear_btn.setVisible(bool(text))

    def suggestion_selected(self, info):
        self.suggestionActivated.emit(info)
        self.suggestions_frame.hide()

    def play_requested(self, info):
        self.playRequested.emit(info)


class Topbar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet("background-color: #000000; border-bottom: 1px solid #262626;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(20)

        # Sidebar button
        sidebar_btn = QPushButton()
        sidebar_btn.setIcon(QIcon("./res/menu.png"))
        sidebar_btn.setCursor(Qt.PointingHandCursor)
        sidebar_btn.setFixedSize(56, 56)
        sidebar_btn.setIconSize(QSize(34, 34))
        sidebar_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 28px;
            }
            QPushButton:hover { background-color: #1f1f1f; }
        """)
        layout.addWidget(sidebar_btn)

        # AURIX Logo button
        logo_btn = QPushButton("AURIX")
        logo_btn.setFont(QFont("Segoe UI", 20, QFont.Black))
        logo_btn.setIcon(QIcon("./res/pulse.png"))
        logo_btn.setIconSize(QSize(52, 52))
        logo_btn.setCursor(Qt.PointingHandCursor)
        logo_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                letter-spacing: 2px;
            }
        """)
        logo_btn.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(logo_btn)

        # Search bar
        layout.addSpacing(80)
        self.search_box = SearchBox()
        layout.addWidget(self.search_box)

        # Spacer before profile
        layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Expanding))

        # Profile Picture Button
        profile_btn = QPushButton()
        profile_btn.setFixedSize(40, 40)
        profile_btn.setCursor(Qt.PointingHandCursor)
        profile_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 20px;
                background-color: transparent;
                border-image: url("res/profile.png") 0 fill;
            }
        """)
        profile_btn.clicked.connect(lambda: print("Profile button clicked!"))

        layout.addWidget(profile_btn)
