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

def get_thumbnail(data: dict):
    thumbnails = data.get("thumbnails", [])
    pref = -100
    url_thmb = ""

    for thumbnail in thumbnails:
        preference = thumbnail.get("preference")
        if preference > pref:
            url = thumbnail.get("url", "")
            _, ext = os.path.splitext(url)
            if ext == ".jpg":
                pref = preference
                url_thmb = url

    return url_thmb


class NoLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass



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
        print(f"file_path => {self.file_path}")
        self.thumbnail_path = f"C:\\Users\\freya\\Downloads\\m\\{os.path.splitext(os.path.basename(self.file_path))[0]}.jpg"
        print(f"thumbnail_path => {self.thumbnail_path}")


    def run(self):
        try:
            if not self.is_processing_emitted:
                self.is_processing_emitted = True
                self._emit_progress_hook("loading")

            info = self._download()
            self._add_tags(info) #

            self._emit_progress_hook("done")
            self.finished.emit(self.title, self.subtitle_text, self.file_path, self.track_id)
        except Exception as e:
            print(f"Error In Downloading : {e}")
            self._emit_progress_hook("error")
            self.finished.emit(None, None, None, None)


    def _file_path(self):
        return f"{self.down_path}\\{self.filename()}"
        

    def filename(self):
        title_path = self.make_title_path()
        return f"{title_path}.mp3"
    
    def remove_ext_file_path(self):
        return os.path.splitext(self.file_path)[0]
    

    def make_title_path(self, title = None):
        not_include = ' <>:"/\\|?*'+"'"
        title_path = ""

        if title == None:
            title = self.title

        for w in title:
            if w in not_include:
                if title_path[-1:] != " ":
                    title_path += " "
            else:
                title_path += w

        return title_path
    

    def _add_tags(self, down_info: dict):
        channel = down_info.get("channel", "Aurix")
        description = down_info.get("description", "Aurix")
        original_url = down_info.get("original_url", "Aurix")
                    # add ID3 tags
        audio = MP3(self.file_path, ID3=ID3)
        audio.tags.add(TIT2(encoding=3, text=str(self.title)))
        audio.tags.add(TPE1(encoding=3, text=str(channel)))
        audio.tags.add(TDES(encoding=3, text=str(description)))
        audio.tags.add(TPUB(encoding=3, text=str(channel)))
        audio.tags.add(WPUB(encoding=3, text=str(original_url)))

        try:
            audio.add_tags()
        except Exception as e:
            print("Error[ID3_add_tag] :", e)

        try:
            url_thmb = get_thumbnail(down_info)
            print(url_thmb)
            response = get_request(url_thmb)
            data = response.content
            with open(self.thumbnail_path, "wb") as tf:
                tf.write(data)

            audio.tags.add(
                APIC(
                    encoding=0,
                    mime="image/jpeg",
                    type=0,
                    desc="",
                    data=data,
                )
            )
        except Exception as e:
            print("Error[thumbnail_to_mp3] :", e)

        audio.save()



        
    def _download(self) -> dict:
        if self.url == None:
            raise ValueError("Please provide a video or playlist url....")

        ydl_opts =ydl_opts = {
            # get best audio format from YT / YT Music
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
                with open("t.json", "w") as tf:
                    tf.write(json.dumps(info_dict))
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
    url = "https://music.youtube.com/watch?v=Het4pXDENBI"
