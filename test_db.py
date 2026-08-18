from database import get_db_connection, init_db
import sys

print("Testing connection...")
db = get_db_connection()
if db is not None:
    print("Connection successful!")
else:
    print("Connection failed!")
