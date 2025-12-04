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


def get_video_info(url : str = None) -> dict:
    if not url:
        raise ValueError(("Url can't be empty..."))
    
    videos_info = {}
    
    ydl_opts = {
        'quiet': True,  # Suppress output
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        with open("t.json", "w") as tf:
            tf.write(json.dumps(info))

        return info
        title = info.get("title", "no_title")
    
        formats = info.get('formats', [])
        best_audio_format = None


        # audio format....file_size....
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':  # Audio-only formats
                if not best_audio_format or f.get('filesize', 0) > best_audio_format.get('filesize', 0):
                    best_audio_format = f

        best_audio_size = best_audio_format.get('filesize', 0) if best_audio_format and best_audio_format.get('filesize') else 0
        
        videos_info["mp3"] = {
            "size" : best_audio_size,
            "id" : "mp3",
            "resolution" : "none"
        }

        # Video resolutions....
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get("format_note") != None:
                resolution = f.get('resolution')
                if not resolution:
                    continue

                format_id = f.get('format_id')

                # add audio size into video size 
                # if video is premimum then size = 0
                filesize = f.get('filesize', 0) + best_audio_size if f.get('filesize') else 0
                format_note = f.get('format_note') # quality of the 
                
                if videos_info.get(format_note): #format_note exits in info
                    # filesize is greter video quality is better
                    if videos_info[format_note]["size"] > filesize:
                        continue

                videos_info[format_note] = {
                    "size" : filesize,
                    "id" : format_id,
                    "resolution" : resolution
                }

    return videos_info, title



class Dtube(QThread): # download tube
    finished = pyqtSignal(str, str, str)

    def __init__(self, title: str = None, subtitle_text: str = None, url: str = None, parent = None, folder: str = None):
        super().__init__(parent)

        self.url = url

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
        # try:
        info = self._download()
        self._add_tags(info) #
        self.finished.emit(self.title, self.subtitle_text, self.file_path)
        # except Exception as e:
        #     print(f"Error In Downloading : {e}")
        #     self.finished.emit(None, None, None, None)


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
            'outtmpl': self.remove_ext_file_path(),

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


    def progress_hook(self, d):
        """
        Hook function to display progress during the download.
        """
    
        try:
            if d['status'] == 'downloading':

                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', d.get('total_bytes_estimate', 0))
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                filename = d.get('filename', '')
                tmpfilename = d.get('tmpfilename', '')

                if not self.is_video_dowloaded:
                    self.video_size = total

                else:
                    #update the musicccc...
                    downloaded += self.video_size
                    total += self.video_size


                time_left = f"{timeCal(eta)} left"
                speed = format_size(speed)
                prog_info = "(%s of  %s ,  %s/s)" %(format_size(downloaded) , format_size(total), speed)


                status = {
                    "status" : "downloading",
                    "filename" : filename,
                    "downloaded" : downloaded,
                    "eta" : time_left,
                    "progress" : prog_info,
                }

                self.progress(status)


            elif d['status'] == 'finished':
                filename = d.get('filename', '')

                status = {
                    "status" : "finished",
                    "filename" : filename
                }

                if not self.is_video_dowloaded:
                    self.is_video_dowloaded = True
                
                self.progress(status)


            elif d['status'] == 'error':
                status = {
                    "status" : "error",
                }
    
                self.progress(status)

        except:
            pass

    
   
        

if __name__ == "__main__":
    url = "https://music.youtube.com/watch?v=Het4pXDENBI"
    info = get_video_info(url=url)
    # url  = "https://www.youtube.com/playlist?list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt"#shradha
