# filepath: c:\Users\Anvay Uparkar\Python\JARVIS\jarvis_speak.py
import pyttsx3
import eel
import pygame
import os
from gtts import gTTS
from token_store import *
engine = pyttsx3.init()

def speak(text):
    print(f"Jarvis: {text}")
    try:
        eel.DisplayMessage(text)
    except Exception:
        pass
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save("response.mp3")
        
        # Read the file and send to frontend for playback & lip-sync
        with open("response.mp3", "rb") as f:
            audio_data = f.read()
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            eel.play_audio_blob(base64_audio)()
            
        # Clean up
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")
            
    except Exception as e:
        print(f"TTS Error: {e}")
        engine.say(text)
        engine.runAndWait()