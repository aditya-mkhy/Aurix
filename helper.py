from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QObject
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QPen, QColor, QPainterPath
from PyQt5.QtWidgets import QWidget
import os
import requests
from ytmusicapi import YTMusic
from util import is_mp3
from databse import DataBase
from typing import List
from util import gen_thumbnail_path, COVER_DIR_PATH
from PIL import Image

YT_MUSIC = YTMusic()


def create_playlist_cover(image_paths, output_path, size=290):
    # only one image in the list
    if len(image_paths) == 1:
        img = Image.open(image_paths[0])
        img.save(output_path,  "JPEG", quality=100)
        return output_path
    
    images = []
    for path in image_paths[:4]:
        if os.path.exists(path):
            img = Image.open(path).convert("RGB")
            images.append(img)

    if not images:
        return
    
    if len(images) < 4:
        images.insert(2, images[1])
        images.insert(3, images[0])

    # Resize each image to quarter size
    half = size // 2
    images = [img.resize((half, half), Image.LANCZOS) for img in images]

    # Create blank canvas
    collage = Image.new("RGB", (size, size), (0, 0, 0))

    # Paste images (2x2 grid)
    collage.paste(images[0], (0, 0))
    collage.paste(images[1], (half, 0))
    collage.paste(images[2], (0, half))
    collage.paste(images[3], (half, half))

    collage.save(output_path, "JPEG", quality=100)
    return output_path


class LoadFiles(QObject):
    addOneSong = pyqtSignal(int, int, str, str, str, str)
    finished = pyqtSignal(bool)

    def __init__(self, dataBase: DataBase = None, parent = None):
        super().__init__(parent)

        self.dataBase = dataBase

        # list of id's of the song wich does not exists anymore
        # so to remove later add here
        self._to_delete: List[int] = []

        self.sleep_on_count = 10
        self.count = 0
        self.song_index = -1
        self.batch_size = 10

        self.all_songs = []

    def add_song_batch(self, start_index: int):
        end_index = start_index + self.batch_size

        for song in self.all_songs[start_index : end_index]:
            self.song_index += 1
            print("ide==> ", self.song_index)

            if not os.path.exists(song['path']):
                print(f"PathNotFound [{song['id']}] => {song['path']}")
                # add to delete later
                self._to_delete.append(song['id'])
                continue


            cover_path = os.path.join(COVER_DIR_PATH, song['cover_path'])
            if not os.path.exists(cover_path):
                # if cover path not found...
                print(f"Cover ===> {song['cover_path']}")
                if song['cover_path'] == "":
                    # if cover not in db
                    # gen new cover_path
                    cover_path = gen_thumbnail_path()
                
                else:
                    # get filename  from prev path
                    filename = os.path.basename(song['cover_path'])
                    cover_path = os.path.join(COVER_DIR_PATH, filename)

                # extract cover from song and save to cover directory
                cover_path = extract_cover_save(song['path'], cover_path)

                if not cover_path:
                    # this song doesn't have a cover
                    # using default cover image
                    cover_path = "default cover."  # add later
                    print(f"CoverNotPath not found in the song file... ==> {song['path']}")
                    print("Plase  check manually......")

                # save new path to db
                filename = os.path.basename(cover_path)
                self.dataBase.update_song(song_id=song['id'], cover_path=filename)


            self.addOneSong.emit(self.song_index, song['id'], song['title'], song['subtitle'], song['path'], cover_path)

        if end_index < len(self.all_songs):
            QTimer.singleShot(300, lambda idx=end_index: self.add_song_batch(idx))

        else:
            self.finished.emit(True)


    def run(self):
        self.all_songs = self.dataBase.get_song()
        self.add_song_batch(0)


def round_pix_form_path(path: str, width:int, height:int, radius: int = 8) -> QPixmap:
    pix = QPixmap(path)
    return round_pix(pix, width, height, radius)

def round_pix(pix: QPixmap,  width:int, height:int, radius: int = 8) -> QPixmap:
    if pix.isNull():
        return pix
    
    rounded = QPixmap(QSize(width, height))
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)

    path = QPainterPath()
    path.addRoundedRect(0, 0, width, height, radius, radius)

    painter.setClipPath(path)

    painter.drawPixmap(0, 0, pix.scaled(width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
    painter.end()
  
    return rounded


def crop_and_save_img(img_data: bytes, out_path: str, from_left: int = 0, from_right: int = 0) -> str:
    if not out_path:
        raise ValueError("Enter a valid out_path..")
    
    pix = QPixmap()
    if not pix.loadFromData(img_data):
        raise ValueError("Invalid image data or unsupported format")
    
    width = pix.width()
    
    width = max(1, width - from_left - from_right)
    pix = pix.copy(from_left, 0, width, pix.height())

    _, ext = os.path.splitext(out_path)
    ext = ext[1:].upper() # remove dot(.) and captalize
    pix.save(out_path, ext)

    return out_path

def extract_cover_save(song_path: str, cover_path: str):
    tags = ID3(song_path)
    for frame in tags.values():
        if isinstance(frame, APIC):
            with open(cover_path, "wb") as tf:
                tf.write(frame.data)
            return cover_path


def get_mp3_metadata(path: str) -> dict:
    audio = MP3(path)
    info = {
        "duration": int(audio.info.length),
        "sample_rate": audio.info.sample_rate,
        "channels": audio.info.channels,
        "bitrate": audio.info.bitrate,
        "mode": audio.info.mode,  # Stereo, JointStereo etc.
        "version": audio.info.version,
        "layer": audio.info.layer,
    }

    return info


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
                    "artists" : item["artists"],
                    "thumbnail_url" : thumbnail_url,
                    "videoId" : item["videoId"]
                })

            else:
                
                custom_result2.append({
                    "title" : item["title"],
                    "subtitle" : subtitle,
                    "artists" : item["artists"],
                    "thumbnail_url" : thumbnail_url,
                    "videoId" : item["videoId"]
                })

            count += 1

        return custom_result, custom_result2
    

class ConfigResult(QThread):
    add_one = pyqtSignal(str, str, list, str, QPixmap)
    finished = pyqtSignal(bool)

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result

    def run(self):

        for item in self.result:
            title = item["title"]
            subtitle = item["subtitle"]
            artists = item["artists"]
            vid = item['videoId']

            thumbnail_url = item["thumbnail_url"]

            try:
                resp = requests.get(thumbnail_url, timeout=10)
                resp.raise_for_status()
                pix = QPixmap()
                pix.loadFromData(resp.content)

                self.add_one.emit(title, subtitle, artists, vid, pix)

            except Exception as e:
                self.add_one.emit(title, subtitle, artists, vid, None)

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


    def _list_music(self, directory: str):
        for file in os.listdir(directory):
            absolute_path = os.path.join(directory, file)

            if os.path.isfile(absolute_path):
                self._add_song(absolute_path)
            # not handling the recursive directory..
            
    def _add_song(self, path: str):
        if not is_mp3(path):
            return
        
        # giving time to lead the window fully then add files...
        if self.count != -1:
            self.count += 1
            
            if self.count > 8:
                # return
                QThread.sleep(2)
                self.count = -1
        else:
            QThread.msleep(15)
  

        tags = ID3(path)

        def _get_text(tag_id):
            frame = tags.get(tag_id)
            if frame and hasattr(frame, "text") and frame.text:
                return str(frame.text[0])
            return None
        
        title = _get_text("TIT2")
        publisher = _get_text("TPUB")
        if not publisher:
            publisher = _get_text("TIT3")

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
        # draw an arc that rotates
        painter.drawArc(rect, self.angle * 16, 120 * 16)



if __name__ == "__main__":
    image_list = [
        "C:\\Users\\dgg\\.aurix\\cvr\\9xer8vedluesck35zaqjhamwzkvc6k.jpg",
        "C:\\Users\\dgg\\.aurix\\cvr\\0xqss2rnaw6yxoeip2mcfmrmg9cd55.jpg",
        "C:\\Users\\dgg\\.aurix\\cvr\\0rp0887rq1vyg0kmx9m3wtveosz195.jpg",
        # "C:\\Users\\dgg\\.aurix\\cvr\\2urof5ipq7tgvfu59j0l0b8ouw3eo8.jpg",
    ]

    outpath = "C:\\Users\\dgg\\.aurix\\cvr\\playlist_2.jpg"

    path = create_playlist_cover(image_list, outpath, size=712)
    