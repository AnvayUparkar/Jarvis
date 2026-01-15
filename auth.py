# auth.py - Authentication Module for Jarvis
# Handles user registration, login, and session management via Eel.

import eel
import sqlite3
import datetime
import traceback
from database import get_db_connection, DB_PATH

# ============================================================================
# BCRYPT DEPENDENCY CHECK
# ============================================================================
try:
    import bcrypt
    print("[AUTH] ✅ bcrypt module loaded successfully.")
except ImportError as e:
    print(f"[AUTH] ❌ CRITICAL: 'bcrypt' module not found!")
    print(f"[AUTH] Please run: pip install bcrypt")
    print(f"[AUTH] Details: {e}")
    bcrypt = None

# ============================================================================
# SESSION STATE (Simple global state for single-user desktop app)
# ============================================================================
current_session = {
    "authenticated": False,
    "user_id": None,
    "username": None,
    "email": None
}


# ============================================================================
# USER REGISTRATION
# ============================================================================
@eel.expose
def user_register(username, email, password):
    """
    Registers a new user with bcrypt password hashing.
    Called by login.html registration form.
    Returns: {"success": bool, "message": str}
    """
    print(f"\n[AUTH] 📝 REGISTER request: username='{username}', email='{email}'")

    # Input validation
    if not username or not email or not password:
        print("[AUTH] ❌ Validation Failed: Missing required fields")
        return {"success": False, "message": "All fields are required."}

    if not bcrypt:
        print("[AUTH] ❌ Server Error: bcrypt not available")
        return {"success": False, "message": "Server configuration error (missing bcrypt)."}

    print(f"[AUTH] 🔍 Using Database: {DB_PATH}")

    conn = get_db_connection()
    if not conn:
        print("[AUTH] ❌ Database connection failed")
        return {"success": False, "message": "Database connection failed."}

    try:
        cursor = conn.cursor()

        # Check for duplicate username or email
        print(f"[AUTH] Checking for existing user...")
        cursor.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        )
        existing = cursor.fetchone()

        if existing:
            print(f"[AUTH] ⚠️ User already exists (ID: {existing['id']})")
            return {"success": False, "message": "Username or Email already exists."}

        # Hash password with bcrypt
        print("[AUTH] Hashing password with bcrypt...")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Insert new user
        print("[AUTH] Inserting user into database...")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, datetime.datetime.now())
        )
        conn.commit()

        print(f"[AUTH] ✅ Registration SUCCESSFUL for: {username}")
        return {"success": True, "message": "Registration successful"}

    except sqlite3.IntegrityError as e:
        print(f"[AUTH] ⚠️ Integrity error (duplicate): {e}")
        return {"success": False, "message": "Username or Email already exists."}
    except Exception as e:
        print(f"[AUTH] ❌ EXCEPTION during registration: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"An error occurred: {str(e)}"}
    finally:
        conn.close()


# ============================================================================
# USER LOGIN
# ============================================================================
@eel.expose
def user_login(username, password):
    """
    Authenticates a user using bcrypt password verification.
    Called by login.html login form.
    Returns: {"success": bool, "message": str}
    """
    global current_session
    print(f"\n[AUTH] 🔐 LOGIN request: username='{username}'")

    # Input validation
    if not username or not password:
        print("[AUTH] ❌ Validation Failed: Missing credentials")
        return {"success": False, "message": "Username and password required."}

    if not bcrypt:
        print("[AUTH] ❌ Server Error: bcrypt not available")
        return {"success": False, "message": "Server configuration error (missing bcrypt)."}

    print(f"[AUTH] 🔍 Using Database: {DB_PATH}")

    conn = get_db_connection()
    if not conn:
        print("[AUTH] ❌ Database connection failed")
        return {"success": False, "message": "Database connection failed."}

    try:
        cursor = conn.cursor()

        # Fetch user by username
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            print(f"[AUTH] ❌ User not found: {username}")
            return {"success": False, "message": "Invalid credentials."}

        # Get stored password hash
        stored_hash = user['password_hash']

        # Ensure hash is bytes (handle legacy TEXT storage if any)
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            print(f"[AUTH] ✅ Login SUCCESSFUL for: {username}")

            # Update session
            current_session["authenticated"] = True
            current_session["user_id"] = user["id"]
            current_session["username"] = user["username"]
            current_session["email"] = user["email"]

            return {"success": True, "message": "Login successful"}
        else:
            print(f"[AUTH] ❌ Password mismatch for: {username}")
            return {"success": False, "message": "Invalid credentials."}

    except Exception as e:
        print(f"[AUTH] ❌ EXCEPTION during login: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"An error occurred: {str(e)}"}
    finally:
        conn.close()


# ============================================================================
# SESSION MANAGEMENT (Required by home.html)
# ============================================================================
@eel.expose
def get_authenticated_user_info():
    """Returns current session state for frontend checks."""
    return {
        "authenticated": current_session["authenticated"],
        "name": current_session["username"],
        "email": current_session["email"]
    }


@eel.expose
def set_authenticated_user(name, email):
    """Sets session state after successful authentication."""
    global current_session
    print(f"[AUTH] 🔓 Setting session for: {name}")
    current_session["authenticated"] = True
    current_session["username"] = name
    current_session["email"] = email
    return {"success": True}


@eel.expose
def logout_user():
    """Clears the session state."""
    global current_session
    print(f"[AUTH] 🔒 Logging out: {current_session.get('username', 'Unknown')}")
    current_session = {
        "authenticated": False,
        "user_id": None,
        "username": None,
        "email": None
    }
    return {"success": True, "message": "Logged out successfully"}


# ============================================================================
# GOOGLE LOGIN (Required by home.html - returns email lookup for compatibility)
# ============================================================================
@eel.expose
def verify_and_authenticate_google(email):
    """
    Compatibility function for home.html's Google-style login.
    Looks up user by email and authenticates without password verification.
    NOTE: This is a less secure flow; use user_login for proper auth.
    """
    print(f"\n[AUTH] 📧 verify_and_authenticate_google: email='{email}'")

    if not email:
        return {"success": False, "message": "Email is required."}

    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database connection failed."}

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ? OR username = ?",
            (email, email)
        )
        user = cursor.fetchone()

        if user:
            print(f"[AUTH] ✅ User found: {user['username']}")
            return {
                "success": True,
                "message": "Authentication verified.",
                "user_name": user["username"],
                "user_email": user["email"]
            }
        else:
            print(f"[AUTH] ❌ User not found: {email}")
            return {"success": False, "message": "User not found. Please register first."}

    except Exception as e:
        print(f"[AUTH] ❌ EXCEPTION: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"An error occurred: {str(e)}"}
    finally:
        conn.close()


@eel.expose
def google_login_register(token_or_data):
    """Placeholder for future Google OAuth integration."""
    print("[AUTH] ⚠️ google_login_register called (not implemented)")
    return {"success": False, "message": "Google Login is not yet configured."}
