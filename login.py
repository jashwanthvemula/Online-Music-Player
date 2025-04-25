import customtkinter as ctk
from tkinter import messagebox
import subprocess  # To open signup.py and home.py
import mysql.connector
import hashlib
import os

# Initialize CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Login Function -------------------
def login_user():
    """Authenticate user and open home page if successful"""
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
            "SELECT user_id, first_name, last_name FROM Users WHERE email = %s AND password = %s",
            (email, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            user_id, first_name, last_name = user
            messagebox.showinfo("Success", f"Welcome {first_name} {last_name}!")
            
            # Create user files directory if not exists
            user_dir = f"temp/user_{user_id}"
            os.makedirs(user_dir, exist_ok=True)
            
            # Save user ID to a file for session persistence
            with open("current_user.txt", "w") as f:
                f.write(str(user_id))
                
            root.destroy()
            open_home_page()
        else:
            messagebox.showerror("Login Failed", "Invalid Email or Password.")
    
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Navigation Functions -------------------
def open_home_page():
    """Open the home page after successful login"""
    try:
        subprocess.Popen(["python", "home.py"])
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open home page: {e}")

def open_signup_page():
    """Open the signup page"""
    try:
        subprocess.Popen(["python", "signup.py"])
        root.destroy()  # Close current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open signup page: {e}")

# ---------------- Main Application Window ----------------
try:
    # Create temp directory for temporary files if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    
    # Main window with adjusted proportions
    root = ctk.CTk()
    root.title("Online Music System - Login")
    root.geometry("700x500")
    root.resizable(False, False)

    # Main Frame with rounded corners
    main_frame = ctk.CTkFrame(root, corner_radius=20)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Left Side - Branding (adjusted color to match image)
    left_frame = ctk.CTkFrame(main_frame, fg_color="#B146EC", width=350, height=480, corner_radius=20)
    left_frame.pack(side="left", fill="both")

    # Title on the left side - adjusted position
    title_label = ctk.CTkLabel(left_frame, text="Online Music\nSystem",
                              font=("Arial", 36, "bold"), text_color="white")
    title_label.place(relx=0.5, rely=0.22, anchor="center")

    # Description text below title - adjusted position
    desc_label = ctk.CTkLabel(left_frame, text="Enjoy unlimited *ad-free music*\nanytime, anywhere. Access premium\nplaylists and high-quality audio\nstreaming.",
                              font=("Arial", 14), text_color="white", justify="center")
    desc_label.place(relx=0.5, rely=0.40, anchor="center")

    # Add music bird illustration
    ctk.CTkLabel(left_frame, text="🎵🐦", font=("Arial", 40), text_color="white").place(relx=0.5, rely=0.75, anchor="center")

    # Right Side - Login Form
    right_frame = ctk.CTkFrame(main_frame, fg_color="white", width=350, height=480, corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)

    # Create a container for the right side content with proper padding
    content_frame = ctk.CTkFrame(right_frame, fg_color="white")
    content_frame.pack(fill="both", expand=True, padx=40, pady=40)

    # Welcome Back! label
    welcome_label = ctk.CTkLabel(content_frame, text="Welcome Back!", 
                                font=("Arial", 28, "bold"), text_color="#B146EC")
    welcome_label.pack(anchor="w", pady=(5, 0))

    # Subtitle
    subtitle_label = ctk.CTkLabel(content_frame, text="Login to explore a world of non-stop music.",
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
                              fg_color="white", text_color="black")
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
                                 show="*")
    password_entry.pack(fill="x", side="left", expand=True)
    
    password_icon = ctk.CTkLabel(password_frame, text="🔒", font=("Arial", 14), fg_color="transparent")
    password_icon.pack(side="right", padx=(0, 10))

    # Remember Me & Forgot Password row - proper spacing
    remember_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    remember_frame.pack(fill="x", pady=(5, 20))

    # Remember me checkbox
    remember_var = ctk.BooleanVar()
    remember_check = ctk.CTkCheckBox(remember_frame, text="Remember me", 
                                    variable=remember_var, 
                                    text_color="#333333", font=("Arial", 12),
                                    fg_color="#B146EC", border_color="#DDDDDD",
                                    checkbox_height=20, checkbox_width=20)
    remember_check.pack(side="left")

    # Forgot password link
    forgot_pass = ctk.CTkLabel(remember_frame, text="Forgot password?", 
                              font=("Arial", 12), text_color="gray",
                              cursor="hand2")
    forgot_pass.pack(side="right")

    # Login button with login icon
    login_button = ctk.CTkButton(content_frame, text="Login", 
                                font=("Arial", 14, "bold"),
                                fg_color="#B146EC", hover_color="#9333EA", 
                                text_color="white", corner_radius=8, 
                                height=45, command=login_user)
    login_button.pack(fill="x", pady=(10, 25))
    
    # Add an arrow icon to the login button (simulating the icon in the image)
    login_icon_label = ctk.CTkLabel(login_button, text="→", font=("Arial", 16, "bold"), text_color="white")
    login_icon_label.place(relx=0.9, rely=0.5, anchor="e")

    # Don't have an account text
    signup_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    signup_frame.pack(pady=0)

    account_label = ctk.CTkLabel(signup_frame, text="Don't have an account? ", 
                                font=("Arial", 12), text_color="#333333")
    account_label.pack(side="left")

    # "Sign up" in purple and bold
    signup_label = ctk.CTkLabel(signup_frame, text="Sign up", 
                               font=("Arial", 12, "bold"), 
                               text_color="#B146EC", cursor="hand2")
    signup_label.pack(side="left")
    signup_label.bind("<Button-1>", lambda e: open_signup_page())

    # Start the main loop
    root.mainloop()

except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")  # This keeps the console open