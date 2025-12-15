import sqlite3
from typing import List, Dict
from util import DATABASE_PATH, dict_format


class DataBase():
    def __init__(self):

        self.conn = sqlite3.connect(DATABASE_PATH)
        
        # row_factory to get dict-like rows
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        if self.is_not_init():
            print(f"Initializing DataBase")
            self._db_init()
            self._init_basic_data()

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
            "current_song" : "none",
            "current_playlist" : "none",
            "vol" : "80",
            "repeat" : "0",
            "suffle" : "0",
        }

        for key, value in data.items():
            self.cursor.execute(
                """INSERT INTO basic (key, value) VALUES (?, ?) 
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;""", (key, value))
            
        self.conn.commit()

    def add_playlist(
            self, title: str, subtitle: str, author: str, count: int, 
            duration: int, plays: int, cover_path: str, commit = True
        ):
            
        try:
            self.cursor.execute(
                """INSERT INTO playlist (title, subtitle, author, count, duration, plays, cover_path)
                VALUES (?, ?, ?, ?, ?, ?, ?) """, 
                (title, subtitle, author, count, duration, plays, cover_path)
            )

        except sqlite3.IntegrityError:
            # handle duplicate
            print(f"Playlist with title '{title}' already exists")
            return False
        
        if commit:
            self.commit()

        return True
    
    def get_playlist(self, playlist_id: int = None):
        if playlist_id is not None:
              self.cursor.execute("SELECT * FROM playlist WHERE id=?", (playlist_id,))
              return self.cursor.fetchone()
        
        self.cursor.execute("SELECT * FROM playlist")
        return self.cursor.fetchall()
    
    def update_playlist(self, playlist_id: int, **update):
        self._update_column("playlist", playlist_id, **update)

    def add_playlist_song(self, playlist_id: int, song_id: int, commit = True):
        try:
            self.cursor.execute(
                    "INSERT INTO playlist_song (p_id, s_id) VALUES (?, ?)", (playlist_id, song_id)
                    )
        
        except sqlite3.IntegrityError:
            # handle duplicate
            print(f"Song with id : {song_id} already exists in playlist : {playlist_id}")
            return False
        
        if commit:
            self.commit()

        return True
    

    def get_playlist_song(self, playlist_id: int):
        if playlist_id is not None:
              self.cursor.execute("SELECT s_id FROM playlist_song WHERE p_id=?", (playlist_id,))
              return self.cursor.fetchall()
        
        self.cursor.execute("SELECT * FROM playlist_song")
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
    # db.delete_song(song_id=40)

    print(db.get_songid_by_vid(vid="hgQInx5xH5E"))

    for song in dict_format(db.get_song()):
        print(song)
        print()
