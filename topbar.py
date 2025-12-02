from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
    QLabel, QPushButton, QScrollArea, QSpacerItem, 
    QLineEdit, QSizePolicy, QToolButton
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette


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

        # Thumbnail / Icon
        thumb = QLabel()
        thumb.setFixedSize(56, 56)
        pix = None
        if info.get("thumbnail"):
            try:
                pix = QPixmap(info["thumbnail"]).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            except Exception:
                pix = None
        if pix is None:
            # placeholder square
            pix = QPixmap(56, 56)
            pix.fill(QColor("#333333"))
        thumb.setPixmap(pix)
        thumb.setStyleSheet("border-radius:6px;")
        h.addWidget(thumb)

        # Text area (title + subtitle)
        v = QVBoxLayout()
        v.setSpacing(2)
        v.setContentsMargins(0, 6, 0, 6)

        title_lbl = QLabel()
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        title_lbl.setStyleSheet("color: #FFFFFF;")
        title_lbl.setText(self._highlight_title(info.get("title", ""), self.query))
        title_lbl.setTextFormat(Qt.RichText)
        title_lbl.setWordWrap(False)
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
        h.addWidget(play_btn, 0, Qt.AlignVCenter)

        # hover feedback and ripple-like effect: change background on hover via stylesheet on parent container
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
            QWidget:hover {
                background: #0f0f0f;
            }
        """)

    def _highlight_title(self, title: str, query: str) -> str:
        """Simple bold-highlight (first matching chunk)."""
        if not query:
            return title
        low = title.lower()
        q = query.lower()
        idx = low.find(q)
        if idx == -1:
            return title
        before = title[:idx]
        match = title[idx: idx + len(query)]
        after = title[idx + len(query):]
        # highlight match with slightly lighter color
        return f'{before}<span style="color:#FFFFFF; font-weight:700;">{match}</span>{after}'

    def mousePressEvent(self, event):
        # clicking row triggers activation
        self.parent().parent().parent().suggestion_selected(self.info)
        super().mousePressEvent(event)

    def _on_play_clicked(self):
        # event bubbled to outer SearchBox
        self.parent().parent().parent().play_requested(self.info)


class SearchBox(QWidget):
    """
    Reusable search box widget with suggestion dropdown.
    Usage:
        sb = SearchBox()
        sb.queryChanged.connect(...)      # live typing
        sb.searchTriggered.connect(...)   # enter pressed
        sb.suggestionActivated.connect(...)  # suggestion clicked
        sb.playRequested.connect(...)     # play icon clicked
        sb.set_suggestions(list_of_dicts, query)
    """
    suggestionActivated = pyqtSignal(dict)
    playRequested = pyqtSignal(dict)
    searchTriggered = pyqtSignal(str)
    queryChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background: transparent;")

        self.container = QVBoxLayout(self)
        self.container.setContentsMargins(0, 0, 0, 0)
        self.container.setSpacing(6)

        # Search bar (rounded)
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
        h.addSpacing(8)
        self.search_icon = QLabel()
        search_pixmap = QPixmap("res/search.png")
        self.search_pixmap = search_pixmap.scaled(QSize(30, 30),Qt.KeepAspectRatio,Qt.SmoothTransformation)

        # active search icon
        active_search_pixmap = QPixmap("res/active-search.png")
        self.active_search_pixmap = active_search_pixmap.scaled(QSize(30, 30),Qt.KeepAspectRatio,Qt.SmoothTransformation)

        self.search_icon.setPixmap(self.search_pixmap)
        self.search_icon.setFixedSize(40, 40)
        self.search_icon.setStyleSheet("background: transparent; border: none;")
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

        self.input.focusInEvent = self._on_focus_in
        self.input.focusOutEvent = self._on_focus_out
        h.addWidget(self.input, 1)

        # Clear button
        self.clear_btn = QToolButton()
        self.clear_btn.setIcon(QIcon.fromTheme("edit-clear") or QIcon())
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QToolButton { border: none; background: transparent; color: #fff; }
            QToolButton:hover { background: rgba(255,255,255,0.04); border-radius: 12px; }
        """)
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.clicked.connect(self.clear)
        h.addWidget(self.clear_btn)

        self.container.addWidget(bar)

        # Suggestion panel (hidden until suggestions exist)
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

        # scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.suggestions_container = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(0)
        self.suggestions_container.setStyleSheet("background: transparent;")

        self.scroll.setWidget(self.suggestions_container)
        sv_layout.addWidget(self.scroll)
        self.container.addWidget(self.suggestions_frame)

        # internal state
        self._current_suggestions = []

        # keep maximum height for dropdown
        self.suggestions_frame.setMaximumHeight(360)

    def _on_focus_in(self, event):
        self.search_icon.setPixmap(self.active_search_pixmap)
        return QLineEdit.focusInEvent(self.input, event)


    def _on_focus_out(self, event):
        self.search_icon.setPixmap(self.search_pixmap)
        return QLineEdit.focusOutEvent(self.input, event)


    # ---------- public API ----------
    def set_suggestions(self, suggestions: list, query: str = ""):
        """
        suggestions: list of dicts: {id, title, subtitle, thumbnail}
        query: the current input text for highlighting matches
        """
        self._current_suggestions = suggestions or []
        # clear layout
        while self.suggestions_layout.count():
            w = self.suggestions_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        if not suggestions:
            self.suggestions_frame.setVisible(False)
            return

        for info in suggestions:
            item = SearchSuggestionItem(info, query)
            # connect via SearchBox wrapper methods using parents
            self.suggestions_layout.addWidget(item)

            # thin divider between items
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background-color: #1f1f1f; margin-left: 10px; margin-right: 6px;")
            self.suggestions_layout.addWidget(div)

        self.suggestions_layout.addStretch()
        self.suggestions_frame.setVisible(True)

    def hide_suggestions(self):
        self.suggestions_frame.setVisible(False)

    def clear(self):
        self.input.clear()
        self.hide_suggestions()
        self.clear_btn.setVisible(False)

    # ---------- signals and events ----------
    def _on_return(self):
        q = self.input.text().strip()
        if q:
            self.searchTriggered.emit(q)

    def _on_text_changed(self, text):
        self.queryChanged.emit(text)
        self.clear_btn.setVisible(bool(text))
        # caller should call set_suggestions(...) with remote results

    def suggestion_selected(self, info: dict):
        # internal helper called by item
        self.suggestionActivated.emit(info)
        # hide suggestions after selection
        self.hide_suggestions()

    def play_requested(self, info: dict):
        self.playRequested.emit(info)

    # ---------- utility ----------
    def _icon_pixmap_search(self, size=18):
        # small vector-like pixmap search: we return an SVG-like drawn pixmap placeholder
        p = QPixmap(size, size)
        p.fill(Qt.transparent)
        # fallback: use small circle icon; keep it simple
        # For real project, load an SVG from assets
        return p


class Topbar(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.setFixedHeight(90)
        self.setStyleSheet("background-color: #000000; border-bottom: 1px solid #262626;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(20)

        layout.addSpacing(10)


        # close sidebar button
        sidebar_btn = QPushButton()
        sidebar_btn.setIcon(QIcon("./res/menu.png"))
        sidebar_btn.setIconSize(QSize(34, 34))
        sidebar_btn.setFixedSize(56, 56)
        sidebar_btn.setCursor(Qt.PointingHandCursor)

        sidebar_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 28px;
            }
            QPushButton:hover {
                background-color: #1f1f1f;
                border-radius: 28px;
            }
            QPushButton:pressed {
                background-color: #262626;
                border-radius: 28px;
            }
        """)

   
        layout.addWidget(sidebar_btn)

        # logo
        logo_btn = QPushButton("AURIX")  
        logo_btn.setFont(QFont("Segoe UI", 20, QFont.Black))
        logo_btn.setIcon(QIcon("./res/pulse.png"))
        logo_btn.setIconSize(QSize(52, 52))
        logo_btn.setFixedSize(180, 56) 
        logo_btn.setCursor(Qt.PointingHandCursor)

        logo_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                color: white; 
                letter-spacing: 2px;
            }
        """)

        logo_btn.setLayoutDirection(Qt.RightToLeft)  # Ensures icon right, text left

        layout.addWidget(logo_btn)

        layout.addSpacing(80)

        # Center: search bar
        self.search_box = SearchBox()
        layout.addWidget(self.search_box)

        # Add spacer before the profile button
        layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))


        profile_btn = QPushButton()
        profile_btn.setObjectName("profileButton")
        profile_btn.setFixedSize(40, 40)
        profile_btn.setCursor(Qt.PointingHandCursor)

        profile_btn.setStyleSheet("""
            QPushButton#profileButton {
                border: none;
                padding: 0;
                border-radius: 20px;
                background-color: transparent;
                border-image: url("res/profile.png") 0 fill;
            }
        """)

        layout.addWidget(profile_btn)

        profile_btn.clicked.connect(lambda: print("Profile button clicked!"))

        layout.addSpacing(80)