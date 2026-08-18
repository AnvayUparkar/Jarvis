# database.py - MongoDB Database Handler for Jarvis Authentication

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "jarvis_db"
# Keep DB_PATH for backwards compatibility in logging if needed
DB_PATH = MONGO_URI

def get_db_connection():
    """
    Establishes a connection to the MongoDB database.
    Returns the database object.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        # Verify connection
        client.admin.command('ping')
        db = client[DB_NAME]
        return db
    except Exception as e:
        print(f"[DATABASE]  Connection error: {e}")
        return None

def init_db():
    """
    Initializes the database. For MongoDB, collections are created implicitly,
    but we can create indexes here if needed.
    """
    print(f"\n[DATABASE]   INITIALIZING DATABASE (MongoDB)")
    print(f"[DATABASE]   URI: {MONGO_URI}")

    db = get_db_connection()
    if db is None:
        print("[DATABASE]  Failed to connect for initialization.")
        return False

    try:
        # Create unique indexes for users collection
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True)
        print("[DATABASE]  Users collection indexes ensured.")
        return True
    except Exception as e:
        print(f"[DATABASE]  Initialization error: {e}")
        return False
