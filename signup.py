import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import hashlib
import subprocess  # To open login.py
import os

# ------------------- Database Connection -------------------
def connect_db():
    """Connect to the MySQL database"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Replace with your MySQL username
            password="new_password",  # Replace with your MySQL password
            database="online_music_system"  # Replace with your database name
        )
        return connection
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection Error", 
                            f"Failed to connect to database: {err}")
        return None

# ------------------- Password Hashing -------------------
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Validation Functions -------------------
def validate_email(email):
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Password validation - at least 8 characters"""
    return len(password) >= 8

# ------------------- Sign Up Function -------------------
def signup_user():
    """Register a new user in the database"""
    full_name = fullname_entry.get()
    email = email_entry.get()
    password = password_entry.get()
    confirm_password = confirm_password_entry.get()

    # Check if any fields are empty
    if not full_name or not email or not password or not confirm_password:
        messagebox.showwarning("Input Error", "All fields are required.")
        return

    # Validate email format
    if not validate_email(email):
        messagebox.showwarning("Email Error", "Please enter a valid email address.")
        return

    # Validate password strength
    if not validate_password(password):
        messagebox.showwarning("Password Error", "Password must be at least 8 characters long.")
        return

    # Check if passwords match
    if password != confirm_password:
        messagebox.showwarning("Password Error", "Passwords do not match.")
        return

    # Split full name into first and last name (assuming space separator)
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Hash the password
    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        if not connection:
            return
            
        cursor = connection.cursor()

        # Check if email already exists
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        if cursor.fetchone():
            messagebox.showwarning("Registration Error", "This email is already registered.")
            return

        # Insert the user data into the database
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)",
            (first_name, last_name, email, hashed_password)
        )

        # Get the new user ID
        user_id = cursor.lastrowid

        # Create default playlist for the user
        cursor.execute(
            "INSERT INTO Playlists (user_id, name, description) VALUES (%s, %s, %s)",
            (user_id, "Favorites", "My favorite songs")
        )

        connection.commit()
        messagebox.showinfo("Success", "User registered successfully!")
        
        # After successful registration, redirect to login page
        open_login_page()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Open Login Page -------------------
def open_login_page():
    """Open the login page and close the signup page"""
    try:
        subprocess.Popen(["python", "login.py"])  # Open login.py after successful signup
        root.destroy()  # Close the current signup window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open login page: {e}")

# ------------------- Responsive Layout Functions -------------------
def adjust_layout_for_resolution(event=None):
    """Adjust layout based on current window size"""
    width = root.winfo_width()
    height = root.winfo_height()
    
    # Minimum functional size check
    if width < 500 or height < 400:
        return  # Too small to adjust meaningfully
    
    # Get the scale factors compared to the design resolution
    width_scale = width / 700
    height_scale = height / 500
    
    # Determine if we're in compact mode (window too small for side-by-side)
    compact_mode = width < 650
    
    if compact_mode:
        # Switch to stacked layout
        if left_frame.winfo_manager() == "pack":
            # First unpack both frames
            left_frame.pack_forget()
            right_frame.pack_forget()
            
            # Make left frame shorter for the brand
            left_frame.configure(height=150)
            
            # Re-pack in stacked mode
            left_frame.pack(fill="x", expand=False)
            right_frame.pack(fill="both", expand=True)
            
            # Adjust brand text layout
            title_label.place(relx=0.5, rely=0.5, anchor="center")
            desc_label.pack_forget()  # Hide description in compact mode
            bird_label.pack_forget()  # Hide bird emoji in compact mode
    else:
        # Switch to side-by-side layout
        if left_frame.winfo_manager() == "pack" and left_frame.winfo_height() != height:
            # First unpack both frames
            left_frame.pack_forget()
            right_frame.pack_forget()
            
            # Restore left frame size
            left_frame.configure(height=480)
            
            # Re-pack in side-by-side mode
            left_frame.pack(side="left", fill="both")
            right_frame.pack(side="right", fill="both", expand=True)
            
            # Restore brand text layout
            title_label.place(relx=0.5, rely=0.22, anchor="center")
            desc_label.place(relx=0.5, rely=0.40, anchor="center")
            bird_label.place(relx=0.5, rely=0.75, anchor="center")
    
    # Resize font sizes based on screen size
    font_scale = min(width_scale, height_scale)
    
    # Ensure font scale stays reasonable
    font_scale = max(0.8, min(font_scale, 1.2))
    
    # Update fonts for key elements
    title_label.configure(font=("Arial", int(36 * font_scale), "bold"))
    
    if not compact_mode:
        desc_label.configure(font=("Arial", int(14 * font_scale)))
        bird_label.configure(font=("Arial", int(40 * font_scale)))
    
    # Adjust form elements
    right_title_label.configure(font=("Arial", int(28 * font_scale), "bold"))
    subtitle_label.configure(font=("Arial", int(12 * font_scale)))
    
    # Update padding based on screen size
    content_frame.pack_configure(padx=int(40 * width_scale), pady=int(40 * height_scale))

# ----------------- Setup UI -----------------
try:
    # Create temp directory for temporary files if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    
    ctk.set_appearance_mode("light")  # Light Mode
    ctk.set_default_color_theme("blue")

    # Main window
    root = ctk.CTk()
    root.title("Online Music System - Sign Up")
    root.geometry("700x500")  # Default starting size
    root.minsize(500, 400)    # Minimum functional size
    
    # Main Frame with rounded corners
    main_frame = ctk.CTkFrame(root, corner_radius=20)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Left Side - Branding with purple color
    left_frame = ctk.CTkFrame(main_frame, fg_color="#B146EC", width=350, height=480, corner_radius=20)
    left_frame.pack(side="left", fill="both")

    # Title on the left side
    title_label = ctk.CTkLabel(left_frame, text="Online Music\nSystem",
                              font=("Arial", 36, "bold"), text_color="white")
    title_label.place(relx=0.5, rely=0.22, anchor="center")

    # Description text below title
    desc_label = ctk.CTkLabel(left_frame, 
                             text="Join now to experience unlimited\n*ad-free music*, create custom\nplaylists, and explore new songs.",
                             font=("Arial", 14), text_color="white", justify="center")
    desc_label.place(relx=0.5, rely=0.40, anchor="center")

    # Add music bird illustration (same as login page)
    bird_label = ctk.CTkLabel(left_frame, text="🎵🐦", font=("Arial", 40), text_color="white")
    bird_label.place(relx=0.5, rely=0.75, anchor="center")

    # Right Side - Signup Form
    right_frame = ctk.CTkFrame(main_frame, fg_color="white", width=350, height=480, corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)

    # Content container with padding
    content_frame = ctk.CTkFrame(right_frame, fg_color="white")
    content_frame.pack(fill="both", expand=True, padx=40, pady=40)

    # Create an Account title
    right_title_label = ctk.CTkLabel(content_frame, text="Create an Account", 
                              font=("Arial", 28, "bold"), text_color="#B146EC")
    right_title_label.pack(anchor="w", pady=(0, 0))

    # Subtitle
    subtitle_label = ctk.CTkLabel(content_frame, text="Sign up to start your journey into the world of music.",
                                 font=("Arial", 12), text_color="gray")
    subtitle_label.pack(anchor="w", pady=(0, 25))

    # Full Name label
    fullname_label = ctk.CTkLabel(content_frame, text="Full Name", 
                                 font=("Arial", 14, "bold"), text_color="#333333")
    fullname_label.pack(anchor="w", pady=(0, 5))

    # Full Name Entry with person icon
    fullname_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    fullname_frame.pack(fill="x", pady=(0, 15))

    fullname_entry = ctk.CTkEntry(fullname_frame, font=("Arial", 12), 
                                 height=45, corner_radius=8,
                                 border_width=1, border_color="#DDDDDD",
                                 fg_color="white", text_color="black")
    fullname_entry.pack(fill="x", side="left", expand=True)

    person_icon = ctk.CTkLabel(fullname_frame, text="👤", font=("Arial", 14), fg_color="transparent")
    person_icon.pack(side="right", padx=(0, 10))

    # Email Address label
    email_label = ctk.CTkLabel(content_frame, text="Email Address", 
                              font=("Arial", 14, "bold"), text_color="#333333")
    email_label.pack(anchor="w", pady=(0, 5))

    # Email Entry with envelope icon
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
    password_label.pack(anchor="w", pady=(0, 5))

    # Password Entry with lock icon
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

    # Confirm Password label
    confirm_password_label = ctk.CTkLabel(content_frame, text="Confirm Password", 
                                         font=("Arial", 14, "bold"), text_color="#333333")
    confirm_password_label.pack(anchor="w", pady=(0, 5))

    # Confirm Password Entry with lock icon
    confirm_password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    confirm_password_frame.pack(fill="x", pady=(0, 15))

    confirm_password_entry = ctk.CTkEntry(confirm_password_frame, font=("Arial", 12), 
                                         height=45, corner_radius=8, 
                                         border_width=1, border_color="#DDDDDD",
                                         fg_color="white", text_color="black", 
                                         show="*")
    confirm_password_entry.pack(fill="x", side="left", expand=True)

    confirm_password_icon = ctk.CTkLabel(confirm_password_frame, text="🔒", font=("Arial", 14), fg_color="transparent")
    confirm_password_icon.pack(side="right", padx=(0, 10))

    # Sign Up button with arrow icon (to match login button)
    signup_button = ctk.CTkButton(content_frame, text="Sign Up", 
                                 font=("Arial", 14, "bold"),
                                 fg_color="#B146EC", hover_color="#9333EA", 
                                 text_color="white", corner_radius=8, 
                                 height=45, command=signup_user)
    signup_button.pack(fill="x", pady=(10, 20))

    # Add an arrow icon to the signup button (matching login)
    signup_icon_label = ctk.CTkLabel(signup_button, text="→", font=("Arial", 16, "bold"), text_color="white")
    signup_icon_label.place(relx=0.9, rely=0.5, anchor="e")

    # Already have an account text
    login_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    login_frame.pack(pady=0)

    account_label = ctk.CTkLabel(login_frame, text="Already have an account? ", 
                                font=("Arial", 12), text_color="#333333")
    account_label.pack(side="left")

    login_label = ctk.CTkLabel(login_frame, text="Login", 
                              font=("Arial", 12, "bold"), 
                              text_color="#B146EC", cursor="hand2")
    login_label.pack(side="left")
    login_label.bind("<Button-1>", lambda e: open_login_page())
    
    # Set up the window resize event binding
    root.bind("<Configure>", adjust_layout_for_resolution)
    
    # Initial layout adjustment after rendering
    root.update_idletasks()
    adjust_layout_for_resolution()

    # Run the application
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")  # This keeps the console open