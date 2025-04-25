import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import os
import io
from pygame import mixer
import threading
import time

# Initialize mixer for music playback
mixer.init()

# Current song information
current_song = {
    "id": None,
    "title": "No song playing",
    "artist": "",
    "playing": False,
    "paused": False
}

# ------------------- Database Functions -------------------
def connect_db():
    """Connect to the MySQL database"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="new_password",
            database="online_music_system"
        )
        return connection
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection Error", 
                            f"Failed to connect to database: {err}")
        return None

def get_current_user():
    """Get the current logged-in user information"""
    try:
        # Read user ID from file
        if not os.path.exists("current_user.txt"):
            messagebox.showerror("Error", "You are not logged in!")
            open_login_page()
            return None
            
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
            
        if not user_id:
            messagebox.showerror("Error", "User ID not found!")
            open_login_page()
            return None
            
        connection = connect_db()
        if not connection:
            return None
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, first_name, last_name, email FROM Users WHERE user_id = %s",
            (user_id,)
        )
        
        user = cursor.fetchone()
        return user
        
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def search_songs(query, search_type="all"):
    """Search for songs in the database"""
    try:
        if not query:
            return []
            
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        search_param = f"%{query}%"
        
        # Different queries based on search type
        if search_type == "song":
            query = """
            SELECT s.song_id, s.title, a.name as artist_name, al.title as album_name, 
                   g.name as genre, s.duration
            FROM Songs s
            JOIN Artists a ON s.artist_id = a.artist_id
            LEFT JOIN Albums al ON s.album_id = al.album_id
            LEFT JOIN Genres g ON s.genre_id = g.genre_id
            WHERE s.title LIKE %s
            ORDER BY s.title
            """
            cursor.execute(query, (search_param,))
        
        elif search_type == "artist":
            query = """
            SELECT s.song_id, s.title, a.name as artist_name, al.title as album_name, 
                   g.name as genre, s.duration
            FROM Songs s
            JOIN Artists a ON s.artist_id = a.artist_id
            LEFT JOIN Albums al ON s.album_id = al.album_id
            LEFT JOIN Genres g ON s.genre_id = g.genre_id
            WHERE a.name LIKE %s
            ORDER BY s.title
            """
            cursor.execute(query, (search_param,))
            
        elif search_type == "album":
            query = """
            SELECT s.song_id, s.title, a.name as artist_name, al.title as album_name, 
                   g.name as genre, s.duration
            FROM Songs s
            JOIN Artists a ON s.artist_id = a.artist_id
            LEFT JOIN Albums al ON s.album_id = al.album_id
            LEFT JOIN Genres g ON s.genre_id = g.genre_id
            WHERE al.title LIKE %s
            ORDER BY s.title
            """
            cursor.execute(query, (search_param,))
            
        else:  # "all" - search everything
            query = """
            SELECT s.song_id, s.title, a.name as artist_name, al.title as album_name, 
                   g.name as genre, s.duration
            FROM Songs s
            JOIN Artists a ON s.artist_id = a.artist_id
            LEFT JOIN Albums al ON s.album_id = al.album_id
            LEFT JOIN Genres g ON s.genre_id = g.genre_id
            WHERE s.title LIKE %s OR a.name LIKE %s OR al.title LIKE %s
            ORDER BY s.title
            """
            cursor.execute(query, (search_param, search_param, search_param))
        
        songs = cursor.fetchall()
        
        # Format durations to MM:SS
        for song in songs:
            minutes, seconds = divmod(song['duration'] or 0, 60)  # Handle None values
            song['duration_formatted'] = f"{minutes}:{seconds:02d}"
        
        return songs
        
    except mysql.connector.Error as e:
        print(f"Error searching songs: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_recent_songs(limit=6):
    """Get recently added songs"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT s.song_id, s.title, a.name as artist_name 
        FROM Songs s
        JOIN Artists a ON s.artist_id = a.artist_id
        ORDER BY s.upload_date DESC
        LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        songs = cursor.fetchall()
        
        return songs
        
    except mysql.connector.Error as e:
        print(f"Error fetching recent songs: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_song_data(song_id):
    """Get binary song data from database"""
    try:
        connection = connect_db()
        if not connection:
            return None
            
        cursor = connection.cursor()
        
        query = "SELECT file_data, file_type FROM Songs WHERE song_id = %s"
        cursor.execute(query, (song_id,))
        
        result = cursor.fetchone()
        if result:
            return {'data': result[0], 'type': result[1]}
        return None
        
    except mysql.connector.Error as e:
        print(f"Error getting song data: {e}")
        return None
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def record_listening_history(song_id):
    """Record that the current user listened to a song"""
    try:
        # Get current user ID
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
            
        connection = connect_db()
        if not connection:
            return
            
        cursor = connection.cursor()
        
        query = "INSERT INTO Listening_History (user_id, song_id) VALUES (%s, %s)"
        cursor.execute(query, (user_id, song_id))
        connection.commit()
        
    except Exception as e:
        print(f"Error recording listening history: {e}")
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Music Player Functions -------------------
def play_song(song_id):
    """Play a song from its binary data in the database"""
    global current_song
    
    try:
        # Get song data from database
        song_data = get_song_data(song_id)
        if not song_data:
            messagebox.showerror("Error", "Could not retrieve song data")
            return False
            
        # Get additional song info for display
        connection = connect_db()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT s.title, a.name as artist_name FROM Songs s JOIN Artists a ON s.artist_id = a.artist_id WHERE s.song_id = %s",
                (song_id,)
            )
            song_info = cursor.fetchone()
            cursor.close()
            connection.close()
        else:
            song_info = {"title": "Unknown", "artist_name": "Unknown"}
            
        # Create a temporary file to play the song
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file = os.path.join(temp_dir, f"song_{song_id}.{song_data['type']}")
        
        # Write binary data to temp file
        with open(temp_file, 'wb') as f:
            f.write(song_data['data'])
            
        # Load and play the song
        mixer.music.load(temp_file)
        mixer.music.play()
        
        # Update current song info
        current_song = {
            "id": song_id,
            "title": song_info["title"],
            "artist": song_info["artist_name"],
            "playing": True,
            "paused": False
        }
        
        # Update UI elements
        if 'now_playing_label' in globals():
            now_playing_label.configure(text=f"Now Playing: {current_song['title']} - {current_song['artist']}")
        
        if 'play_btn' in globals():
            play_btn.configure(text="⏸️")
        
        # Record in listening history
        record_listening_history(song_id)
        
        return True
        
    except Exception as e:
        print(f"Error playing song: {e}")
        messagebox.showerror("Error", f"Could not play song: {e}")
        return False

def toggle_play_pause():
    """Toggle between play and pause states"""
    global current_song
    
    if current_song["id"] is None:
        # No song loaded - do nothing
        return
    elif current_song["paused"]:
        # Resume paused song
        mixer.music.unpause()
        current_song["paused"] = False
        current_song["playing"] = True
        play_btn.configure(text="⏸️")
    elif current_song["playing"]:
        # Pause playing song
        mixer.music.pause()
        current_song["paused"] = True
        current_song["playing"] = False
        play_btn.configure(text="▶️")

def play_next_song():
    """Placeholder for playing next song"""
    messagebox.showinfo("Info", "Next song feature will be implemented with playlists")

def play_previous_song():
    """Placeholder for playing previous song"""
    messagebox.showinfo("Info", "Previous song feature will be implemented with playlists")

# ------------------- Navigation Functions -------------------
def open_home_page():
    """Open the home page"""
    try:
        subprocess.Popen(["python", "home.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open home page: {e}")

def open_playlist_page():
    """Open the playlist page"""
    try:
        subprocess.Popen(["python", "playlist.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open playlist page: {e}")

def open_download_page():
    """Open the download page"""
    try:
        subprocess.Popen(["python", "download.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open download page: {e}")

def open_recommend_page():
    """Open the recommendations page"""
    try:
        subprocess.Popen(["python", "recommend.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open recommendations page: {e}")

def open_login_page():
    """Logout and open the login page"""
    try:
        # Stop any playing music
        if mixer.music.get_busy():
            mixer.music.stop()
            
        # Remove current user file
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
            
        subprocess.Popen(["python", "login.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to logout: {e}")

def perform_search(event=None):
    """Search for songs and update the search results"""
    # Clear previous search results
    for widget in songs_section.winfo_children():
        if widget != songs_title:  # Keep the section title
            widget.destroy()
    
    # Get search query
    query = search_entry.get()
    
    if not query:
        # If no query, just show recent songs
        display_songs(get_recent_songs(), "Recent Songs")
        return
    
    # Perform the search
    search_results = search_songs(query)
    
    # Display results
    if search_results:
        display_songs(search_results, f"Search Results for '{query}'")
    else:
        no_results_label = ctk.CTkLabel(
            songs_section, 
            text=f"No songs found for '{query}'", 
            font=("Arial", 14),
            text_color="#A0A0A0"
        )
        no_results_label.pack(pady=20)

def display_songs(songs, section_subtitle=None):
    """Display songs in the search results section"""
    # Update section subtitle if provided
    if section_subtitle:
        songs_title.configure(text=f"🔍 {section_subtitle}")
    
    if not songs:
        no_songs_label = ctk.CTkLabel(
            songs_section, 
            text="No songs available", 
            font=("Arial", 14),
            text_color="#A0A0A0"
        )
        no_songs_label.pack(pady=20)
        return
    
    # Create song rows
    for song in songs:
        # Create a frame for each song row
        song_frame = ctk.CTkFrame(songs_section, fg_color="#1A1A2E", corner_radius=10, height=50)
        song_frame.pack(fill="x", pady=5)
        
        # Format the song display text
        if "album_name" in song and song["album_name"]:
            display_text = f"🎵 {song['artist_name']} - {song['title']} ({song['album_name']})"
        else:
            display_text = f"🎵 {song['artist_name']} - {song['title']}"
        
        # Add duration if available
        if "duration_formatted" in song:
            display_text += f" ({song['duration_formatted']})"
        
        # Song name and info
        song_label = ctk.CTkLabel(
            song_frame, 
            text=display_text, 
            font=("Arial", 14), 
            text_color="white",
            anchor="w"
        )
        song_label.pack(side="left", padx=15, fill="y")
        
        # Play button
        play_icon = ctk.CTkLabel(
            song_frame, 
            text="▶️", 
            font=("Arial", 16), 
            text_color="#22C55E"
        )
        play_icon.pack(side="right", padx=15)
        
        # Add play song command
        song_id = song["song_id"]
        
        # Make the whole row clickable
        song_frame.bind("<Button-1>", lambda e, sid=song_id: play_song(sid))
        song_label.bind("<Button-1>", lambda e, sid=song_id: play_song(sid))
        play_icon.bind("<Button-1>", lambda e, sid=song_id: play_song(sid))

# ------------------- Initialize App -------------------
try:
    # Get current user info
    user = get_current_user()
    if not user:
        # Redirect to login if not logged in
        open_login_page()
        exit()

    # ---------------- Initialize App ----------------
    ctk.set_appearance_mode("dark")  # Dark mode
    ctk.set_default_color_theme("blue")  # Default theme

    root = ctk.CTk()
    root.title("Online Music System - Search Songs")
    root.geometry("1000x600")  # Adjusted to match the image proportions
    root.resizable(False, False)

    # ---------------- Main Frame ----------------
    main_frame = ctk.CTkFrame(root, fg_color="#1E1E2E", corner_radius=15)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------------- Sidebar Navigation ----------------
    sidebar = ctk.CTkFrame(main_frame, width=250, height=580, fg_color="#111827", corner_radius=10)
    sidebar.pack(side="left", fill="y", padx=(10, 0), pady=10)

    # Sidebar Title
    title_label = ctk.CTkLabel(sidebar, text="Online Music\nSystem", font=("Arial", 20, "bold"), text_color="white")
    title_label.pack(pady=(25, 30))

    # Sidebar Menu Items with navigation commands
    home_btn = ctk.CTkButton(sidebar, text="🏠 Home", font=("Arial", 14), 
                          fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                          anchor="w", corner_radius=0, height=40, command=open_home_page)
    home_btn.pack(fill="x", pady=5, padx=10)

    search_btn = ctk.CTkButton(sidebar, text="🔍 Search", font=("Arial", 14), 
                            fg_color="#111827", hover_color="#1E293B", text_color="white",
                            anchor="w", corner_radius=0, height=40)
    search_btn.pack(fill="x", pady=5, padx=10)

    playlist_btn = ctk.CTkButton(sidebar, text="🎵 Playlist", font=("Arial", 14), 
                              fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                              anchor="w", corner_radius=0, height=40, command=open_playlist_page)
    playlist_btn.pack(fill="x", pady=5, padx=10)

    download_btn = ctk.CTkButton(sidebar, text="⬇️ Download", font=("Arial", 14), 
                              fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                              anchor="w", corner_radius=0, height=40, command=open_download_page)
    download_btn.pack(fill="x", pady=5, padx=10)

    recommend_btn = ctk.CTkButton(sidebar, text="🎧 Recommend Songs", font=("Arial", 14), 
                                fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                                anchor="w", corner_radius=0, height=40, command=open_recommend_page)
    recommend_btn.pack(fill="x", pady=5, padx=10)

    logout_btn = ctk.CTkButton(sidebar, text="🚪 Logout", font=("Arial", 14), 
                             fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                             anchor="w", corner_radius=0, height=40, command=open_login_page)
    logout_btn.pack(fill="x", pady=5, padx=10)

    # Now playing label
    now_playing_frame = ctk.CTkFrame(sidebar, fg_color="#111827", height=40)
    now_playing_frame.pack(side="bottom", fill="x", pady=(0, 10), padx=10)
    
    now_playing_label = ctk.CTkLabel(now_playing_frame, 
                                   text="Now Playing: No song playing", 
                                   font=("Arial", 12), 
                                   text_color="#A0A0A0",
                                   wraplength=220)
    now_playing_label.pack(pady=5)

    # Music player controls at bottom of sidebar
    player_frame = ctk.CTkFrame(sidebar, fg_color="#111827", height=50)
    player_frame.pack(side="bottom", fill="x", pady=10, padx=10)

    # Control buttons with functionality
    prev_btn = ctk.CTkButton(player_frame, text="⏮️", font=("Arial", 18), 
                            fg_color="#111827", hover_color="#1E293B", 
                            width=40, height=40, command=play_previous_song)
    prev_btn.pack(side="left", padx=10)

    play_btn = ctk.CTkButton(player_frame, text="▶️", font=("Arial", 18), 
                           fg_color="#111827", hover_color="#1E293B", 
                           width=40, height=40, command=toggle_play_pause)
    play_btn.pack(side="left", padx=10)

    next_btn = ctk.CTkButton(player_frame, text="⏭️", font=("Arial", 18), 
                           fg_color="#111827", hover_color="#1E293B", 
                           width=40, height=40, command=play_next_song)
    next_btn.pack(side="left", padx=10)

    # ---------------- Main Content ----------------
    content_frame = ctk.CTkFrame(main_frame, fg_color="#131B2E", corner_radius=10)
    content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # Header with username
    header_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=40)
    header_frame.pack(fill="x", padx=20, pady=(20, 0))

    # Left side: Search Songs
    search_label = ctk.CTkLabel(header_frame, text="Search Songs", font=("Arial", 24, "bold"), text_color="white")
    search_label.pack(side="left")

    # Right side: Username - updated with actual user name
    user_label = ctk.CTkLabel(header_frame, 
                           text=f"Hello, {user['first_name']} {user['last_name']}!", 
                           font=("Arial", 14), text_color="#A0A0A0")
    user_label.pack(side="right")

    # ---------------- Search Bar ----------------
    search_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    search_frame.pack(fill="x", padx=20, pady=(30, 20))

    # Search type selection
    search_type_frame = ctk.CTkFrame(search_frame, fg_color="#131B2E")
    search_type_frame.pack(fill="x", pady=(0, 10))
    
    search_type_var = ctk.StringVar(value="all")
    
    # Search type options
    search_all_radio = ctk.CTkRadioButton(
        search_type_frame, 
        text="All", 
        variable=search_type_var, 
        value="all",
        fg_color="#B146EC",
        text_color="#A0A0A0"
    )
    search_all_radio.pack(side="left", padx=(0, 20))
    
    search_songs_radio = ctk.CTkRadioButton(
        search_type_frame, 
        text="Songs", 
        variable=search_type_var, 
        value="song",
        fg_color="#B146EC",
        text_color="#A0A0A0"
    )
    search_songs_radio.pack(side="left", padx=(0, 20))
    
    search_artists_radio = ctk.CTkRadioButton(
        search_type_frame, 
        text="Artists", 
        variable=search_type_var, 
        value="artist",
        fg_color="#B146EC",
        text_color="#A0A0A0"
    )
    search_artists_radio.pack(side="left", padx=(0, 20))
    
    search_albums_radio = ctk.CTkRadioButton(
        search_type_frame, 
        text="Albums", 
        variable=search_type_var, 
        value="album",
        fg_color="#B146EC",
        text_color="#A0A0A0"
    )
    search_albums_radio.pack(side="left")

    # Search entry with rounded corners
    search_entry = ctk.CTkEntry(search_frame, 
                              placeholder_text="Search for songs, artists, or albums...",
                              font=("Arial", 14), text_color="#FFFFFF",
                              fg_color="#1A1A2E", border_color="#2A2A4E", 
                              height=45, corner_radius=10)
    search_entry.pack(side="left", fill="x", expand=True)
    
    # Bind Enter key to search
    search_entry.bind("<Return>", perform_search)
    
    # Search button
    search_button = ctk.CTkButton(
        search_frame, 
        text="Search", 
        font=("Arial", 14, "bold"),
        fg_color="#B146EC", 
        hover_color="#9333EA", 
        corner_radius=10,
        command=perform_search,
        height=45,
        width=100
    )
    search_button.pack(side="right", padx=(10, 0))

    # ---------------- Songs Section ----------------
    songs_section = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    songs_section.pack(fill="both", expand=True, padx=20, pady=10)

    # Section title
    songs_title = ctk.CTkLabel(songs_section, text="Recent Songs 🎵", 
                             font=("Arial", 20, "bold"), text_color="#B146EC")
    songs_title.pack(anchor="w", pady=(0, 15))

    # Show recent songs on initial load
    display_songs(get_recent_songs(), "Recent Songs")

    # ---------------- Run Application ----------------
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"Error in search.py: {e}")
    traceback.print_exc()
    messagebox.showerror("Error", f"An error occurred: {e}")
    input("Press Enter to exit...")  # This keeps console open