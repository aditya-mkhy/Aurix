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
            CREATE TABLE IF NOT EXISTS playlist_song (
                p_id INTEGER,
                s_id INTEGER
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

        self.conn.commit()

    def add_song(self, title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path, commit = True):
        self.cursor.execute(
            """INSERT INTO songs (title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """, 
            (title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path)
        )

        if commit:
            self.commit()

                
    def get_song(self, song_id: int = None):
        if song_id is not None:
              self.cursor.execute("SELECT * FROM songs WHERE id=?", (song_id,))
              row = self.cursor.fetchone()
              return row
        

        self.cursor.execute("SELECT * FROM songs")
        return self.cursor.fetchall()
    
    def update_song(self, song_id, **kwargs):
        self._update_column("songs", song_id, **kwargs)

    def update_plalist(self, ):
        pass

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
    # vol = db.get_basic("vol")
    # print(f"Volume : {vol}")

    title = "Danny"
    subtitle = "best mahadev seong sing by mukho"
    artist = "aditya mukhiya"
    vid = "none"
    duration = 565
    plays = 10
    liked = 10
    skip = 500

    path = "C:\\Users\\freya\\Music\\Ve Haaniyaan.mp3"
    cover_path = ""

    # # db.add_song(title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path, commit=True)
    # songs = db.get_song(song_id=1)
    # print(db.dict_format(songs))

    # print("-------update----------------")
    # db.update_song(1, title="Love you Plaku", subtitle = "i want you", cover_path = "plak.jpg")

    # songs = db.get_song(song_id=1)
    # print(db.dict_format(songs))

    db.add_playlist("fav songs", "All favroute song aere there", "Aditya Mukhiya", 400, 500, 2, "fav.png")

