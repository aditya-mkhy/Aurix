import os
from datetime import datetime
import yt_dlp
from PyQt5.QtCore import pyqtSignal, QThread
from mutagen.id3 import ID3, TIT2, TIT3, TPE1, TALB, APIC, COMM, TDRC, TXXX
from mutagen.mp3 import MP3
from requests  import get as get_request
from util import make_title_path, gen_thumbnail_path, MUSIC_DIR_PATH
from helper import crop_and_save_img

class NoLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def date_to_id3(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")


def get_mp3_tags(file_path: str, *requested_tags):

    audio = MP3(file_path, ID3=ID3)
    tags = audio.tags

    if tags is None:
        return {} if not requested_tags else {t: None for t in requested_tags}

    # Helper to read a tag safely
    def read(tag_name):
        # TITLE
        if tag_name == "title":
            frame = tags.get("TIT2")
            return frame.text[0] if frame else None
        
        # SUBTITLE
        if tag_name == "subtitle":
            frame = tags.get("TIT3")
            return frame.text[0] if frame else None
        
        # ARTISTS
        if tag_name == "artists":
            frame = tags.get("TPE1")
            return frame.text if frame else None
        
        # ALBUM
        if tag_name == "album":
            frame = tags.get("TALB")
            return frame.text[0] if frame else None
        
        # DESCRIPTION
        if tag_name == "description":
            comms = tags.getall("COMM")
            for c in comms:
                if c.desc == "Description":
                    return c.text
            return None
        
        # RELEASE DATE
        if tag_name == "release_date":
            frame = tags.get("TDRC")
            return str(frame.text[0]) if frame else None
        
        # YOUTUBE VIDEO ID (TXXX)
        if tag_name == "id":
            frames = tags.getall("TXXX")
            for f in frames:
                if f.desc == "YT_ID":
                    return f.text[0]
            return None
        
        # ORIGINAL URL (WXXX)
        if tag_name == "original_url":
            frames = tags.getall("WXXX")
            for f in frames:
                if f.desc == "ORIGINAL_URL":
                    return f.url
            return None

        return None  # unknown tag

    # If specific tags requested → return only those
    if requested_tags:
        return {tag: read(tag) for tag in requested_tags}

    # Otherwise return ALL
    all_tags = {
        "title": read("title"),
        "subtitle": read("subtitle"),
        "artists": read("artists"),
        "album": read("album"),
        "description": read("description"),
        "release_date": read("release_date"),
        "id": read("id"),
        "original_url": read("original_url"),
    }

    return all_tags

    
def gen_path(title: str, vid: str, artists: list = None) -> str | None:
    artists = [artist['name'] for artist in artists] # dict into list

    title_path = make_title_path(title)
    filename = f"{title_path}.mp3"

    path = os.path.join(MUSIC_DIR_PATH, filename)
    
    # if path not exists
    if not os.path.exists(path):
        return path
    
    # artists
    last = None
    if len(artists) > 1:
        last = artists.pop()

    all_artists = ", ".join(artists) + (f" & {last}" if last else "")

    # file path with artists
    filename = f"{title_path} by {all_artists}.mp3"
    path = os.path.join(MUSIC_DIR_PATH, filename)

    if not os.path.exists(path):
        return path
    
    # if still exists. add yt_id
    filename = f"{title_path} by {all_artists} with id - {vid}.mp3"
    path = os.path.join(MUSIC_DIR_PATH, filename)

    if not os.path.exists(path):
        return path
    # if still exits.. means all ready downloaded..


class Dtube(QThread): # download tube
    """
    Docstring for Dtube

    title : song title
    subtitle : song subtitle
    artists : list of artists
    vid : video id -> SBrs9-Xb2dk
    track_id : row_id for navigating the called UI row
    parent: parent
    """
    finished = pyqtSignal(str, str, str, str, str, str, int, int)
    progress = pyqtSignal(int, str, int)


    def __init__(self, title: str, subtitle: str, artists: list, vid: str, track_id: int, parent = None):
        
        super().__init__(parent)
        self.title = title
        if title == None:
            raise ValueError("Title can't be empty...")
        
        # remove song from subtitle
        if "song" in subtitle.lower():
            subtitle = subtitle[subtitle.find("•") + 1 : ]

        self.subtitle = subtitle.strip()

        self.artists = artists
        self.vid = vid

        self.url = f"https://music.youtube.com/watch?v={self.vid}"
        self.track_id = track_id

        self.is_processing_emitted = False 
        self.is_downloading_emitted = False 

        # to send dowloading mode only once
        self.is_converting_emitted = False 

        self.format_id = "bv*"

        self.is_video_dowloaded = False
        self.video_size = 0
        self.file_path = gen_path(self.title, self.vid, self.artists)

        # audio tags...
        self.tags = None
        self.cover_path = None  # value is added when "_add_tags" is called


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

            artist = ",".join(ext_info['artists']) # to store in database

            self.finished.emit(
                self.title, self.subtitle, artist, self.vid,
                self.file_path, self.cover_path,
                ext_info["duration"], self.track_id
            )

        except Exception as e:
            print(f"Error In Downloading : {e}")
            self._emit_progress_hook("error")
            self.finished.emit(None, None, None, None, None, None, None, None)

    
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

    
    def _get_thumbnail(self, data: dict):
        # get best thumbnail in jpg format
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

    def _extract_info(self, info: dict):
        useful_info = {}

        if "requested_downloads" in info:
            # download info....
            useful_info["file_path"] = info["requested_downloads"][0]["filepath"]

        # useful_info["available_at"] = info["available_at"]
        useful_info["artists"] = info["artists"]
        # useful_info["creators"] = info["creators"]
        # useful_info["fulltitle"] = info["fulltitle"]
        # useful_info["original_url"] = info["original_url"]

        useful_info["album"] = info["album"]
        # useful_info["categories"] = info["categories"]
        useful_info["duration"] = info["duration"]

        useful_info["id"] = info["id"]
        useful_info["title"] = info["title"]
        useful_info["description"] = info["description"]
        # useful_info["view_count"] = info["view_count"]
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
        self._set_single_frame(TIT3(encoding=3, text=str(self.subtitle)))

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
            # save the cropped thumbanil into folder
            self.cover_path = self.save_thumnail(url = info['thumbnail'])

            with open(self.cover_path, "rb") as ff:
                data = ff.read()

            audio.tags.add(APIC(encoding=0, mime="image/jpeg", type=0, desc="Cover", data=data))

        except Exception as e:
            print("Error [thumbnail_to_mp3] : ", e)
        # Finally, write the tags to file
        audio.save()

    def save_thumnail(self, url: str):
        path = gen_thumbnail_path()
        response = get_request(url)
        path = crop_and_save_img(img_data=response.content, out_path=path, from_left=284, from_right=284)
        return path



if __name__ == "__main__":
    url = "https://i.ytimg.com/vi/r7Rn4ryE_w8/maxresdefault.jpg"
