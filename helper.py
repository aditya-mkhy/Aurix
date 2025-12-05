from mutagen.id3 import ID3, APIC, TIT2, TLEN, TCON, TPE1, TALB, TDES, TPUB, WPUB, TDRL
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QIcon, QPen
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QMenu
)

import os
import sys
import requests
from ytmusicapi import YTMusic

YT_MUSIC = YTMusic()

class YTSearchThread(QThread):
    finished = pyqtSignal(list, list)

    def __init__(self, query: str, parent = None):
        super().__init__(parent)

        self.filter = "songs"
        self.limit = 20
        self.thumbnail_size = 120
        self.query = query

    def run(self):
        try:
            result1, result2 = self.search()
            self.finished.emit(result1, result2)
        except:
            self.finished.emit([], [])


    def search(self) -> list:
        results = YT_MUSIC.search(
            self.query, 
            filter=self.filter, 
            limit=self.limit,
        )

        custom_result = []
        custom_result2 =[]

        count = 0

        for item in results:

            if count >= self.limit:
                break

            thumbnail_url = ""

            for thumbnail in item["thumbnails"]:
                thumbnail_url = thumbnail["url"]
                if thumbnail["width"] ==  self.thumbnail_size:
                    break

            artists = []
            for artist in item["artists"]:
                artists.append(artist["name"])

            last = None
            if len(artists) > 1:
                last = artists.pop()

            all_artists = ", ".join(artists) + (f" & {last}" if last else "")

            result_type = "Song" if item["resultType"] == "song" else "Video"

            subtitle = f"{result_type} • " + all_artists + f" • {item["views"]} plays"

            #Song • Pritam, Kamaal Khan, Nakash Aziz & Dev Negi 123M plays

            if count % 2 == 0:
                custom_result.append({
                    "title" : item["title"],
                    "subtitle" : subtitle,
                    "thumbnail_url" : thumbnail_url,
                    "videoId" : item["videoId"]
                })

            else:
                
                custom_result2.append({
                    "title" : item["title"],
                    "subtitle" : subtitle,
                    "thumbnail_url" : thumbnail_url,
                    "videoId" : item["videoId"]
                })

            count += 1

        return custom_result, custom_result2
    

class ConfigResult(QThread):
    add_one = pyqtSignal(str, str, str, QPixmap)
    finished = pyqtSignal(bool)

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result

    def run(self):

        for item in self.result:
            title = item["title"]
            subtitle = item["subtitle"]
            url = f"https://music.youtube.com/watch?v={item['videoId']}"
            thumbnail_url = item["thumbnail_url"]

            try:
                resp = requests.get(thumbnail_url, timeout=15)
                resp.raise_for_status()
                pix = QPixmap()
                pix.loadFromData(resp.content)

                self.add_one.emit(title, subtitle, url, pix)

            except Exception as e:
                self.add_one.emit(title, subtitle, url, pix, QPixmap())

        self.finished.emit(True)



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

    def __init__(self, music_dirs: list = None, parent = None):
        super().__init__(parent)
        self.music_dirs = self._ensure_list(music_dirs)
        self.sleep_on_count = 10
        self.count = 0

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
        return os.path.splitext(path)[1].lower() == ".mp3"
        

    def _list_music(self, directory: str):
        for file in os.listdir(directory):
            absolute_path = os.path.join(directory, file)

            if os.path.isfile(absolute_path):
                self._add_song(absolute_path)
            # not handling the recursive directory..
            
    def _add_song(self, path: str):
        if not self._is_mp3(path):
            return
        
        # giving time to lead the window fully then add files...
        if self.count != -1:
            self.count += 1
            print(self.count)
            if self.count > 6:
                QThread.sleep(2)
                self.count = -1
                
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
                # song with cover is uselesss... 
                break




class CircularProgress(QWidget):
    def __init__(self, size=60, parent=None):
        super().__init__(parent)
        self._value = 0   # 0–100
        self.size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setValue(self, value: int):
        self._value = max(0, min(100, value))  # clamp
        self.update()  # refresh UI

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(6, 6, -6, -6)
        radius = min(rect.width(), rect.height()) // 2

        # background circle
        bg_pen = QPen(QColor(120, 120, 120, 120), 6)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)

        # progress arc
        angle = int(360 * (self._value / 100))
        progress_pen = QPen(QColor("#00944D"), 6)  # neon green like YT Premium
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(rect, -90 * 16, -angle * 16)

        # text
        painter.setPen(Qt.white)
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(self.rect().adjusted(4, 0, 4, 0), Qt.AlignCenter, f"{self._value}%")

class ConvertingSpinner(QWidget):
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setFixedSize(size, size)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def rotate(self):
        self.angle = (self.angle - 10) % 360
        self.update()

    def start(self):
        self.show()
        self.timer.start(30)

    def stop(self):
        self.timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(6, 6, -6, -6)

        # background circle
        bg_pen = QPen(QColor(120, 120, 120, 100), 6)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)

        pen = QPen(QColor("#00944D"), 6)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        # draw an arc (chunk) that rotates
        painter.drawArc(rect, self.angle * 16, 120 * 16)


class LoadingSpinner(QWidget):
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setFixedSize(size, size)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def start(self):
        self.show()
        self.timer.start(30)

    def stop(self):
        self.timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(6, 6, -6, -6)

        # background circle
        bg_pen = QPen(QColor(120, 120, 120, 100), 6)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)

        pen = QPen(QColor("#FFFFFF"), 6)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        # draw an arc (chunk) that rotates
        painter.drawArc(rect, self.angle * 16, 120 * 16)



if __name__ == "__main__":
    yts = YTSearchThread("Naach Meri Jaan")
    # yts.run()
