# AURIX – Music Player

Aurix is a modern desktop music player inspired by Spotify & YouTube Music,
built using PyQt5 and pygame mixer.
&nbsp; &nbsp; &nbsp; 


### UI Preview
<img width="1919" height="1019" alt="Screenshot 2025-12-07 032834" src="https://github.com/user-attachments/assets/665ab749-6fc9-4165-b18a-72ef6771fac9" />
&nbsp; &nbsp; &nbsp; 

<img width="1516" height="921" alt="image" src="https://github.com/user-attachments/assets/8fedc0a8-38f8-4c2c-9200-b4511dce2f9d" />
&nbsp; &nbsp; &nbsp; 


&nbsp; &nbsp; &nbsp; 

## 🚀 Current Highlights

### 🎨 Modern UI / UX
- Spotify-inspired **dark theme**
- Clean layouts with responsive resizing
- Context-style popup dialogs
- Hover-based interactions (play buttons, overlays)
- Smooth visual hierarchy (no clutter)

### 📀 Playlist System
- Create and manage playlists
- Dedicated **PlaylistPlayerWindow**
  - Left panel: playlist details & artwork
  - Right panel: track list with hover play actions
- Playlist order stored and managed at database level
- One reusable player window — dynamic data loading

### 🎵 Track Handling
- Local music playback
- Per-track metadata (title, artist, duration, cover)
- Human-readable duration formatting
- Centralized playback state (UI reacts to data)

### 🗃 Database-Driven Architecture
- SQLite database
- Proper relational schema:
  - `songs`
  - `playlist`
  - `playlist_song` (many-to-many with position)
- Playlist ordering handled via `position`
- Clean separation between **data**, **logic**, and **UI**

---

## Technologies Used

| Feature | Technology |
|--------|------------|
| UI Framework | PyQt5 |
| Audio Engine | pygame.mixer |
| Metadata | Mutagen |
| Web Search & Download | YouTube Music backend |
| Image Processing | QPixmap + custom trimming |
&nbsp; &nbsp; &nbsp; 


## License

Aurix is an open-source project.  
Free to use, modify, and experiment with.
&nbsp; &nbsp; &nbsp; 

## Credits

**Made with ❤️, Python, and late-night coding.**


