# --- HOTWORD + COMMAND LOOP WITH UI FEEDBACK ---

import eel
import speech_recognition as sr
import time
import pygame
import pvporcupine
import pyaudio
import struct
from main import listen, processCommand, speak, refresh_token

# Initialize PyGame for optional sound playback
pygame.mixer.init()

# Initialize Eel with frontend
eel.init("www")

# Hotword detection loop

def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(
            access_key="cjFMSJ+voIyCw/yJdgE7XGglN7zHJSZqs8AnjYa0QJN+m7dkuXlAaQ==",
            keyword_paths=[r"C:\Users\Anvay Uparkar\Python\JARVIS\Jarvis_en_windows_v3_0_0.ppn"]
        )
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print("[Hotword] Listening for 'Jarvis'...")
        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)

            keyword_index = porcupine.process(keyword)

            if keyword_index >= 0:
                print("[Hotword] Detected 'Jarvis'")
                return True

    except Exception as e:
        print(f"[Hotword Error]: {e}")
        return False

    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()


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
