# engine/features.py (EXAMPLE - YOU'LL NEED TO IMPLEMENT ACTUAL HOTWORD LOGIC)
# This is a placeholder. You'll need to install pvporcupine and pyaudio
# pip install pvporcupine pyaudio

import pvporcupine
import pyaudio
import struct
import os
import time
# main.py (MODIFIED for continuous listening)
import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
import pygame
import os
from gtts import gTTS
import google.generativeai as google_ai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import subprocess
import pywhatkit as kit
import re
import logging
import pygetwindow as gw
import pyautogui
from PIL import Image
import time
from urllib.parse import quote
import threading
import eel
import sys
import queue
from jarvis_speak import speak
from token_store import load_token
import struct
import threading
import time
import subprocess
import os
from get_google_contacts import get_contact_number
from token_store import *


# Replace with your Porcupine access key and model path
# You can get an AccessKey at https://console.picovoice.ai/
PORCUPINE_ACCESS_KEY = "cjFMSJ+voIyCw/yJdgE7XGglN7zHJSZqs8AnjYa0QJN+m7dkuXlAaQ=="
# Path to your Porcupine model (.ppn file)
# Example: os.path.join(os.path.dirname(__file__), 'jarvis_en_windows_v2_1_0.ppn')
PORCUPINE_MODEL_PATH = r"C:\Users\Anvay Uparkar\Python\JARVIS\Jarvis_en_windows_v3_0_0.ppn" # <--- IMPORTANT: Update this path!

def hotword(command_queue):
    print("Hotword listener initialized.")
    try:
        porcupine = pvporcupine.create(
            access_key=PORCUPINE_ACCESS_KEY,
            keyword_paths=[PORCUPINE_MODEL_PATH]
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print(f"Listening for hotword '{os.path.basename(PORCUPINE_MODEL_PATH).replace('.ppn', '')}'...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Hotword detected! Jarvis is now active.")
                command_queue.put("activate_jarvis") # Send activation signal
                # Optionally, you might want to pause hotword detection for a bit
                # or have a more sophisticated state management
                time.sleep(2) # Prevent immediate re-detection
                print("Resuming hotword detection...")

    except ImportError:
        print("Error: pvporcupine, pyaudio, or struct not found. Please install them.")
    except Exception as e:
        print(f"Error in hotword detection: {e}")
    finally:
        if 'porcupine' in locals() and porcupine is not None:
            porcupine.delete()
        if 'audio_stream' in locals() and audio_stream is not None:
            audio_stream.close()
        if 'pa' in locals() and pa is not None:
            pa.terminate()



# # --- WhatsApp and Contact Functions ---
# def get_contact_number(name_to_search):
#     # Ensure token_store.py's load_token is used here to get the correct credentials
#     token_data = load_token()
#     if not token_data:
#         print("No Google Contacts token found. Please authenticate.")
#         return None

#     try:
#         creds = Credentials(
#             token=token_data["token"],
#             refresh_token=token_data["refresh_token"],
#             token_uri=token_data["token_uri"],
#             client_id=token_data["client_id"],
#             client_secret=token_data["client_secret"],
#             scopes=token_data["scopes"],
#         )
#         service = build('people', 'v1', credentials=creds)
#         results = service.people().connections().list(
#             resourceName='people/me',
#             pageSize=1000,
#             personFields='names,phoneNumbers').execute()
#         connections = results.get('connections', [])

#         for person in connections:
#             names = person.get('names', [])
#             phone_numbers = person.get('phoneNumbers', [])
#             if names and phone_numbers:
#                 name = names[0].get('displayName').lower()
#                 if name_to_search.lower() in name:
#                     number = phone_numbers[0].get('value')
#                     cleaned_number = re.sub(r'\D', '', number)
#                     return cleaned_number
#         return None
#     except Exception as e:
#         print(f"Error accessing Google Contacts: {e}")
#         return None


# def extract_phone_number(text):
#     """
#     Extracts a 10+ digit number from the voice command, handling common spoken number formats.
#     """
#     cleaned_text = text.lower().replace("number", "").replace("call", "").replace("dial", "").strip()
#     cleaned_text = re.sub(r'[()\s-]', '', cleaned_text)

#     # Modified regex to allow optional '+' at the beginning for international numbers
#     match = re.search(r'\b\+?\d{10,15}\b', cleaned_text)
#     if match:
#         return match.group()
#     return None



# def whatsApp(mobile_no, message, flag, name):
#     target_tab = 0
#     jarvis_message = ""

#     if flag == 'message':
#         target_tab = 12
#         jarvis_message = f"Message sent successfully to {name}"
#     elif flag == 'call':
#         target_tab = 6
#         message = ''
#         jarvis_message = f"Calling {name}"
#     elif flag == 'video_call':
#         target_tab = 5
#         message = ''
#         jarvis_message = f"Starting video call with {name}"
#     else:
#         display_message("Invalid WhatsApp action requested.")
#         speak("Invalid WhatsApp action requested.")
#         return

#     encoded_message = quote(message)
#     print(f"Encoded message: {encoded_message}")

#     whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

#     try:
#         subprocess.run(f'start "" "{whatsapp_url}"', shell=True)
#         time.sleep(5)

#         whatsapp_window = None
#         for _ in range(5):
#             windows = gw.getWindowsWithTitle('WhatsApp')
#             if windows:
#                 for win in windows:
#                     if "WhatsApp" in win.title:
#                         whatsapp_window = win
#                         break
#             if whatsapp_window:
#                 break
#             time.sleep(1)

#         if whatsapp_window:
#             whatsapp_window.activate()
#             time.sleep(1)
#         else:
#             display_message("Could not find WhatsApp window. Please ensure it's open.")
#             speak("Could not find WhatsApp window. Please ensure it's open.")
#             logging.warning("WhatsApp window not found for hotkey navigation.")
#             return

#         pyautogui.hotkey('ctrl', 'f')
#         time.sleep(1)

#         for i in range(target_tab):
#             pyautogui.hotkey('tab')
#             time.sleep(0.1)

#         pyautogui.hotkey('enter')
#         display_message(jarvis_message)
#         speak(jarvis_message)
#         logging.info(f"WhatsApp action '{flag}' completed for {name}.")

#     except Exception as e:
#         display_message(f"An error occurred during the WhatsApp operation: {e}")
#         speak(f"An error occurred during the WhatsApp operation: {e}")
#         logging.error(f"WhatsApp function error: {e}")

# def jarvis_whatsapp_message(contact_query, message_text):
#     phone_number = None
#     number_from_query = extract_phone_number(contact_query)
#     if number_from_query:
#         phone_number = number_from_query
#         speak(f"Found number {phone_number} from your command. Preparing WhatsApp message.")
#     else:
#         speak(f"Searching for {contact_query} in your Google Contacts for WhatsApp message.")
#         phone_number = get_contact_number(contact_query)
        
#     if phone_number:
#         if not phone_number.startswith('+'):
#             # If it's a 10-digit number, assume Indian and prepend +91
#             if len(phone_number) == 10:
#                 phone_number = '+91' + phone_number
#                 speak(f"Assuming Indian number, formatting to {phone_number}")
#             else:
#                 # If not 10 digits and no '+', prompt for full number
#                 speak(f"The number '{phone_number}' does not start with a country code and is not a 10-digit number. Please specify the full number including the country code (e.g., +1 for USA, +91 for India).")
#                 return
        
#         whatsApp(phone_number, message_text, 'message', contact_query)
#     else:
#         speak("Sorry, I could not find a number for that contact to send a WhatsApp message.")

# def jarvis_whatsapp_call(contact_query):
#     phone_number = None
#     number_from_query = extract_phone_number(contact_query)
#     if number_from_query:
#         phone_number = number_from_query
#         speak(f"Found number {phone_number} from your command. Preparing WhatsApp call.")
#     else:
#         speak(f"Searching for {contact_query} in your Google Contacts for WhatsApp call.")
#         phone_number = get_contact_number(contact_query)
        
#     if phone_number:
#         if not phone_number.startswith('+'):
#             if len(phone_number) == 10:
#                 phone_number = '+91' + phone_number
#                 speak(f"Assuming Indian number, formatting to {phone_number}")
#             else:
#                 speak(f"The number '{phone_number}' does not start with a country code and is not a 10-digit number. Please specify the full number including the country code (e.g., +1 for USA, +91 for India).")
#                 return
            
#         whatsApp(phone_number, '', 'call', contact_query) # Message is empty for calls
#     else:
#         speak("Sorry, I could not find a number for that contact to make a WhatsApp call.")

# def jarvis_whatsapp_video_call(contact_query):
#     phone_number = None
#     number_from_query = extract_phone_number(contact_query)
#     if number_from_query:
#         phone_number = number_from_query
#         speak(f"Found number {phone_number} from your command. Preparing WhatsApp video call.")
#     else:
#         speak(f"Searching for {contact_query} in your Google Contacts for WhatsApp video call.")
#         phone_number = get_contact_number(contact_query)
        
#     if phone_number:
#         if not phone_number.startswith('+'):
#             if len(phone_number) == 10:
#                 phone_number = '+91' + phone_number
#                 speak(f"Assuming Indian number, formatting to {phone_number}")
#             else:
#                 speak(f"The number '{phone_number}' does not start with a country code and is not a 10-digit number. Please specify the full number including the country code (e.g., +1 for USA, +91 for India).")
#                 return
            
#         whatsApp(phone_number, '', 'video_call', contact_query) # Message is empty for video calls
#     else:
#         speak("Sorry, I could not find a number for that contact to make a WhatsApp video call.")

# def display_message(message):
#     try:
#         eel.displayMessage(message)  # Correct casing
#     except Exception as e:
#         print(f"Error sending message to frontend: {e}")
#         # Handle the error gracefully, e.g., log it or provide a default behavior



