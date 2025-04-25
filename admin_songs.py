import customtkinter as ctk
from tkinter import messagebox, filedialog, simpledialog, ttk
import mysql.connector
import subprocess
import os
import io
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
import magic  # For file type detection (install with: pip install python-magic)

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

def get_admin_info():
    """Get the current admin information"""
    try:
        # Read admin ID from file
        if not os.path.exists("current_admin.txt"):
            messagebox.showerror("Error", "Admin session not found!")
            open_admin_login_page()
            return None
            
        with open("current_admin.txt", "r") as f:
            admin_id = f.read().strip()
            
        if not admin_id:
            messagebox.showerror("Error", "Admin ID not found!")
            open_admin_login_page()
            return None
            
        connection = connect_db()
        if not connection:
            return None
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, first_name, last_name, email FROM Users WHERE user_id = %s AND is_admin = 1",
            (admin_id,)
        )
        
        admin = cursor.fetchone()
        if not admin:
            messagebox.showerror("Access Denied", "You do not have admin privileges!")
            open_admin_login_page()
            return None
            
        return admin
        
    except Exception as e:
        print(f"Error getting admin info: {e}")
        return None
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_all_songs():
    """Get all songs from the database"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT s.song_id, s.title, a.name as artist_name, al.title as album_name,
               g.name as genre_name, s.duration, s.file_size, s.file_type, s.upload_date
        FROM Songs s
        JOIN Artists a ON s.artist_id = a.artist_id
        LEFT JOIN Albums al ON s.album_id = al.album_id
        LEFT JOIN Genres g ON s.genre_id = g.genre_id
        ORDER BY s.upload_date DESC
        """
        
        cursor.execute(query)
        songs = cursor.fetchall()
        
        # Format durations to MM:SS
        for song in songs:
            minutes, seconds = divmod(song['duration'] or 0, 60)
            song['duration_formatted'] = f"{minutes}:{seconds:02d}"
            
            # Format file size
            song['file_size_formatted'] = format_file_size(song['file_size'])
        
        return songs
        
    except mysql.connector.Error as e:
        print(f"Error fetching songs: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def delete_song(song_id):
    """Delete a song from the database"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # First delete from related tables to avoid foreign key constraints
        tables = [
            "Playlist_Songs",
            "User_Favorites",
            "Listening_History"
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE song_id = %s", (song_id,))
        
        # Now delete the song itself
        cursor.execute("DELETE FROM Songs WHERE song_id = %s", (song_id,))
        
        connection.commit()
        return True
        
    except mysql.connector.Error as e:
        print(f"Error deleting song: {e}")
        return False
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_artists():
    """Get list of artists from the database"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT artist_id, name FROM Artists ORDER BY name"
        cursor.execute(query)
        
        return cursor.fetchall()
        
    except mysql.connector.Error as e:
        print(f"Error fetching artists: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_genres():
    """Get list of genres from the database"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT genre_id, name FROM Genres ORDER BY name"
        cursor.execute(query)
        
        return cursor.fetchall()
        
    except mysql.connector.Error as e:
        print(f"Error fetching genres: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def add_new_artist(name):
    """Add a new artist to the database"""
    try:
        connection = connect_db()
        if not connection:
            return None
            
        cursor = connection.cursor()
        
        cursor.execute("INSERT INTO Artists (name) VALUES (%s)", (name,))
        connection.commit()
        
        new_id = cursor.lastrowid
        return new_id
        
    except mysql.connector.Error as e:
        print(f"Error adding artist: {e}")
        return None
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def format_file_size(size_bytes):
    """Format file size from bytes to human-readable format"""
    if not size_bytes:
        return "0 B"
    
    # Define size units
    units = ['B', 'KB', 'MB', 'GB']
    size = float(size_bytes)
    unit_index = 0
    
    # Convert to appropriate unit
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    # Return formatted size
    return f"{size:.2f} {units[unit_index]}"

def upload_song(file_path, title, artist_id, genre_id=None):
    """Upload a song to the database"""
    try:
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return None
        
        # Get file information
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(file_path)[1][1:].lower()  # Get extension without dot
        
        # Get song duration using mutagen
        try:
            if file_type == 'mp3':
                audio = MP3(file_path)
            elif file_type == 'flac':
                audio = FLAC(file_path)
            elif file_type in ['wav', 'wave']:
                audio = WAVE(file_path)
            else:
                # Fallback for other formats
                audio = mutagen.File(file_path)
                
            duration = int(audio.info.length)
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            duration = 0
        
        # Read file binary data
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        # Insert into database
        connection = connect_db()
        if not connection:
            return None
            
        cursor = connection.cursor()
        
        query = """
        INSERT INTO Songs (title, artist_id, genre_id, duration, file_data, file_type, file_size)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (title, artist_id, genre_id, duration, file_data, file_type, file_size)
        
        cursor.execute(query, values)
        connection.commit()
        
        # Return the new song ID
        new_song_id = cursor.lastrowid
        return new_song_id
        
    except mysql.connector.Error as e:
        print(f"Error uploading song: {e}")
        messagebox.showerror("Database Error", f"Failed to upload song: {e}")
        return None
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Navigation Functions -------------------
def return_to_dashboard():
    """Return to admin dashboard"""
    try:
        subprocess.Popen(["python", "admin.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open admin dashboard: {e}")

def open_admin_login_page():
    """Open the admin login page"""
    try:
        # Remove admin session
        if os.path.exists("current_admin.txt"):
            os.remove("current_admin.txt")
            
        subprocess.Popen(["python", "admin_login.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open admin login: {e}")

# ------------------- UI Functions -------------------
def refresh_song_list():
    """Refresh the song list display"""
    # Clear the treeview
    for item in songs_tree.get_children():
        songs_tree.delete(item)
    
    # Get updated songs
    songs = get_all_songs()
    
    # Add songs to treeview
    for i, song in enumerate(songs, 1):
        songs_tree.insert(
            "", "end", 
            values=(
                i,
                song["title"], 
                song["artist_name"], 
                song["genre_name"] or "", 
                song["duration_formatted"], 
                song["file_size_formatted"],
                song["song_id"]
            )
        )

def confirm_delete_song():
    """Confirm and delete selected song"""
    selected = songs_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Required", "Please select a song to delete.")
        return
    
    # Get the song ID from the selected item
    song_id = songs_tree.item(selected, 'values')[-1]  # Last column contains song_id
    song_title = songs_tree.item(selected, 'values')[1]  # Second column contains title
    
    # Confirmation dialog
    confirm = messagebox.askyesno(
        "Confirm Delete", 
        f"Are you sure you want to delete the song '{song_title}'?\n\nThis action cannot be undone."
    )
    
    if confirm:
        if delete_song(song_id):
            messagebox.showinfo("Success", f"Song '{song_title}' deleted successfully!")
            refresh_song_list()
        else:
            messagebox.showerror("Error", f"Failed to delete song '{song_title}'.")

def handle_upload_song():
    """Handle the song upload process"""
    # Ask user to select an audio file
    file_path = filedialog.askopenfilename(
        title="Select a song file",
        filetypes=[("Audio Files", "*.mp3 *.wav *.flac"), ("All files", "*.*")]
    )
    
    if not file_path:  # User cancelled
        return
    
    # Get song title from file name
    default_title = os.path.splitext(os.path.basename(file_path))[0]
    
    # Create upload dialog
    upload_dialog = ctk.CTkToplevel(root)
    upload_dialog.title("Upload Song")
    upload_dialog.geometry("400x300")
    upload_dialog.transient(root)
    upload_dialog.grab_set()
    
    # Center the dialog
    upload_dialog.update_idletasks()
    width = upload_dialog.winfo_width()
    height = upload_dialog.winfo_height()
    x = (upload_dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (upload_dialog.winfo_screenheight() // 2) - (height // 2)
    upload_dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    # Dialog title
    ctk.CTkLabel(
        upload_dialog, 
        text="Upload New Song", 
        font=("Arial", 18, "bold")
    ).pack(pady=(20, 20))
    
    # Song title input
    title_frame = ctk.CTkFrame(upload_dialog)
    title_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(title_frame, text="Title:", width=100).pack(side="left")
    title_var = ctk.StringVar(value=default_title)
    title_entry = ctk.CTkEntry(title_frame, textvariable=title_var, width=200)
    title_entry.pack(side="left", padx=5)
    
    # Get artists
    artists = get_artists()
    artist_names = [artist["name"] for artist in artists]
    artist_ids = [artist["artist_id"] for artist in artists]
    
    # Artist selection
    artist_frame = ctk.CTkFrame(upload_dialog)
    artist_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(artist_frame, text="Artist:", width=100).pack(side="left")
    artist_var = ctk.StringVar()
    if artist_names:
        artist_var.set(artist_names[0])
    
    artist_menu = ctk.CTkOptionMenu(
        artist_frame, 
        variable=artist_var,
        values=artist_names,
        width=200
    )
    artist_menu.pack(side="left", padx=5)
    
    # New artist button
    def add_artist():
        artist_name = simpledialog.askstring("New Artist", "Enter artist name:")
        if artist_name:
            new_id = add_new_artist(artist_name)
            if new_id:
                # Update the artist lists
                artist_names.append(artist_name)
                artist_ids.append(new_id)
                artist_menu.configure(values=artist_names)
                artist_var.set(artist_name)
    
    new_artist_btn = ctk.CTkButton(
        artist_frame, 
        text="+", 
        width=30, 
        command=add_artist
    )
    new_artist_btn.pack(side="left", padx=5)
    
    # Get genres
    genres = get_genres()
    genre_names = [genre["name"] for genre in genres]
    genre_ids = [genre["genre_id"] for genre in genres]
    
    # Genre selection
    genre_frame = ctk.CTkFrame(upload_dialog)
    genre_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(genre_frame, text="Genre:", width=100).pack(side="left")
    genre_var = ctk.StringVar()
    if genre_names:
        genre_var.set(genre_names[0])
    
    genre_menu = ctk.CTkOptionMenu(
        genre_frame, 
        variable=genre_var,
        values=genre_names,
        width=200
    )
    genre_menu.pack(side="left", padx=5)
    
    # File info
    file_frame = ctk.CTkFrame(upload_dialog)
    file_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(file_frame, text="File:", width=100).pack(side="left")
    file_label = ctk.CTkLabel(file_frame, text=os.path.basename(file_path))
    file_label.pack(side="left", padx=5)
    
    # Upload button
    def do_upload():
        title = title_var.get()
        if not title:
            messagebox.showwarning("Input Error", "Please enter a song title")
            return
        
        # Get selected artist ID
        artist_name = artist_var.get()
        artist_index = artist_names.index(artist_name)
        artist_id = artist_ids[artist_index]
        
        # Get selected genre ID
        genre_name = genre_var.get()
        genre_index = genre_names.index(genre_name)
        genre_id = genre_ids[genre_index]
        
        # Upload song
        song_id = upload_song(file_path, title, artist_id, genre_id)
        
        if song_id:
            messagebox.showinfo("Success", f"Song '{title}' uploaded successfully!")
            upload_dialog.destroy()
            refresh_song_list()
        else:
            messagebox.showerror("Error", "Failed to upload song.")
    
    upload_btn = ctk.CTkButton(
        upload_dialog,
        text="Upload Song",
        command=do_upload,
        fg_color="#B146EC",
        hover_color="#9333EA"
    )
    upload_btn.pack(pady=20)

# ------------------- Main Application -------------------
try:
    # Verify admin privileges
    admin = get_admin_info()
    if not admin:
        exit()
    
    # Initialize app
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Admin - Manage Songs")
    root.geometry("1000x600")
    
    # Main frame
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Header
    header_frame = ctk.CTkFrame(main_frame, height=60, fg_color="#1A1A2E")
    header_frame.pack(fill="x", padx=10, pady=10)
    
    # Title
    ctk.CTkLabel(
        header_frame, 
        text="Manage Songs", 
        font=("Arial", 24, "bold"),
        text_color="#B146EC"
    ).pack(side="left", padx=20)
    
    # Admin name
    ctk.CTkLabel(
        header_frame,
        text=f"Admin: {admin['first_name']} {admin['last_name']}",
        font=("Arial", 14)
    ).pack(side="right", padx=20)
    
    # Back button
    back_btn = ctk.CTkButton(
        header_frame,
        text="← Back to Dashboard",
        command=return_to_dashboard,
        fg_color="#2563EB",
        hover_color="#1D4ED8",
        height=32
    )
    back_btn.pack(side="right", padx=20)
    
    # Content area
    content_frame = ctk.CTkFrame(main_frame, fg_color="#131B2E")
    content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    # Action buttons
    action_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=50)
    action_frame.pack(fill="x", padx=20, pady=20)
    
    # Upload button
    upload_btn = ctk.CTkButton(
        action_frame,
        text="+ Upload New Song",
        command=handle_upload_song,
        fg_color="#16A34A",
        hover_color="#15803D",
        height=40
    )
    upload_btn.pack(side="left", padx=(0, 10))
    
    # Delete button
    delete_btn = ctk.CTkButton(
        action_frame,
        text="🗑️ Delete Selected Song",
        command=confirm_delete_song,
        fg_color="#DC2626",
        hover_color="#B91C1C",
        height=40
    )
    delete_btn.pack(side="left")
    
    # Refresh button
    refresh_btn = ctk.CTkButton(
        action_frame,
        text="🔄 Refresh List",
        command=refresh_song_list,
        fg_color="#B146EC",
        hover_color="#9333EA",
        height=40
    )
    refresh_btn.pack(side="right")
    
    # Songs list with scrollbar
    songs_frame = ctk.CTkFrame(content_frame, fg_color="#1A1A2E")
    songs_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    # Create Treeview with ttk.Scrollbar
    tree_frame = ctk.CTkFrame(songs_frame)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create a custom style for the Treeview
    style = ttk.Style()
    style.theme_use("default")
    
    # Configure colors for dark mode
    style.configure(
        "Treeview",
        background="#1E1E2E",
        foreground="white",
        fieldbackground="#1E1E2E",
        borderwidth=0
    )
    style.map(
        "Treeview", 
        background=[("selected", "#B146EC")],
        foreground=[("selected", "white")]
    )
    
    # Add scrollbar
    tree_scroll = ttk.Scrollbar(tree_frame)
    tree_scroll.pack(side="right", fill="y")
    
    # Create Treeview with columns
    songs_tree = ttk.Treeview(
        tree_frame,
        columns=("id", "title", "artist", "genre", "duration", "size", "song_id"),
        show="headings",
        height=20,
        yscrollcommand=tree_scroll.set
    )
    songs_tree.pack(fill="both", expand=True)
    
    # Configure scrollbar
    tree_scroll.config(command=songs_tree.yview)
    
    # Format columns
    songs_tree.heading("id", text="#")
    songs_tree.heading("title", text="Title")
    songs_tree.heading("artist", text="Artist")
    songs_tree.heading("genre", text="Genre")
    songs_tree.heading("duration", text="Duration")
    songs_tree.heading("size", text="Size")
    songs_tree.heading("song_id", text="ID")
    
    # Set column widths and alignment
    songs_tree.column("id", width=50, anchor="center")
    songs_tree.column("title", width=250, anchor="w")
    songs_tree.column("artist", width=150, anchor="w")
    songs_tree.column("genre", width=100, anchor="w")
    songs_tree.column("duration", width=80, anchor="center")
    songs_tree.column("size", width=80, anchor="e")
    songs_tree.column("song_id", width=50, anchor="center")
    
    # Statistics footer
    stats_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=30)
    stats_frame.pack(fill="x", padx=20, pady=(0, 10))
    
    stats_label = ctk.CTkLabel(
        stats_frame,
        text="Loading songs...",
        font=("Arial", 12),
        text_color="#A0A0A0"
    )
    stats_label.pack(side="left")
    
    # Load songs after the UI is created
    root.after(100, lambda: [
        refresh_song_list(),
        stats_label.configure(text=f"Total Songs: {len(songs_tree.get_children())}")
    ])
    
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
    messagebox.showerror("Error", f"An error occurred: {e}")