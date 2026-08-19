"""
Hotword Detection Module for Jarvis
====================================
Provides continuous background listening for the "Jarvis" wake word using Porcupine.
Activates Jarvis only when the wake word is detected, then returns to passive listening.

Features:
- Continuous non-blocking listening
- Detects wake word "Jarvis" using Porcupine (Picovoice)
- Sends activation signal via queue
- Includes cooldown to prevent false retriggers
- Minimal CPU usage with efficient frame processing
"""

import pvporcupine
import pyaudio
import struct
import os
import time
import threading
import queue
import sys

# Import Porcupine access key from apikey.py
try:
    from apikey import PORCUPINE_ACCESS_KEY
except ImportError:
    # Fallback if apikey.py doesn't exist
    PORCUPINE_ACCESS_KEY = None

# Path to Porcupine model file (.ppn)
# Using the full path to the Jarvis model included in the repository
# Path to Porcupine model file (.ppn)
# Using the "Jarvis" wake word model (v4.0.0 compatible with pvporcupine library)
PORCUPINE_MODEL_PATH = r"C:\Users\Anvay Uparkar\Hackathon projects\JARVIS - Copy\Jarvis\Jarvis_en_windows_v4_0_0.ppn"

# Configuration
COOLDOWN_SECONDS = 1.2  # Cooldown after activation to prevent false retriggers


def hotword(command_queue, conversation_mode_active):
    """
    Continuous hotword detection listener for "Hello Mirage" wake word.
    
    Args:
        command_queue: multiprocessing.Queue for sending activation signals to main process
        conversation_mode_active: multiprocessing.Event to synchronize microphone access
        
    This function:
    - Initializes Porcupine with the Hello Mirage model
    - Opens a continuous audio stream
    - Processes audio frames for hotword detection
    - Sends "activate_mirage" signal when wake word is detected
    - Includes cooldown to prevent rapid re-triggering
    - Handles cleanup on exit
    """
    # Validate access key
    if not PORCUPINE_ACCESS_KEY:
        print("[❌ HOTWORD] Fatal error: PORCUPINE_ACCESS_KEY not found in apikey.py")
        print("[📋 HOTWORD] Please add PORCUPINE_ACCESS_KEY to your apikey.py file")
        return
    
    porcupine = None
    audio_stream = None
    pa = None
    last_activation_time = 0
    
    try:
        print("[🎙️ HOTWORD] Initializing Porcupine hotword detector...")
        
        # Initialize Porcupine with the Hello Mirage wake word model
        porcupine = pvporcupine.create(
            access_key=PORCUPINE_ACCESS_KEY,
            keyword_paths=[PORCUPINE_MODEL_PATH],
            sensitivities=[1.0]
        )
        
        print(f"[✅ HOTWORD] Porcupine initialized successfully")
        print(f"[🎤 HOTWORD] Sample rate: {porcupine.sample_rate} Hz")
        print(f"[📊 HOTWORD] Frame length: {porcupine.frame_length} samples")
        
        # Initialize PyAudio for continuous microphone input
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=None  # Use default input device
        )
        
        print(f"[🎙️ HOTWORD] Audio stream opened, beginning continuous listening for wake word 'Jarvis'...")
        print(f"[⏱️ HOTWORD] Cooldown period: {COOLDOWN_SECONDS} seconds after detection")
        
        # Main listening loop
        while True:
            # Check if Conversation Mode is active, and if so release the mic
            if conversation_mode_active.is_set():
                if audio_stream is not None:
                    print("[🎙️ HOTWORD] Pausing hotword listener (releasing microphone for Conversation Mode)")
                    try:
                        audio_stream.stop_stream()
                        audio_stream.close()
                    except Exception as e:
                        print(f"[⚠️ HOTWORD] Error closing audio stream: {e}")
                    audio_stream = None
                time.sleep(0.5)
                continue

            # Reclaim microphone if Conversation Mode is no longer active
            if audio_stream is None:
                print("[🎙️ HOTWORD] Resuming hotword listener (reclaiming microphone)")
                try:
                    audio_stream = pa.open(
                        rate=porcupine.sample_rate,
                        channels=1,
                        format=pyaudio.paInt16,
                        input=True,
                        frames_per_buffer=porcupine.frame_length,
                        input_device_index=None
                    )
                except Exception as e:
                    print(f"[❌ HOTWORD] Error reclaiming microphone: {e}")
                    time.sleep(1.0)
                    continue

            try:
                # Read audio frame from microphone
                pcm_data = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                
                # Unpack binary audio data into PCM samples
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm_data)
                
                # Process audio frame with Porcupine
                keyword_index = porcupine.process(pcm)
                
                # Check if wake word was detected (keyword_index >= 0)
                if keyword_index >= 0:
                    current_time = time.time()
                    
                    # Apply cooldown to prevent false retriggers
                    if current_time - last_activation_time >= COOLDOWN_SECONDS:
                        print(f"\n[🔊 HOTWORD] ✨ Wake word 'Jarvis' DETECTED! Activating...")
                        
                        # Send activation signal to main process via queue
                        try:
                            command_queue.put("activate_mirage", timeout=1)
                            print(f"[📤 HOTWORD] Activation signal sent to main process")
                        except queue.Full:
                            print(f"[⚠️ HOTWORD] Queue is full, activation signal not sent")
                        
                        # Update cooldown timestamp
                        last_activation_time = current_time
                        
                        # Brief silence to allow activation to register
                        time.sleep(0.5)
                    else:
                        # Cooldown still active, ignore detection
                        time_remaining = COOLDOWN_SECONDS - (current_time - last_activation_time)
                        print(f"[⏳ HOTWORD] Cooldown active ({time_remaining:.1f}s remaining), ignoring detection")
                
            except Exception as e:
                print(f"[⚠️ HOTWORD] Error processing audio frame: {e}")
                time.sleep(0.1)
                continue
    
    except ImportError as e:
        print(f"[❌ HOTWORD] Import error - missing required library: {e}")
        print(f"[📦 HOTWORD] Please install required packages:")
        print(f"    pip install pvporcupine pyaudio")
        sys.exit(1)
        
    except FileNotFoundError:
        print(f"[❌ HOTWORD] Porcupine model file not found at: {PORCUPINE_MODEL_PATH}")
        print(f"[📁 HOTWORD] Please ensure the .ppn file exists at the specified path")
        sys.exit(1)
        
    except Exception as e:
        print(f"[⚠️ HOTWORD] Porcupine initialization failed or crashed: {e}")
        print(f"[📋 HOTWORD] Error type: {type(e).__name__}")
        print("[🔄 HOTWORD] Attempting to start fallback hotword detection...")
        try:
            import speech_recognition as sr
            import audio_engine
            
            print("[🎙️ HOTWORD] Falling back to audio_engine.py...")
            recognizer = audio_engine.get_tuned_recognizer()
            # We want it to be responsive but not cut off "Jarvis" mid-word
            recognizer.pause_threshold = 0.8
            recognizer.non_speaking_duration = 0.3
            mic = sr.Microphone(sample_rate=16000)
            
            triggers = ["jarvis", "hello mirage", "hey mirage", "hi mirage", "mirage", "jar", "javis", "garvis"]
            
            last_activation_time = 0
            
            print("[🎙️ HOTWORD] Speech fallback listening for 'Jarvis'...")
            
            while True:
                if conversation_mode_active.is_set():
                    time.sleep(0.5)
                    continue

                try:
                    # Enter/exit mic context inside loop to release the audio device dynamically
                    with mic as source:
                        # Use smart_listen for normalization and safety, skip calibration to prevent 1-second gaps
                        audio = audio_engine.smart_listen(recognizer, source, timeout=1.0, phrase_time_limit=3.0, calibrate=False, quiet=True)
                    
                    text = recognizer.recognize_google(audio).lower()
                    if text:
                        print(f"[🎙️ HOTWORD] Heard: {text}")
                    
                    if any(trigger in text for trigger in triggers):
                        current_time = time.time()
                        if current_time - last_activation_time >= COOLDOWN_SECONDS:
                            print(f"\n[🔊 HOTWORD] ✨ Wake word DETECTED (Fallback: '{text}')! Activating...")
                            try:
                                command_queue.put("activate_mirage", timeout=1)
                                print(f"[📤 HOTWORD] Activation signal sent to main process")
                            except queue.Full:
                                print(f"[⚠️ HOTWORD] Queue is full, activation signal not sent")
                            last_activation_time = current_time
                            time.sleep(0.5)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    print("[⚠️ HOTWORD] Network error in fallback. Retrying...")
                    time.sleep(1)
                except sr.WaitTimeoutError:
                    continue
                except Exception as ex:
                    print(f"[⚠️ HOTWORD] Fallback error: {ex}")
                    time.sleep(1)

        except ImportError:
            print("[❌ HOTWORD] SpeechRecognition module not found for fallback. Please run: pip install SpeechRecognition")
            sys.exit(1)
        
    finally:
        # Cleanup resources
        print(f"\n[🧹 HOTWORD] Cleaning up resources...")
        
        try:
            if audio_stream is not None:
                audio_stream.stop_stream()
                audio_stream.close()
                print(f"[✅ HOTWORD] Audio stream closed")
        except Exception as e:
            print(f"[⚠️ HOTWORD] Error closing audio stream: {e}")
        
        try:
            if pa is not None:
                pa.terminate()
                print(f"[✅ HOTWORD] PyAudio terminated")
        except Exception as e:
            print(f"[⚠️ HOTWORD] Error terminating PyAudio: {e}")
        
        try:
            if porcupine is not None:
                porcupine.delete()
                print(f"[✅ HOTWORD] Porcupine deleted")
        except Exception as e:
            print(f"[⚠️ HOTWORD] Error deleting Porcupine: {e}")
        
        print(f"[🛑 HOTWORD] Hotword detection stopped")



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



