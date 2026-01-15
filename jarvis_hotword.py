# --- HOTWORD + COMMAND LOOP WITH UI FEEDBACK ---

import eel
import speech_recognition as sr
import time
import pygame
from wake_word import WakeWordDetector

# Initialize detector once to reuse resources effectively
detector = WakeWordDetector()

def hotword():
    """
    Listens for the wake word using the robust Auto-Fallback system.
    Returns True when wake word is detected.
    """
    try:
        # The listen() method handles Porcupine -> Fallback logic internally
        return detector.listen()
    except Exception as e:
        print(f"[Hotword Error]: {e}")
        return False


@eel.expose
def run_jarvis_loop():
    speak("Initializing Jarvis...")
    refresh_token()

    while True:
        try:
            triggered = hotword()
            if triggered:
                eel.DisplayMessage("Yes?")
                eel.HideHood()
                speak("Yes?")

                command = listen()
                if command:
                    eel.senderText(command)
                    processCommand(command)
                else:
                    eel.receiverText("I didn't hear a command.")
                
                # Reset UI
                eel.DisplayMessage("Ask me anything")
                eel.ShowHood()

        except Exception as e:
            print(f"[Jarvis Loop Error]: {e}")


# Launch Eel app
if __name__ == "__main__":
    eel.start("index.html", mode=None, port=8000)
