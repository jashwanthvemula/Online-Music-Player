import mysql.connector
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import hashlib
import random
import time
import shutil
import io
from PIL import Image

# ------------------- Database Setup Functions -------------------
def connect_db_server():
    """Connect to MySQL server without specifying a database"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="new_password"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL server: {err}")
        return None

def connect_db():
    """Connect to the specific database"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="new_password",
            database="online_music_system"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def create_database():
    """Create the database and tables"""
    try:
        # First connect to server
        connection = connect_db_server()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Create database
        print("Creating database...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS online_music_system")
        cursor.execute("USE online_music_system")
        
        # Create Users table
        print("Creating Users table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(64) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create Artists table
        print("Creating Artists table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Artists (
            artist_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            bio TEXT,
            image_url VARCHAR(255)
        )
        """)
        
        # Create Albums table
        print("Creating Albums table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Albums (
            album_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            artist_id INT,
            release_year INT,
            cover_art MEDIUMBLOB,
            FOREIGN KEY (artist_id) REFERENCES Artists(artist_id) ON DELETE SET NULL
        )
        """)
        
        # Create Genres table
        print("Creating Genres table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Genres (
            genre_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE
        )
        """)
        
        # Create Songs table
        print("Creating Songs table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Songs (
            song_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            artist_id INT,
            album_id INT,
            genre_id INT,
            duration INT,
            file_data LONGBLOB NOT NULL,
            file_type VARCHAR(10) NOT NULL,
            file_size INT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (artist_id) REFERENCES Artists(artist_id) ON DELETE SET NULL,
            FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE SET NULL,
            FOREIGN KEY (genre_id) REFERENCES Genres(genre_id) ON DELETE SET NULL
        )
        """)
        
        # Create Playlists table
        print("Creating Playlists table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Playlists (
            playlist_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        """)
        
        # Create Playlist_Songs junction table
        print("Creating Playlist_Songs table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Playlist_Songs (
            playlist_id INT NOT NULL,
            song_id INT NOT NULL,
            position INT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (playlist_id, song_id),
            FOREIGN KEY (playlist_id) REFERENCES Playlists(playlist_id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES Songs(song_id) ON DELETE CASCADE
        )
        """)
        
        # Create User_Favorites table
        print("Creating User_Favorites table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS User_Favorites (
            user_id INT NOT NULL,
            song_id INT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, song_id),
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES Songs(song_id) ON DELETE CASCADE
        )
        """)
        
        # Create Listening_History table
        print("Creating Listening_History table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Listening_History (
            history_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            song_id INT NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES Songs(song_id) ON DELETE CASCADE
        )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Database and tables created successfully!")
        return True
        
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        return False

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_default_users():
    """Add default users including admin"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            print(f"Users table already has {user_count} records. Skipping default users.")
            cursor.close()
            connection.close()
            return True
        
        # Default users
        default_users = [
            # Admin user
            ("Admin", "User", "admin@music.com", hash_password("admin123"), True),
            # Regular users
            ("John", "Doe", "john@example.com", hash_password("password123"), False),
            ("Jane", "Smith", "jane@example.com", hash_password("password123"), False),
            ("Alice", "Johnson", "alice@example.com", hash_password("password123"), False),
            ("Bob", "Williams", "bob@example.com", hash_password("password123"), False)
        ]
        
        # Insert users
        print("Adding default users...")
        for first_name, last_name, email, password, is_admin in default_users:
            cursor.execute(
                "INSERT INTO Users (first_name, last_name, email, password, is_admin) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, email, password, is_admin)
            )
        
        connection.commit()
        print(f"Added {len(default_users)} default users successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"Error adding default users: {err}")
        return False

def add_default_genres():
    """Add default music genres"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if genres already exist
        cursor.execute("SELECT COUNT(*) FROM Genres")
        genre_count = cursor.fetchone()[0]
        
        if genre_count > 0:
            print(f"Genres table already has {genre_count} records. Skipping default genres.")
            cursor.close()
            connection.close()
            return True
        
        # Default genres
        default_genres = [
            "Pop", "Rock", "Hip Hop", "R&B", "Country", 
            "Jazz", "Classical", "Electronic", "Blues", "Reggae",
            "Folk", "Metal", "Punk", "Soul", "Funk",
            "Disco", "Techno", "House", "Ambient", "Indie"
        ]
        
        # Insert genres
        print("Adding default genres...")
        for genre in default_genres:
            cursor.execute("INSERT INTO Genres (name) VALUES (%s)", (genre,))
        
        connection.commit()
        print(f"Added {len(default_genres)} default genres successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"Error adding default genres: {err}")
        return False

def add_default_artists():
    """Add default artists"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if artists already exist
        cursor.execute("SELECT COUNT(*) FROM Artists")
        artist_count = cursor.fetchone()[0]
        
        if artist_count > 0:
            print(f"Artists table already has {artist_count} records. Skipping default artists.")
            cursor.close()
            connection.close()
            return True
        
        # Default artists with bios
        default_artists = [
            ("The Weeknd", "Abel Makkonen Tesfaye, known professionally as the Weeknd, is a Canadian singer, songwriter, and record producer."),
            ("Dua Lipa", "Dua Lipa is an English singer and songwriter. After working as a model, she signed with Warner Bros. Records in 2014."),
            ("Ed Sheeran", "Edward Christopher Sheeran MBE is an English singer-songwriter, record producer, musician, and actor."),
            ("Taylor Swift", "Taylor Alison Swift is an American singer-songwriter. Her discography spans multiple genres, and her songwriting is often inspired by her personal life."),
            ("Billie Eilish", "Billie Eilish Pirate Baird O'Connell is an American singer-songwriter. She first gained public attention in 2015 with her debut single 'Ocean Eyes'."),
            ("Drake", "Aubrey Drake Graham is a Canadian rapper, singer, and actor. Drake initially gained recognition as an actor on the teen drama television series Degrassi: The Next Generation."),
            ("Ariana Grande", "Ariana Grande-Butera is an American singer, songwriter, and actress. Her four-octave vocal range has received critical acclaim."),
            ("Beyoncé", "Beyoncé Giselle Knowles-Carter is an American singer, songwriter, record producer, and actress."),
            ("Post Malone", "Austin Richard Post, known professionally as Post Malone, is an American rapper, singer, and songwriter."),
            ("Justin Bieber", "Justin Drew Bieber is a Canadian singer. He was discovered by American record executive Scooter Braun.")
        ]
        
        # Insert artists
        print("Adding default artists...")
        for name, bio in default_artists:
            cursor.execute(
                "INSERT INTO Artists (name, bio) VALUES (%s, %s)",
                (name, bio)
            )
        
        connection.commit()
        print(f"Added {len(default_artists)} default artists successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"Error adding default artists: {err}")
        return False

def add_default_albums():
    """Add default albums"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if albums already exist
        cursor.execute("SELECT COUNT(*) FROM Albums")
        album_count = cursor.fetchone()[0]
        
        if album_count > 0:
            print(f"Albums table already has {album_count} records. Skipping default albums.")
            cursor.close()
            connection.close()
            return True
        
        # Get artist IDs
        cursor.execute("SELECT artist_id, name FROM Artists")
        artists = {name: artist_id for artist_id, name in cursor.fetchall()}
        
        # Default albums with artist IDs
        default_albums = [
            ("After Hours", artists.get("The Weeknd", 1), 2020),
            ("Future Nostalgia", artists.get("Dua Lipa", 2), 2020),
            ("÷ (Divide)", artists.get("Ed Sheeran", 3), 2017),
            ("1989", artists.get("Taylor Swift", 4), 2014),
            ("When We All Fall Asleep, Where Do We Go?", artists.get("Billie Eilish", 5), 2019),
            ("Scorpion", artists.get("Drake", 6), 2018),
            ("Thank U, Next", artists.get("Ariana Grande", 7), 2019),
            ("Lemonade", artists.get("Beyoncé", 8), 2016),
            ("Hollywood's Bleeding", artists.get("Post Malone", 9), 2019),
            ("Justice", artists.get("Justin Bieber", 10), 2021)
        ]
        
        # Insert albums
        print("Adding default albums...")
        for title, artist_id, release_year in default_albums:
            cursor.execute(
                "INSERT INTO Albums (title, artist_id, release_year) VALUES (%s, %s, %s)",
                (title, artist_id, release_year)
            )
        
        connection.commit()
        print(f"Added {len(default_albums)} default albums successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"Error adding default albums: {err}")
        return False

def add_dummy_songs():
    """Add dummy/placeholder songs"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if songs already exist
        cursor.execute("SELECT COUNT(*) FROM Songs")
        song_count = cursor.fetchone()[0]
        
        if song_count > 0:
            print(f"Songs table already has {song_count} records. Skipping dummy songs.")
            cursor.close()
            connection.close()
            return True
        
        # Get artist IDs
        cursor.execute("SELECT artist_id, name FROM Artists")
        artists = {name: artist_id for artist_id, name in cursor.fetchall()}
        
        # Get album IDs
        cursor.execute("SELECT album_id, title FROM Albums")
        albums = {title: album_id for album_id, title in cursor.fetchall()}
        
        # Get genre IDs
        cursor.execute("SELECT genre_id, name FROM Genres")
        genres = {name: genre_id for genre_id, name in cursor.fetchall()}
        
        # Dummy songs data
        dummy_songs = [
            # Song title, artist, album, genre, duration in seconds
            ("Blinding Lights", "The Weeknd", "After Hours", "Pop", 201),
            ("Save Your Tears", "The Weeknd", "After Hours", "Pop", 215),
            ("Levitating", "Dua Lipa", "Future Nostalgia", "Pop", 203),
            ("Don't Start Now", "Dua Lipa", "Future Nostalgia", "Pop", 183),
            ("Shape of You", "Ed Sheeran", "÷ (Divide)", "Pop", 233),
            ("Castle on the Hill", "Ed Sheeran", "÷ (Divide)", "Pop", 261),
            ("Blank Space", "Taylor Swift", "1989", "Pop", 231),
            ("Shake It Off", "Taylor Swift", "1989", "Pop", 219),
            ("Bad Guy", "Billie Eilish", "When We All Fall Asleep, Where Do We Go?", "Pop", 194),
            ("God's Plan", "Drake", "Scorpion", "Hip Hop", 198),
            ("7 Rings", "Ariana Grande", "Thank U, Next", "Pop", 178),
            ("Formation", "Beyoncé", "Lemonade", "R&B", 206),
            ("Circles", "Post Malone", "Hollywood's Bleeding", "Pop", 215),
            ("Peaches", "Justin Bieber", "Justice", "Pop", 198),
            ("Stay", "Justin Bieber", "Justice", "Pop", 141)
        ]
        
        # Dummy audio data - just a placeholder WAV file
        print("Creating dummy audio data...")
        dummy_audio_data = create_dummy_audio()
        dummy_file_size = len(dummy_audio_data)
        dummy_file_type = "wav"
        
        # Insert songs
        print("Adding dummy songs...")
        for title, artist_name, album_title, genre_name, duration in dummy_songs:
            # Get IDs from mappings
            artist_id = artists.get(artist_name, 1)  # Default to ID 1 if not found
            album_id = albums.get(album_title, 1)    # Default to ID 1 if not found
            genre_id = genres.get(genre_name, 1)     # Default to ID 1 if not found
            
            cursor.execute(
                """
                INSERT INTO Songs (title, artist_id, album_id, genre_id, duration, file_data, file_type, file_size)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (title, artist_id, album_id, genre_id, duration, dummy_audio_data, dummy_file_type, dummy_file_size)
            )
        
        connection.commit()
        print(f"Added {len(dummy_songs)} dummy songs successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"Error adding dummy songs: {err}")
        return False

def create_dummy_audio():
    """Create a dummy WAV file data for placeholder"""
    # This creates a very simple WAV file with 1 second of silence
    # Complete WAV header and minimal data
    wav_header = bytearray([
        # RIFF header
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # Chunk size (36 + data size)
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        
        # Format subchunk
        0x66, 0x6d, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Subchunk size (16 bytes)
        0x01, 0x00,              # Audio format (1 = PCM)
        0x01, 0x00,              # Number of channels (1)
        0x44, 0xac, 0x00, 0x00,  # Sample rate (44100 Hz)
        0x44, 0xac, 0x00, 0x00,  # Byte rate (44100 * 1 * 1)
        0x01, 0x00,              # Block align (1)
        0x08, 0x00,              # Bits per sample (8)
        
        # Data subchunk
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00   # Data size (filled in below)
    ])
    
    # Generate 1 second of silence at 44.1kHz
    silence_duration = 1  # seconds
    sample_rate = 44100
    num_samples = silence_duration * sample_rate
    silent_data = bytearray([128] * num_samples)  # 128 = silence for 8-bit PCM
    
    # Update data size
    data_size = len(silent_data)
    wav_header[40:44] = data_size.to_bytes(4, byteorder='little')
    
    # Update RIFF chunk size
    riff_chunk_size = 36 + data_size
    wav_header[4:8] = riff_chunk_size.to_bytes(4, byteorder='little')
    
    # Combine header and data
    wav_data = wav_header + silent_data
    
    return wav_data

def add_default_playlists():
    """Add default playlists"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if playlists already exist
        cursor.execute("SELECT COUNT(*) FROM Playlists")
        playlist_count = cursor.fetchone()[0]
        
        if playlist_count > 0:
            print(f"Playlists table already has {playlist_count} records. Skipping default playlists.")
            cursor.close()
            connection.close()
            return True
        
        # Get user IDs
        cursor.execute("SELECT user_id FROM Users")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Create system playlists (user_id 0)
        system_playlists = [
            (0, "Top Hits", "Most popular songs right now"),
            (0, "Chill Vibes", "Relaxing music for your downtime"),
            (0, "Workout Mix", "Energetic tracks to keep you moving")
        ]
        
        # Insert system playlists
        print("Adding system playlists...")
        for user_id, name, description in system_playlists:
            cursor.execute(
                "INSERT INTO Playlists (user_id, name, description) VALUES (%s, %s, %s)",
                (user_id, name, description)
            )
        
        # Create user playlists (one for each user)
        user_playlists = []
        for user_id in user_ids:
            if user_id > 0:  # Skip admin user
                user_playlists.append((user_id, f"My Favorites", "My favorite songs"))
                user_playlists.append((user_id, f"Road Trip", "Perfect for long drives"))
        
        # Insert user playlists
        print("Adding user playlists...")
        for user_id, name, description in user_playlists:
            cursor.execute(
                "INSERT INTO Playlists (user_id, name, description) VALUES (%s, %s, %s)",
                (user_id, name, description)
            )
        
        connection.commit()
        print(f"Added {len(system_playlists) + len(user_playlists)} default playlists successfully!")
        
        # Now add songs to playlists
        cursor.execute("SELECT playlist_id FROM Playlists")
        playlist_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT song_id FROM Songs")
        song_ids = [row[0] for row in cursor.fetchall()]
        
        if song_ids:
            print("Adding songs to playlists...")
            # For each playlist, add 3-5 random songs
            for playlist_id in playlist_ids:
                # Choose a random number of songs (3-5)
                num_songs = random.randint(3, min(5, len(song_ids)))
                # Choose random songs
                playlist_songs = random.sample(song_ids, num_songs)
                
                # Add songs to playlist
                for position, song_id in enumerate(playlist_songs, 1):
                    cursor.execute(
                        "INSERT INTO Playlist_Songs (playlist_id, song_id, position) VALUES (%s, %s, %s)",
                        (playlist_id, song_id, position)
                    )
        
        connection.commit()
        print("Added songs to playlists successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"Error adding default playlists: {err}")
        return False

def add_sample_listening_history():
    """Add sample listening history for users"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if listening history already exists
        cursor.execute("SELECT COUNT(*) FROM Listening_History")
        history_count = cursor.fetchone()[0]
        
        if history_count > 0:
            print(f"Listening_History table already has {history_count} records. Skipping sample history.")
            cursor.close()
            connection.close()
            return True
        
        # Get user IDs (except admin)
        cursor.execute("SELECT user_id FROM Users WHERE is_admin = 0")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Get song IDs
        cursor.execute("SELECT song_id FROM Songs")
        song_ids = [row[0] for row in cursor.fetchall()]
        
        if not song_ids or not user_ids:
            print("No songs or users found. Skipping sample listening history.")
            cursor.close()
            connection.close()
            return False
        
        print("Adding sample listening history...")
        # For each user, add 5-15 listening records
        for user_id in user_ids:
            # Choose a random number of plays (5-15)
            num_plays = random.randint(5, 15)
            
            # Generate random plays
            for _ in range(num_plays):
                # Choose a random song
                song_id = random.choice(song_ids)
                
                # Add to listening history
                cursor.execute(
                    "INSERT INTO Listening_History (user_id, song_id) VALUES (%s, %s)",
                    (user_id, song_id)
                )
        
        connection.commit()
        
        # Check how many were added
        cursor.execute("SELECT COUNT(*) FROM Listening_History")
        new_count = cursor.fetchone()[0]
        
        print(f"Added {new_count} listening history records successfully!")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"Error adding sample listening history: {err}")
        return False

def create_temp_directory():
    """Create a temp directory for storing temporary files"""
    try:
        if not os.path.exists("temp"):
            os.makedirs("temp")
            print("Created temp directory for temporary files.")
        return True
    except Exception as e:
        print(f"Error creating temp directory: {e}")
        return False

# ------------------- Splash Screen -------------------
def show_splash_screen():
    """Display a splash screen while setting up the database"""
    # Setup splash window
    splash_root = ctk.CTk()
    splash_root.title("Online Music System - Setup")
    splash_root.geometry("400x300")
    splash_root.overrideredirect(True)  # No window border
    
    # Center the window
    screen_width = splash_root.winfo_screenwidth()
    screen_height = splash_root.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 300) // 2
    splash_root.geometry(f"400x300+{x}+{y}")
    
    # Create a frame with rounded corners and purple color
    splash_frame = ctk.CTkFrame(splash_root, corner_radius=20, fg_color="#B146EC")
    splash_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # App title
    ctk.CTkLabel(
        splash_frame, 
        text="Online Music System", 
        font=("Arial", 28, "bold"),
        text_color="white"
    ).pack(pady=(40, 5))
    
    # App icon/logo
    ctk.CTkLabel(
        splash_frame, 
        text="🎵🐦", 
        font=("Arial", 50),
        text_color="white"
    ).pack(pady=10)
    
    # Loading text
    loading_label = ctk.CTkLabel(
        splash_frame, 
        text="Initializing...", 
        font=("Arial", 14),
        text_color="white"
    )
    loading_label.pack(pady=10)
    
    # Progress bar
    progress = ctk.CTkProgressBar(splash_frame, width=320)
    progress.pack(pady=10)
    progress.set(0)
    
    # Status message
    status_label = ctk.CTkLabel(
        splash_frame,
        text="",
        font=("Arial", 12),
        text_color="white"
    )
    status_label.pack(pady=5)
    
    # Setup steps with corresponding progress values
    setup_steps = [
        ("Creating database schema...", 0.1, create_database),
        ("Adding default users...", 0.2, add_default_users),
        ("Adding music genres...", 0.3, add_default_genres),
        ("Adding artists...", 0.4, add_default_artists),
        ("Adding albums...", 0.5, add_default_albums),
        ("Adding sample songs...", 0.6, add_dummy_songs),
        ("Creating playlists...", 0.8, add_default_playlists),
        ("Adding listening history...", 0.9, add_sample_listening_history),
        ("Creating temporary directories...", 0.95, create_temp_directory)
    ]
    
    # Function to run setup in steps
    def run_setup():
        # Initialize progress
        progress.set(0.05)
        loading_label.configure(text="Starting setup...")
        splash_root.update_idletasks()
        time.sleep(0.5)
        
        # Run each setup step
        setup_success = True
        for message, prog_value, step_function in setup_steps:
            # Update UI
            loading_label.configure(text=message)
            status_label.configure(text="")
            progress.set(prog_value)
            splash_root.update_idletasks()
            
            # Run step
            try:
                result = step_function()
                if not result:
                    setup_success = False
                    status_label.configure(text="Error! Check console for details.")
            except Exception as e:
                setup_success = False
                print(f"Error during setup: {e}")
                status_label.configure(text=f"Error: {str(e)[:30]}...")
            
            # Small delay for visual feedback
            time.sleep(0.3)
        
        # Complete setup
        progress.set(1.0)
        
        if setup_success:
            loading_label.configure(text="Setup completed successfully!")
            status_label.configure(text="Launching application...")
        else:
            loading_label.configure(text="Setup completed with errors.")
            status_label.configure(text="See console for details. Launching application...")
        
        splash_root.update_idletasks()
        time.sleep(1.5)
        
        # Close splash and launch application
        splash_root.destroy()
        launch_application()
    
    # Add a small admin login link at the bottom
    admin_link = ctk.CTkLabel(
        splash_frame,
        text="Admin Login",
        font=("Arial", 10),
        text_color="white",
        cursor="hand2"
    )
    admin_link.pack(side="bottom", pady=5)
    admin_link.bind("<Button-1>", lambda e: [splash_root.destroy(), launch_admin_login()])
    
    # Start setup after a short delay
    splash_root.after(500, run_setup)
    
    # Start the splash screen
    splash_root.mainloop()

# ------------------- Launch Application -------------------
def launch_application():
    """Launch the application starting with the login screen"""
    try:
        # Clear any existing user session
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
        
        if os.path.exists("current_admin.txt"):
            os.remove("current_admin.txt")
        
        # Start the login page
        subprocess.Popen(["python", "login.py"])
    except Exception as e:
        print(f"Error launching application: {e}")
        messagebox.showerror("Error", f"Failed to launch application: {e}")

def launch_admin_login():
    """Launch the admin login page"""
    try:
        # Clear any existing user session
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
        
        if os.path.exists("current_admin.txt"):
            os.remove("current_admin.txt")
        
        # Start the admin login page
        subprocess.Popen(["python", "admin_login.py"])
    except Exception as e:
        print(f"Error launching admin login: {e}")
        messagebox.showerror("Error", f"Failed to launch admin login: {e}")

# ------------------- Main Entry Point -------------------
if __name__ == "__main__":
    try:
        # Set the appearance mode for splash screen
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Show splash screen and setup database
        show_splash_screen()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to start login page directly if splash screen fails
        try:
            launch_application()
        except:
            pass
        
        # Keep console open in case of error
        input("Press Enter to exit...")