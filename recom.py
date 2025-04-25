import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import os
import random
from pygame import mixer
import io

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

def get_user_listening_history(limit=5):
    """Get songs the user has listened to recently"""
    try:
        # Get current user ID
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
            
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT s.song_id, s.title, a.name as artist_name, g.genre_id, g.name as genre_name,
               COUNT(lh.history_id) as play_count
        FROM Listening_History lh
        JOIN Songs s ON lh.song_id = s.song_id
        JOIN Artists a ON s.artist_id = a.artist_id
        LEFT JOIN Genres g ON s.genre_id = g.genre_id
        WHERE lh.user_id = %s
        GROUP BY s.song_id
        ORDER BY lh.played_at DESC
        LIMIT %s
        """
        
        cursor.execute(query, (user_id, limit))
        history = cursor.fetchall()
        
        return history
        
    except Exception as e:
        print(f"Error getting listening history: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_favorite_genres():
    """Get user's favorite genres based on listening history"""
    try:
        # Get current user ID
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
            
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT g.genre_id, g.name as genre_name, COUNT(lh.history_id) as count
        FROM Listening_History lh
        JOIN Songs s ON lh.song_id = s.song_id
        JOIN Genres g ON s.genre_id = g.genre_id
        WHERE lh.user_id = %s AND g.genre_id IS NOT NULL
        GROUP BY g.genre_id
        ORDER BY count DESC
        LIMIT 3
        """
        
        cursor.execute(query, (user_id,))
        genres = cursor.fetchall()
        
        return genres
        
    except Exception as e:
        print(f"Error getting favorite genres: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_favorite_artists():
    """Get user's favorite artists based on listening history"""
    try:
        # Get current user ID
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
            
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT a.artist_id, a.name as artist_name, COUNT(lh.history_id) as count
        FROM Listening_History lh
        JOIN Songs s ON lh.song_id = s.song_id
        JOIN Artists a ON s.artist_id = a.artist_id
        WHERE lh.user_id = %s
        GROUP BY a.artist_id
        ORDER BY count DESC
        LIMIT 3
        """
        
        cursor.execute(query, (user_id,))
        artists = cursor.fetchall()
        
        return artists
        
    except Exception as e:
        print(f"Error getting favorite artists: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_recommended_songs(limit=8):
    """Get songs recommended based on user's listening history"""
    try:
        # Get current user ID
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
        
        # Get favorite genres and artists
        favorite_genres = get_favorite_genres()
        favorite_artists = get_favorite_artists()
        
        # No history yet, return random songs
        if not favorite_genres and not favorite_artists:
            return get_random_songs(limit)
            
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        # Get songs the user has already listened to
        cursor.execute(
            "SELECT song_id FROM Listening_History WHERE user_id = %s",
            (user_id,)
        )
        listened_songs = [row['song_id'] for row in cursor.fetchall()]
        
        # Build genre filter
        genre_filter = ""
        genre_params = []
        if favorite_genres:
            genre_ids = [g['genre_id'] for g in favorite_genres]
            placeholders = ", ".join(["%s"] * len(genre_ids))
            genre_filter = f"OR s.genre_id IN ({placeholders})"
            genre_params = genre_ids
        
        # Build artist filter
        artist_filter = ""
        artist_params = []
        if favorite_artists:
            artist_ids = [a['artist_id'] for a in favorite_artists]
            placeholders = ", ".join(["%s"] * len(artist_ids))
            artist_filter = f"OR s.artist_id IN ({placeholders})"
            artist_params = artist_ids
        
        # Exclude songs the user has already heard
        exclusion_filter = ""
        exclusion_params = []
        if listened_songs:
            placeholders = ", ".join(["%s"] * len(listened_songs))
            exclusion_filter = f"AND s.song_id NOT IN ({placeholders})"
            exclusion_params = listened_songs
        
        # If user hasn't listened to any songs, don't use the exclusion filter
        if not listened_songs:
            exclusion_filter = ""
            exclusion_params = []
        
        # Query for recommendations based on genres and artists
        query = f"""
        SELECT s.song_id, s.title, a.name as artist_name, g.name as genre_name
        FROM Songs s
        JOIN Artists a ON s.artist_id = a.artist_id
        LEFT JOIN Genres g ON s.genre_id = g.genre_id
        WHERE 1=0 {genre_filter} {artist_filter} {exclusion_filter}
        ORDER BY RAND()
        LIMIT %s
        """
        
        all_params = genre_params + artist_params + exclusion_params + [limit]
        cursor.execute(query, all_params)
        recommendations = cursor.fetchall()
        
        # If we don't have enough recommendations, fill with random songs
        if len(recommendations) < limit:
            remaining = limit - len(recommendations)
            
            # Get IDs of already recommended songs
            recommended_ids = [song['song_id'] for song in recommendations]
            
            # Add listened songs to the exclusion list
            excluded_songs = recommended_ids + listened_songs if listened_songs else recommended_ids
            
            # Get random songs excluding those already recommended or listened to
            random_songs = get_random_songs(remaining, excluded_songs)
            
            # Combine recommendations
            recommendations.extend(random_songs)
        
        return recommendations
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return get_random_songs(limit)  # Fallback to random songs
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_random_songs(limit=8, exclude_ids=None):
    """Get random songs from the database"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        # Exclude songs if specified
        exclusion_filter = ""
        params = []
        
        if exclude_ids and len(exclude_ids) > 0:
            placeholders = ", ".join(["%s"] * len(exclude_ids))
            exclusion_filter = f"WHERE s.song_id NOT IN ({placeholders})"
            params = exclude_ids
        
        query = f"""
        SELECT s.song_id, s.title, a.name as artist_name, g.name as genre_name
        FROM Songs s
        JOIN Artists a ON s.artist_id = a.artist_id
        LEFT JOIN Genres g ON s.genre_id = g.genre_id
        {exclusion_filter}
        ORDER BY RAND()
        LIMIT %s
        """
        
        params.append(limit)
        cursor.execute(query, params)
        songs = cursor.fetchall()
        
        # If no songs in database yet, return dummy data
        if not songs:
            songs = [
                {"song_id": 1, "title": "Blinding Lights", "artist_name": "The Weeknd", "genre_name": "Pop"},
                {"song_id": 2, "title": "Levitating", "artist_name": "Dua Lipa", "genre_name": "Pop"},
                {"song_id": 3, "title": "Believer", "artist_name": "Imagine Dragons", "genre_name": "Rock"},
                {"song_id": 4, "title": "Shape of You", "artist_name": "Ed Sheeran", "genre_name": "Pop"}
            ]
            # Shuffle and limit
            random.shuffle(songs)
            songs = songs[:limit]
        
        return songs
        
    except Exception as e:
        print(f"Error getting random songs: {e}")
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

def open_search_page():
    """Open the search page"""
    try:
        subprocess.Popen(["python", "search.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open search page: {e}")

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

def refresh_recommendations():
    """Refresh the recommendations display"""
    # Clear previous recommendations
    for widget in songs_frame.winfo_children():
        if widget != title_label and widget != subtitle_label:
            widget.destroy()
    
    # Get new recommendations
    display_recommendations()
    
    # Show success message
    messagebox.showinfo("Refreshed", "Recommendations have been updated!")

def display_recommendations():
    """Display recommended songs in the UI"""
    # Get recommended songs
    recommended_songs = get_recommended_songs(8)
    
    # Display songs
    for song in recommended_songs:
        # Create song row
        song_frame = ctk.CTkFrame(songs_frame, fg_color="#1A1A2E", corner_radius=10, height=50)
        song_frame.pack(fill="x", pady=5, ipady=5)
        
        # Make sure the frame stays at desired height
        song_frame.pack_propagate(False)
        
        # Get display text with icon
        song_icon = "🎵"
        display_text = f"{song_icon} {song['artist_name']} - {song['title']}"
        if song.get('genre_name'):
            display_text += f" ({song['genre_name']})"
        
        # Song label with icon
        song_label = ctk.CTkLabel(song_frame, text=display_text, font=("Arial", 14), text_color="white")
        song_label.pack(side="left", padx=20)
        
        # Play button
        play_btn = ctk.CTkButton(song_frame, text="▶️ Play", font=("Arial", 12), 
                               fg_color="#B146EC", hover_color="#9333EA", 
                               width=80, height=30,
                               command=lambda sid=song["song_id"]: play_song(sid))
        play_btn.pack(side="right", padx=20)
        
        # Make frame clickable
        song_frame.bind("<Button-1>", lambda e, sid=song["song_id"]: play_song(sid))
        song_label.bind("<Button-1>", lambda e, sid=song["song_id"]: play_song(sid))

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
    root.title("Online Music System - Recommended Songs")
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
                            fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                            anchor="w", corner_radius=0, height=40, command=open_search_page)
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
                                fg_color="#111827", hover_color="#1E293B", text_color="white",
                                anchor="w", corner_radius=0, height=40)
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

    # Left side: Recommended Songs
    recommend_label = ctk.CTkLabel(header_frame, text="Recommended Songs", font=("Arial", 24, "bold"), text_color="white")
    recommend_label.pack(side="left")

    # Right side: Username - updated with actual user name
    user_label = ctk.CTkLabel(header_frame, 
                            text=f"Hello, {user['first_name']} {user['last_name']}!", 
                            font=("Arial", 14), text_color="#A0A0A0")
    user_label.pack(side="right")

    # ---------------- Songs You Might Like ----------------
    songs_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    songs_frame.pack(fill="both", expand=True, padx=20, pady=(40, 0))

    # Section title - centered
    title_label = ctk.CTkLabel(songs_frame, text="Songs You Might Like 🎵", 
                              font=("Arial", 24, "bold"), text_color="#B146EC")
    title_label.pack(pady=(0, 5))

    # Subtitle - centered with personalized text
    subtitle_text = "Discover music based on your listening history." 
    if not get_user_listening_history():
        subtitle_text = "Start listening to songs to get personalized recommendations."
        
    subtitle_label = ctk.CTkLabel(songs_frame, text=subtitle_text, 
                                 font=("Arial", 14), text_color="#A0A0A0")
    subtitle_label.pack(pady=(0, 20))

    # Display recommendations
    display_recommendations()

    # Refresh button at the bottom
    button_frame = ctk.CTkFrame(songs_frame, fg_color="#131B2E")
    button_frame.pack(pady=25)

    refresh_button = ctk.CTkButton(button_frame, text="⟳ Refresh", font=("Arial", 14, "bold"), 
                                  fg_color="#B146EC", hover_color="#9333EA", 
                                  corner_radius=5, height=40, width=140,
                                  command=refresh_recommendations)
    refresh_button.pack()

    # ---------------- Run Application ----------------
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"Error in recommend.py: {e}")
    traceback.print_exc()
    messagebox.showerror("Error", f"An error occurred: {e}")
    input("Press Enter to exit...")  # This keeps console open