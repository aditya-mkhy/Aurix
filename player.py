from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


class PlayerEngine(QObject):
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    stateChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer()
        self.current_path = None

        self.player.positionChanged.connect(self.positionChanged)
        self.player.durationChanged.connect(self.durationChanged)
        self.player.stateChanged.connect(self.stateChanged)

    def load(self, path: str):
        """Load a file and be ready to play."""
        self.current_path = path
        url = QUrl.fromLocalFile(path)
        self.player.setMedia(QMediaContent(url))

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()

    def stop(self):
        self.player.stop()

    def set_position(self, pos: int):
        self.player.setPosition(int(pos))

    def set_volume(self, vol: int):
        self.player.setVolume(int(vol))

    def state(self):
        return self.player.state()

    def duration(self):
        return self.player.duration()

    def position(self):
        return self.player.position()
