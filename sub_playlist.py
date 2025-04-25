import customtkinter as ctk

# ---------------- Initialize App ----------------
ctk.set_appearance_mode("dark")  # Dark mode
ctk.set_default_color_theme("blue")  # Default theme

root = ctk.CTk()
root.title("Online Music System - Playlist")
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

# Sidebar Menu Items
menu_items = [
    ("🏠 Home", "#111827", "#A0A0A0"),
    ("🔍 Search", "#111827", "#A0A0A0"),
    ("🎵 Playlist", "#111827", "white"),  # Highlighted as active
    ("⬇️ Download", "#111827", "#A0A0A0"),
    ("🎧 Recommend Songs", "#111827", "#A0A0A0"),
    ("🚪 Logout", "#111827", "#A0A0A0")
]

for text, bg_color, text_color in menu_items:
    btn = ctk.CTkButton(sidebar, text=text, font=("Arial", 14), 
                      fg_color=bg_color, hover_color="#1E293B", text_color=text_color,
                      anchor="w", corner_radius=0, height=40)
    btn.pack(fill="x", pady=5, padx=10)

# Music player controls at bottom of sidebar
player_frame = ctk.CTkFrame(sidebar, fg_color="#111827", height=50)
player_frame.pack(side="bottom", fill="x", pady=20, padx=10)

# Control buttons
prev_btn = ctk.CTkButton(player_frame, text="⏮️", font=("Arial", 18), 
                         fg_color="#111827", hover_color="#1E293B", width=40, height=40)
prev_btn.pack(side="left", padx=10)

play_btn = ctk.CTkButton(player_frame, text="▶️", font=("Arial", 18), 
                         fg_color="#111827", hover_color="#1E293B", width=40, height=40)
play_btn.pack(side="left", padx=10)

next_btn = ctk.CTkButton(player_frame, text="⏭️", font=("Arial", 18), 
                         fg_color="#111827", hover_color="#1E293B", width=40, height=40)
next_btn.pack(side="left", padx=10)

# ---------------- Main Content ----------------
content_frame = ctk.CTkFrame(main_frame, fg_color="#131B2E", corner_radius=10)
content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Header with username
header_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=40)
header_frame.pack(fill="x", padx=20, pady=(20, 0))

# Left side: Playlist
playlist_label = ctk.CTkLabel(header_frame, text="Playlist", font=("Arial", 24, "bold"), text_color="white")
playlist_label.pack(side="left")

# Right side: Username
user_label = ctk.CTkLabel(header_frame, text="Hello, User!", font=("Arial", 14), text_color="#A0A0A0")
user_label.pack(side="right")

# ---------------- Currently Playing Playlist ----------------
currently_playing_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
currently_playing_frame.pack(fill="x", padx=20, pady=(40, 10))

# Section title - centered
currently_playing_title = ctk.CTkLabel(currently_playing_frame, text="Currently Playing Playlist", 
                                      font=("Arial", 24, "bold"), text_color="#B146EC")
currently_playing_title.pack(pady=(0, 5))

# Subtitle - centered
subtitle = ctk.CTkLabel(currently_playing_frame, text="Choose a song to play from your playlist!", 
                       font=("Arial", 14), text_color="#A0A0A0")
subtitle.pack(pady=(0, 20))

# Song list container
songs_frame = ctk.CTkFrame(currently_playing_frame, fg_color="#1A1A2E", corner_radius=10)
songs_frame.pack(fill="x", pady=10, ipady=15)

# Song list
songs = [
    ("Don Toliver - No Idea [Official Music Video].mp3", "green"),
    ("Rick Astley - Never Gonna Give You Up (Official Music).mp3", "white")
]

for song, color in songs:
    # Song row
    song_row = ctk.CTkFrame(songs_frame, fg_color="#1A1A2E", height=30)
    song_row.pack(fill="x", padx=15, pady=5)
    
    # Bullet point and song name
    if color == "green":
        bullet = "• "
        text_color = "#22C55E"  # Green color for the first song
    else:
        bullet = "• "
        text_color = "white"
    
    song_label = ctk.CTkLabel(song_row, text=f"{bullet}{song}", 
                             font=("Arial", 14), text_color=text_color, anchor="w")
    song_label.pack(side="left", fill="x")

# Button container
button_frame = ctk.CTkFrame(currently_playing_frame, fg_color="#131B2E")
button_frame.pack(pady=(20, 0))

# Play button
play_button = ctk.CTkButton(button_frame, text="▶ PLAY", font=("Arial", 14, "bold"), 
                           fg_color="#B146EC", hover_color="#9333EA", 
                           corner_radius=5, height=40, width=140)
play_button.pack(side="left", padx=10)

# Refresh button
refresh_button = ctk.CTkButton(button_frame, text="⟳ REFRESH", font=("Arial", 14, "bold"), 
                              fg_color="#3A3A5E", hover_color="#4A4A6E", 
                              corner_radius=5, height=40, width=140)
refresh_button.pack(side="left", padx=10)

# ---------------- Run Application ----------------
root.mainloop()