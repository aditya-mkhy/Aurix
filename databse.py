import sqlite3
from PyQt5.QtCore import QObject
from typing import List, Dict




class DataBase():
    def __init__(self):
        self.file_name = "./res/aurix.db"
        self.conn = sqlite3.connect(self.file_name)

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
                vid TEXT,
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

                
    def get_song(self, song_id: int = None):
        if song_id is not None:
              self.cursor.execute("SELECT * FROM songs WHERE id=?", (song_id,))
              row = self.cursor.fetchone()
              return row
        

        self.cursor.execute("SELECT * FROM songs")
        return self.cursor.fetchall()
    
    def update_song(self, song_id, **update):
        self._update_column("songs", song_id, **update)


    def _update_column(self, table: str, column_id: int, **kwargs):
        query = f'UPDATE {table} SET {", ".join(f"{key} = ?" for key in kwargs.keys())} WHERE id = ?'

        values = list(kwargs.values())
        values.append(column_id) # id at last

        self.cursor.execute(query, values)
        self.conn.commit()

    
    def dict_format(self, items: List[Dict]):
        if not isinstance(items, list):
            return dict(items)
        return [dict(row) for row in items]


if __name__ == "__main__":
    db = DataBase()
    basic = db.get_basic()
    print(basic)


    # db.add_song("Tu har lamha", "Bobby-Imran Topic", "aditya", "", 400, 1, 1, 34, "tuhar.mp3", "none")
    # db.add_song("Ve haaniyaan", "Palak & Adi", "aditya", "", 200, 1, 1, 3, "vehniya.mp3", "tuhar.mp3")
    # songs = db.get_song(song_id=1)
    # print(db.dict_format(songs))

    # print("-------update----------------")
    # db.update_song(1, title="Love you Plaku", subtitle = "i want you", cover_path = "plak.jpg")

    # songs = db.get_song(song_id=1)
    # print(db.dict_format(songs))

    # db.add_playlist("eng songs", "best eng song", "Aditya Mukhiya", 100, 20, 0, "aditya.png")

    # playlists = db.get_playlist(playlist_id=1)
    # print(db.dict_format(playlists))

    # db.add_playlist_song(1, 20)

    # pl_songs = db.get_playlist_song(1)
    # print(db.dict_format(pl_songs))

    # db.update_playlist(1, title = "Fav Song", subtitle= "My fav song")