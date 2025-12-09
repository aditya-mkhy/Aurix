import sqlite3
from PyQt5.QtCore import QObject

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
    
    
    def add_into_playlist(self, playlist_id, song_id):
        pass


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

    def add_song(self, title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path, commit = False):
        self.cursor.execute(
            """INSERT INTO songs (title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """, 
            (title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path)
        )

        if commit:
            self.commit()

                


if __name__ == "__main__":
    db = DataBase()
    vol = db.get_basic("vol")
    print(f"Volume : {vol}")

    title = "mhadev ji"
    subtitle = "best mahadev seong sing by mukho"
    artist = "aditya mukhiya"
    vid = "none"
    duration = 2345
    plays = 45
    liked = 1
    skip = 5

    path = "C:\\Users\\freya\\Music\\Bhala.mp3"
    cover_path = ""

    db.add_song(title, subtitle, artist, vid, duration, plays, liked, skip, path, cover_path, commit=True)

