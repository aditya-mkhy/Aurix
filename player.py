import os
import pygame


class MusicPlayer:
    def __init__(self):
        # init pygame mixer only (no window)
        pygame.mixer.init()
        self._current_path = None
        self._is_paused = False

    def load(self, path: str):
        """Load an audio file, ready to play."""
        if not os.path.isfile(path):
            print("File not found:", path)
            return

        self._current_path = path
        pygame.mixer.music.load(path)
        self._is_paused = False

    def play(self, path: str = None):
        """
        Play current file.
        If `path` is given, load it first then play.
        """
        if path is not None:
            self.load(path)

        if self._current_path is None:
            print("No file loaded")
            return

        pygame.mixer.music.play(loops=-1)
        self._is_paused = False

    def pause(self):
        if not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
        else:
            pygame.mixer.music.unpause()
            self._is_paused = False

    def stop(self):
        pygame.mixer.music.stop()
        self._is_paused = False

    def set_volume(self, vol: float):
        """
        vol: 0.0 to 1.0
        """
        vol = max(0.0, min(1.0, float(vol)))
        pygame.mixer.music.set_volume(vol)

    def is_playing(self) -> bool:
        return pygame.mixer.music.get_busy() and not self._is_paused
