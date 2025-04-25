import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import hashlib
import os

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

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Login Function -------------------
def login_admin():
    """Authenticate admin and open admin dashboard if successful"""
    email = email_entry.get()
    password = password_entry.get()

    if not email or not password:
        messagebox.showwarning("Input Error", "Please enter both email and password.")
        return
    
    # Hash the password for security
    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        if not connection:
            return
            
        cursor = connection.cursor()
        cursor.execute(
            "SELECT user_id, first_name, last_name FROM Users WHERE email = %s AND password = %s AND is_admin = 1",
            (email, hashed_password)
        )
        admin = cursor.fetchone()

        if admin:
            admin_id, first_name, last_name = admin
            messagebox.showinfo("Success", f"Welcome Admin {first_name} {last_name}!")
            
            # Save admin ID to a file for session persistence
            with open("current_admin.txt", "w") as f:
                f.write(str(admin_id))
                
            root.destroy()
            open_admin_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid Email or Password or Not an Admin Account.")
    
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Navigation Functions -------------------
def open_admin_dashboard():
    """Open the admin dashboard after successful login"""
    try:
        subprocess.Popen(["python", "admin.py"])
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open admin dashboard: {e}")

def open_user_login():
    """Open the regular user login page"""
    try:
        subprocess.Popen(["python", "login.py"])
        root.destroy()  # Close current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open login page: {e}")

# ---------------- Main Application Window ----------------
try:
    # Create temp directory for temporary files if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    
    # Main window - adjusted to match the image proportions
    ctk.set_appearance_mode("dark")  # Dark mode
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Online Music System - Admin Login")
    root.geometry("700x500")  # Changed to match image proportions
    root.resizable(False, False)

    # Main Frame with rounded corners
    main_frame = ctk.CTkFrame(root, corner_radius=20)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Left Side - Branding (adjusted color to match image)
    left_frame = ctk.CTkFrame(main_frame, fg_color="#B146EC", width=350, height=480, corner_radius=20)
    left_frame.pack(side="left", fill="both")

    # Title on the left side - adjusted position
    title_label = ctk.CTkLabel(left_frame, text="Admin\nControl Panel",
                              font=("Arial", 36, "bold"), text_color="white")
    title_label.place(relx=0.5, rely=0.22, anchor="center")

    # Description text below title - adjusted position
    desc_label = ctk.CTkLabel(left_frame, text="Manage your online music system.\nAdd songs, manage users,\nview statistics and more.",
                              font=("Arial", 14), text_color="white", justify="center")
    desc_label.place(relx=0.5, rely=0.40, anchor="center")

    # Add admin icon
    ctk.CTkLabel(left_frame, text="👨‍💼", font=("Arial", 40), text_color="white").place(relx=0.5, rely=0.75, anchor="center")

    # Right Side - Login Form
    right_frame = ctk.CTkFrame(main_frame, fg_color="white", width=350, height=480, corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)

    # Create a container for the right side content with proper padding
    content_frame = ctk.CTkFrame(right_frame, fg_color="white")
    content_frame.pack(fill="both", expand=True, padx=40, pady=40)

    # Admin Login title
    welcome_label = ctk.CTkLabel(content_frame, text="Admin Login", 
                                font=("Arial", 28, "bold"), text_color="#B146EC")
    welcome_label.pack(anchor="w", pady=(5, 0))

    # Subtitle
    subtitle_label = ctk.CTkLabel(content_frame, text="Login with admin credentials to manage the system.",
                                 font=("Arial", 12), text_color="gray")
    subtitle_label.pack(anchor="w", pady=(0, 30))

    # Email Address label
    email_label = ctk.CTkLabel(content_frame, text="Email Address", 
                              font=("Arial", 14, "bold"), text_color="#333333")
    email_label.pack(anchor="w", pady=(0, 5))

    # Email entry with proper icon placement
    email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    email_frame.pack(fill="x", pady=(0, 15))
    
    email_entry = ctk.CTkEntry(email_frame, font=("Arial", 12), 
                              height=45, corner_radius=8,
                              border_width=1, border_color="#DDDDDD",
                              fg_color="white", text_color="black",
                              placeholder_text="admin@music.com")
    email_entry.pack(fill="x", side="left", expand=True)
    
    email_icon = ctk.CTkLabel(email_frame, text="✉️", font=("Arial", 14), fg_color="transparent")
    email_icon.pack(side="right", padx=(0, 10))

    # Password label
    password_label = ctk.CTkLabel(content_frame, text="Password", 
                                 font=("Arial", 14, "bold"), text_color="#333333")
    password_label.pack(anchor="w", pady=(5, 5))

    # Password entry with proper icon placement
    password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    password_frame.pack(fill="x", pady=(0, 15))
    
    password_entry = ctk.CTkEntry(password_frame, font=("Arial", 12), 
                                 height=45, corner_radius=8, 
                                 border_width=1, border_color="#DDDDDD",
                                 fg_color="white", text_color="black", 
                                 show="*",
                                 placeholder_text="admin123")
    password_entry.pack(fill="x", side="left", expand=True)
    
    password_icon = ctk.CTkLabel(password_frame, text="🔒", font=("Arial", 14), fg_color="transparent")
    password_icon.pack(side="right", padx=(0, 10))

    # Login button with login icon
    login_button = ctk.CTkButton(content_frame, text="Admin Login", 
                                font=("Arial", 14, "bold"),
                                fg_color="#B146EC", hover_color="#9333EA", 
                                text_color="white", corner_radius=8, 
                                height=45, command=login_admin)
    login_button.pack(fill="x", pady=(10, 25))
    
    # Add an arrow icon to the login button
    login_icon_label = ctk.CTkLabel(login_button, text="→", font=("Arial", 16, "bold"), text_color="white")
    login_icon_label.place(relx=0.9, rely=0.5, anchor="e")

    # Regular user login link
    user_login_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    user_login_frame.pack(pady=0)

    user_login_label = ctk.CTkLabel(user_login_frame, text="Not an admin? ", 
                                font=("Arial", 12), text_color="#333333")
    user_login_label.pack(side="left")

    # "User Login" in purple and bold
    login_label = ctk.CTkLabel(user_login_frame, text="User Login", 
                               font=("Arial", 12, "bold"), 
                               text_color="#B146EC", cursor="hand2")
    login_label.pack(side="left")
    login_label.bind("<Button-1>", lambda e: open_user_login())

    # Start the main loop
    root.mainloop()

except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")  # This keeps console open