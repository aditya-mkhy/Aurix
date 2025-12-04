from mutagen.id3 import ID3, APIC, TIT2, TLEN, TCON, TPE1, TALB, TDES, TPUB, WPUB, TDRL
import os
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap

def get_pixmap(path: str):
    if not os.path.isfile:
        return QPixmap()
    
    tags = ID3(path)
    for frame in tags.values():
        if isinstance(frame, APIC):
            pix = QPixmap()
            pix.loadFromData(frame.data)
            return pix
        
    return QPixmap()


class LocalFilesLoader(QThread):
    config_one = pyqtSignal(str, str, str, QPixmap)
    finished = pyqtSignal(bool)

    def __init__(self, music_dirs: list = [],parent = None):
        super().__init__(parent)
        self.music_dirs = self._ensure_list(music_dirs)

    def _ensure_list(self, x):
        if x is None:
            return []

        if isinstance(x, (list, tuple)):
            return list(x)
        return [x]

    
    def run(self):
        for dirctory in self.music_dirs:
            if os.path.isfile(dirctory):
                self._add_song(dirctory)
                continue

            if os.path.isdir(dirctory):
                self._list_music(dirctory)
                continue

            print(f"Error => This is not a file nor a dirctory.")

        self.finished.emit(True)

    def _is_mp3(self, path: str):
        return os.path.splitext(path)[1] == ".mp3"
        

    def _list_music(self, directory: str):
        for file in os.listdir(directory):
            absolute_path = os.path.join(directory, file)

            if os.path.isfile(absolute_path):
                self._add_song(absolute_path)
            # not handling the recursive directory..
            
    def _add_song(self, path: str):
        if not self._is_mp3(path):
            return
                
        tags = ID3(path)

        def _get_text(tag_id):
            frame = tags.get(tag_id)
            if frame and hasattr(frame, "text") and frame.text:
                return str(frame.text[0])
            return None
        
        title = _get_text("TIT2")
        publisher = _get_text("TPUB")

        # info = {
        #     "title":   _get_text("TIT2"),
        #     "publisher": _get_text("TPUB"),
        #     # "length":  _get_text("TLEN"),
        #     # "genre":   _get_text("TCON"),
        #     # "artist":  _get_text("TPE1"),
        #     # "album":   _get_text("TALB"),
        #     # "desc":    _get_text("TDES"),
        #     # "publisher_url": _get_text("WPUB"),
        #     # "release_date": _get_text("TDRL"),
        # }

        for frame in tags.values():
            if isinstance(frame, APIC):
                pix = QPixmap()
                pix.loadFromData(frame.data)
                self.config_one.emit(title, publisher, path, pix)
                break