import base64
# auth.py - Authentication Module for Jarvis
# Handles user registration, login, and session management via Eel.

import eel
import datetime
import traceback
from database import get_db_connection, DB_PATH
import pymongo.errors

# ============================================================================
# BCRYPT DEPENDENCY CHECK
# ============================================================================
try:
    import bcrypt
    print("[AUTH]  bcrypt module loaded successfully.")
except ImportError as e:
    print(f"[AUTH]  CRITICAL: 'bcrypt' module not found!")
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
    print(f"\n[AUTH]  REGISTER request: username='{username}', email='{email}'")

    # Input validation
    if not username or not email or not password:
        print("[AUTH]  Validation Failed: Missing required fields")
        return {"success": False, "message": "All fields are required."}

    if not bcrypt:
        print("[AUTH]  Server Error: bcrypt not available")
        return {"success": False, "message": "Server configuration error (missing bcrypt)."}

    print(f"[AUTH]  Using Database: {DB_PATH}")

    db = get_db_connection()
    if db is None:
        print("[AUTH]  Database connection failed")
        return {"success": False, "message": "Database connection failed."}

    try:
        # Check for duplicate username or email
        print(f"[AUTH] Checking for existing user...")
        existing = db.users.find_one({
            "$or": [{"username": username}, {"email": email}]
        })

        if existing:
            print(f"[AUTH]  User already exists (ID: {existing['_id']})")
            return {"success": False, "message": "Username or Email already exists."}

        # Hash password with bcrypt
        print("[AUTH] Hashing password with bcrypt...")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Insert new user
        print("[AUTH] Inserting user into database...")
        db.users.insert_one({
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.datetime.now()
        })

        print(f"[AUTH]  Registration SUCCESSFUL for: {username}")
        return {"success": True, "message": "Registration successful"}

    except pymongo.errors.DuplicateKeyError as e:
        print(f"[AUTH]  Integrity error (duplicate): {e}")
        return {"success": False, "message": "Username or Email already exists."}
    except Exception as e:
        print(f"[AUTH]  EXCEPTION during registration: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"An error occurred: {str(e)}"}


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
    print(f"\n[AUTH]  LOGIN request: username='{username}'")

    # Input validation
    if not username or not password:
        print("[AUTH]  Validation Failed: Missing credentials")
        return {"success": False, "message": "Username and password required."}

    if not bcrypt:
        print("[AUTH]  Server Error: bcrypt not available")
        return {"success": False, "message": "Server configuration error (missing bcrypt)."}

    print(f"[AUTH]  Using Database: {DB_PATH}")

    db = get_db_connection()
    if db is None:
        print("[AUTH]  Database connection failed")
        return {"success": False, "message": "Database connection failed."}

    try:
        # Fetch user by username or email
        user = db.users.find_one({"$or": [{"username": username}, {"email": username}]})

        if not user:
            print(f"[AUTH]  User not found: {username}")
            return {"success": False, "message": "Invalid credentials."}

        # Get stored password hash
        stored_hash = user['password_hash']

        # Ensure hash is bytes (handle legacy TEXT storage if any)
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            print(f"[AUTH]  Login SUCCESSFUL for: {username}")

            # Update session
            current_session["authenticated"] = True
            current_session["user_id"] = str(user["_id"])
            current_session["username"] = user["username"]
            current_session["email"] = user["email"]

            # Quietly check/refresh Google token
            try:
                from google_auth_helpers import get_current_user_email
                google_email = get_current_user_email(allow_interaction=False)
                if google_email:
                    if google_email.lower() == user.get("email", "").lower():
                        print(f"[AUTH] Google token quietly refreshed and verified for {google_email}")
                    else:
                        print(f"[AUTH] Google token is valid, but associated with different email: {google_email}")
                else:
                    print("[AUTH] No valid Google token found. Google services will require authentication.")
            except Exception as e:
                print(f"[AUTH] Background Google token check failed: {e}")

            return {
                "success": True, 
                "message": "Login successful",
                "user_name": user["username"],
                "user_email": user["email"],
                "avatar": user.get("avatar", "preset:fa-user")
            }
        else:
            print(f"[AUTH]  Password mismatch for: {username}")
            return {"success": False, "message": "Invalid credentials."}

    except Exception as e:
        print(f"[AUTH]  EXCEPTION during login: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"An error occurred: {str(e)}"}


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
    print(f"[AUTH]  Setting session for: {name}")
    current_session["authenticated"] = True
    current_session["username"] = name
    current_session["email"] = email
    return {"success": True}


@eel.expose
def logout_user():
    """Clears the session state."""
    global current_session
    print(f"[AUTH]  Logging out: {current_session.get('username', 'Unknown')}")
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
    print(f"\n[AUTH]  verify_and_authenticate_google: email='{email}'")

    if not email:
        return {"success": False, "message": "Email is required."}

    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection failed."}

    try:
        user = db.users.find_one({
            "$or": [{"email": email}, {"username": email}]
        })

        if user:
            print(f"[AUTH]  User found: {user['username']}")
            return {
                "success": True,
                "message": "Authentication verified.",
                "user_name": user["username"],
                "user_email": user["email"],
                "avatar": user.get("avatar", "preset:fa-user")
            }
        else:
            print(f"[AUTH]  User not found: {email}")
            return {"success": False, "message": "User not found. Please register first."}

    except Exception as e:
        print(f"[AUTH]  EXCEPTION: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"An error occurred: {str(e)}"}


@eel.expose
def google_login_register(token_or_data):
    """Placeholder for future Google OAuth integration."""
    print("[AUTH]  google_login_register called (not implemented)")
    return {"success": False, "message": "Google Login is not yet configured."}


@eel.expose
def update_avatar(avatar_type, avatar_data):
    """
    Updates the user's avatar in the database.
    avatar_type: 'preset' or 'upload'
    avatar_data: fontawesome class OR base64 string
    """
    if not current_session.get("authenticated"):
        return {"success": False, "message": "Not authenticated"}
        
    user_id = current_session.get("user_id")
    try:
        from bson.objectid import ObjectId
        import os
        if avatar_type == 'preset':
            db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"avatar": f"preset:{avatar_data}"}})
            return {"success": True, "avatar": f"preset:{avatar_data}"}
        elif avatar_type == 'upload':
            if ',' in avatar_data:
                avatar_data = avatar_data.split(',')[1]
                
            img_data = base64.b64decode(avatar_data)
            filename = f"avatar_{user_id}.png"
            filepath = os.path.join('www', 'assets', 'avatars', filename)
            
            with open(filepath, 'wb') as f:
                f.write(img_data)
                
            db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"avatar": f"file:{filename}"}})
            return {"success": True, "avatar": f"file:{filename}"}
    except Exception as e:
        print(f"[AUTH] Error updating avatar: {e}")
        return {"success": False, "message": str(e)}
