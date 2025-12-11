import time
from pytube import YouTube ,Playlist
import os
from pathlib import Path
import yt_dlp
import threading
# from util import format_size, timeCal
import json

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from mutagen.id3 import ID3, TIT2, TLEN, TCON, TPE1, TALB, TDES, TPUB, WPUB, TDRL, APIC
from mutagen.mp3 import MP3
from requests  import get as get_request
from util import make_title_path


from typing import Iterable, Optional, Union
from mutagen.mp3 import MP3
from mutagen.id3 import (
    ID3, TIT2, TIT3, TPE1, TALB, COMM,
    TDRC, TXXX, WXXX
)
from datetime import datetime


class NoLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def date_to_id3(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")


class Dtube(QThread): # download tube
    finished = pyqtSignal(str, str, str, int)
    progress = pyqtSignal(int, str, int)

    def __init__(
            self, title: str = None, 
            subtitle_text: str = None, 
            url: str = None, 
            track_id: int = None, 
            parent = None, 
            folder: str = None
    ):
        
        super().__init__(parent)

        self.url = url
        self.track_id = track_id
        self.is_processing_emitted = False 
        self.is_downloading_emitted = False 
        # to send dowloading mode only once
        self.is_converting_emitted = False 


        # save folder... default music
        self.down_path = str(Path.home())+f'\\Music'

        if folder:
            if os.path.exists(folder):
                self.down_path = folder
            else:
                print(f"Folder Not Exists : {folder}")
                print(f"using default : {self.down_path}")


        self.title = title
        self.subtitle_text = subtitle_text
        
        if title == None:
            raise ValueError("Title can't be empty...")

        self.format_id = "bv*"

        self.is_video_dowloaded = False
        self.video_size = 0
        self.file_path = self._file_path()

        self.tags = None

    def _extract_info(self, info: dict):
        useful_info = {}

        if "requested_downloads" in info:
            # download info....
            useful_info["file_path"] = info["requested_downloads"][0]["filepath"]

        useful_info["available_at"] = info["available_at"]
        useful_info["artists"] = info["artists"]
        useful_info["creators"] = info["creators"]
        useful_info["fulltitle"] = info["fulltitle"]
        useful_info["original_url"] = info["original_url"]

        useful_info["album"] = info["album"]
        useful_info["categories"] = info["categories"]
        useful_info["duration"] = info["duration"]

        useful_info["id"] = info["id"]
        useful_info["title"] = info["title"]
        useful_info["description"] = info["description"]
        useful_info["view_count"] = info["view_count"]
        useful_info["release_date"] = info["release_date"]

        # get best thumbnail in jpg format
        useful_info["thumbnail"] = self._get_thumbnail(info)

        if not useful_info["thumbnail"]:
            # if not found.. use the default one
            useful_info["thumbnail"] = info["thumbnail"]
    
        return useful_info

    def _set_single_frame(self, frame):
        if not self.tags:
            raise ValueError("Tag is not set to the object")
        
        self.tags.delall(frame.FrameID)
        self.tags.add(frame)

    def _add_tags(self, info: dict) -> None:
        # if downloaf  file exists in the info
        if "file_path" in info and os.path.exists(info["file_path"]):
            self.file_path = info["file_path"]

        audio = MP3(self.file_path, ID3=ID3)

        # Ensure the file has an ID3 tag container
        if audio.tags is None:
            audio.add_tags()

        self.tags = audio.tags

        # title
        title = info['title'] if 'title' in info else self.title
        self._set_single_frame(TIT2(encoding=3, text=str(title)))

        # Subtitle
        self._set_single_frame(TIT3(encoding=3, text=str(self.subtitle_text)))

        # Artists -> list
        artists = info.get("artists")
        if artists:
            artist_list = [str(a) for a in artists]
            self._set_single_frame(TPE1(encoding=3, text=artist_list))

        # Album
        album = info.get("album")
        if album:
            self._set_single_frame(TALB(encoding=3, text=str(album)))

        # Description
        description = info.get("description")
        if description:
            # Delete all COMM frames with this description/lang to avoid duplicates
            self.tags.delall("COMM")
            self.tags.add(COMM(encoding=3, lang="eng", desc="Description", text=str(description),))


        # Release date
        release_date = info.get("release_date")
        if release_date:
            release_date = date_to_id3(release_date)
            self._set_single_frame(TDRC(encoding=3, text=str(release_date)))

        # Custom: YouTube video ID (user-defined text frame)
        video_id = info.get("id")
        if video_id:
            # TXXX with desc="YT_ID"
            # Remove any previous YT_ID frame
            for frame in list(self.tags.getall("TXXX")):
                if getattr(frame, "desc", "") == "YT_ID":
                    self.tags.delall("TXXX")
                    break

            self.tags.add(TXXX(encoding=3, desc="YT_ID", text=str(video_id),))


        # add cover image...
        try:
            response = get_request(info['thumbnail'])
            self.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=response.content))

        except Exception as e:
            print("Error [thumbnail_to_mp3] : ", e)

        # Finally, write the tags to file
        audio.save()



    def run(self):
        try:
            if not self.is_processing_emitted:
                self.is_processing_emitted = True
                self._emit_progress_hook("loading")

            info = self._download()
            ext_info = self._extract_info(info)

            # add tags...
            self._add_tags(ext_info) #

            # emit status
            self._emit_progress_hook("done")
            self.finished.emit(self.title, self.subtitle_text, self.file_path, self.track_id)

        except Exception as e:
            print(f"Error In Downloading : {e}")
            self._emit_progress_hook("error")
            self.finished.emit(None, None, None, None)

    def _get_thumbnail(self, data: dict):
        thumbnails = data.get("thumbnails", [])
        pref = -100
        url_thmb = None

        for thumbnail in thumbnails:
            preference = thumbnail.get("preference")
            if preference > pref:
                url = thumbnail.get("url", "")
                _, ext = os.path.splitext(url)
                if ext == ".jpg":
                    pref = preference
                    url_thmb = url

        return url_thmb


    def _file_path(self):
        return f"{self.down_path}\\{self.filename()}"
        

    def filename(self):
        title_path = make_title_path(self.title)
        return f"{title_path}.mp3"
    
    def remove_ext_file_path(self):
        return os.path.splitext(self.file_path)[0]


    def _download(self) -> dict:
        if self.url == None:
            raise ValueError("Please provide a video or playlist url....")

        ydl_opts =ydl_opts = {
            # get best audio format from YT / YT Music
            # "cookiesfrombrowser": ("chrome",),
            'format': 'bestaudio[acodec=opus]/bestaudio[acodec^=mp4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            "logger": NoLogger(),
            'outtmpl': self.remove_ext_file_path(),
            "progress_hooks": [self._progress_hook], 
            # hide ffmpeg conversion messages
            "postprocessor_args": ['-hide_banner', '-loglevel', 'error'],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',   # output codec
                'preferredquality': '0',   # '0' = best VBR, or '320' for 320kbps CBR
            }],
        }

      
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=True)  # Downloads the video
                # with open("t.json", "w") as tf:
                #     tf.write(json.dumps(info_dict))

                return info_dict

        except Exception as e:
            print(f"An error occurred: {e}")
            return {}
        

    def _emit_progress_hook(self, type: str, value: int = 0):
        self.progress.emit(self.track_id, type, value)


    def _progress_hook(self, d):
        # Extracting metadata
        if d['status'] in ("extracting", "downloading playlist", "pre_process"):
            if not self.is_processing_emitted:
                self.is_processing_emitted = True
                self._emit_progress_hook("loading")
            return

        # Active download
        if d['status'] == 'downloading':

            _percent = d.get("_percent", None)
            # if not found..
            if _percent is None:
                total_bytes = d.get("total_bytes", 0)
                downloaded_bytes = d.get("downloaded_bytes", 0)

                try:
                    _percent = int((downloaded_bytes / total_bytes) * 100)
                except:
                    _percent = 0

            else:
                _percent = int(_percent)
            


            if not self.is_downloading_emitted:
                self.is_downloading_emitted = True
                self._emit_progress_hook("downloading")

            self._emit_progress_hook("percentage", int(_percent))
            return

        # Download finished but not processed (FFmpeg next)
        if d['status'] == 'finished':
            if not self.is_converting_emitted:
                self.is_converting_emitted = True
                self._emit_progress_hook("converting")
            return

        # Post-processing (FFmpeg convertion)
        if d['status'] == 'postprocess':
            # if not emmitted...
            if not self.is_converting_emitted:
                self.is_converting_emitted = True
                self._emit_progress_hook("converting")

            # You can check keys to know post type:
            pp_state = d.get("postprocessor", "").lower()
        
            if "ffmpeg" in pp_state:
                print("ffmpeg is working...")
            return

        # Fully done
        if d['status'] == 'postprocess_done':
            # done will be emmited only when everything is finished... like adding tags
            return

        if d['status'] == 'error':
            print("Error Occured...")
            self._emit_progress_hook("error")


if __name__ == "__main__":
    # d = Dtube()

    with open("t.json", "r") as ff:
        json_data = json.loads(ff.read())

    info = Dtube._exract_info("", json_data)

