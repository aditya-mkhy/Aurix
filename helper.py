from mutagen.id3 import ID3, APIC, TIT2, TLEN, TCON, TPE1, TALB, TDES, TPUB, WPUB, TDRL
import os
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread

class LocalFilesLoader(QThread):
    config_one = pyqtSignal()
    finished = pyqtSignal(bool)

    def __init__(self, music_dirs: list = [],parent = None):
        super().__init__(parent)
        self.music_dirs = music_dirs

    
    def run(self):
        for dirctory in self.music_dirs:
            if os.path.isfile(dirctory):
                self._add_song(dirctory)
                continue

            if os.path.isdir(dirctory):
                self._list_music(dirctory)
                continue

            print(f"Error => This is not a file nor a dirctory.")

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
        path = None

        def _get_text(tag_id):
            frame = tags.get(tag_id)
            if frame and hasattr(frame, "text") and frame.text:
                return str(frame.text[0])
            return None

        info = {
            "title":   _get_text("TIT2"),
            "length":  _get_text("TLEN"),   # usually in ms (string)
            "genre":   _get_text("TCON"),
            "artist":  _get_text("TPE1"),
            "album":   _get_text("TALB"),
            "desc":    _get_text("TDES"),
            "publisher": _get_text("TPUB"),
            "publisher_url": _get_text("WPUB"),
            "release_date": _get_text("TDRL"),
        }

        # ---- Extract cover (APIC frame) ----
        cover_data = None
        cover_mime = None

        # APIC frames can have descriptors like 'APIC:', 'APIC:Cover', etc.
        apic_frame = None
        for frame in tags.values():
            if isinstance(frame, APIC):
                apic_frame = frame
                break

        if apic_frame is not None:
            cover_data = apic_frame.data
            cover_mime = apic_frame.mime

            if cover_save_path:
                filename = f"{make_title_path(info['title'])}.jpg"
                path = os.path.join(cover_save_path, filename)
                with open(path, "wb") as tf:
                    tf.write(cover_data)



        return info, path
            