import eel
import time # For simulating delays or time-based actions
import datetime # For handling date/time in Python functions (e.g., getting current time)
import sys # For exiting the application

# --- 1. Initialize Eel ---
# This tells Eel where to find your web files (HTML, CSS, JS).
# '.' means the current directory where app.py resides.
# If your web files were in a subfolder like 'web', you would use eel.init('web').
eel.init(r'C:\Users\Anvay Uparkar\Python\JARVIS\www')

# --- 2. Expose Python Functions to JavaScript ---
# Use @eel.expose decorator above any Python function you want to call from JavaScript.

@eel.expose
def allCommands(command=""):
    """
    This Python function can be called from JavaScript using eel.allCommands().
    It simulates processing a command and calling JavaScript functions.
    """
    print(f"Python received command: {command}")

    # Example of Python calling exposed JavaScript functions:
    # These JavaScript functions are defined in your controller.js and exposed with eel.expose().

    if command == "time":
        current_time = datetime.now().strftime("%I:%M %p")
        # Call JavaScript's DisplayMessage function to show time in frontend
        eel.DisplayMessage(f"The current time is {current_time}.")()
        # Call JavaScript's receiverText to show time in chat box as AI response
        eel.receiverText(f"The current time is {current_time}.")()

    elif command == "date":
        current_date = datetime.now().strftime("%B %d, %Y")
        eel.DisplayMessage(f"Today's date is {current_date}.")()
        eel.receiverText(f"Today's date is {current_date}.")()

    elif command == "hello":
        eel.DisplayMessage("Hello! How can I help you?")()
        eel.receiverText("Hello! How can I help you?")()

    elif command == "exit":
        eel.DisplayMessage("Goodbye!")()
        eel.receiverText("Goodbye!")()
        time.sleep(2) # Give time for message to display
        sys.exit(0) # Exit the Python application

    else:
        # If no specific command, just display a generic message
        eel.DisplayMessage("Command processed. Waiting for next instruction.")()
        eel.receiverText(f"You said: {command}")()

    # After processing, potentially hide the SiriWave and show the hood
    eel.ShowHood()() # Call JavaScript's ShowHood function


@eel.expose
def playAssistantSound():
    """
    Python function to simulate playing an assistant sound.
    This is called by JavaScript when the mic button is clicked.
    """
    print("Playing assistant sound (Python side simulation)...")
    # In a real application, you'd integrate a text-to-speech engine here.
    # For now, it just prints to the console.


# --- 3. Start the Eel Application ---
# eel.start() launches the web server and opens the browser window.
# 'index.html' is the starting page.
# mode specifies the browser to use (e.g., 'chrome', 'edge', 'firefox').
# size sets the initial window dimensions.
try:
    eel.start('index.html', mode='chrome', size=(1000, 700))
except Exception as e:
    print(f"Failed to start Eel: {e}")
    print("Please ensure you have Google Chrome (or specified browser) installed and it's in your system's PATH.")
    print("You can try other modes like 'edge' or 'firefox', or run in a default browser with mode=None.")
    # Fallback to a simpler start if the preferred mode fails
    try:
        eel.start('index.html', size=(1000, 700)) # Try without a specific mode
    except Exception as e_fallback:
        print(f"Fallback Eel start also failed: {e_fallback}")
        print("Exiting application.")
        sys.exit(1)

# In your app.py, after defining your Python functions:
@eel.expose
def allCommands(command=""):
    # ...
    if command == "time":
        current_time = datetime.now().strftime("%I:%M %p")
        # Call JavaScript's DisplayMessage function and execute it with ()
        eel.DisplayMessage(f"The current time is {current_time}.")()
        # Call JavaScript's receiverText function
        eel.receiverText(f"The current time is {current_time}.")()
    # ...