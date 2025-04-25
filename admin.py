import customtkinter as ctk
from tkinter import messagebox, simpledialog
import mysql.connector
import subprocess
import os
import datetime

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
            open_login_page()
            return None
            
        with open("current_admin.txt", "r") as f:
            admin_id = f.read().strip()
            
        if not admin_id:
            messagebox.showerror("Error", "Admin ID not found!")
            open_login_page()
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
            open_login_page()
            return None
            
        return admin
        
    except Exception as e:
        print(f"Error getting admin info: {e}")
        return None
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_system_stats():
    """Get system statistics for the dashboard"""
    try:
        connection = connect_db()
        if not connection:
            return {
                "total_users": 0,
                "total_songs": 0,
                "total_playlists": 0,
                "total_downloads": 0
            }
            
        cursor = connection.cursor()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM Users")
        total_users = cursor.fetchone()[0]
        
        # Get song count
        cursor.execute("SELECT COUNT(*) FROM Songs")
        total_songs = cursor.fetchone()[0]
        
        # Get playlist count
        cursor.execute("SELECT COUNT(*) FROM Playlists")
        total_playlists = cursor.fetchone()[0]
        
        # Approximate downloads (listening history entries)
        cursor.execute("SELECT COUNT(*) FROM Listening_History")
        total_downloads = cursor.fetchone()[0]
        
        return {
            "total_users": total_users,
            "total_songs": total_songs,
            "total_playlists": total_playlists,
            "total_downloads": total_downloads
        }
        
    except mysql.connector.Error as e:
        print(f"Error getting system stats: {e}")
        return {
            "total_users": 0,
            "total_songs": 0,
            "total_playlists": 0,
            "total_downloads": 0
        }
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_recent_activities(limit=4):
    """Get recent system activities"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        # Get recent user registrations
        user_query = """
        SELECT 'user_registered' as activity_type, 
               CONCAT(first_name, ' ', last_name) as item,
               created_at as timestamp
        FROM Users
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        # Get recent song uploads
        song_query = """
        SELECT 'song_uploaded' as activity_type,
               CONCAT(s.title, ' - ', a.name) as item,
               s.upload_date as timestamp
        FROM Songs s
        JOIN Artists a ON s.artist_id = a.artist_id
        ORDER BY s.upload_date DESC
        LIMIT %s
        """
        
        # Get recent playlist creations
        playlist_query = """
        SELECT 'playlist_created' as activity_type,
               p.name as item,
               p.created_at as timestamp
        FROM Playlists p
        ORDER BY p.created_at DESC
        LIMIT %s
        """
        
        # Get recent listening activity (downloads)
        download_query = """
        SELECT 'song_played' as activity_type,
               CONCAT(s.title, ' - ', a.name) as item,
               lh.played_at as timestamp
        FROM Listening_History lh
        JOIN Songs s ON lh.song_id = s.song_id
        JOIN Artists a ON s.artist_id = a.artist_id
        ORDER BY lh.played_at DESC
        LIMIT %s
        """
        
        # Execute all queries
        cursor.execute(user_query, (limit,))
        users = cursor.fetchall()
        
        cursor.execute(song_query, (limit,))
        songs = cursor.fetchall()
        
        cursor.execute(playlist_query, (limit,))
        playlists = cursor.fetchall()
        
        cursor.execute(download_query, (limit,))
        downloads = cursor.fetchall()
        
        # Combine all activities
        all_activities = users + songs + playlists + downloads
        
        # Sort by timestamp (most recent first)
        all_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit to requested number
        all_activities = all_activities[:limit]
        
        # Format activities for display
        formatted_activities = []
        for activity in all_activities:
            activity_type = activity["activity_type"]
            item = activity["item"]
            timestamp = activity["timestamp"]
            
            # Calculate relative time
            time_diff = datetime.datetime.now() - timestamp
            if time_diff.days < 1:
                hours = time_diff.seconds // 3600
                minutes = (time_diff.seconds % 3600) // 60
                if hours > 0:
                    time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
                else:
                    time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            elif time_diff.days == 1:
                time_str = "Yesterday"
            else:
                time_str = f"{time_diff.days} days ago"
            
            # Format action based on activity type
            if activity_type == "user_registered":
                action = "👤 New user registered"
            elif activity_type == "song_uploaded":
                action = "🎵 New song uploaded"
            elif activity_type == "playlist_created":
                action = "📁 Playlist created"
            elif activity_type == "song_played":
                action = "⬇️ Song played"
            else:
                action = "🔄 System activity"
            
            formatted_activities.append((action, item, time_str))
        
        return formatted_activities
        
    except mysql.connector.Error as e:
        print(f"Error getting recent activities: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Admin Functions -------------------
def open_manage_users():
    """Open the manage users page"""
    try:
        subprocess.Popen(["python", "admin_users.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open manage users page: {e}")

def open_manage_songs():
    """Open the manage songs page"""
    try:
        subprocess.Popen(["python", "admin_songs.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open manage songs page: {e}")

def open_manage_playlists():
    """Open the manage playlists page"""
    try:
        subprocess.Popen(["python", "admin_playlists.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open manage playlists page: {e}")

def open_reports():
    """Open the reports and analytics page"""
    try:
        subprocess.Popen(["python", "admin_reports.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open reports page: {e}")

def open_login_page():
    """Logout and open the login page"""
    try:
        # Remove admin session file
        if os.path.exists("current_admin.txt"):
            os.remove("current_admin.txt")
            
        subprocess.Popen(["python", "login.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to logout: {e}")

def refresh_dashboard():
    """Refresh the dashboard data"""
    # Update stats
    stats = get_system_stats()
    
    # Update stat values
    user_count_label.configure(text=str(stats["total_users"]))
    song_count_label.configure(text=str(stats["total_songs"]))
    playlist_count_label.configure(text=str(stats["total_playlists"]))
    download_count_label.configure(text=str(stats["total_downloads"]))
    
    # Update recent activities
    # First, clear existing activities
    for widget in activity_list_frame.winfo_children():
        widget.destroy()
    
    # Get fresh activities
    activities = get_recent_activities()
    
    # Display activities
    if not activities:
        no_activity_label = ctk.CTkLabel(
            activity_list_frame, 
            text="No recent activities found", 
            font=("Arial", 12), 
            text_color="#A0A0A0"
        )
        no_activity_label.pack(pady=20)
    else:
        for action, item, time in activities:
            activity_item = ctk.CTkFrame(activity_list_frame, fg_color="#1A1A2E", height=40)
            activity_item.pack(fill="x", padx=10, pady=5)
            
            action_label = ctk.CTkLabel(activity_item, text=action, font=("Arial", 12, "bold"), text_color="white")
            action_label.pack(side="left", padx=10)
            
            item_label = ctk.CTkLabel(activity_item, text=item, font=("Arial", 12), text_color="#A0A0A0")
            item_label.pack(side="left", padx=10)
            
            time_label = ctk.CTkLabel(activity_item, text=time, font=("Arial", 12), text_color="#B146EC")
            time_label.pack(side="right", padx=10)

# ------------------- Initialize App -------------------
try:
    # Verify admin privileges
    admin = get_admin_info()
    if not admin:
        # Redirect to login if not admin
        open_login_page()
        exit()

    # ---------------- Initialize App ----------------
    ctk.set_appearance_mode("dark")  # Dark mode
    ctk.set_default_color_theme("blue")  # Default theme

    root = ctk.CTk()
    root.title("Online Music System - Admin Dashboard")
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

    # Sidebar Menu Items - Admin specific options with navigation commands
    dashboard_btn = ctk.CTkButton(sidebar, text="📊 Dashboard", font=("Arial", 14), 
                                fg_color="#111827", hover_color="#1E293B", text_color="white",
                                anchor="w", corner_radius=0, height=40)
    dashboard_btn.pack(fill="x", pady=5, padx=10)

    manage_users_btn = ctk.CTkButton(sidebar, text="👥 Manage Users", font=("Arial", 14), 
                                    fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                                    anchor="w", corner_radius=0, height=40, command=open_manage_users)
    manage_users_btn.pack(fill="x", pady=5, padx=10)

    manage_songs_btn = ctk.CTkButton(sidebar, text="🎵 Manage Songs", font=("Arial", 14), 
                                    fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                                    anchor="w", corner_radius=0, height=40, command=open_manage_songs)
    manage_songs_btn.pack(fill="x", pady=5, padx=10)

    manage_playlists_btn = ctk.CTkButton(sidebar, text="📁 Manage Playlists", font=("Arial", 14), 
                                        fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                                        anchor="w", corner_radius=0, height=40, command=open_manage_playlists)
    manage_playlists_btn.pack(fill="x", pady=5, padx=10)

    reports_btn = ctk.CTkButton(sidebar, text="📈 Reports & Analytics", font=("Arial", 14), 
                              fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                              anchor="w", corner_radius=0, height=40, command=open_reports)
    reports_btn.pack(fill="x", pady=5, padx=10)

    logout_btn = ctk.CTkButton(sidebar, text="🚪 Logout", font=("Arial", 14), 
                             fg_color="#111827", hover_color="#1E293B", text_color="#A0A0A0",
                             anchor="w", corner_radius=0, height=40, command=open_login_page)
    logout_btn.pack(fill="x", pady=5, padx=10)

    # ---------------- Main Content ----------------
    content_frame = ctk.CTkFrame(main_frame, fg_color="#131B2E", corner_radius=10)
    content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # Header with username
    header_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=40)
    header_frame.pack(fill="x", padx=20, pady=(20, 0))

    # Left side: Admin Dashboard
    dashboard_label = ctk.CTkLabel(header_frame, text="Admin Dashboard", font=("Arial", 24, "bold"), text_color="white")
    dashboard_label.pack(side="left")

    # Right side: Admin Name
    admin_label = ctk.CTkLabel(header_frame, 
                             text=f"Hello, {admin['first_name']} {admin['last_name']}!", 
                             font=("Arial", 14), text_color="#A0A0A0")
    admin_label.pack(side="right")

    # Refresh button on header
    refresh_btn = ctk.CTkButton(header_frame, text="🔄 Refresh", font=("Arial", 12), 
                              fg_color="#2563EB", hover_color="#1D4ED8", 
                              text_color="white", corner_radius=5, 
                              width=100, height=30, command=refresh_dashboard)
    refresh_btn.pack(side="right", padx=15)

    # ---------------- Quick Overview Section ----------------
    overview_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    overview_frame.pack(fill="x", padx=20, pady=(40, 20))

    # Section title
    overview_title = ctk.CTkLabel(overview_frame, text="Quick Overview 📊", 
                                 font=("Arial", 20, "bold"), text_color="#B146EC")
    overview_title.pack(anchor="w", pady=(0, 15))

    # Stats grid container
    stats_frame = ctk.CTkFrame(overview_frame, fg_color="#131B2E")
    stats_frame.pack(fill="x")

    # Get initial stats
    stats = get_system_stats()

    # Stats cards
    stat_colors = [
        ("👥 Total Users", "#16A34A"),  # Green
        ("🎵 Total Songs", "#2563EB"),  # Blue
        ("📁 Playlists Created", "#FACC15"),  # Yellow
        ("⬇️ Total Plays", "#DC2626")  # Red
    ]

    # Create global references to stat labels for updating
    user_count_label = None
    song_count_label = None
    playlist_count_label = None
    download_count_label = None

    # Create stats cards
    for i, (name, color) in enumerate(stat_colors):
        stat_card = ctk.CTkFrame(stats_frame, fg_color="#1A1A2E", corner_radius=10, width=160, height=90)
        stat_card.pack(side="left", padx=10, expand=True)
        stat_card.pack_propagate(False)  # Keep fixed size
        
        # Center the content vertically
        stat_icon = ctk.CTkLabel(stat_card, text=name, font=("Arial", 12, "bold"), text_color="white")
        stat_icon.pack(pady=(20, 5))
        
        # Get the correct stat value
        if i == 0:  # Users
            stat_value = stats["total_users"]
            user_count_label = ctk.CTkLabel(stat_card, text=str(stat_value), font=("Arial", 22, "bold"), text_color=color)
            user_count_label.pack()
        elif i == 1:  # Songs
            stat_value = stats["total_songs"]
            song_count_label = ctk.CTkLabel(stat_card, text=str(stat_value), font=("Arial", 22, "bold"), text_color=color)
            song_count_label.pack()
        elif i == 2:  # Playlists
            stat_value = stats["total_playlists"]
            playlist_count_label = ctk.CTkLabel(stat_card, text=str(stat_value), font=("Arial", 22, "bold"), text_color=color)
            playlist_count_label.pack()
        elif i == 3:  # Downloads/Plays
            stat_value = stats["total_downloads"]
            download_count_label = ctk.CTkLabel(stat_card, text=str(stat_value), font=("Arial", 22, "bold"), text_color=color)
            download_count_label.pack()

    # ---------------- Manage Actions Section ----------------
    actions_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    actions_frame.pack(fill="x", padx=20, pady=(20, 0))

    # Section title
    actions_title = ctk.CTkLabel(actions_frame, text="Manage System ⚙️", 
                                font=("Arial", 20, "bold"), text_color="#B146EC")
    actions_title.pack(anchor="w", pady=(0, 15))

    # Action buttons container
    buttons_frame = ctk.CTkFrame(actions_frame, fg_color="#131B2E")
    buttons_frame.pack(fill="x")

    # Action buttons with commands
    manage_users_action = ctk.CTkButton(buttons_frame, text="👥 Manage Users", 
                                       font=("Arial", 14, "bold"), 
                                       fg_color="#B146EC", hover_color="#9333EA", 
                                       text_color="white", height=50, corner_radius=8,
                                       command=open_manage_users)
    manage_users_action.pack(side="left", padx=10, expand=True)

    manage_songs_action = ctk.CTkButton(buttons_frame, text="🎵 Manage Songs", 
                                       font=("Arial", 14, "bold"), 
                                       fg_color="#2563EB", hover_color="#1D4ED8", 
                                       text_color="white", height=50, corner_radius=8,
                                       command=open_manage_songs)
    manage_songs_action.pack(side="left", padx=10, expand=True)

    manage_playlists_action = ctk.CTkButton(buttons_frame, text="📁 Manage Playlists", 
                                          font=("Arial", 14, "bold"), 
                                          fg_color="#16A34A", hover_color="#15803D", 
                                          text_color="white", height=50, corner_radius=8,
                                          command=open_manage_playlists)
    manage_playlists_action.pack(side="left", padx=10, expand=True)

    # ---------------- Recent Activity Section ----------------
    activity_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E")
    activity_frame.pack(fill="both", expand=True, padx=20, pady=(20, 20))

    # Section title
    activity_title = ctk.CTkLabel(activity_frame, text="Recent Activity 📝", 
                                 font=("Arial", 20, "bold"), text_color="#B146EC")
    activity_title.pack(anchor="w", pady=(0, 15))

    # Activity list container
    activity_list_frame = ctk.CTkFrame(activity_frame, fg_color="#1A1A2E", corner_radius=10)
    activity_list_frame.pack(fill="both", expand=True)

    # Get recent activities
    activities = get_recent_activities()

    # Display activities
    if not activities:
        no_activity_label = ctk.CTkLabel(
            activity_list_frame, 
            text="No recent activities found", 
            font=("Arial", 12), 
            text_color="#A0A0A0"
        )
        no_activity_label.pack(pady=20)
    else:
        for action, item, time in activities:
            activity_item = ctk.CTkFrame(activity_list_frame, fg_color="#1A1A2E", height=40)
            activity_item.pack(fill="x", padx=10, pady=5)
            
            action_label = ctk.CTkLabel(activity_item, text=action, font=("Arial", 12, "bold"), text_color="white")
            action_label.pack(side="left", padx=10)
            
            item_label = ctk.CTkLabel(activity_item, text=item, font=("Arial", 12), text_color="#A0A0A0")
            item_label.pack(side="left", padx=10)
            
            time_label = ctk.CTkLabel(activity_item, text=time, font=("Arial", 12), text_color="#B146EC")
            time_label.pack(side="right", padx=10)

    # ---------------- Run Application ----------------
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"Error in admin.py: {e}")
    traceback.print_exc()
    messagebox.showerror("Error", f"An error occurred: {e}")
    input("Press Enter to exit...")  # This keeps console open