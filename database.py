# database.py - SQLite Database Handler for Jarvis Authentication
# Uses absolute paths to guarantee persistent storage in the project root.

import sqlite3
import os

# ============================================================================
# CRITICAL: Force absolute path to db.sqlite in the SAME directory as this file
# This prevents the "empty database" issue when running from different directories
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite")


def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    Returns a connection object with row_factory set for dict-like access.
    """
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"[DATABASE] ❌ Connection error: {e}")
        return None


def init_db():
    """
    Initializes the database and creates the users table if it doesn't exist.
    Called once at application startup.
    """
    print(f"\n[DATABASE] 🛠️  INITIALIZING DATABASE")
    print(f"[DATABASE] 📂  Path: {DB_PATH}")

    conn = get_db_connection()
    if not conn:
        print("[DATABASE] ❌ Failed to connect for initialization.")
        return False

    try:
        cursor = conn.cursor()

        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()

        if not table_exists:
            # Create users table with BLOB for password_hash (bcrypt returns bytes)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("[DATABASE] ✅ Users table created successfully.")
        else:
            print("[DATABASE] ℹ️  Users table already exists.")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"[DATABASE] ❌ Initialization error: {e}")
        if conn:
            conn.close()
        return False
