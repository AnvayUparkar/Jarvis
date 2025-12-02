import eel
import os

# Set the web folder path (adjust if needed)
WEB_DIR = r'C:\Users\Anvay Uparkar\Python\JARVIS\www'
eel.init(WEB_DIR)

# Your eel.expose functions and other Python logic go here

if __name__ == "__main__":
    try:
        eel.start('index.html', size=(1000, 600))  # Use a free port
    except Exception as e:
        print(f"Eel startup error: {e}")