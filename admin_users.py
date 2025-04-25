import customtkinter as ctk
from tkinter import messagebox, simpledialog, ttk
import mysql.connector
import subprocess
import os
import hashlib

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

def get_all_users():
    """Get all users from the database"""
    try:
        connection = connect_db()
        if not connection:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.is_admin, u.created_at,
               COUNT(DISTINCT p.playlist_id) as playlist_count,
               COUNT(DISTINCT lh.history_id) as listening_count
        FROM Users u
        LEFT JOIN Playlists p ON u.user_id = p.user_id
        LEFT JOIN Listening_History lh ON u.user_id = lh.user_id
        GROUP BY u.user_id
        ORDER BY u.created_at DESC
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        return users
        
    except mysql.connector.Error as e:
        print(f"Error fetching users: {e}")
        return []
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def delete_user(user_id):
    """Delete a user from the database"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if this is an admin user
        cursor.execute("SELECT is_admin FROM Users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            messagebox.showerror("Error", "Cannot delete an admin user.")
            return False
        
        # The foreign key constraints with ON DELETE CASCADE should
        # automatically delete related records in other tables
        cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
        
        connection.commit()
        return True
        
    except mysql.connector.Error as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def toggle_admin_status(user_id, current_status):
    """Toggle user's admin status"""
    try:
        connection = connect_db()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Toggle the admin status
        new_status = 0 if current_status else 1
        
        cursor.execute(
            "UPDATE Users SET is_admin = %s WHERE user_id = %s",
            (new_status, user_id)
        )
        
        connection.commit()
        return True
        
    except mysql.connector.Error as e:
        print(f"Error updating admin status: {e}")
        return False
    finally:
        if 'connection' in locals() and connection and connection.is_connected():
            cursor.close()
            connection.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_new_user(first_name, last_name, email, password, is_admin=0):
    """Add a new user to the database"""
    try:
        connection = connect_db()
        if not connection:
            return None
            
        cursor = connection.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        if cursor.fetchone():
            messagebox.showerror("Error", "A user with this email already exists.")
            return None
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Insert user
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, email, password, is_admin) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, hashed_password, is_admin)
        )
        
        # Get new user ID
        new_user_id = cursor.lastrowid
        
        # Create default playlist for user
        cursor.execute(
            "INSERT INTO Playlists (user_id, name, description) VALUES (%s, %s, %s)",
            (new_user_id, "Favorites", "My favorite songs")
        )
        
        connection.commit()
        return new_user_id
        
    except mysql.connector.Error as e:
        print(f"Error adding user: {e}")
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
def refresh_user_list():
    """Refresh the user list display"""
    # Clear the treeview
    for item in users_tree.get_children():
        users_tree.delete(item)
    
    # Get updated users
    users = get_all_users()
    
    # Add users to treeview
    for i, user in enumerate(users, 1):
        # Format admin status
        admin_status = "Yes" if user["is_admin"] else "No"
        
        # Format created date
        created_date = user["created_at"].strftime("%Y-%m-%d")
        
        users_tree.insert(
            "", "end", 
            values=(
                i,
                f"{user['first_name']} {user['last_name']}",
                user["email"],
                admin_status,
                created_date,
                user["playlist_count"],
                user["listening_count"],
                user["user_id"]
            )
        )
    
    # Update stats
    stats_label.configure(text=f"Total Users: {len(users_tree.get_children())}")

def confirm_delete_user():
    """Confirm and delete selected user"""
    selected = users_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Required", "Please select a user to delete.")
        return
    
    # Get the user ID from the selected item
    user_id = users_tree.item(selected, 'values')[-1]  # Last column contains user_id
    user_name = users_tree.item(selected, 'values')[1]  # Second column contains name
    
    # Confirmation dialog
    confirm = messagebox.askyesno(
        "Confirm Delete", 
        f"Are you sure you want to delete the user '{user_name}'?\n\nThis will delete ALL data associated with this user, including playlists and listening history.\n\nThis action cannot be undone."
    )
    
    if confirm:
        if delete_user(user_id):
            messagebox.showinfo("Success", f"User '{user_name}' deleted successfully!")
            refresh_user_list()
        else:
            messagebox.showerror("Error", f"Failed to delete user '{user_name}'.")

def toggle_selected_admin_status():
    """Toggle admin status for selected user"""
    selected = users_tree.selection()
    if not selected:
        messagebox.showwarning("Selection Required", "Please select a user to modify.")
        return
    
    # Get the user info from the selected item
    user_id = users_tree.item(selected, 'values')[-1]  # Last column contains user_id
    user_name = users_tree.item(selected, 'values')[1]  # Second column contains name
    current_status = users_tree.item(selected, 'values')[3] == "Yes"  # Fourth column is admin status
    
    # New status message
    new_status_msg = "remove admin privileges from" if current_status else "grant admin privileges to"
    
    # Confirmation dialog
    confirm = messagebox.askyesno(
        "Confirm Admin Status Change", 
        f"Are you sure you want to {new_status_msg} '{user_name}'?"
    )
    
    if confirm:
        if toggle_admin_status(user_id, current_status):
            status_msg = "removed from" if current_status else "granted to"
            messagebox.showinfo("Success", f"Admin privileges {status_msg} '{user_name}' successfully!")
            refresh_user_list()
        else:
            messagebox.showerror("Error", f"Failed to update admin status for '{user_name}'.")

def handle_add_user():
    """Display dialog to add a new user"""
    # Create dialog
    add_dialog = ctk.CTkToplevel(root)
    add_dialog.title("Add New User")
    add_dialog.geometry("400x450")
    add_dialog.transient(root)
    add_dialog.grab_set()
    
    # Center the dialog
    add_dialog.update_idletasks()
    width = add_dialog.winfo_width()
    height = add_dialog.winfo_height()
    x = (add_dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (add_dialog.winfo_screenheight() // 2) - (height // 2)
    add_dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    # Dialog title
    ctk.CTkLabel(
        add_dialog, 
        text="Add New User", 
        font=("Arial", 18, "bold")
    ).pack(pady=(20, 20))
    
    # First name input
    first_name_frame = ctk.CTkFrame(add_dialog)
    first_name_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(first_name_frame, text="First Name:", width=100).pack(side="left")
    first_name_var = ctk.StringVar()
    first_name_entry = ctk.CTkEntry(first_name_frame, textvariable=first_name_var, width=200)
    first_name_entry.pack(side="left", padx=5)
    
    # Last name input
    last_name_frame = ctk.CTkFrame(add_dialog)
    last_name_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(last_name_frame, text="Last Name:", width=100).pack(side="left")
    last_name_var = ctk.StringVar()
    last_name_entry = ctk.CTkEntry(last_name_frame, textvariable=last_name_var, width=200)
    last_name_entry.pack(side="left", padx=5)
    
    # Email input
    email_frame = ctk.CTkFrame(add_dialog)
    email_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(email_frame, text="Email:", width=100).pack(side="left")
    email_var = ctk.StringVar()
    email_entry = ctk.CTkEntry(email_frame, textvariable=email_var, width=200)
    email_entry.pack(side="left", padx=5)
    
    # Password input
    password_frame = ctk.CTkFrame(add_dialog)
    password_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(password_frame, text="Password:", width=100).pack(side="left")
    password_var = ctk.StringVar()
    password_entry = ctk.CTkEntry(password_frame, textvariable=password_var, width=200, show="*")
    password_entry.pack(side="left", padx=5)
    
    # Confirm password input
    confirm_password_frame = ctk.CTkFrame(add_dialog)
    confirm_password_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(confirm_password_frame, text="Confirm:", width=100).pack(side="left")
    confirm_password_var = ctk.StringVar()
    confirm_password_entry = ctk.CTkEntry(confirm_password_frame, textvariable=confirm_password_var, width=200, show="*")
    confirm_password_entry.pack(side="left", padx=5)
    
    # Admin checkbox
    admin_frame = ctk.CTkFrame(add_dialog)
    admin_frame.pack(fill="x", padx=20, pady=10)
    
    admin_var = ctk.BooleanVar(value=False)
    admin_checkbox = ctk.CTkCheckBox(
        admin_frame,
        text="Grant Admin Privileges",
        variable=admin_var
    )
    admin_checkbox.pack(pady=5)
    
    # Add user function
    def do_add_user():
        # Get form values
        first_name = first_name_var.get().strip()
        last_name = last_name_var.get().strip()
        email = email_var.get().strip()
        password = password_var.get()
        confirm_password = confirm_password_var.get()
        is_admin = 1 if admin_var.get() else 0
        
        # Validate inputs
        if not first_name or not last_name or not email or not password:
            messagebox.showwarning("Input Error", "All fields are required.")
            return
            
        if password != confirm_password:
            messagebox.showwarning("Password Error", "Passwords do not match.")
            return
            
        if len(password) < 8:
            messagebox.showwarning("Password Error", "Password must be at least 8 characters long.")
            return
            
        # Email validation
        import re
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, email):
            messagebox.showwarning("Email Error", "Please enter a valid email address.")
            return
        
        # Add user to database
        new_user_id = add_new_user(first_name, last_name, email, password, is_admin)
        
        if new_user_id:
            messagebox.showinfo("Success", f"User '{first_name} {last_name}' added successfully!")
            add_dialog.destroy()
            refresh_user_list()
        else:
            messagebox.showerror("Error", "Failed to add user. Check console for details.")
    
    # Add button
    add_btn = ctk.CTkButton(
        add_dialog,
        text="Add User",
        command=do_add_user,
        fg_color="#B146EC",
        hover_color="#9333EA"
    )
    add_btn.pack(pady=20)

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
    root.title("Admin - Manage Users")
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
        text="Manage Users", 
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
    
    # Add user button
    add_btn = ctk.CTkButton(
        action_frame,
        text="+ Add New User",
        command=handle_add_user,
        fg_color="#16A34A",
        hover_color="#15803D",
        height=40
    )
    add_btn.pack(side="left", padx=(0, 10))
    
    # Delete user button
    delete_btn = ctk.CTkButton(
        action_frame,
        text="🗑️ Delete Selected User",
        command=confirm_delete_user,
        fg_color="#DC2626",
        hover_color="#B91C1C",
        height=40
    )
    delete_btn.pack(side="left", padx=(0, 10))
    
    # Toggle admin button
    toggle_admin_btn = ctk.CTkButton(
        action_frame,
        text="👑 Toggle Admin Status",
        command=toggle_selected_admin_status,
        fg_color="#FACC15",
        hover_color="#CA8A04",
        text_color="black",
        height=40
    )
    toggle_admin_btn.pack(side="left")
    
    # Refresh button
    refresh_btn = ctk.CTkButton(
        action_frame,
        text="🔄 Refresh List",
        command=refresh_user_list,
        fg_color="#B146EC",
        hover_color="#9333EA",
        height=40
    )
    refresh_btn.pack(side="right")
    
    # Users list with scrollbar
    users_frame = ctk.CTkFrame(content_frame, fg_color="#1A1A2E")
    users_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    # Create Treeview with ttk.Scrollbar
    tree_frame = ctk.CTkFrame(users_frame)
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
    users_tree = ttk.Treeview(
        tree_frame,
        columns=("id", "name", "email", "admin", "created", "playlists", "history", "user_id"),
        show="headings",
        height=20,
        yscrollcommand=tree_scroll.set
    )
    users_tree.pack(fill="both", expand=True)
    
    # Configure scrollbar
    tree_scroll.config(command=users_tree.yview)
    
    # Format columns
    users_tree.heading("id", text="#")
    users_tree.heading("name", text="Name")
    users_tree.heading("email", text="Email")
    users_tree.heading("admin", text="Admin")
    users_tree.heading("created", text="Created")
    users_tree.heading("playlists", text="Playlists")
    users_tree.heading("history", text="Plays")
    users_tree.heading("user_id", text="ID")
    
    # Set column widths and alignment
    users_tree.column("id", width=40, anchor="center")
    users_tree.column("name", width=180, anchor="w")
    users_tree.column("email", width=200, anchor="w")
    users_tree.column("admin", width=80, anchor="center")
    users_tree.column("created", width=100, anchor="center")
    users_tree.column("playlists", width=80, anchor="center")
    users_tree.column("history", width=80, anchor="center")
    users_tree.column("user_id", width=50, anchor="center")
    
    # Statistics footer
    stats_frame = ctk.CTkFrame(content_frame, fg_color="#131B2E", height=30)
    stats_frame.pack(fill="x", padx=20, pady=(0, 10))
    
    stats_label = ctk.CTkLabel(
        stats_frame,
        text="Loading users...",
        font=("Arial", 12),
        text_color="#A0A0A0"
    )
    stats_label.pack(side="left")
    
    # Load users after the UI is created
    root.after(100, refresh_user_list)
    
    root.mainloop()
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
    messagebox.showerror("Error", f"An error occurred: {e}")