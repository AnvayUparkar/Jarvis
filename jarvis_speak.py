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
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        pygame.mixer.init()
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")
    except Exception:
        engine.say(text)
        engine.runAndWait()