import os
import json
import hashlib
import secrets
from datetime import datetime

USERS_DB_FILE = 'users_database.json'

# --- Password Hashing ---
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hash_ = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f'{salt}${hash_.hex()}'

def verify_password(password, hashed):
    try:
        salt, hash_val = hashed.split('$')
        return hash_password(password, salt) == hashed
    except Exception:
        return False

# --- User DB Helpers ---
def load_users():
    if not os.path.exists(USERS_DB_FILE):
        return {}
    with open(USERS_DB_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# --- Local Registration ---
def register_user(username, email, password):
    users = load_users()
    if username in users:
        return {"success": False, "message": "Username already exists"}
    for u in users.values():
        if u.get('email') == email:
            return {"success": False, "message": "Email already registered"}
    hashed = hash_password(password)
    users[username] = {
        "username": username,
        "email": email,
        "password_hash": hashed,
        "created_at": datetime.utcnow().isoformat(),
        "auth_method": "local"
    }
    save_users(users)
    return {"success": True, "username": username, "email": email}

# --- Local Login ---
def login_user(username, password):
    users = load_users()
    user = users.get(username)
    if not user:
        return {"success": False, "message": "User not found"}
    if not verify_password(password, user['password_hash']):
        return {"success": False, "message": "Incorrect password"}
    return {"success": True, "username": username, "email": user['email']}

# --- Get User Info ---
def get_user_info(username):
    users = load_users()
    user = users.get(username)
    if not user:
        return {"success": False, "message": "User not found"}
    return {"success": True, **user}

# --- Change Password ---
def change_password(username, old_password, new_password):
    users = load_users()
    user = users.get(username)
    if not user:
        return {"success": False, "message": "User not found"}
    if not verify_password(old_password, user['password_hash']):
        return {"success": False, "message": "Old password incorrect"}
    user['password_hash'] = hash_password(new_password)
    save_users(users)
    return {"success": True, "message": "Password changed"}

# --- Google Login/Register ---
def google_login_or_register(email, name, google_id):
    users = load_users()
    # Try to find by email
    for username, user in users.items():
        if user.get('email') == email:
            # Link Google if not already
            user['auth_method'] = 'google'
            user['google_id'] = google_id
            save_users(users)
            return {"success": True, "username": username, "email": email}
    # Register new user
    username = email.split('@')[0]
    base_username = username
    i = 1
    while username in users:
        username = f"{base_username}{i}"
        i += 1
    users[username] = {
        "username": username,
        "email": email,
        "password_hash": None,
        "created_at": datetime.utcnow().isoformat(),
        "auth_method": "google",
        "google_id": google_id,
        "name": name
    }
    save_users(users)
    return {"success": True, "username": username, "email": email}
