import customtkinter as ctk
from tkinter import messagebox, simpledialog
import mysql.connector
import subprocess
import os
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

def get_system_playlists():
    """Get featured/system playlists from the database"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        # Get playlists where user_id is NULL (system playlists)
        # or with most songs for featured playlists
        query = """
        SELECT p.playlist_id, p.name, COUNT(ps.song_id) AS song_count
        FROM Playlists p
        LEFT JOIN Playlist_Songs ps ON p.playlist_id = ps.playlist_id
        WHERE p.user_id = 0
        GROUP BY p.playlist_id
        ORDER BY song_count DESC
        LIMIT 3
        """
        
        cursor.execute(query)
        playlists = cursor.fetchall()
        
        # If no system playlists found, create default ones
        if not playlists:
            # Create system playlists
            create_default_system_playlists()
            # Fetch them again
            cursor.execute(query)
            playlists = cursor.fetchall()
        
        return playlists
        
    except mysql.connector.Error as e:
        print(f"Error fetching system playlists: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def create_default_system_playlists():
    """Create default system playlists if they don't exist"""
    try:
        connection = connect_db()
        if not connection:
            return
            
        cursor = connection.cursor()
        
        # Create 3 default system playlists
        default_playlists = [
            ("Coding", "Best songs for coding sessions"),
            ("LoFi", "Chilled beats for relaxation"),
            ("Bass", "Heavy bass music for energy")
        ]
        
        for name, description in default_playlists:
            # user_id 0 indicates a system playlist
            cursor.execute(
                "INSERT INTO Playlists (user_id, name, description) VALUES (%s, %s, %s)",
                (0, name, description)
            )
        
        connection.commit()
        
    except mysql.connector.Error as e:
        print(f"Error creating default playlists: {e}")
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_user_playlists():
    """Get the current user's playlists"""
    try:
        # Get current user ID
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
            
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT p.playlist_id, p.name, COUNT(ps.song_id) AS song_count
        FROM Playlists p
        LEFT JOIN Playlist_Songs ps ON p.playlist_id = ps.playlist_id
        WHERE p.user_id = %s
        GROUP BY p.playlist_id
        ORDER BY p.created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        playlists = cursor.fetchall()
        
        return playlists
        
    except Exception as e:
        print(f"Error fetching user playlists: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def create_new_playlist(name, description=""):
    """Create a new playlist for the current user"""
    try:
        # Get current user ID
        with open("current_user.txt", "r") as f:
            user_id = f.read().strip()
            
        connection = connect_db()
        if not connection:
            return None
            
        cursor = connection.cursor()
        
        query = "INSERT INTO Playlists (user_id, name, description) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, name, description))
        
        connection.commit()
        
        # Return the new playlist ID
        new_playlist_id = cursor.lastrowid
        return new_playlist_id
        
    except mysql.connector.Error as e:
        print(f"Error creating playlist: {e}")
        return None
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_playlist_songs(playlist_id):
    """Get songs in a playlist"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT s.song_id, s.title, a.name as artist_name, s.duration,
               ps.position
        FROM Playlist_Songs ps
        JOIN Songs s ON ps.song_id = s.song_id
        JOIN Artists a ON s.artist_id = a.artist_id
        WHERE ps.playlist_id = %s
        ORDER BY ps.position
        """
        
        cursor.execute(query, (playlist_id,))
        songs = cursor.fetchall()
        
        # Format durations to MM:SS
        for song in songs:
            minutes, seconds = divmod(song['duration'] or 0, 60)  # Handle None values
            song['duration_formatted'] = f"{minutes}:{seconds:02d}"
        
        return songs
        
    except mysql.connector.Error as e:
        print(f"Error fetching playlist songs: {e}")
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

def open_playlist_songs(playlist_id, playlist_name):
    """Open a playlist to view its songs"""
    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()
        
    # Header with playlist name
    header_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=40)
    header_frame.pack(fill="x", padx=20, pady=(20, 0))

    # Left side: Playlist name
    playlist_title_label = ctk.CTkLabel(header_frame, text=f"Playlist: {playlist_name}", 
                                      font=("Arial", 24, "bold"), text_color="white")
    playlist_title_label.pack(side="left")

    # Right side: Back button
    back_btn = ctk.CTkButton(header_frame, text="← Back to Playlists", 
                           font=("Arial", 14), fg_color="#B146EC", 
                           hover_color="#9333EA", command=refresh_playlists)
    back_btn.pack(side="right")
    
    # Songs section
    songs_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    songs_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))
    
    # Get songs in this playlist
    songs = get_playlist_songs(playlist_id)
    
    if not songs:
        # No songs in this playlist
        empty_label = ctk.CTkLabel(songs_frame, text="This playlist is empty.", 
                                 font=("Arial", 16), text_color="#A0A0A0")
        empty_label.pack(pady=30)
        
        # Add song button
        add_song_btn = ctk.CTkButton(songs_frame, text="+ Add Songs", 
                                    font=("Arial", 14, "bold"), fg_color="#B146EC", 
                                    hover_color="#9333EA", command=lambda: open_search_page())
        add_song_btn.pack(pady=10)
    else:
        # Song list header
        header = ctk.CTkFrame(songs_frame, fg_color="#131B2E", height=30)
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text="#", font=("Arial", 12, "bold"), text_color="#A0A0A0",
                   width=50).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(header, text="TITLE", font=("Arial", 12, "bold"), text_color="#A0A0A0",
                   width=250).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(header, text="ARTIST", font=("Arial", 12, "bold"), text_color="#A0A0A0",
                   width=200).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(header, text="DURATION", font=("Arial", 12, "bold"), text_color="#A0A0A0",
                   width=100).pack(side="left", padx=(10, 0))
        
        # Songs list
        songs_list_frame = ctk.CTkScrollableFrame(songs_frame, fg_color="#131B2E", 
                                                height=400, corner_radius=0)
        songs_list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Add songs to list
        for i, song in enumerate(songs, 1):
            song_row = ctk.CTkFrame(songs_list_frame, fg_color="#1A1A2E", corner_radius=5, height=40)
            song_row.pack(fill="x", pady=2, padx=5)
            
            # Track number
            ctk.CTkLabel(song_row, text=str(i), font=("Arial", 12), text_color="white",
                       width=50).pack(side="left", padx=(10, 0))
            
            # Song title
            ctk.CTkLabel(song_row, text=song["title"], font=("Arial", 12), text_color="white",
                       width=250, anchor="w").pack(side="left", padx=(10, 0))
            
            # Artist name
            ctk.CTkLabel(song_row, text=song["artist_name"], font=("Arial", 12), text_color="#A0A0A0",
                       width=200, anchor="w").pack(side="left", padx=(10, 0))
            
            # Duration
            ctk.CTkLabel(song_row, text=song["duration_formatted"], font=("Arial", 12), text_color="#A0A0A0",
                       width=100, anchor="w").pack(side="left", padx=(10, 0))
            
            # Play button
            play_btn = ctk.CTkButton(song_row, text="▶️", font=("Arial", 14), fg_color="#1A1A2E",
                                   hover_color="#232342", width=30, height=30, 
                                   command=lambda sid=song["song_id"]: play_song(sid))
            play_btn.pack(side="right", padx=10)
            
            # Make row clickable
            song_row.bind("<Button-1>", lambda e, sid=song["song_id"]: play_song(sid))

def show_create_playlist_dialog():
    """Show dialog to create a new playlist"""
    playlist_name = simpledialog.askstring("New Playlist", "Enter playlist name:")
    
    if playlist_name:
        if len(playlist_name.strip()) == 0:
            messagebox.showwarning("Invalid Name", "Playlist name cannot be empty.")
            return
            
        # Create the playlist
        new_playlist_id = create_new_playlist(playlist_name)
        
        if new_playlist_id:
            messagebox.showinfo("Success", f"Playlist '{playlist_name}' created!")
            refresh_playlists()  # Refresh the playlists view
        else:
            messagebox.showerror("Error", "Failed to create playlist.")

def refresh_playlists():
    """Refresh the playlists view"""
    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()
        
    # Recreate the content
    create_playlists_content()

def create_playlists_content():
    """Create the playlists content in the main frame"""
    # Header with username
    header_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=40)
    header_frame.pack(fill="x", padx=20, pady=(20, 0))

    # Left side: Featured
    featured_label = ctk.CTkLabel(header_frame, text="Playlists", font=("Arial", 24, "bold"), text_color="white")
    featured_label.pack(side="left")

    # Right side: Username
    user_label = ctk.CTkLabel(header_frame, 
                            text=f"Hello, {user['first_name']} {user['last_name']}!", 
                            font=("Arial", 14), text_color="#A0A0A0")
    user_label.pack(side="right")

    # ---------------- System Playlists ----------------
    our_playlists_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    our_playlists_frame.pack(fill="x", padx=20, pady=(40, 20))

    # Section title
    our_playlists_title = ctk.CTkLabel(our_playlists_frame, text="Featured Playlists :", 
                                      font=("Arial", 20, "bold"), text_color="#B146EC")
    our_playlists_title.pack(anchor="w", pady=(0, 20))

    # Playlist cards container
    our_playlists_cards = ctk.CTkFrame(our_playlists_frame, fg_color="#131B2E")
    our_playlists_cards.pack(fill="x")

    # Get system playlists
    system_playlists = get_system_playlists()
    
    if not system_playlists:
        # No featured playlists
        ctk.CTkLabel(our_playlists_cards, text="No featured playlists available", 
                   font=("Arial", 14), text_color="#A0A0A0").pack(pady=10)
    else:
        # Create cards for each featured playlist
        for playlist in system_playlists:
            # Create playlist card
            card = ctk.CTkFrame(our_playlists_cards, fg_color="#1A1A2E", corner_radius=15, 
                               width=150, height=100)
            card.pack(side="left", padx=10)
            card.pack_propagate(False)  # Prevent resizing
            
            # Main label
            label = ctk.CTkLabel(card, text=playlist["name"], 
                               font=("Arial", 16, "bold"), text_color="white")
            label.place(relx=0.5, rely=0.4, anchor="center")
            
            # Song count
            count_label = ctk.CTkLabel(card, text=f"{playlist['song_count']} songs", 
                                     font=("Arial", 12), text_color="#A0A0A0")
            count_label.place(relx=0.5, rely=0.65, anchor="center")
            
            # Make card clickable
            card.bind("<Button-1>", lambda e, pid=playlist["playlist_id"], 
                     pname=playlist["name"]: open_playlist_songs(pid, pname))
            label.bind("<Button-1>", lambda e, pid=playlist["playlist_id"], 
                      pname=playlist["name"]: open_playlist_songs(pid, pname))
            count_label.bind("<Button-1>", lambda e, pid=playlist["playlist_id"], 
                           pname=playlist["name"]: open_playlist_songs(pid, pname))

    # ---------------- Your Playlists ----------------
    your_playlists_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    your_playlists_frame.pack(fill="x", padx=20, pady=(30, 20))

    # Section title
    your_playlists_title = ctk.CTkLabel(your_playlists_frame, text="Your Playlists :", 
                                       font=("Arial", 20, "bold"), text_color="#B146EC")
    your_playlists_title.pack(anchor="w", pady=(0, 20))

    # Playlist cards container
    your_playlists_cards = ctk.CTkFrame(your_playlists_frame, fg_color="#131B2E")
    your_playlists_cards.pack(fill="x")

    # Add new playlist button
    add_playlist = ctk.CTkFrame(your_playlists_cards, fg_color="#2A2A3E", corner_radius=15, 
                               width=150, height=100)
    add_playlist.pack(side="left", padx=10)
    add_playlist.pack_propagate(False)  # Prevent resizing

    # Add Plus sign
    plus_label = ctk.CTkLabel(add_playlist, text="+", font=("Arial", 30, "bold"), text_color="#A0A0A0")
    plus_label.place(relx=0.5, rely=0.4, anchor="center")
    
    # Add text
    new_playlist_label = ctk.CTkLabel(add_playlist, text="New Playlist", 
                                    font=("Arial", 12), text_color="#A0A0A0")
    new_playlist_label.place(relx=0.5, rely=0.65, anchor="center")
    
    # Make button clickable
    add_playlist.bind("<Button-1>", lambda e: show_create_playlist_dialog())
    plus_label.bind("<Button-1>", lambda e: show_create_playlist_dialog())
    new_playlist_label.bind("<Button-1>", lambda e: show_create_playlist_dialog())

    # Get user playlists
    user_playlists = get_user_playlists()
    
    if not user_playlists:
        # No user playlists yet
        no_playlists_label = ctk.CTkLabel(your_playlists_cards, text="You haven't created any playlists yet", 
                                        font=("Arial", 14), text_color="#A0A0A0")
        no_playlists_label.pack(side="left", padx=20, pady=10)
    else:
        # Create cards for each user playlist
        for playlist in user_playlists:
            # Create playlist card
            card = ctk.CTkFrame(your_playlists_cards, fg_color="#1A1A2E", corner_radius=15, 
                               width=150, height=100)
            card.pack(side="left", padx=10)
            card.pack_propagate(False)  # Prevent resizing
            
            # Main label
            label = ctk.CTkLabel(card, text=playlist["name"], 
                               font=("Arial", 16, "bold"), text_color="white")
            label.place(relx=0.5, rely=0.4, anchor="center")
            
            # Song count
            count_label = ctk.CTkLabel(card, text=f"{playlist['song_count']} songs", 
                                     font=("Arial", 12), text_color="#A0A0A0")
            count_label.place(relx=0.5, rely=0.65, anchor="center")
            
            # Make card clickable
            card.bind("<Button-1>", lambda e, pid=playlist["playlist_id"], 
                     pname=playlist["name"]: open_playlist_songs(pid, pname))
            label.bind("<Button-1>", lambda e, pid=playlist["playlist_id"], 
                      pname=playlist["name"]: open_playlist_songs(pid, pname))
            count_label.bind("<Button-1>", lambda e, pid=playlist["playlist_id"], 
                           pname=playlist["name"]: open_playlist_songs(pid, pname))

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
    root.title("Online Music System - Playlists")
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
                              fg_color="#111827", hover_color="#1E293B", text_color="white",
                              anchor="w", corner_radius=0, height=40)
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

    # Create playlists content
    create_playlists_content()

    # ---------------- Run Application ----------------
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"Error in playlist.py: {e}")
    traceback.print_exc()
    messagebox.showerror("Error", f"An error occurred: {e}")
    input("Press Enter to exit...")  # This keeps console open