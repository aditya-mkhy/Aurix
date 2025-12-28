import sqlite3
from typing import List, Dict
from util import DATABASE_PATH, dict_format
import os

class DataBase():
    def __init__(self, path:str = None):
        if path is None:
            path = DATABASE_PATH

        self.conn = sqlite3.connect(path)
        
        # row_factory to get dict-like rows
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        if self.is_not_init():
            print(f"Initializing DataBase")
            self._db_init()
            self._init_basic_data()
            self._init_playlist()

    def commit(self):
        self.conn.commit()

    def add_basic(self, key: str, value: str| int):
        self.cursor.execute('UPDATE basic SET value = ? WHERE key = ?', (str(value), key))
        self.conn.commit()

    def get_basic(self, key: str | None = None):
        if key is not None:
              self.cursor.execute("SELECT value FROM basic WHERE key=?", (key,))
              row = self.cursor.fetchone()
              return row[0] if row else None
        

        self.cursor.execute("SELECT key, value FROM basic")
        return {row["key"]: row["value"] for row in self.cursor.fetchall()}


    def is_not_init(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return self.cursor.fetchall() == []


    def _init_basic_data(self):
        data = {
            "current_song" : "",
            "current_playlist" : "",
            "vol" : "80",
            "repeat" : "0",
            "suffle" : "0",
        }

        for key, value in data.items():
            self.cursor.execute(
                """INSERT INTO basic (key, value) VALUES (?, ?) 
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;""", (key, value))
            
        self.conn.commit()

    def _init_playlist(self):
        # add like playlist on start...
        self.add_playlist(
            title="Liked Music",
            subtitle="📌 Auto playlist",
            author="Self",
            count=0,
            duration=0,
            plays=0,
            cover_path="like_song_cover.png",
        )

    def add_playlist(
            self, title: str, subtitle: str, author: str, count: int, 
            duration: int, plays: int, cover_path: str, commit = True
        ) -> int | None:
            
        try:
            self.cursor.execute(
                """INSERT INTO playlist (title, subtitle, author, count, duration, plays, cover_path)
                VALUES (?, ?, ?, ?, ?, ?, ?) """, 
                (title, subtitle, author, count, duration, plays, cover_path)
            )

        except sqlite3.IntegrityError:
            # handle duplicate
            print(f"Playlist with title '{title}' already exists")
            return
        
        if commit:
            self.commit()
        
        return self.get_playlist_id_by_title(title=title)

    
    def get_playlist_id_by_title(self, title: str):
        self.cursor.execute("SELECT id FROM playlist WHERE title=?", (title,))
        row = self.cursor.fetchone()
        if row is None:
            return
        
        return row["id"]

    
    def get_playlist(self, playlist_id: int = None):
        if playlist_id is not None:
              self.cursor.execute("SELECT * FROM playlist WHERE id=?", (playlist_id,))
              return self.cursor.fetchone()
        
        self.cursor.execute("SELECT * FROM playlist")
        return self.cursor.fetchall()
    
    def update_playlist(self, playlist_id: int, **update):
        self._update_column("playlist", playlist_id, **update)

    def remove_playlist_song(self, playlist_id: int, song_id: int, commit = True):
        self.cursor.execute("DELETE FROM playlist_song WHERE p_id = ? AND s_id = ?", (playlist_id, song_id))
        self.conn.commit()

        if self.cursor.rowcount == 0:
            print(f"[From DB] No song in playlist : {playlist_id} with this id : {song_id}")
            return False
        
        else:
            print(f"[From DB] Song deleted from playlist : {playlist_id} with id : {song_id}")
            return True


    def add_playlist_song(self, playlist_id: int, song_id: int, commit = True):
        position = self._get_next_playlist_song_position(playlist_id=playlist_id)
        
        try:
            self.cursor.execute(
                    "INSERT INTO playlist_song (p_id, s_id, position) VALUES (?, ?, ?)", (playlist_id, song_id, position)
                    )
        
        except sqlite3.IntegrityError:
            # handle duplicate
            print(f"Song with id : {song_id} already exists in playlist : {playlist_id}")
            return False
        
        if commit:
            self.commit()

        return True
    
    def _get_next_playlist_song_position(self, playlist_id: int) -> int:
        self.cursor.execute("""
            SELECT COALESCE(MAX(position), -1) + 1
            FROM playlist_song
            WHERE p_id = ?
        """, (playlist_id,))
        return self.cursor.fetchone()[0]

    

    def get_playlist_song(self, playlist_id: int, detailed = False):
        if not detailed:
              self.cursor.execute("SELECT s_id FROM playlist_song WHERE p_id=? ORDER BY position ASC", (playlist_id,))
              return [song['s_id'] for song in self.cursor.fetchall()]
        
        self.cursor.execute("""
            SELECT s.*
            FROM songs s
            JOIN playlist_song ps ON ps.s_id = s.id
            WHERE ps.p_id = ?
            ORDER BY ps.position;
            """, (playlist_id,))
        return self.cursor.fetchall()
    

    def _db_init(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS basic (
                key TEXT PRIMARY KEY,
                value TEXT
        )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                subtitle TEXT,
                author TEXT,
                count INTEGER,
                duration INTEGER,
                plays INTEGER,        
                cover_path TEXT
        )
        """)


        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                subtitle TEXT,
                artist TEXT,
                vid TEXT UNIQUE,
                duration INTEGER,
                plays INTEGER,
                liked INTEGER,
                skip INTEGER,
                path TEXT UNIQUE,  
                cover_path TEXT
        )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlist_song (
                p_id INTEGER,
                s_id INTEGER,
                position INTEGER,
                FOREIGN KEY(p_id) REFERENCES playlist(id),
                FOREIGN KEY(s_id) REFERENCES songs(id),
                UNIQUE(p_id, s_id)
        )
        """)

        self.conn.commit()

    def add_song(self, title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path, commit = True):
        try:
            self.cursor.execute(
                """INSERT INTO songs (title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                (title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path)
            )

        except sqlite3.IntegrityError:
            # handle duplicate
            print(f"Song with path : {path} already exists.")
            return False

        if commit:
            self.commit()

        return True
    
    def increament_play_count(self, song_id: int):
        song_info = self.get_song(song_id=song_id)
        if not song_info:
            print(f"Error[DB] Song not found in the DB")
            return
        play_count = song_info["plays"] + 1
        self.update_song(song_id=song_id, plays = play_count)
        print(f"PlayCount updated : {play_count}")

    
    def get_song_id(self, path: str = None, vid: str = None):
        if path is not None:
            self.cursor.execute("SELECT id FROM songs WHERE path=?", (path,))

        elif vid is not None:
            self.cursor.execute("SELECT id FROM songs WHERE vid=?", (vid,))

        else:
            return 
        
        row = self.cursor.fetchone()
        return row["id"]

                
    def get_song(self, song_id: int = None):
        if song_id is not None:
              self.cursor.execute("SELECT * FROM songs WHERE id=?", (song_id,))
              row = self.cursor.fetchone()
              return row
        

        self.cursor.execute("SELECT * FROM songs ORDER BY id DESC")
        return self.cursor.fetchall()
    
    def get_all_song_id(self):
        self.cursor.execute("SELECT id FROM songs ORDER BY id DESC")
        all_song_id = [song['id'] for song in self.cursor.fetchall()]
        return all_song_id
    
    def get_liked_song_id(self):
        self.cursor.execute("SELECT id FROM songs WHERE liked = 1 ORDER BY id ASC")
        all_song_id = [song['id'] for song in self.cursor.fetchall()]
        return all_song_id
    
    def get_songid_by_vid(self, vid: str):
        self.cursor.execute("SELECT id FROM songs WHERE vid=?", (vid,))
        data = self.cursor.fetchone()
        if data is None:
            return
        
        return data["id"]
    
    def update_song(self, song_id, **update):
        self._update_column("songs", song_id, **update)

    def delete_song(self, song_id: int):
        self.cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        self.conn.commit()

        if self.cursor.rowcount == 0:
            print(f"[From DB] No song found with this id : {song_id}")
        else:
            print(f"[From DB] Song deleted with id : {song_id}")


    def _update_column(self, table: str, column_id: int, **kwargs):
        query = f'UPDATE {table} SET {", ".join(f"{key} = ?" for key in kwargs.keys())} WHERE id = ?'

        values = list(kwargs.values())
        values.append(column_id) # id at last

        self.cursor.execute(query, values)
        self.conn.commit()



if __name__ == "__main__":
    db = DataBase()
    info = db.get_playlist(playlist_id=1)
    print(dict_format(info))

    # update liked playlist
    # count = 0
    # duration = 0

    # song_list = db.get_playlist_song(1, detailed=True)

    # for song in song_list:
    #     count += 1
    #     duration += song['duration']

    # print(f"Count      :  {count}")
    # print(f"Duration   :  {duration}")

    # # --->

    # db.update_playlist(playlist_id=1, count = count, duration = duration)
