# run.py (MODIFIED)
import multiprocessing
import subprocess
import os
import eel
from main import start 
# from jarvis_speak import speak
from main import * 
from token_store import *  # Ensure this is imported to use the speak function
# To run Jarvis
@eel.expose
def startJarvis(command_queue): # Add command_queue
    print("Process 1 (Jarvis Main Application) is starting.")
    from main import start
    start(command_queue) # Pass the queue

# To run hotword
def listenHotword(command_queue): # Add command_queue
    print("Process 2 (Hotword Listener) is starting.")
    try:
        from engine.features import hotword
        hotword(command_queue) # Pass the queue 
    except ImportError:
        print("Error: Could not import hotword. Make sure 'engine/features.py' exists and is accessible.")
    except Exception as e:
        print(f"Error in hotword process: {e}")

# Start both processes
if __name__ == '__main__':
    # Create a queue for inter-process communication
    command_queue = multiprocessing.Queue()

    # Create the processes
    p1 = multiprocessing.Process(target=startJarvis, args=(command_queue,))
    p2 = multiprocessing.Process(target=listenHotword, args=(command_queue,))

    # Start the processes
    p1.start()
    p2.start()

    # Wait for the Jarvis process to finish
    p1.join()

    # If Jarvis stops, terminate the hotword listener if it's still running
    if p2.is_alive():
        print("Jarvis process stopped. Terminating hotword listener.")
        p2.terminate()
        p2.join() # Wait for the hotword process to fully terminate

    print("System stopped.")