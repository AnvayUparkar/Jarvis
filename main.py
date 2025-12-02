# main.py (Integrated with direct image generation, Question Bot, and Agentic AI Scheduling Assistant)
import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
import pygame
import os
import base64 # Added import for base64 decoding
import json # Added import for JSON decoding
from gtts import gTTS # Corrected import for gTTS
import google.generativeai as google_ai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import subprocess
import pywhatkit as kit
import re # This import is already here globally
import logging
import pygetwindow as gw
import pyautogui
from googleapiclient.errors import HttpError
from PIL import Image
import time
from urllib.parse import quote
import threading
import eel
import sys
import queue # Import queue for multiprocessing.Queue
import os
from apikey import api_data # Import your API keys from apikey.py
import uuid # Import uuid for unique filenames
from volume import *
from shutdown_and_restart import *
from image import * # Ensure this import is active for generate_image_for_jarvis
from token_store import *
from answer_bot import answer_mcq_question # Import the answer_bot function
import datetime as dt # Changed import to alias datetime as dt
from datetime import timedelta # Keep timedelta separate if preferred, or also use dt.timedelta
import functools # For @functools.wraps in decorators
from google.auth.transport.requests import Request # Already imported at top
from google.oauth2.credentials import Credentials # Already imported at top
from google_auth_oauthlib.flow import InstalledAppFlow # Will be used directly in auth functions
from googleapiclient.discovery import build
# NEW: Import the create_google_form function from the integration file
from google_forms_integration import create_google_form
# NEW: Import the generate_formal_email_draft function from gmail.py
import gmail
from gmail import generate_email_body_with_gemini
from email.mime.text import MIMEText # NEW: Import for creating email messages


# Assuming 'speak' function and 'api_data' (for GEN_AI_API_KEY) are accessible
# You will need to pass 'speak' or import it if this file is not run directly
# and relies on a global 'speak' from main.py.
try:
    from apikey import api_data as GEN_AI_API_KEY
except ImportError:
    print("Error: apikey.py not found or GEN_AI_API_KEY not defined. Using placeholder.")
    GEN_AI_API_KEY = "AIzaSyB_H-_FNNVw-Oo10NyPJoOeTpXoXOPRRmY" # Placeholder, replace with actual key if not using apikey.py


# Using a single credentials file for all Google APIs for consistency
GOOGLE_CREDENTIALS_FILE = 'client_secret_133871116699-cn0a6i1lja1n9gkos0f3kr6sia0jej55.apps.googleusercontent.com.json' # Using credentialsnew.json as the primary
GOOGLE_TOKEN_FILE = 'token.json' # Active configuration for storing token
GOOGLE_CALENDAR_TOKEN_FILE = 'calendar_token.json' # Separate token for calendar if needed, or unify

# Define ALL necessary scopes for your application here
SCOPES = [
    'https://www.googleapis.com/auth/calendar.freebusy',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send', # NEW: Added for sending/drafting emails
    'https://www.googleapis.com/auth/forms.responses.readonly', # Add if you need to read responses
    'openid'  # Make sure this is present!
]

SCOPES = list(set(SCOPES)) # Remove duplicates to ensure clean scope list

# Configure Gemini AI - Moved here to ensure GEN_AI_API_KEY is defined
try:
    google_ai.configure(api_key=GEN_AI_API_KEY)
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}. Please check your GEN_AI_API_KEY.")


# --- Google API Authentication (Unified) ---
def get_google_credentials():
    """
    Handles Google OAuth2.0 authentication for all Google APIs used by Jarvis.
    Attempts to load existing credentials from token.json or performs a new
    authorization flow if needed. Ensures all required SCOPES are covered.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(GOOGLE_TOKEN_FILE):
        print("Attempting to load Google credentials from token.json...")
        try:
            creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
            print("✅ Google credentials loaded from token.json.")

            # IMPORTANT: Check if all *currently required* SCOPES are covered by the loaded credentials
            # This is crucial if you add new scopes later.
            if not all(s in creds.scopes for s in SCOPES):
                print("⚠️ Loaded credentials do not cover all required scopes. Forcing re-authentication.")
                creds = None # Force a new authentication flow
            
        except Exception as e:
            print(f"❌ Error loading credentials from token.json: {e}. Re-authenticating.")
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Google credentials expired, attempting to refresh...")
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow # Moved import here
                creds.refresh(Request())
                print("✅ Google credentials refreshed successfully.")
                # After refresh, re-check scopes, just in case refresh didn't update them all (rare but possible)
                if not all(s in creds.scopes for s in SCOPES):
                    print("⚠️ Refreshed credentials still do not cover all required scopes. Initiating new authentication flow.")
                    creds = None
            except Exception as e:
                print(f"❌ Error refreshing credentials: {e}. Initiating new authentication flow.")
                creds = None
        
        if not creds: # If still no valid creds after load/refresh, initiate new flow
            print("Initiating new Google authentication flow...")
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow # Moved import here
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0) # run_local_server handles opening browser and receiving redirect
                print("✅ Google authentication completed.")
            except Exception as e:
                print(f"❌ Error during Google authentication flow: {e}. Ensure '{GOOGLE_CREDENTIALS_FILE}' is valid and present.")
                return None
            
            # Save the credentials for the next run
            try:
                with open(GOOGLE_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("✅ Google credentials saved to token.json.")
            except Exception as e:
                print(f"❌ Error saving credentials to token.py: {e}")
                
    # NEW DEBUG PRINT: Print the scopes that are actually loaded
    if creds:
        print(f"DEBUG: Scopes currently loaded in credentials: {sorted(list(creds.scopes))}")
    else:
        print("DEBUG: No credentials loaded.")

    return creds

# --- Gemini Function to Get Slide Content ---
# This function is now primarily handled by the presentation.py Flask app.
# It's kept here for handle_presentation_command which generates from a topic.
def get_slide_content(topic, speak):
    """
    Generates presentation slide content using Google Gemini with much more detailed information.
    Instructs Gemini to return only JSON in a specific format for up to 6 slides,
    with more extensive headings and content for each slide.
    The content for each slide will directly support and elaborate on its heading.
    'speak' is passed to allow this module to use Jarvis's voice output.
    """
    prompt = f"""Create a 6-slide presentation about {topic}.
    For each slide, provide a very descriptive and detailed heading.
    For the content of each slide, provide at least 5-7 comprehensive bullet points. Each bullet point should be a detailed sentence or phrase, and the content MUST DIRECTLY SUPPORT AND ELABORATE ON THE SLIDE'S HEADING.
    Provide ONLY JSON, which should be an array of objects. Each object represents a slide and must have "heading" and "content" keys.
    The "content" should be a list of detailed bullet points (strings).
    Example format:
    [
        {{"heading": "Introduction: A Deep Dive into the Fundamental Concepts of {topic}", "content": ["Explore the foundational principles and key definitions that underpin {topic}'s complexity.", "Discuss the historical context and evolution of {topic} through significant milestones and discoveries.", "Analyze the core components and mechanisms that drive {topic}'s operations, providing intricate details.", "Highlight the interdisciplinary nature of {topic} and its connections to related fields of study.", "Outline the primary objectives and learning outcomes of this presentation, setting clear expectations." ]}},
        {{... up to 6 slides with highly detailed headings and 5-7 extensive bullet points each ...}}
    ]
    Ensure the JSON is well-formed and does not contain any additional text or markdown outside the JSON block.
    """
    print(f"🧠 Asking Gemini for content on: {topic}")
    speak(f"Thinking about detailed content for {topic}...")
    try:
        # Changed model from 'gemini-pro' to 'gemini-2.0-flash' for better availability
        model = google_ai.GenerativeModel("gemini-2.0-flash") 
        response = model.generate_content(prompt)
        
        json_string = response.text.strip()
        if json_string.startswith("```json"):
            json_string = json_string[7:].strip()
        if json_string.endswith("```"):
            json_string = json_string[:-3].strip()

        slides_data = json.loads(json_string)

        if not isinstance(slides_data, list):
            raise ValueError("Gemini response is not a list of slides.")
        for slide in slides_data:
            if not isinstance(slide, dict) or "heading" not in slide or "content" not in slide:
                raise ValueError("Each slide in Gemini response must be an object with 'heading' and 'content' (list of strings).")
            if not isinstance(slide["content"], list) or not all(isinstance(item, str) for item in slide["content"]):
                raise ValueError("'content' must be a list of strings for each slide.")

        print("✅ Gemini content generated and parsed successfully.")
        return slides_data[:6]
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON from Gemini: {e}")
        speak("I had trouble understanding the content from Gemini. The format might be incorrect.")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred with Gemini: {e}")
        speak("I encountered an issue while generating content with AI.")
        return None

# --- Google Slides API Function to Create Presentation ---
# This function is now primarily handled by the presentation.py Flask app.
# It's kept here for handle_presentation_command which generates from a topic.
def create_google_presentation(topic, slides_content, speak):
    """
    Creates a new Google Slides presentation and populates it with content.
    'speak' is passed to allow this module to use Jarvis's voice output.
    """
    creds = get_google_credentials() # Auth happens every time
    if not creds:
        speak("Failed to authenticate with Google. Cannot create presentation.")
        print("❌ Failed to get Google credentials. Cannot create presentation.")
        return None

    try:
        service = build('slides', 'v1', credentials=creds)
        
        presentation_title = f"{topic} - Jarvis Generated Presentation"
        body = {
            'title': presentation_title
        }
        # Create a new presentation
        presentation = service.presentations().create(body=body).execute()
        presentation_id = presentation.get('presentationId')
        speak(f"Creating a new presentation titled {presentation_title}.")
        print(f"✅ Created presentation with ID: {presentation_id}")

        requests_batch = []

        # --- Step 1: Delete the default first slide ---
        # Get the ID of the automatically created first slide
        initial_presentation_get = service.presentations().get(presentationId=presentation_id).execute()
        initial_slide_id = initial_presentation_get['slides'][0]['objectId'] if initial_presentation_get['slides'] else None
        
        if initial_slide_id:
            requests_batch.append({
                'deleteObject': {
                    'objectId': initial_slide_id
                }
            })
            print(f"Added request to delete default initial slide: {initial_slide_id}")
        else:
            print("No default initial slide found to delete.") # Should rarely happen


        # --- Step 2: Add the main Title Slide (first slide of the presentation) ---
        main_title_slide_id = str(uuid.uuid4()) # Unique ID for our main title slide
        main_title_textbox_id = str(uuid.uuid4()) # Unique ID for the title textbox

        requests_batch.append({
            'createSlide': {
                'objectId': main_title_slide_id,
                'slideLayoutReference': {
                    'predefinedLayout': 'TITLE' # Use a layout with a main title area
                }
            }
        })
        
        # Create a text box for the main title on this new slide
        requests_batch.append({
            'createShape': {
                'objectId': main_title_textbox_id, # Or TITLE placeholder type
                'shapeType': 'TEXT_BOX', 
                'elementProperties': {
                    'pageObjectId': main_title_slide_id,
                    'size': {
                        'width': {'magnitude': 9000000, 'unit': 'EMU'}, # 9M EMU = 900pt
                        'height': {'magnitude': 1000000, 'unit': 'EMU'}
                    },
                    'transform': {
                        'scaleX': 1, 'scaleY': 1, 'shearX': 0, 'shearY': 0, 'translateX': 500000, 'translateY': 1000000, 'unit': 'EMU'
                    }
                }
            }
        })

        # Insert text into the main title text box
        requests_batch.append({
            'insertText': {
                'objectId': main_title_textbox_id, # Target the TEXT BOX ID
                'insertionIndex': 0,
                'text': presentation_title
            }
        })
        
        # --- Step 3: Add content slides based on Gemini's output ---
        for i, slide in enumerate(slides_content):
            current_slide_id = str(uuid.uuid4()) # Unique ID for each new content slide
            title_textbox_id = str(uuid.uuid4()) # Unique ID for slide title textbox
            body_textbox_id = str(uuid.uuid4()) # Unique ID for slide body textbox

            # Create a new slide for content
            requests_batch.append({
                'createSlide': {
                    'objectId': current_slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'BLANK' # Changed from 'TITLE_AND_BODY' to 'BLANK'
                    }
                }
            })

            # Create a text box for the slide title
            requests_batch.append({
                'createShape': {
                    'objectId': title_textbox_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': current_slide_id, # Link to the current slide
                        'size': {
                            'width': {'magnitude': 9000000, 'unit': 'EMU'},
                            'height': {'magnitude': 1000000, 'unit': 'EMU'}
                        },
                        'transform': {
                            'scaleX': 1, 'scaleY': 1, 'shearX': 0, 'shearY': 0, 
                            'translateX': 500000, 'translateY': 500000, 'unit': 'EMU'
                        }
                    }
                }
            })

            # Insert heading into the title text box
            requests_batch.append({
                'insertText': {
                    'objectId': title_textbox_id, # Target the TEXT BOX ID
                    'insertionIndex': 0,
                    'text': slide["heading"]
                }
            })
            
            # Create a text box for the body content
            requests_batch.append({
                'createShape': {
                    'objectId': body_textbox_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': current_slide_id, # Link to the current slide
                        'size': {
                            'width': {'magnitude': 9000000, 'unit': 'EMU'},
                            'height': {'magnitude': 4000000, 'unit': 'EMU'}
                        },
                        'transform': {
                            'scaleX': 1, 'scaleY': 1, 'shearX': 0, 'shearY': 0, 
                            'translateX': 500000, 'translateY': 1500000, 'unit': 'EMU'
                        }
                    }
                }
            })

            content_text = "\n".join([f"• {item}" for item in slide["content"]])
            requests_batch.append({
                'insertText': {
                    'objectId': body_textbox_id, # Target the TEXT BOX ID
                    'insertionIndex': 0,
                    'text': content_text
                }
            })
            
            # Apply bullet point formatting
            if slide["content"] and isinstance(slide["content"], list):
                requests_batch.append({
                    'createParagraphBullets': {
                        'objectId': body_textbox_id, # Target the TEXT BOX ID
                        'textRange': {'type': 'ALL'},
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE' # Corrected field: use bulletPreset
                    }
                })

        # Execute all batch requests
        if requests_batch:
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests_batch}
            ).execute()
            print("✅ Slides populated successfully.")
        else:
            print("No slides content provided by Gemini.")

        editor_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        return editor_url

    except HttpError as err:
        print(f"❌ Google Slides API Error: {err}")
        speak(f"An error occurred with the Google Slides API: {err.resp.status}. Please check permissions.")
        if err.resp.status == 400:
            print("Error 400: Bad Request. Check your request payload and object IDs.")
            # Corrected: Access content using err.content and decode it
            print(f"Response: {err.content.decode('utf-8')}")
        elif err.resp.status == 403:
            print("Error 403: Permissions issue. Ensure Google Drive and Slides APIs are enabled and correct scopes are granted.")
        elif err.resp.status == 404:
            print("Error 404: Resource not found.")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred while interacting with Google Slides: {e}")
        speak("I encountered an unexpected issue while creating the presentation.")
        return None

# --- Jarvis Command Integration for Presentations ---
def handle_presentation_command(command, speak):
    """
    Processes a command to generate and create a presentation.
    'speak' is passed to allow this module to use Jarvis's voice output.
    """
    if "generate presentation on" in command.lower():
        topic = command.lower().replace("generate presentation on", "").strip()
        if not topic:
            speak("Please specify a topic for the presentation. Example: 'generate presentation on quantum physics'")
            return

        slides_content = get_slide_content(topic, speak)
        if slides_content:
            print(f"🎨 Creating Google Slides presentation for topic: {topic}")
            url = create_google_presentation(topic, slides_content, speak)
            if url:
                speak("Google Slides presentation generated successfully. Opening it in your browser.")
                webbrowser.open(url) # This line should be handled by main.py
            else:
                speak("Sorry, I failed to create the Google Slides presentation.")
        else:
            speak("Sorry, I could not generate content for the presentation from Gemini.")
    else:
        print("Unrecognized presentation command within handle_presentation_command.")

# Function to explicitly perform Google authentication (e.g., for an 'auth' command)
def authenticate_google_slides(speak):
    """
    Triggers the Google Slides API authentication process.
    """
    speak("Initiating Google Slides API authentication. Please follow the steps in your browser if prompted.")
    get_google_credentials() # This will now try to load existing, then prompt if needed
    speak("Google authentication flow completed.")

# Add the parent directory to sys.path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# The following imports related to 'jarvis_ai' were causing issues as they are not standard libraries
# or were part of a different project structure. They have been commented out to ensure the core
# functionality of this file works. If these modules are essential for other parts of your Jarvis
# project, please ensure their paths and dependencies are correctly set up.
# from jarvis_ai.dotenv_setup import GEN_AI_API_KEY
# from token_store import load_token, refresh_token, authenticate_and_save_token
# from jarvis_ai.jarvis_canva import get_gemini_slide_text, parse_gemini_output, format_slides
# # from jarvis_ai.canva_api import create_design as create_canva_design

# Import get_contact_number from your get_google_contacts.py
try:
    from get_google_contacts import get_contact_number
except ImportError:
    print("WARNING: Could not import get_contact_number from get_google_contacts.py.")
    print("Ensure 'get_google_contacts.py' is in the correct directory and dependencies are met.")
    # Define a dummy function to prevent errors if import fails
    def get_contact_number(name_to_search):
        print(f"Error: get_contact_number not available. Cannot fetch contact for '{name_to_search}'.")
        return None

# You'll need to ensure these are correctly set up in jarvis_ai.config
try:
    from jarvis_ai.config import MAGIC_EMAIL, MAGIC_API_KEY
except ImportError:
    print("WARNING: Could not import MAGIC_EMAIL or MAGIC_API_KEY from jarvis_ai.config.")
    print("Please ensure jarvis_ai/config.py exists and contains these variables.")
    MAGIC_EMAIL = "your_magic_email"  # Placeholder
    MEGIC_API_KEY = "your_magic_api_key"  # Placeholder

logging.basicConfig(level=logging.INFO, filename='jarvis.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# --- NEW FUNCTION: get_email_from_name ---
def get_email_from_name(name_to_search):
    """
    Retrieves the primary email address for a given contact name from Google Contacts.
    """
    creds = get_google_credentials() # Use the unified credential function
    if not creds:
        print("Failed to authenticate with Google. Cannot retrieve contact email.")
        return None

    try:
        service = build('people', 'v1', credentials=creds)
        
        # Search for contacts by name
        # The 'query' parameter is used for free-text search.
        # 'personFields' specifies the fields to retrieve for each person.
        results = service.people().searchContacts(
            query=name_to_search,
            readMask='emailAddresses' # Request email addresses
        ).execute()

        connections = results.get('results', [])
        if not connections:
            print(f"No contacts found for '{name_to_search}'.")
            return None

        # Iterate through connections to find the first email address
        for person_result in connections:
            person = person_result.get('person', {})
            email_addresses = person.get('emailAddresses', [])
            if email_addresses:
                # Prioritize primary email if available, otherwise take the first one
                for email_entry in email_addresses:
                    if email_entry.get('metadata', {}).get('primary'):
                        print(f"Found primary email for '{name_to_search}': {email_entry['value']}")
                        return email_entry['value']
                # If no primary, return the first email found
                print(f"Found email for '{name_to_search}': {email_addresses[0]['value']}")
                return email_addresses[0]['value']
        
        print(f"No email address found for '{name_to_search}'.")
        return None

    except HttpError as err:
        print(f"Google People API Error: {err}")
        if err.resp.status == 403:
            print("Error 403: Permissions issue. Ensure Google People API is enabled and 'contacts.readonly' scope is granted.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching contact email: {e}")
        return None

# --- NEW FUNCTION: get_current_user_email ---
def get_current_user_email():
    """
    Retrieves the primary email address of the currently authenticated Google user.
    """
    creds = get_google_credentials() # Use the unified credential function
    if not creds:
        print("Failed to authenticate with Google. Cannot retrieve current user email.")
        return None

    try:
        service = build('people', 'v1', credentials=creds)
        # Get the 'me' profile which represents the authenticated user
        profile = service.people().get(resourceName='people/me', personFields='emailAddresses').execute()
        
        email_addresses = profile.get('emailAddresses', [])
        if email_addresses:
            for email_entry in email_addresses:
                if email_entry.get('metadata', {}).get('primary'):
                    print(f"Current user's primary email: {email_entry['value']}")
                    return email_entry['value']
            # If no primary, return the first email found
            if email_addresses:
                print(f"Current user's email: {email_addresses[0]['value']}")
                return email_addresses[0]['value']
        
        print("No email address found for the current user.")
        return None

    except HttpError as err:
        print(f"Google People API Error fetching current user email: {err}")
        if err.resp.status == 403:
            print("Error 403: Permissions issue. Ensure Google People API is enabled and 'userinfo.email' scope is granted.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching current user email: {e}")
        return None


# You'll need to ensure these are correctly set up in jarvis_ai.config
try:
    from jarvis_ai.config import MAGIC_EMAIL, MAGIC_API_KEY
except ImportError:
    print("WARNING: Could not import MAGIC_EMAIL or MAGIC_API_KEY from jarvis_ai.config.")
    print("Please ensure jarvis_ai/config.py exists and contains these variables.")
    MAGIC_EMAIL = "your_magic_email"  # Placeholder
    MEGIC_API_KEY = "your_magic_api_key"  # Placeholder

logging.basicConfig(level=logging.INFO, filename='jarvis.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# Authenticate if no token is found (if these functions exist and are needed)
# The token_store functions are commented out as they might not be universally available
# if not load_token():
#     authenticate_and_save_token()

# Refresh the token before making API requests (if these functions exist and are needed)
# try:
#     refresh_token()
# except Exception as e:
#     print(f"❌ Token refresh failed: {e}")
#     print("Reauthenticating...")
#     authenticate_and_save_token()

# Configure Gemini AI - Centralized here to ensure it uses the correct GEN_AI_API_KEY
# This line was originally inside the global scope as well as jarvis_slides.py's
try:
    google_ai.configure(api_key=GEN_AI_API_KEY)
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}. Please check your GEN_AI_API_KEY.")


recognizer = sr.Recognizer()
engine = pyttsx3.init() # Initialize pyttsx3 engine globally

newsapi = "d2bc3c265525474e8679692fba681fd5"
news_url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}" # Corrected URL

# Global variables
news_index = 0
news_articles = []
is_speaking = False
is_listening = False # This tracks if the main Jarvis is actively listening for a command
jarvis_active = False   # This tracks if Jarvis is in an "active" state (hotword detected or manually activated)

# NEW GLOBAL FLAG: To manage complex, multi-step command flows like scheduling
is_handling_complex_command = False
# NEW GLOBAL FLAG: To manage the MCQ answering mode
in_mcq_answer_mode = False

pygame.mixer.init()

# Spotify API credentials (commented out as per your original code)
SPOTIFY_CLIENT_ID = "d6b433c968455b0d585f70337555a"
SPOTIFY_CLIENT_SECRET = "86720b9e78334136ad3c95d47918353a"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"

# Setup Tesseract OCR Path
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    print("WARNING: pytesseract not found. Notification reading may not work.")
except Exception as e:
    print(f"WARNING: Tesseract OCR setup failed: {e}. Notification reading may not work.")

# Global variable to hold the multiprocessing queue
hotword_queue = None

@eel.expose
def speak(text):
    global is_speaking
    is_speaking = True
    print(f"Jarvis: {text}")

    text = str(text)
    try:
        if hasattr(eel, 'DisplayMessage') and callable(eel.DisplayMessage):
            eel.DisplayMessage(text)
        if hasattr(eel, 'receiverText') and callable(eel.receiverText):
            eel.receiverText(text)
    except Exception as e:
        print(f"Error updating Eel display: {e}")

    try:
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.setProperty('rate', 174)

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
    except Exception as e:
        print(f"Error in speak function (gTTS/pygame): {e}. Falling back to pyttsx3.")
        engine.say(text)
        engine.runAndWait()
    is_speaking = False

# --- [Fine-Tuned listen()] ---
def listen():
    """
    Listens for a command from the user using the default microphone.
    Adjusts for ambient noise and attempts to recognize speech using Google Speech Recognition.
    If 'Jarvis' is in the command, it removes the wake word.
    Handles timeouts and recognition errors.
    """
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as source:
        print("🎙️ Say your command...")
        # Display a message to the frontend indicating listening state
        eel.DisplayMessage("Listening...")
        # Show a typing indicator/Siri wave on the frontend
        eel.ShowTyping()

        # Adjust for ambient noise for a slightly longer duration for better accuracy
        # This helps the recognizer determine the noise level of the environment
        r.adjust_for_ambient_noise(source)

        # Lower the energy threshold: This makes the microphone more sensitive
        # It's a balance: too low and it picks up background noise, too high and it misses quiet speech.
        # Experiment with values like 50, 100, 150, 200 based on your microphone and environment.
        r.energy_threshold = 85 # Slightly lower than 150 for potentially quieter voices

        # Set the pause threshold: This is the maximum length of a pause (in seconds)
        # that will be tolerated before the phrase is considered complete.
        # A shorter pause_threshold means it cuts off speech faster after a silence.
        # A longer one allows for more natural pauses in speech but can delay recognition.
        r.pause_threshold = 1.3 # Use the dynamic threshold passed to the function
        
        # Set an operation timeout: If no speech is detected within this time,
        # a sr.WaitTimeoutError is raised. This prevents the listener from hanging indefinitely.
        r.operation_timeout = 15 # Increased timeout to 15 seconds for longer listening
        # This timeout is crucial for parallel input perception. If the user
        # pauses for too long after a prompt, the voice input might time out
        # before they speak, making it seem unresponsive.

        try:
            # Listen for audio from the source within the operation_timeout limit
            print("Microphone adjusted, listening now...")
            audio = r.listen(source, timeout=r.operation_timeout) 
        except sr.WaitTimeoutError:
            # If no speech is detected within the timeout, hide typing and return empty string
            eel.HideTyping()
            print("⏱️ Listening timed out: No speech detected.")
            eel.DisplayMessage("No command detected.")
            return ""
        except Exception as e:
            # Catch other potential microphone/audio errors
            eel.HideTyping()
            print(f"❌ Audio input error: {e}")
            eel.DisplayMessage("Error accessing microphone.")
            return ""

    try:
        # Attempt to recognize the audio using Google Speech Recognition
        # 'en-IN' is good for Indian English accents.
        print("Recognizing speech...")
        command = r.recognize_google(audio, language='en-IN')
        print(f"Recognized command: {command}")
        eel.HideTyping() # Hide typing indicator after recognition

        # Logic for wake word detection ('jarvis') or continuous listening
        if "jarvis" in command.lower():
            # If 'jarvis' is detected, activate the assistant and remove the wake word
            return command.lower().replace("jarvis", "").strip()
        elif jarvis_active:
            # If Jarvis is already active, process the command directly
            return command
        else:
            # If Jarvis is not active and wake word not detected, ignore the command
            print("Wake word 'Jarvis' not detected. Staying idle.")
            return ""
    except sr.UnknownValueError:
        eel.HideTyping()
        print("❓ Could not understand audio.")
        eel.DisplayMessage("Sorry, I didn't understand that.")
        return ""
    except sr.RequestError as e:
        eel.HideTyping()
        print(f"❌ API error during recognition: {e}")
        eel.DisplayMessage("Sorry, there was an API error connecting to Google Speech Recognition.")
        return ""
    except Exception as e:
        eel.HideTyping()
        print(f"An unexpected error occurred during recognition: {e}")
        eel.DisplayMessage("An unexpected error occurred.")
        return ""


# --- [Fine-Tuned listen_for_response()] ---
def listen_for_response(dynamic_pause_threshold=1.2): # Default reduced pause threshold
    """
    Listens for a short response from the user.
    Uses a dynamic pause threshold to allow for quicker responses.
    """
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as source:
        print("🎙️ Awaiting your response...")
        eel.DisplayMessage("Listening for your response...")
        eel.ShowTyping()

        r.adjust_for_ambient_noise(source) # Slightly shorter ambient noise adjustment for responses
        r.energy_threshold = 80 # Potentially even lower for responses which might be softer
        r.pause_threshold = dynamic_pause_threshold # Use the dynamic threshold
        r.operation_timeout = 30 # Increased timeout for responses

        try:
            print("Microphone adjusted for response, listening now...")
            audio = r.listen(source, timeout=r.operation_timeout)
        except sr.WaitTimeoutError:
            eel.HideTyping()
            print("⏱️ Response timed out: No speech detected.")
            eel.DisplayMessage("No response detected.")
            return ""
        except Exception as e:
            eel.HideTyping()
            print(f"❌ Audio input error for response: {e}")
            eel.DisplayMessage("Error accessing microphone for response.")
            return ""

    try:
        command = r.recognize_google(audio, language='en-IN')
        print(f"Recognized response: {command}")
        eel.HideTyping()
        return command
    except sr.UnknownValueError:
        eel.HideTyping()
        print("❓ Could not understand response.")
        eel.DisplayMessage("Sorry, I didn't understand your response.")
        return ""
    except sr.RequestError as e:
        eel.HideTyping()
        print(f"❌ API error during recognition: {e}")
        eel.DisplayMessage("Sorry, there was an API error recognizing your response.")
        return ""
    except Exception as e:
        eel.HideTyping()
        print(f"An unexpected error occurred during response recognition: {e}")
        eel.DisplayMessage("An unexpected error occurred.")
        return ""


# --- [Fine-Tuned listen_for_response_answer()] ---
def listen_for_response_answer(dynamic_pause_threshold=1.2): # Default reduced pause threshold
    """
    Listens for a short response from the user.
    Uses a dynamic pause threshold to allow for quicker responses.
    """
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as source:
        print("🎙️ Awaiting your response...")
        eel.DisplayMessage("Listening for your response...")
        eel.ShowTyping()

        r.adjust_for_ambient_noise(source) # Slightly shorter ambient noise adjustment for responses
        r.energy_threshold = 85 # Potentially even lower for responses which might be softer
        r.pause_threshold = dynamic_pause_threshold # Use the dynamic threshold
        r.operation_timeout = 50 # Increased timeout for responses

        try:
            print("Microphone adjusted for response, listening now...")
            audio = r.listen(source, timeout=r.operation_timeout)
        except sr.WaitTimeoutError:
            eel.HideTyping()
            print("⏱️ Response timed out: No speech detected.")
            eel.DisplayMessage("No response detected.")
            return ""
        except Exception as e:
            eel.HideTyping()
            print(f"❌ Audio input error for response: {e}")
            eel.DisplayMessage("Error accessing microphone for response.")
            return ""

    try:
        command = r.recognize_google(audio, language='en-IN')
        print(f"Recognized response: {command}")
        eel.HideTyping()
        return command
    except sr.UnknownValueError:
        eel.HideTyping()
        print("❓ Could not understand response.")
        eel.DisplayMessage("Sorry, I didn't understand your response.")
        return ""
    except sr.RequestError as e:
        eel.HideTyping()
        print(f"❌ API error during recognition: {e}")
        eel.DisplayMessage("Sorry, there was an API error recognizing your response.")
        return ""
    except Exception as e:
        eel.HideTyping()
        print(f"An unexpected error occurred during response recognition: {e}")
        eel.DisplayMessage("An unexpected error occurred.")
        return ""


# In listen_from_frontend, do not require manual trigger; listen continuously for wake word
@eel.expose
def continous_listen_loop():
    """
    Main loop for continuous listening for the 'Jarvis' wake word.
    Manages Jarvis's active state and passes commands for processing.
    This loop runs in a separate thread, allowing text input from the GUI
    to be processed in parallel via handle_command_from_frontend.
    """
    global jarvis_active, is_listening, is_handling_complex_command, is_speaking, in_mcq_answer_mode # Added in_mcq_answer_mode
    if is_listening:
        print("Already listening. Skipping new listening loop.")
        return

    is_listening = True
    eel.ShowSiriWave() # Show Siri wave for continuous listening state
    eel.DisplayMessage("Listening for 'Jarvis'...")

    try:
        while True:
            # If Jarvis is currently speaking, pause the listening loop
            while is_speaking:
                time.sleep(0.1) # Small delay to avoid busy-waiting while speaking
            
            # If in MCQ answer mode, listen specifically for questions or "end answer"
            if in_mcq_answer_mode:
                print("Please state your multiple-choice question, or say 'end answer' to exit this mode.")
                command = listen_for_response_answer() # Use listen_for_response_answer here
                if command.lower().strip() == "end answer":
                    in_mcq_answer_mode = False
                    print("Exiting multiple-choice question answering mode. Returning to normal operations.")
                    continue # Go back to the main loop to check jarvis_active
                elif command:
                    # Process the MCQ directly within this loop
                    process_mcq_question(command)
                else:
                    speak("I didn't hear a question. Please try again or say 'end answer'.")
                time.sleep(0.5) # Small delay before next listen in MCQ mode
                continue # Continue the loop to stay in MCQ mode

            # If not in MCQ answer mode, proceed with normal command listening
            command = listen()
            if command:
                if not jarvis_active:
                    jarvis_active = True
                    # Speak to confirm activation and prompt for command
                    # speak("Yes, how can I help you?") # Uncomment if you have a speak function
                    eel.DisplayMessage("Jarvis is active and listening...")
                
                # Display the user's recognized command on the frontend
                eel.DisplayMessage(f"You: {command}")
                # Process the recognized command (this function would handle actions)
                processCommand(command) # Call processCommand here
                
                # After processing, if Jarvis is no longer active (e.g., a 'sleep' command was given)
                if not jarvis_active:
                    eel.HideSiriWave() # Hide Siri wave when Jarvis goes to sleep
                    eel.DisplayMessage("Jarvis is sleeping. Say 'Jarvis' to wake me up.")
                    # Break the loop if Jarvis is no longer active, to allow re-initialization if needed
                    break 
            else:
                # If no command or wake word was recognized, and Jarvis is not active,
                # continue displaying the wake word prompt.
                if not jarvis_active:
                    eel.DisplayMessage("Listening for 'Jarvis'...")
            
            # Small delay to prevent busy-waiting, though r.listen() itself blocks
            time.sleep(0.1) 

    except Exception as e:
        # Catch any exceptions that might occur during the continuous loop
        print(f"Error in continuous listen loop: {e}")
        eel.DisplayMessage(f"An error occurred in the listening loop: {e}")
    finally:
        # Ensure cleanup happens even if an error occurs or loop breaks
        is_listening = False
        eel.HideSiriWave()
        eel.DisplayMessage("Jarvis is sleeping. Say 'Jarvis' to wake me up.") # Final message

import os
from datetime import datetime

import os
import re
from datetime import datetime

def convert_to_24h(hour, minute, meridian):
    if meridian == "pm" and hour != 12:
        hour += 12
    elif meridian == "am" and hour == 12:
        hour = 0
    return hour, minute

def set_windows_alarm(hour, minute, message="This is your Jarvis alarm!"):
    task_name = f"JarvisAlarm_{hour}_{minute}"
    time_str = f"{hour:02d}:{minute:02d}"

    # PowerShell script: plays beep and shows popup at specified time
    powershell_script = f'''
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command \\"[System.Media.SystemSounds]::Beep.Play(); Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('{message}', 'Jarvis Alarm')\\""
$trigger = New-ScheduledTaskTrigger -Daily -At {time_str}
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "{task_name}" -Description "Jarvis alarm" -Force
'''

    # Save PowerShell script
    with open("set_alarm.ps1", "w") as f:
        f.write(powershell_script)

    # Run PowerShell script
    os.system("powershell -ExecutionPolicy Bypass -File set_alarm.ps1")
    speak(f"Alarm set for {time_str}")

def parse_alarm_time(command):
    match = re.search(r'(\d{1,2})[:\s](\d{2})\s*(am|pm)', command.lower())
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        meridian = match.group(3)
        if 1 <= hour <= 12 and 0 <= minute <= 59:
            return convert_to_24h(hour, minute, meridian)
    return None

# Text + voice input unified
def handle_alarm_command(command):
    result = parse_alarm_time(command)
    if result:
        hour24, minute24 = result
        set_windows_alarm(hour24, minute24)
    else:
        speak("Please specify the time like 7:30 AM or 6 15 PM.")

text_input_command = None
import eel

@eel.expose
def receive_text_command(command):
    global text_input_command
    text_input_command = command
    print("📥 Received from GUI:", text_input_command)

# Dictionary to store the last uploaded file details (filename, base64_content)
# This allows Jarvis to "remember" the file when "complete" command is given.
# This allows Jarvis to "remember" the file when "complete" command is given.
last_uploaded_file = {}

@eel.expose
def upload_attachment(filename, base64_content, mime_type):
    """
    Receives a file from the frontend (Base64 encoded), decodes it, and saves it.
    Then asks the user what to do with it.
    """
    global last_uploaded_file
    try:
        # Sanitize filename to prevent directory traversal attacks
        safe_filename = os.path.basename(filename)
        # Add a unique UUID to prevent overwriting and ensure unique names
        unique_filename = f"{uuid.uuid4()}_{safe_filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        # Decode the Base64 content
        missing_padding = len(base64_content) % 4
        if missing_padding:
            base64_content += '=' * (4 - missing_padding)
        file_data = base64.b64decode(base64_content)

        # Write the binary data to a file
        with open(file_path, 'wb') as f:
            f.write(file_data)

        print(f"File saved successfully: {file_path}")
        # Store the last uploaded file details
        last_uploaded_file = {
            "path": file_path, # Store the actual path for direct file reading
            "filename": safe_filename,
            "base64_content": base64_content, # Store original base64 for file_completion.py
            "mime_type": mime_type
        }

        # Ask the user what to do with it, explicitly mentioning both input methods
        speak(f"Received {safe_filename}. What should I do with it? You can tell me by voice, or type your command in the chatbox.")
        # The frontend will now wait for user input after this prompt.
        return {"status": "success", "message": f"File '{safe_filename}' uploaded and saved as '{unique_filename}'"}
    except Exception as e:
        print(f"Error uploading file: {e}")
        # Return an error response to JavaScript
        return {"status": "error", "message": str(e)}

@eel.expose
def handle_file_command(command, input_text=None, language="English"): # Added language parameter
    """
    Receives user commands specifically related to the last uploaded file.
    Optionally handles user-provided text input instead of file.
    """
    global last_uploaded_file
    cmd = command.lower().strip()

    # Define command patterns and their corresponding Flask URLs and actions
    # Use more specific patterns for worksheet commands to extract the level
    command_patterns = {
        r"create level (\d+) worksheet": {"url": "http://127.0.0.1:5008/generate-worksheet", "action": "worksheet generation", "level_extract": True},
        r"create worksheet": {"url": "http://127.0.0.1:5008/generate-worksheet", "action": "worksheet generation", "level_extract": False},
        "generate presentation from file": {"url": "http://127.0.0.1:5005/generate-presentation-from-file", "action": "presentation generation"},
        "generate questions": {"url_file": "http://127.0.0.1:5004/generate-questions",
                               "url_no_file": "http://127.0.0.1:5004/generate-questions-no-file",
                               "action": "question generation"},
        "analyze marks": {"url": "http://127.0.0.1:5009/analyze-marks", "action": "marks analysis"}, # NEW: Marks analysis
        "complete": {"url": "http://127.0.0.1:5002/complete-file", "action": "completion"},
        "analyze": {"url": "http://127.0.0.1:5003/analyze-file", "action": "analysis"},
        "summarize": {"url": "http://127.0.0.1:5003/summarization", "action": "summarization"},
        "solve": {"url": "http://127.0.0.1:5006/solve-question", "action": "problem solving"},
        "get information": {"url": "http://127.0.0.1:5007/get-information", "action": "information retrieval"},
        # NEW: Lesson Plan command
        "plan lesson": {"url": "http://127.0.0.1:5010/plan-lesson", "action": "lesson plan generation"},
        "generate lesson plan": {"url": "http://127.0.0.1:5010/plan-lesson", "action": "lesson plan generation"},
    }

    selected_command_info = None
    target_level = None

    # Iterate through patterns to find a match, prioritizing specific ones
    for pattern_str, info in command_patterns.items():
        if info.get("level_extract"):
            match = re.search(pattern_str, cmd)
            if match:
                selected_command_info = info
                target_level = int(match.group(1))
                break
        elif pattern_str in cmd:
            selected_command_info = info
            break

    if not selected_command_info:
        speak("I'm not sure what you mean by that. Please specify a valid action for the file (e.g., 'complete', 'analyze', 'summarize', 'generate questions', 'generate presentation from file', 'create worksheet', 'solve', 'get information', 'analyze marks', 'plan lesson').")
        return

    flask_url = selected_command_info["url"] if "url" in selected_command_info else None
    action_type = selected_command_info["action"]
    payload = {}

    # Determine the correct Flask URL and construct payload
    if action_type == "question generation":
        if last_uploaded_file:
            flask_url = selected_command_info["url_file"]
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"]
            }
        # Inside handle_file_command, for question generation without file
        else:
            flask_url = selected_command_info["url_no_file"]
            action_type = "question generation without file"

            topic = None
            if input_text:
                topic = input_text.strip()
                print(f"DEBUG: Topic from input_text: {topic}")
            else:
                speak("What topic would you like questions about?")
                print("DEBUG: Jarvis asked for topic, waiting for voice input...")
                topic = listen()
                print(f"DEBUG: Voice input received for topic: {topic}")

            if not topic:
                speak("No topic provided. Cannot generate questions.")
                return
            payload["topic"] = topic
            
    elif action_type == "worksheet generation":
        if last_uploaded_file:
            # Flask URL is already determined by the pattern match
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"]
            }
            if target_level: # Add target_level to payload if specified
                payload["level"] = target_level
                action_type = f"level {target_level} worksheet generation"
        else:
            speak(f"I don't have a file to process for '{action_type}' right now. Please upload one.")
            return
    elif action_type == "lesson plan generation": # NEW: Lesson plan generation payload
        if last_uploaded_file:
            flask_url = selected_command_info["url"]
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"]
            }
            # Optionally, ask for teacher notes here if you want to add that feature
            # speak("Do you have any specific notes or requirements for the lesson plan?")
            # teacher_notes = listen_for_response().strip()
            # if teacher_notes:
            #     payload["teacher_notes"] = teacher_notes
        else:
            speak(f"I don't have a file to process for '{action_type}' right now. Please upload one.")
            return
    elif action_type == "presentation generation":
        if last_uploaded_file:
            flask_url = selected_command_info["url"]
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"]
            }
            payload["use_template"] = False
            payload["template_id"] = None
        else:
            speak(f"I don't have a file to process for '{action_type}' right now. Please upload one.")
            return
    elif action_type == "problem solving":
        if last_uploaded_file:
            flask_url = selected_command_info["url"]
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"]
            }
        else:
            speak(f"I don't have a file to process for '{action_type}' right now. Please upload one.")
            return
    elif action_type == "information retrieval":
        if last_uploaded_file:
            flask_url = selected_command_info["url"]
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"],
                "language": language # Pass the extracted language here
            }
        else:
            speak(f"I don't have a file to process for '{action_type}' right now. Please upload one.")
            return
    elif action_type == "marks analysis": # NEW: Marks analysis payload
        if last_uploaded_file:
            flask_url = selected_command_info["url"]
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"]
            }
        else:
            speak(f"I don't have an Excel file to analyze marks from. Please upload one.")
            return
    # FIX START: Explicitly handle 'complete', 'analyze', 'summarize' when last_uploaded_file exists
    elif action_type == "completion" or action_type == "analysis" or action_type == "summarization":
        if last_uploaded_file:
            # flask_url is already set by selected_command_info["url"]
            payload = {
                "file_data": last_uploaded_file["base64_content"],
                "filename": last_uploaded_file["filename"],
                "mime_type": last_uploaded_file["mime_type"]
            }
        else:
            speak(f"I don't have a file to process for '{action_type}' right now. Please upload one.")
            return
    # FIX END
    else: # This 'else' block should now primarily handle cases where input_text might be the primary source
        if input_text:
            payload["text_input"] = input_text
            # flask_url should already be set by selected_command_info["url"] if it's a valid command
        elif not last_uploaded_file: # If no input_text and no last_uploaded_file, then we can't proceed
            speak(f"I don't have a file or text to process for '{action_type}' right now. Please upload one or provide text input.")
            return

    speak(f"Okay, I will perform {action_type}.")
    print(f"DEBUG: Preparing {action_type} request to Flask URL: {flask_url} with payload: {payload if payload else 'No explicit payload (file-based operation likely)'}")

    response = None # Initialize response to None to prevent UnboundLocalError
    try:
        # For marks analysis, we need to send the file as multipart/form-data
        if action_type == "marks analysis":
            files = {'file': (last_uploaded_file['filename'], base64.b64decode(last_uploaded_file['base64_content']), last_uploaded_file['mime_type'])}
            response = requests.post(flask_url, files=files)
        else:
            response = requests.post(flask_url, json=payload)
        
        response.raise_for_status() # This will raise an HTTPError for bad responses (4xx or 5xx)

        # --- MODIFIED: Check for JSON response containing file data for worksheet/lesson plan generation ---
        if action_type == "worksheet generation" or "worksheet generation" in action_type or action_type == "lesson plan generation": # Added lesson plan
            result = response.json()
            # Check for 'completed_filename' and 'completed_file_data' (from file_completion.py)
            # OR 'lesson_plan_filename' and 'lesson_plan_data' (from lesson_planner.py)
            if result.get("completed_filename") and result.get("completed_file_data"):
                completed_filename = result["completed_filename"]
                completed_file_data = result["completed_file_data"]
            elif result.get("lesson_plan_filename") and result.get("lesson_plan_data"): # NEW: Check for lesson plan keys
                completed_filename = result["lesson_plan_filename"]
                completed_file_data = result["lesson_plan_data"]
            else:
                speak(f"File {action_type} failed. No completed file or data received.")
                print(f"ERROR: File {action_type} response missing expected file data keys: {result}")
                return # Exit if no expected data

            try:
                if hasattr(eel, 'downloadCompletedFile') and callable(getattr(eel, 'downloadCompletedFile')):
                    eel.downloadCompletedFile(completed_file_data, completed_filename)()
                    speak(f"{action_type.replace(' generation', '')} '{completed_filename}' generated and ready for download.")
                else:
                    print("WARNING: eel.downloadCompletedFile is not defined or not callable in the frontend.")
                    speak(f"{action_type.replace(' generation', '')} '{completed_filename}' generated. Download functionality not available.")

            except Exception as e:
                print(f"ERROR: Failed to call eel.downloadCompletedFile for {action_type}: {e}")
                speak(f"An issue occurred while preparing your {action_type} download. Error: {e}")
            return # Exit the function as it's handled
        elif action_type == "marks analysis": # Handle marks analysis response
            result = response.json()
            if result.get("status") == "success":
                messages_to_send = result.get("messages_to_send", []) # Get the list of messages
                
                if messages_to_send:
                    speak(f"Marks analysis completed. Preparing to send {len(messages_to_send)} WhatsApp messages to students with low marks.")
                    for msg_data in messages_to_send:
                        student_name = msg_data['student_name']
                        phone_number = msg_data['phone_number']
                        message_content = msg_data['message']
                        
                        # Call the main.py's whatsApp function for actual desktop automation
                        # Make sure your main.py's whatsApp function is accessible here.
                        # The 'target_tab' logic from your provided whatsApp function will be used.
                        whatsApp(phone_number, message_content, 'message', student_name)
                        
                        print(f"Attempted WhatsApp to {student_name} ({phone_number}): {message_content[:100]}...")
                        time.sleep(2) # Add a small delay between sending attempts if desired

                    speak("All WhatsApp messages have been initiated. Please check your WhatsApp Desktop or Web for confirmation and sending.")
                else:
                    speak("Marks analysis completed. No students found with marks less than 10, so no messages were sent.")
                
                # Optionally, display a summary in the frontend
                # Assuming eel.receiverText is defined and accessible
                # eel.receiverText(f"<b>Marks Analysis Report:</b><br><br>"
                #                  f"Status: {result.get('status')}<br>"
                #                  f"Low marks students found: {result.get('low_marks_students_count')}<br>"
                #                  f"Messages prepared: {len(messages_to_send)}<br><br>"
                #                  f"Check your WhatsApp for messages to be sent.")
            else:
                speak(f"Marks analysis failed: {result.get('message', 'Unknown error')}")
                print(f"ERROR: Marks analysis failed: {result}")
            return # Exit the function as it's handled

        # If it's not a worksheet download or marks analysis, assume it's JSON and try to parse it
        result = response.json()

        if "question generation" in action_type:
            if result.get("questions"):
                questions_list = result["questions"]
                speak(f"Successfully generated {len(questions_list)} questions.")
                print(f"Generated {len(questions_list)} questions.")

                for i, q in enumerate(questions_list):
                    question_text = q.get('question', 'No question text provided').strip()
                    question_type = q.get('type', 'Unknown').strip()
                    difficulty = q.get('difficulty', 'Unknown').strip()
                    correct_answer = str(q.get('correct_answer', '')).strip().lower()

                    speak_text = f"Question {i+1}: {question_text}"
                    print(f"\n--- Question {i+1} ---")
                    print(f"Question: {question_text} (Type: {question_type}, Difficulty: {difficulty})")

                    if question_type == "Multiple Choice":
                        options_text_spoken = ""
                        options_for_check = []
                        if q.get('options') and isinstance(q['options'], list):
                            for idx, option in enumerate(q['options']):
                                option_str = str(option).strip()
                                options_text_spoken += f" Option {chr(65 + idx)}. {option_str}." # Added period for clarity
                                options_for_check.append(option_str.lower())
                                print(f"   Option {chr(65 + idx)}: {option_str}")
                        else:
                            print("   (Missing or invalid options for MCQ)")
                        speak_text += options_text_spoken
                        speak(speak_text)
                    else:
                        speak(speak_text)
                    time.sleep(0.5)

                    user_response = listen_for_response(dynamic_pause_threshold=0.9).strip().lower()

                    if user_response:
                        speak(f"I heard you say: {user_response}")
                        print(f"DEBUG: User response detected: '{user_response}'")
                        time.sleep(1)

                        is_correct = False
                        if question_type == "Multiple Choice":
                            if user_response == correct_answer:
                                is_correct = True
                            elif len(options_for_check) > 0:
                                try:
                                    option_index_from_letter = ord(user_response) - ord('a')
                                    if 0 <= option_index_from_letter < len(options_for_check):
                                        if options_for_check[option_index_from_letter] == correct_answer:
                                            is_correct = True
                                except TypeError:
                                    pass

                            if not is_correct and correct_answer:
                                if user_response == correct_answer:
                                    is_correct = True
                                elif correct_answer in user_response:
                                    is_correct = True
                                elif user_response in options_for_check and user_response == correct_answer:
                                    is_correct = True

                            if is_correct:
                                speak("That's the correct answer!")
                            else:
                                speak(f"That's incorrect. The correct answer was: {q.get('correct_answer', 'not provided')}.")
                        else:
                            speak(f"You answered: '{user_response}'.")
                            if correct_answer:
                                speak(f"The expected answer was: {q.get('correct_answer', 'not provided')}.")
                            else:
                                speak("Moving to the next question.")

                    else:
                        speak("No response detected. Moving to the next question.")
                        print("DEBUG: No user response detected.")
                        time.sleep(1.5)
            else:
                speak(f"File {action_type} failed. No questions received.")
                print(f"ERROR: File {action_type} response missing 'questions' data: {result}")
        elif action_type == "presentation generation":
            if result.get("presentation_url"):
                presentation_url = result["presentation_url"]
                speak("Google Slides presentation generated successfully from your file. Opening it in your browser.")
                webbrowser.open(presentation_url)
            else:
                speak(f"File {action_type} failed. No presentation URL received.")
                print(f"ERROR: File {action_type} response missing 'presentation_url': {result}")
        elif action_type == "problem solving":
            if result.get("solution"):
                solution_text = result["solution"]
                speak("I have a solution for the problem. Displaying it now.")
                # Assuming eel.receiverText is defined and accessible
                # eel.receiverText(f"<b>Problem Solution:</b><br><br>{solution_text}")
            else:
                speak(f"File {action_type} failed. No solution received.")
                print(f"ERROR: File {action_type} response missing 'solution': {result}")
        elif action_type == "information retrieval":
            if result.get("information"):
                information_text = result["information"]
                speak("I have retrieved the information. Displaying it now.")
                # Remove text within parentheses and asterisks for speaking
                information_text_for_speak = re.sub(r'\s*\([^)]*\)', '', information_text) # Remove parentheses
                information_text_for_speak = information_text_for_speak.replace('*', '').strip() # Remove asterisks
                speak(information_text_for_speak) # Modified to speak without bracketed text or asterisks
            else:
                speak(f"File {action_type} failed. No information received.")
                print(f"ERROR: File {action_type} response missing 'information': {result}")
        else: # For completion, analysis, summarization (and now worksheet if not caught above)
            if result.get("completed_filename") and result.get("completed_file_data"):
                completed_filename = result["completed_filename"]
                completed_file_data = result["completed_file_data"]
                try:
                    if hasattr(eel, 'downloadCompletedFile') and callable(getattr(eel, 'downloadCompletedFile')):
                        eel.downloadCompletedFile(completed_file_data, completed_filename)()
                        speak(f"File '{completed_filename}' {action_type} completed and ready for download.")
                    else:
                        print("WARNING: eel.downloadCompletedFile is not defined or not callable in the frontend.")
                        speak(f"File '{completed_filename}' {action_type} completed. Download functionality not available.")

                except Exception as e:
                    print(f"ERROR: Failed to call eel.downloadCompletedFile: {e}")
                    speak(f"An issue occurred while preparing your worksheet download. Error: {e}")
            else:
                speak(f"File {action_type} failed. No completed file or data received.")
                print(f"ERROR: File {action_type} response missing 'completed_filename' or 'completed_file_data': {result}")

    except requests.exceptions.RequestException as req_err:
        error_detail = ""
        if response is not None and hasattr(req_err, 'response') and req_err.response is not None: # Check if response is not None
            try:
                # Attempt to parse JSON from the error response
                error_json = req_err.response.json()
                if isinstance(error_json, dict):
                    error_detail = error_json.get('error', req_err.response.text)
                else:
                    error_detail = req_err.response.text # Fallback if not a dict
            except json.JSONDecodeError:
                # If the error response itself is not JSON, use its raw text
                error_detail = req_err.response.text if req_err.response else str(req_err)
            except Exception as inner_e:
                print(f"DEBUG: Error extracting error_detail from response: {inner_e}")
                error_detail = req_err.response.text if req_err.response else str(req_err)
        else:
            error_detail = str(req_err)

        speak(f"Failed to connect to the file {action_type} service or an issue occurred with the request. Error: {error_detail}")
        print(f"ERROR: Flask service connection error or bad request: {req_err}. Details: {error_detail}")
    except json.JSONDecodeError as json_err:
        speak(f"Received invalid response from file {action_type} service.")
        # Check if response is not None before accessing its text
        response_text = response.text if response is not None and hasattr(response, 'text') else 'No response text available.'
        print(f"ERROR: JSON decoding error from Flask response: {json_err}. Response text: {response_text}")
    except Exception as e:
        speak(f"An unexpected error occurred during file {action_type}: {e}")
        print(f"ERROR: General error during file {action_type}: {e}")
    finally:
        # Clear last_uploaded_file only if it was used for a file-based operation
        # The 'question generation without file' path should not clear it.
        if last_uploaded_file and action_type != "question generation without file":
            last_uploaded_file = {}
            print("DEBUG: last_uploaded_file cleared.")
            
# --- Core Jarvis Functions (same as before) ---
def find_phone_link_window():
    windows = gw.getWindowsWithTitle('Phone Link')
    return windows[0] if windows else None

def read_notifications(window):
    if not window:
        speak("Phone Link is not open.")
        return

    window.activate()
    time.sleep(1)

    x, y, width, height = window.left + 200, window.top + 100, 400, 500
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    screenshot.save('notification_area.png')

    try:
        if 'pytesseract' in sys.modules:
            text = pytesseract.image_to_string(Image.open('notification_area.png'))
        else:
            text = ""
            print("pytesseract not available for OCR. Skipping notification read.")
    except Exception as e:
        print(f"Error with Tesseract OCR during notification read: {e}. Ensure Tesseract is installed and path is correct.")
        text = ""

    if text.strip():
        speak(f"You have a notification: {text}")
    else:
        speak("No new notifications detected or could not read them.")

import requests

def generate_image_pollinations(prompt: str, save_path="assets/generated_pollinations_image.png"):
    try:
        from urllib.parse import quote
        import requests

        safe_prompt = quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}"

        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"🌐 Pollinations image saved to {save_path}")
            return save_path
        else:
            print("❌ Pollinations failed.")
            return None
    except Exception as e:
        print("❌ Pollinations error:", e)
        return None


def send_reply(window, reply_text):
    if not window:
        speak("Phone Link is not open.")
        return

    x, y = window.left + 250, window.top + 600
    pyautogui.click(x, y)
    time.sleep(1)

    pyautogui.write(reply_text, interval=0.05)
    pyautogui.press('enter')
    speak("Reply sent!")

def PlayYoutube(query):
    search_term = query.replace("play", "").replace("on youtube", "").strip()
    speak(f"Playing {search_term} on YouTube")
    kit.playonyt(search_term)

def fetch_news():
    global news_index, news_articles
    speak("Fetching the latest news")
    r = requests.get(news_url)
    if r.status_code == 200:
        data = r.json()
        news_articles = data.get('articles', [])
        news_index = 0
        if news_articles:
            for article in news_articles[:3]:
                speak(article['title'])
            news_index += 3
        else:
            speak("No news articles found.")
    else:
        speak(f"Failed to fetch news. Status code: {r.status_code}")

def fetch_next_news():
    global news_index, news_articles
    if news_articles:
        next_articles = news_articles[news_index:news_index + 3]
        if next_articles:
            for article in next_articles:
                speak(article['title'])
            news_index += 3
        else:
            speak("No more news articles available.")
    else:
        speak("Please say 'news' first to fetch the latest headlines.")

def aiProcess(command):
    model = google_ai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(
        f"You are a virtual assistant named Jarvis skilled in general tasks like Alexa and Google Cloud.\n{command}")
    return response.text

def build_gemini_prompt(topic):
    """
    Generates a prompt for Gemini AI based on the given topic.
    """
    return f"Create a detailed presentation outline on the topic: {topic}"

def open_website(url):
    speak(f"Opening {url}")
    webbrowser.open(url)

import requests

def generate_image_pollinations(prompt, output_path="pollinations_output.jpg"):
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return output_path
    else:
        print(f"Pollinations error: {response.status_code}")
        return None


# --- WhatsApp and Contact Functions ---
# get_contact_number is now imported from get_google_contacts.py
@eel.expose
def extract_phone_number(text):
    """
    Extracts a 10+ digit number from the voice command, handling common spoken number formats.
    """
    cleaned_text = text.lower().replace("number", "").replace("call", "").replace("dial", "").strip()
    cleaned_text = re.sub(r'[()\s-]', '', cleaned_text)

    # Modified regex to allow optional '+' at the beginning for international numbers
    match = re.search(r'\b\+?\d{10,15}\b', cleaned_text)
    if match:
        return match.group()
    return None

def whatsApp(mobile_no, message, flag, name):
    jarvis_message = ""
    whatsapp_url = ""

    # Define tab count based on action
    if flag == 'message':
        target_tab = 12 # Changed from 13 to 12 as per your request
        encoded_message = quote(message)
        whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
        jarvis_message = "Message sent successfully to " + name
    elif flag == 'call':
        target_tab = 6
        whatsapp_url = f"whatsapp://send?phone={mobile_no}"
        jarvis_message = "Calling " + name + " on WhatsApp."
    elif flag == 'video_call':
        target_tab = 5
        whatsapp_url = f"whatsapp://send?phone={mobile_no}"
        jarvis_message = "Starting video call with " + name + " on WhatsApp."
    else:
        speak("Invalid WhatsApp action requested.")
        return

    print(f"[DEBUG] Starting WhatsApp Desktop...")
    try:
        subprocess.run('start whatsapp://', shell=True)
        time.sleep(5)  # Give WhatsApp time to open

        print(f"[DEBUG] Opening WhatsApp URL: {whatsapp_url}")
        subprocess.run(f'start "" "{whatsapp_url}"', shell=True)
        time.sleep(8)  # Allow time to open and load

        whatsapp_window = None
        for _ in range(10):
            windows = gw.getWindowsWithTitle('WhatsApp')
            if windows:
                for win in windows:
                    if "WhatsApp" in win.title and not win.isMinimized:
                        whatsapp_window = win
                        break
            if whatsapp_window:
                break
            time.sleep(1)

        if whatsapp_window:
            print("[DEBUG] Activating WhatsApp window.")
            whatsapp_window.activate()
            try:
                whatsapp_window.maximize()
            except Exception:
                pass
            time.sleep(2)
            pyautogui.click(whatsapp_window.left + 100, whatsapp_window.top + 100)
            time.sleep(1)
        else:
            if flag == 'message':
                web_url = f"https://wa.me/{mobile_no}?text={encoded_message}"
                webbrowser.open(web_url)
                speak("WhatsApp Desktop not found, opening WhatsApp Web instead.")
            else:
                speak("Could not find WhatsApp window. Please ensure it is open and not minimized.")
            return

        print(f"[DEBUG] Simulating Ctrl+F to focus WhatsApp.")
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(1.5)

        print(f"[DEBUG] Pressing Tab {target_tab} times to reach {flag} button.")
        for _ in range(target_tab):
            pyautogui.press('tab')
            time.sleep(0.25)

        print(f"[DEBUG] Pressing Enter to trigger {flag}.")
        pyautogui.press('enter')
        speak(jarvis_message)

    except Exception as e:
        speak(f"An error occurred during the WhatsApp operation: {e}")
        print(f"[ERROR] {e}")

def jarvis_whatsapp_message(contact_query, message_text):
    phone_number = None
    name_for_response = contact_query # Default to query if not a number

    number_from_query = extract_phone_number(contact_query)
    if number_from_query:
        phone_number = number_from_query
        speak(f"Detected number {phone_number} from your command. Preparing WhatsApp message.")
        name_for_response = phone_number # Use number in response if extracted
    else:
        speak(f"Searching for {contact_query} in your Google Contacts.")
        phone_number = get_contact_number(contact_query)
        if phone_number:
            speak(f"Found {contact_query} with number {phone_number}.")
        else:
            name_for_response = contact_query

    if phone_number:
        if not phone_number.startswith('+'):
            if len(phone_number) == 10:
                phone_number = '+91' + phone_number
                speak(f"Assuming Indian number, formatting to {phone_number}")
            else:
                speak(f"The number '{phone_number}' does not start with a country code and is not a 10-digit number. Please specify the full number including the country code (e.g., +1 for USA, +91 for India).")
                return

        whatsApp(phone_number, message_text, 'message', name_for_response)
    else:
        speak("Sorry, I could not find a number for that contact to send a WhatsApp message.")

def jarvis_whatsapp_call(contact_query):
    phone_number = None
    name_for_response = contact_query

    number_from_query = extract_phone_number(contact_query)
    if number_from_query:
        phone_number = number_from_query
        speak(f"Detected number {phone_number} from your command. Preparing WhatsApp call.")
        name_for_response = phone_number
    else:
        speak(f"Searching for {contact_query} in your Google Contacts.")
        phone_number = get_contact_number(contact_query)
        if phone_number:
            speak(f"Found {contact_query} with number {phone_number}.")
        else:
            name_for_response = contact_query

    if phone_number:
        if not phone_number.startswith('+'):
            if phone_number.startswith('91') and len(phone_number) == 12:
                phone_number = '+' + phone_number
                speak(f"Detected number with Indian country code. Formatting to {phone_number}")
            elif len(phone_number) == 10:
                phone_number = '+91' + phone_number
                speak(f"Assuming Indian number, formatting to {phone_number}")
            else:
                speak(f"The number '{phone_number}' does not start with a country code and is not a 10-digit number. Please specify the full number including the country code (e.g., +1 for USA, +91 for India).")
                return

        whatsApp(phone_number, '', 'call', name_for_response)  # Message is empty for calls
    else:
        speak("Sorry, I could not find a number for that contact to make a WhatsApp call.")


def jarvis_whatsapp_video_call(contact_query):
    phone_number = None
    name_for_response = contact_query

    number_from_query = extract_phone_number(contact_query)
    if number_from_query:
        phone_number = number_from_query
        speak(f"Detected number {phone_number} from your command. Preparing WhatsApp video call.")
        name_for_response = phone_number
    else:
        speak(f"Searching for {contact_query} in your Google Contacts.")
        phone_number = get_contact_number(contact_query)
        if phone_number:
            speak(f"Found {contact_query} with number {phone_number}.")
        else:
            name_for_response = contact_query

    if phone_number:
        if not phone_number.startswith('+'):
            if len(phone_number) == 10:
                phone_number = '+91' + phone_number
                speak(f"Assuming Indian number, formatting to {phone_number}")
            else:
                speak(f"The number '{phone_number}' does not start with a country code and is not a 10-digit number. Please specify the full number including the country code (e.g., +1 for USA, +91 for India).")
                return

        whatsApp(phone_number, '', 'video_call', name_for_response) # Message is empty for video calls
    else:
        speak("Sorry, I could not find a number for that contact to make a WhatsApp video call.")


# --- FILE ATTACHMENT HANDLING ---
# Create a directory for uploaded files if it's not exist
UPLOAD_FOLDER = 'web/uploaded_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Note: The `upload_attachment` function is now defined above to set `last_uploaded_file`

@eel.expose
def get_weather(city="Mumbai"):
    import requests
    from datetime import datetime, timedelta
    from apikey import weather_api
    import collections

    city = city.strip().title()
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={weather_api}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != "200":
            eel.receiverText(f"⚠️ Couldn't get weather for {city}.")
            return

        forecasts = data["list"]
        forecast_by_day = collections.defaultdict(list)

        for entry in forecasts:
            date_txt = entry["dt_txt"]
            date = date_txt.split(" ")[0]
            forecast_by_day[date].append(entry)

        today = datetime.now().date()
        output_html = f"<b>📍 Weather Forecast for {city}</b><br><br>"
        today_spoken_text = ""

        for i in range(3):
            day = today + timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            readable_day = day.strftime("%A, %d %B")

            if day_str not in forecast_by_day:
                continue
            entries = forecast_by_day[day_str]
            temps = [e["main"]["temp"] for e in entries]
            avg_temp = round(sum(temps) / len(temps), 1)

            conditions = [e["weather"][0]["description"] for e in entries]
            most_common = max(set(conditions), key=conditions.count)
            icon = "☀️" if "clear" in most_common else \
                   "🌧️" if "rain" in most_common else \
                   "⛈️" if "thunder" in most_common or "storm" in most_common else \
                   "☁️" if "cloud" in most_common else \
                   "❄️" if "snow" in most_common else \
                   "🌫️" if "fog" in most_common or "mist" in most_common else "️"

            output_html += (
                f"{icon} <b>{readable_day}</b><br>"
                f"Condition: {most_common.title()}<br>"
                f"Avg Temperature: {avg_temp}°C<br><br>"
            )

            # Save today's text for TTS
            if i == 0:
                today_spoken_text = (
                    f"Today in {city}, the weather is mostly {most_common}, "
                    f"with an average temperature of {avg_temp} degrees Celsius."
                )

        # Send to frontend
        eel.receiverText(output_html)

        # Call your speak() function
        if today_spoken_text:
            speak(today_spoken_text)

    except Exception as e:
        eel.receiverText("⚠️ Error fetching weather.")
        print(f"[ERROR] {e}")


import pyautogui
import time

def open_app_by_search(app_name):
    """
    Opens an application by using the Windows search bar.

    Args:
        app_name (str): The name of the application to open (e.g., "notepad", "chrome").
    """
    print(f"🔍 Searching for: {app_name}")
    
    # Press Win + S (open search bar)
    pyautogui.hotkey('win', 's')
    time.sleep(1)  # Give the search bar time to open
    
    # Type the app name
    pyautogui.typewrite(app_name, interval=0.05)
    time.sleep(1)  # Give Windows search time to find the app
    # Press Enter to open the app
    pyautogui.press('enter')
    print(f"🚀 Attempting to open: {app_name}")

def confirm_and_execute(action):
    speak(f"Are you sure you want to {action}? Say 'yes' to confirm.")
    response = listen()
    if response and "yes" in response.lower():
        if action == "shutdown":
            shutdown()
        elif action == "restart":
            restart()
    else:
        speak(f"{action.capitalize()} cancelled.")

# --- Configuration for Scheduling Assistant ---
# Separate token file for Calendar to avoid conflicts with Slides token, though they can share if scopes allow

# GOOGLE_CREDENTIALS_FILE is defined globally at the top

# --- Utility Functions ---
def print_message(message, level="info"):
    """Prints messages with formatting based on level."""
    if level == "info":
        print(f"ℹ️ {message}")
    elif level == "success":
        print(f"✅ {message}")
    elif level == "warning":
        print(f"⚠️ {message}")
    elif level == "error":
        print(f"❌ {message}")
    elif level == "agent":
        print(f"🤖 Agent: {message}")
    elif level == "debug":
        print(f"🐛 DEBUG: {message}") # Added debug level for verbose output
    else:
        print(message)

def retry_on_exception(retries=3, delay=2, exceptions=(Exception,)):
    """Decorator to retry a function on specified exceptions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print_message(f"Attempt {i + 1}/{retries} failed: {e}", "warning")
                    if i < retries - 1:
                        time.sleep(delay)
            raise # Re-raise the last exception if all retries fail
        return wrapper
    return decorator

# --- Google Calendar API Authentication ---
@retry_on_exception(retries=2, delay=5, exceptions=(HttpError,))
def get_google_calendar_credentials_main():
    """
    Handles Google OAuth2.0 authentication for Google Calendar API within main.py.
    Uses a separate token file to avoid overwriting existing Jarvis tokens.
    """
    creds = None
    if os.path.exists(GOOGLE_CALENDAR_TOKEN_FILE):
        print_message("Attempting to load Google Calendar credentials from calendar_token.json...")
        try:
            creds = Credentials.from_authorized_user_file(GOOGLE_CALENDAR_TOKEN_FILE, SCOPES)
            print_message("Google Calendar credentials loaded.", "success")
            # Check if all required calendar scopes are covered
            if not all(s in creds.scopes for s in SCOPES): # Check against the full SCOPES list
                print_message("Loaded calendar credentials do not cover all required scopes. Forcing re-authentication.", "warning")
                creds = None
        except Exception as e:
            print_message(f"Error loading credentials from calendar_token.json: {e}. Re-authenticating.", "error")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print_message("Google credentials expired, attempting to refresh...")
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow # Moved import here
                # Use the existing flow to refresh credentials
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds.refresh(Request())
                print_message("Google Calendar credentials refreshed successfully.", "success")
                if not all(s in creds.scopes for s in SCOPES): # Re-check scopes after refresh
                    print_message("Refreshed credentials still do not cover all required scopes. Initiating new authentication flow.", "warning")
                    creds = None
            except Exception as e:
                print_message(f"Error refreshing credentials: {e}. Initiating new authentication flow.", "error")
                creds = None
        
        if not creds:
            print_message("Initiating new Google Calendar authentication flow...")
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow # Moved import here
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                print_message("Google Calendar authentication completed.", "success")
            except Exception as e:
                print_message(f"Error during Google Calendar authentication flow: {e}. Ensure '{GOOGLE_CREDENTIALS_FILE}' is valid and present and that you have enabled 'Google Calendar API' in Google Cloud Console.", "error")
                return None
            
            try:
                with open(GOOGLE_CALENDAR_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print_message("Google Calendar credentials saved to calendar_token.json.", "success")
            except Exception as e:
                print_message(f"Error saving credentials to calendar_token.json: {e}", "error")
                
    return creds


# --- Google Calendar API Interactions ---
@retry_on_exception(retries=3, delay=2, exceptions=(HttpError,))
def get_free_busy_slots(service, participant_emails, start_time: dt.datetime, end_time: dt.datetime): # Use dt.datetime
    """
    Fetches free/busy information for a list of participants within a specified time range.
    Times should be timezone-aware (UTC recommended).
    """
    print_message(f"Checking free/busy for {len(participant_emails)} participants from {start_time.isoformat()} to {end_time.isoformat()}...", "info")
    
    # Ensure times are timezone-aware (UTC)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=dt.timezone.utc) # Use dt.timezone
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=dt.timezone.utc) # Use dt.timezone

    items = [{"id": email} for email in participant_emails]
    
    body = {
        "timeMin": start_time.isoformat(),
        "timeMax": end_time.isoformat(),
        "items": items
    }
    
    try:
        response = service.freebusy().query(body=body).execute()
        print_message("Free/busy information fetched.", "success")
        return response['calendars']
    except HttpError as error:
        print_message(f"Failed to fetch free/busy information: {error}", "error")
        raise
    except Exception as e:
        print_message(f"An unexpected error occurred while fetching free/busy: {e}", "error")
        raise

@retry_on_exception(retries=3, delay=2, exceptions=(HttpError,))
def create_calendar_event(service, event_details: dict):
    """
    Creates a new event on the user's Google Calendar.
    `event_details` should be a dictionary following Google Calendar API's Event resource format.
    """
    print_message(f"Attempting to create event: '{event_details.get('summary', 'No Title')}'...", "info")
    try:
        event = service.events().insert(calendarId='primary', body=event_details).execute()
        print_message(f"Event created: {event.get('htmlLink')}", "success")
        return event
    except HttpError as error:
        print_message(f"Failed to create event: {error}", "error")
        raise
    except Exception as e:
        print_message(f"An unexpected error occurred while creating event: {e}", "error")
        raise

# --- Agentic Logic with Gemini ---
def get_gemini_model_for_scheduling():
    """Initializes and returns the Gemini Pro model for scheduling tasks."""
    try:
        model = google_ai.GenerativeModel("gemini-2.5-flash") # Using gemini-2.5-flash for potentially better performance
        return model
    except Exception as e:
        print_message(f"Failed to load Gemini model for scheduling: {e}", "error")
        raise

def generate_negotiation_message(gemini_model, meeting_title: str, current_slot: str, proposed_new_slot: str, conflict_reason: str):
    """
    Uses Gemini to generate a polite reschedule request message.
    """
    prompt = f"""
    You are an AI scheduling assistant. Your goal is to draft a polite and professional message to reschedule a meeting.

    Meeting Title: "{meeting_title}"
    Current Proposed Slot: "{current_slot}"
    Proposed New Slot: "{proposed_new_slot}"
    Reason for conflict (internal to you, for context): "{conflict_reason}"

    Please write a polite, concise, and professional email or message body that:
    1. Acknowledges the current proposed slot.
    2. Explains that there is a conflict.
    3. Proposes the new slot.
    4. Asks for confirmation or alternative if the new slot doesn't work.
    
    Do NOT include salutations or closings (e.g., "Hi,", "Sincerely,"). Focus only on the core message.
    """
    print_message(f"Generating negotiation message for '{meeting_title}'...", "agent")
    try:
        response = gemini_model.generate_content(prompt) # Use the passed gemini_model
        return response.text.strip()
    except Exception as e:
        print_message(f"Failed to generate negotiation message with Gemini: {e}", "error")
        return "Apologies, I encountered an issue while generating the reschedule message. Can we discuss alternative times for this meeting?"

# Sample scheduler function to initiate a meeting proposal
def propose_meeting_with_peer(to_email, topic="Sync Meeting", duration_minutes=30):
    # Dynamically get the current user's email for AGENT_ID
    agent_id = get_current_user_email()
    if not agent_id:
        speak("Unable to determine your agent email. Please ensure you are authenticated.")
        return

    creds = get_google_calendar_credentials_main()
    if not creds:
        speak("Unable to access calendar. Please authenticate first.")
        return

    service = build("calendar", "v3", credentials=creds)
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    end = now + dt.timedelta(days=2)

    # Get your available slots
    freebusy = get_free_busy_slots(service, ["primary"], now, end)
    busy_times = freebusy['primary'].get('busy', [])

    def is_available(time_to_check): # Renamed 'time' parameter to 'time_to_check' to avoid conflict with 'time' module
        return all(not (dt.datetime.fromisoformat(b['start']) <= time_to_check < dt.datetime.fromisoformat(b['end'])) for b in busy_times)

    proposed_times = []
    current = now.replace(hour=10, minute=0, second=0, microsecond=0)
    while len(proposed_times) < 5 and current < end:
        if is_available(current):
            proposed_times.append(current.isoformat())
        current += dt.timedelta(minutes=30)

    payload = {
        "from": agent_id, # Use the dynamically fetched agent_id
        "type": "meeting_request",
        "topic": topic,
        "proposed_times": proposed_times,
        "duration_minutes": duration_minutes
    }

    # Peer URL is fixed for this local setup
    peer_url = "http://localhost:5001/receive" 
    
    speak(f"Proposing a meeting to {to_email}...")
    try:
        response = requests.post(peer_url, json=payload)
        if response.ok:
            reply = response.json()
            if reply.get("status") == "confirmed":
                speak(f"Meeting confirmed for {reply.get('time')}")
            elif reply.get("status") == "counter_proposal":
                alt_time = reply.get("alternative_time")
                speak(f"They are unavailable at your times but suggested {alt_time}. Trying to confirm...")
                # Attempt to confirm their suggested time
                event = {
                    'summary': topic,
                    'start': {'dateTime': alt_time, 'timeZone': 'UTC'},
                    'end': {'dateTime': (dt.datetime.fromisoformat(alt_time) + dt.timedelta(minutes=duration_minutes)).isoformat(), 'timeZone': 'UTC'},
                    'attendees': [{'email': to_email}, {'email': agent_id}] # Add both attendees
                }
                service.events().insert(calendarId="primary", body=event).execute()
                speak(f"Meeting rescheduled to their available time at {alt_time}. Do you want to reschedule again or try someone else?")
                # Wait for user response (voice or text)
                response = listen_for_response().lower() # Changed to listen_for_response
                if "reschedule" in response:
                    speak("Okay, I’ll look for another time.")
                    propose_meeting_with_peer(to_email, topic, duration_minutes)
                elif "someone else" in response:
                    speak("Who would you like me to contact instead?")
                    new_name = listen_for_response() # Changed to listen_for_response
                    new_email = get_email_from_name(new_name)
                    if new_email:
                        propose_meeting_with_peer(new_email, topic, duration_minutes)
                    else:
                        speak("I couldn't find their email. Please check your contacts.")
            else:
                speak("They were not available at the proposed times.")
        else:
            speak("Failed to contact their assistant.")
    except Exception as e:
        speak(f"Error contacting the agent: {e}")

def find_optimal_slot_and_negotiate(
    calendar_service,
    gemini_model,
    meeting_title: str,
    participants: list[str],
    duration_minutes: int,
    start_search_date: dt.date, # Use dt.date
    end_search_date: dt.date, # Use dt.date
    preferred_start_time_of_day: str = "09:00", # HH:MM string
    preferred_end_time_of_day: str = "17:00", # HH:MM string
    listen_func=None # Added listen_func as an argument
):
    """
    Orchestrates the process of finding optimal meeting slots and simulating negotiation.
    """
    print_message(f"Initiating scheduling for: '{meeting_title}' with {', '.join(participants)}", "agent")

    # Parse preferred start and end times into hour and minute integers
    # This is where the ValueError can occur if preferred_start_time_of_day or preferred_end_time_of_day
    # are not in the expected "HH:MM" format.
    try:
        PREFERRED_START_HOUR = int(preferred_start_time_of_day.split(":")[0])
        PREFERRED_START_MINUTE = int(preferred_start_time_of_day.split(":")[1])
    except (ValueError, IndexError):
        print_message(f"WARNING: Could not parse preferred_start_time_of_day: '{preferred_start_time_of_day}'. Defaulting to 9 AM.", "warning")
        PREFERRED_START_HOUR = 9
        PREFERRED_START_MINUTE = 0

    try:
        PREFERRED_END_HOUR = int(preferred_end_time_of_day.split(":")[0])
        PREFERRED_END_MINUTE = int(preferred_end_time_of_day.split(":")[1])
    except (ValueError, IndexError):
        print_message(f"WARNING: Could not parse preferred_end_time_of_day: '{preferred_end_time_of_day}'. Defaulting to 5 PM.", "warning")
        PREFERRED_END_HOUR = 17
        PREFERRED_END_MINUTE = 0
    
    # Ensure listen_func is provided
    if listen_func == None:
        print_message("Error: listen_func was not provided to find_optimal_slot_and_negotiate.", "error")
        return None

    # Add yourself (the primary calendar user) to participants if not already included
    all_participants = list(set(participants + ['primary'])) 

    current_date = start_search_date
    while current_date <= end_search_date:
        speak(f"Searching for slots on {current_date.strftime('%Y-%m-%d')}...")
        print_message(f"Searching for slots on {current_date.strftime('%Y-%m-%d')}...", "agent")
        
        try:
            # Use dt.datetime and dt.time for clarity and to avoid potential shadowing
            day_start = dt.datetime.combine(current_date, dt.time(PREFERRED_START_HOUR, PREFERRED_START_MINUTE, 0))
        except TypeError as e:
            print_message(f"ERROR: TypeError when creating day_start datetime object: {e}", "error")
            print_message(f"DEBUG: current_date={current_date} (type={type(current_date)}), PREFERRED_START_HOUR={PREFERRED_START_HOUR} (type={type(PREFERRED_START_HOUR)}), PREFERRED_START_MINUTE={PREFERRED_START_MINUTE} (type={type(PREFERRED_START_MINUTE)})", "debug")
            raise # Re-raise the exception to propagate the error

        try:
            # Use dt.datetime and dt.time for clarity and to avoid potential shadowing
            day_end = dt.datetime.combine(current_date, dt.time(PREFERRED_END_HOUR, PREFERRED_END_MINUTE, 0))
        except TypeError as e:
            print_message(f"ERROR: TypeError when creating day_end datetime object: {e}", "error")
            print_message(f"DEBUG: current_date={current_date} (type={type(current_date)}), PREFERRED_END_HOUR={PREFERRED_END_HOUR} (type={type(PREFERRED_END_HOUR)}), PREFERRED_END_MINUTE={PREFERRED_END_MINUTE} (type={type(PREFERRED_END_MINUTE)})", "debug")
            raise # Re-raise the exception to propagate the error

        day_start = day_start.replace(tzinfo=dt.timezone.utc) # Use dt.timezone
        day_end = day_end.replace(tzinfo=dt.timezone.utc) # Use dt.timezone

        free_busy_info = {}
        try:
            free_busy_info = get_free_busy_slots(calendar_service, all_participants, day_start, day_end)
        except Exception as e:
            print_message(f"Could not get free/busy for {current_date}: {e}", "warning")
            current_date += dt.timedelta(days=1) # Use dt.timedelta
            continue

        busy_slots_per_person = {}
        for email, calendar_data in free_busy_info.items():
            busy_slots_per_person[email] = []
            for busy_period in calendar_data.get('busy', []):
                start = dt.datetime.fromisoformat(busy_period['start']).astimezone(dt.timezone.utc) # Use dt.datetime and dt.timezone
                end = dt.datetime.fromisoformat(busy_period['end']).astimezone(dt.timezone.utc) # Use dt.datetime and dt.timezone
                busy_slots_per_person[email].append((start, end))
        
        potential_slots = []
        slot_start_time = day_start
        while slot_start_time + dt.timedelta(minutes=duration_minutes) <= day_end: # Use dt.timedelta
            slot_end_time = slot_start_time + dt.timedelta(minutes=duration_minutes) # Use dt.timedelta
            is_free_for_all = True
            
            for email in all_participants:
                for busy_start, busy_end in busy_slots_per_person.get(email, []):
                    if slot_start_time < busy_end and slot_end_time > busy_start:
                        is_free_for_all = False
                        break
                if not is_free_for_all:
                    break
            
            if is_free_for_all:
                potential_slots.append((slot_start_time, slot_end_time))
                slot_start_time = slot_end_time 
            else:
                slot_start_time += dt.timedelta(minutes=15) # Use dt.timedelta
        
        if potential_slots:
            chosen_start, chosen_end = potential_slots[0]
            print_message(f"Found a potential slot: {chosen_start.isoformat()} - {chosen_end.isoformat()}", "success")
            
            # Loop for user confirmation
            while True:
                speak(f"I found a potential slot on {chosen_start.strftime('%B %d, %Y')} from {chosen_start.strftime('%I:%M %p')} to {chosen_end.strftime('%I:%M %p')}. Should I propose this?")
                user_confirm = listen_func().lower().strip() # Use listen_func here
                print_message(f"DEBUG: User confirmation input: '{user_confirm}'", "debug") # Debug print

                if "yes" in user_confirm: # Changed to 'in' for more flexibility
                    event_body = {
                        'summary': meeting_title,
                        'start': {
                            'dateTime': chosen_start.isoformat(),
                            'timeZone': 'UTC',
                        },
                        'end': {
                            'dateTime': chosen_end.isoformat(),
                            'timeZone': 'UTC',
                        },
                        'attendees': [{'email': email} for email in participants],
                        'reminders': {
                            'useDefault': True,
                        },
                    }
                    created_event = create_calendar_event(calendar_service, event_body)
                    if created_event:
                        speak(f"Meeting '{meeting_title}' confirmed for {chosen_start.strftime('%B %d, %Y')} at {chosen_start.strftime('%I:%M %p')}!")
                        return created_event
                    else:
                        speak("Failed to create event after confirmation.")
                        return None
                elif "propose alternative" in user_confirm or "no" in user_confirm:
                    speak("Okay, let's look for other options or you can provide a specific one verbally.")
                    break # Exit confirmation loop to continue searching for slots
                elif not user_confirm: # No response detected
                    speak("I didn't hear a reply. Please say 'yes' to confirm, 'no' to decline, or 'propose alternative' to look for other options.")
                    continue # Continue the confirmation loop to re-prompt
                else:
                    speak("I didn't understand your response. Please say 'yes' to confirm, 'no' to decline, or 'propose alternative' to look for other options.")
                    continue # Continue the confirmation loop to re-prompt

        current_date += dt.timedelta(days=1) # Use dt.timedelta

    speak("No optimal slots found within the search range.")
    print_message("No optimal slots found within the search range.", "info")

    # NEW LOGIC: Offer to initiate agent-to-agent negotiation if no slots found
    # This applies if there's exactly one other participant to negotiate with.
    # Exclude 'primary' from participants count for this logic, as 'primary' is always you.
    external_participants = [p for p in participants if p != 'primary']
    if len(external_participants) == 1: 
        peer_email = external_participants[0]
        speak(f"Would you like me to initiate a negotiation with {peer_email} to find an alternative time? Say 'yes' or 'no'.")
        user_response = listen_func().lower().strip()

        if "yes" in user_response:
            speak(f"Okay, initiating negotiation with {peer_email}.")
            # Call the propose_meeting_with_peer function
            # This function will handle sending the proposal and listening for replies.
            propose_meeting_with_peer(peer_email, meeting_title, duration_minutes)
            return None # Indicate that a negotiation was initiated, but no event was created yet by this function
        else:
            speak("Okay, I will not initiate a negotiation at this time.")
            return None
    else:
        speak("I can only initiate direct agent-to-agent negotiation if there's exactly one other participant. For multiple participants, you might need to adjust your search criteria or manually coordinate.")
        return None


# --- New handle_scheduling_command function ---
def handle_scheduling_command(command, speak):
    """
    Processes a command to schedule a new meeting.
    It first attempts to parse details from the 'command' text using Gemini,
    then prompts the user for any missing information.
    """
    calendar_service = None
    try:
        creds = get_google_calendar_credentials_main() # Use the main.py specific credential function
        if creds:
            calendar_service = build('calendar', 'v3', credentials=creds)
            print_message("Google Calendar service initialized for scheduling.", "success")
        else:
            speak("Could not get Google Calendar credentials. Cannot schedule meeting.")
            print_message("Could not get Google Calendar credentials. Exiting.", "error")
            return
    except Exception as e:
        speak(f"Initialization error for Google Calendar: {e}.")
        print_message(f"Initialization error for Google Calendar: {e}", "error")
        return

    gemini_model = None
    try:
        gemini_model = google_ai.GenerativeModel("gemini-2.5-flash") # Use the scheduling-specific Gemini model getter
        print_message("Gemini model initialized for scheduling.", "success")
    except Exception as e:
        speak(f"Failed to load Gemini model for scheduling: {e}", "error")
        raise

    # --- Step 1: Use Gemini to parse the command if provided ---
    parsed_details = {}
    if command:
        speak("Analyzing your command for meeting details...")
        parsing_prompt = f"""
        Extract the following meeting details from the user's command.
        If a detail is not explicitly mentioned, leave its value as null.
        Provide the output as a JSON object.

        Command: "{command}"

        Expected JSON format:
        {{
            "meeting_title": "string | null",
            "participant_emails": "array of strings | null",
            "duration_minutes": "integer | null",
            "search_start_date": "DD-MM-YYYY string | null",
            "search_end_date": "DD-MM-YYYY string | null",
            "preferred_start_time": "HH:MM string | null",
            "preferred_end_time": "HH:MM string | null"
        }}

        Example:
        Command: "Schedule a sync-up with alice@example.com and bob@example.com for 45 minutes on 01-07-2025 at 10 AM."
        Output:
        {{
            "meeting_title": "sync-up",
            "participant_emails": ["alice@example.com", "bob@example.com"],
            "duration_minutes": 45,
            "search_start_date": "01-07-2025",
            "search_end_date": "01-07-2025",
            "preferred_start_time": "10:00",
            "preferred_end_time": null
        }}
        """
        try:
            # Call Gemini to parse the command.
            response = gemini_model.generate_content(parsing_prompt)
            parsed_json_str = response.text
            parsed_details = json.loads(parsed_json_str)
            print_message(f"Parsed details from command: {parsed_details}", "info")
        except json.JSONDecodeError as e:
            speak(f"Could not understand the command fully. JSON parsing error: {e}. I will ask for details manually.")
            print_message(f"Error decoding JSON from Gemini response: {e}", "error")
            parsed_details = {} # Reset to empty to force manual prompts
        except Exception as e:
            speak(f"An error occurred while parsing the command with Gemini: {e}. I will ask for details manually.")
            print_message(f"Error parsing command with Gemini: {e}", "error")
            parsed_details = {} # Reset to empty to force manual prompts

    # --- Helper function to parse spoken dates like "29th June 2025" ---
    def parse_spoken_date(date_string):
        # Remove ordinal suffixes (st, nd, rd, th)
        date_string = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_string, flags=re.IGNORECASE)

        # Month name to number mapping
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }

        # Try to parse "DD MonthYYYY" or "Month DDYYYY"
        patterns = [
            r'(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})',  # DD MonthYYYY
            r'([a-zA-Z]+)\s+(\d{1,2})\s+(\d{4})'   # Month DDYYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, date_string, re.IGNORECASE)
            if match:
                try:
                    if pattern == patterns[0]: # DD MonthYYYY
                        day = int(match.group(1))
                        month_name = match.group(2).lower()
                        year = int(match.group(3))
                    else: # Month DDYYYY
                        month_name = match.group(1).lower()
                        day = int(match.group(2))
                        year = int(match.group(3))

                    month = month_map.get(month_name)
                    if month:
                        date_obj = dt.datetime(year, month, day).date() # Use dt.datetime
                        return date_obj.strftime('%d-%m-%Y')
                except (ValueError, KeyError):
                    continue # Try next pattern or return None

        # If no spoken format matched, try DD-MM-YYYY directly
        try:
            date_obj = dt.datetime.strptime(date_string, '%d-%m-%Y').date() # Use dt.datetime
            return date_obj.strftime('%d-%m-%Y')
        except ValueError:
            pass

        return None # If no format is recognized

    # --- Helper function to parse spoken times like "9 AM" or "14:30" ---
    def parse_spoken_time(time_string):
        time_string = time_string.lower().strip()

        # Try 24-hour format (HH:MM)
        match_24h = re.match(r'(\d{1,2}):(\d{2})', time_string)
        if match_24h:
            hour = int(match_24h.group(1))
            minute = int(match_24h.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"

        # Try 12-hour format (H AM/PM, HH:MM AM/PM, H o'clock)
        match_12h = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|o\'clock)?', time_string)
        if match_12h:
            hour = int(match_12h.group(1))
            minute = int(match_12h.group(2)) if match_12h.group(2) else 0
            meridian = match_12h.group(3)

            if 1 <= hour <= 12 and 0 <= minute <= 59:
                if meridian == 'pm' and hour != 12:
                    hour += 12
                elif meridian == 'am' and hour == 12:
                    hour = 0
                return f"{hour:02d}:{minute:02d}"
            elif meridian == 'o\'clock': # Handle "X o'clock"
                if 1 <= hour <= 12:
                    # Assume AM if not specified, or if it's "12 o'clock" it could be noon or midnight
                    # For simplicity, assume 24-hour for "o'clock" if no AM/PM
                    return f"{hour:02d}:00" if hour <= 12 else f"{hour:02d}:00" # This needs refinement for AM/PM context if no meridian
                
        return None # If no format is recognized

    # --- Step 2: Collect missing information, prompting the user ---
    # Helper function to get information, checking parsed_details first
    def get_info(prompt_text, key, type_converter=None, validation_func=None, error_message="Invalid input. Please try again."):
        # Check if the value was already parsed from the command
        value = parsed_details.get(key)
        if value is not None and value != "": # Ensure it's not null or empty string from parsing
            if key in ["search_start_date", "search_end_date"]:
                # Try parsing spoken date format first for date fields
                parsed_val = parse_spoken_date(str(value))
                if parsed_val:
                    print_message(f"Using parsed spoken date for {key}: {parsed_val}", "info")
                    return parsed_val
                else:
                    print_message(f"Parsed value '{value}' for '{key}' could not be interpreted as a date. Prompting user.", "warn")
                    value = None # Force prompt if initial parse fails
            elif key in ["preferred_start_time", "preferred_end_time"]:
                # Try parsing spoken time format first for time fields
                parsed_val = parse_spoken_time(str(value))
                if parsed_val:
                    print_message(f"Using parsed spoken time for {key}: {parsed_val}", "info")
                    return parsed_val
                else:
                    print_message(f"Parsed value '{value}' for '{key}' could not be interpreted as a time. Prompting user.", "warn")
                    value = None # Force prompt if initial parse fails
            else:
                # Existing logic for other types
                if type_converter:
                    try:
                        converted_value = type_converter(value)
                        if validation_func and not validation_func(converted_value):
                            print_message(f"Parsed value '{value}' for '{key}' failed validation. Prompting user.", "warn")
                            value = None
                        else:
                            print_message(f"Using parsed value for {key}: {converted_value}", "info")
                            return converted_value
                    except ValueError:
                        print_message(f"Parsed value '{value}' for '{key}' could not be converted. Prompting user.", "warn")
                        value = None
                else:
                    print_message(f"Using parsed value for {key}: {value}", "info")
                    return value

        # If value is still None (not parsed or invalid parsed value), prompt the user
        while True:
            speak(prompt_text) # Ask the main question
            user_input = listen_for_response().strip() # Use listen_for_response here
            
            # Debug print to show what listen_for_response returned
            print_message(f"DEBUG: listen_for_response returned for '{key}': '{user_input}'", "debug")

            if not user_input:
                speak("I didn't hear anything. Please provide a value, or say 'cancel' to stop.")
                continue

            if user_input.lower() == 'cancel':
                speak("Operation cancelled.")
                return None

            if key in ["search_start_date", "search_end_date"]:
                # Try parsing spoken date from user_input
                parsed_val = parse_spoken_date(user_input)
                if parsed_val:
                    return parsed_val
                else:
                    speak(error_message) # Use the specific error message for date format
                    continue
            elif key in ["preferred_start_time", "preferred_end_time"]:
                # Try parsing spoken time from user_input
                parsed_val = parse_spoken_time(user_input)
                if parsed_val:
                    return parsed_val
                else:
                    speak(error_message) # Use the specific error message for time format
                    continue
            else:
                if type_converter:
                    try:
                        converted_input = type_converter(user_input)
                        if validation_func and not validation_func(converted_input):
                            speak(error_message)
                            continue
                        return converted_input
                    except ValueError:
                        speak(error_message)
                        continue
                else:
                    return user_input

    # Meeting Title
    meeting_title = get_info(
        "What is the title of the meeting?",
        "meeting_title"
    )
    if meeting_title is None: # Check for None, indicating user cancelled
        speak("No meeting title provided. Cancelling scheduling.")
        return

    # Participant Emails
    # Participant emails might be parsed as a list, or as a comma-separated string.
    # Handle both cases.
    final_participant_emails = []
    
    # Check if participant_emails were already parsed from command
    parsed_participant_input = parsed_details.get("participant_emails")
    if isinstance(parsed_participant_input, list):
        # If it's a list, process each item
        for entry in parsed_participant_input:
            entry_str = str(entry).strip()
            if re.match(r"[^@]+@[^@]+\.[^@]+", entry_str): # Simple regex for email validation
                final_participant_emails.append(entry_str)
            else:
                speak(f"Attempting to find email for {entry_str} from your contacts.")
                email_from_contact = get_email_from_name(entry_str)
                if email_from_contact:
                    final_participant_emails.append(email_from_contact)
                else:
                    speak(f"Could not find an email for '{entry_str}' in your Google Contacts. Please provide a valid email or ensure the contact exists.")
    else:
        # If not a list (or None), prompt the user for input
        while True:
            speak("Who are the participants? Please provide their names or email addresses separated by commas.")
            participant_input_str = listen_for_response().strip()
            
            if not participant_input_str:
                speak("No participants entered. Please provide at least one participant, or say 'cancel' to stop.")
                continue
            if participant_input_str.lower() == 'cancel':
                speak("Operation cancelled.")
                return

            temp_participants = [item.strip() for item in participant_input_str.split(',') if item.strip()]
            
            resolved_emails = []
            all_resolved = True
            for participant_entry in temp_participants:
                if re.match(r"[^@]+@[^@]+\.[^@]+", participant_entry): # Simple regex for email validation
                    resolved_emails.append(participant_entry)
                else:
                    speak(f"Attempting to find email for {participant_entry} from your contacts.")
                    email_from_contact = get_email_from_name(participant_entry)
                    if email_from_contact:
                        resolved_emails.append(email_from_contact)
                    else:
                        speak(f"Could not find an email for '{participant_entry}' in your Google Contacts. Please provide a valid email for this person or ensure the contact exists.")
                        all_resolved = False
                        break # Stop and re-prompt if any name cannot be resolved
            
            if all_resolved:
                final_participant_emails = resolved_emails
                break # Exit the loop if all participants are resolved
            else:
                # If not all resolved, the loop continues to re-prompt
                continue

    if not final_participant_emails:
        speak("No valid participants with email addresses provided. Cancelling scheduling.")
        return


    # Duration Minutes
    duration_minutes = get_info(
        "What is the duration of the meeting in minutes? For example, 60 for one hour.",
        "duration_minutes",
        type_converter=int,
        validation_func=lambda x: x > 0,
        error_message="Invalid duration. Please provide a positive number in minutes."
    )
    if duration_minutes is None:
        speak("Invalid duration. Cancelling scheduling.")
        return

    # Search Start Date
    search_start_date_str = get_info(
        "What is the earliest date I should start looking for a slot? Say it in DD-MM-YYYY format, for example, 01-07-2025, or naturally like '29th June 2025'.",
        "search_start_date",
        error_message="Invalid start date format. Please use DD-MM-YYYY or a natural date like '29th June 2025'."
    )
    if search_start_date_str is None:
        speak("Invalid start date. Cancelling scheduling.")
        return
    try:
        search_start_date = dt.datetime.strptime(search_start_date_str, '%d-%m-%Y').date() # Use dt.datetime
    except ValueError:
        speak("Invalid start date format. Please use DD-MM-YYYY. Cancelling scheduling.")
        return

    # Search End Date
    search_end_date_str = get_info(
        "What is the latest date I should look for a slot? Say it in DD-MM-YYYY format, for example, 30-07-2025, or naturally like '29th June 2025'.",
        "search_end_date",
        error_message="Invalid end date format. Please use DD-MM-YYYY or a natural date like '29th June 2025'."
    )
    if search_end_date_str is None:
        speak("Invalid end date. Cancelling scheduling.")
        return
    try:
        search_end_date = dt.datetime.strptime(search_end_date_str, '%d-%m-%Y').date() # Use dt.datetime
    except ValueError:
        speak("Invalid end date format. Please use DD-MM-YYYY. Cancelling scheduling.")
        return

    # Preferred Start Time
    preferred_start_time = get_info(
        "What is your preferred start time of day? For example, 09:00 for 9 AM, or just say '9 AM'.",
        "preferred_start_time",
        error_message="Invalid start time format. Please use HH:MM (e.g., 09:00) or natural language (e.g., '9 AM')."
    ) or "09:00" # Default if no input or user cancels

    # Preferred End Time
    preferred_end_time = get_info(
        "What is your preferred end time of day? For example, 17:00 for 5 PM, or just say '5 PM'.",
        "preferred_end_time",
        error_message="Invalid end time format. Please use HH:MM (e.g., 17:00) or natural language (e.g., '5 PM')."
    ) or "17:00" # Default if no input or user cancels


    # Call the core scheduling logic, passing the listen function
    find_optimal_slot_and_negotiate(
        calendar_service,
        gemini_model,
        meeting_title,
        final_participant_emails, # Use the resolved emails
        duration_minutes,
        search_start_date,
        search_end_date,
        preferred_start_time,
        preferred_end_time,
        listen_func=listen_for_response # Pass the listen_for_response function
    )

# NEW: handle_attendance function
def handle_attendance(command, input_text=None):
    """
    Handles commands related to attendance file storage and download.
    """
    global last_uploaded_file
    attendance_flask_url = "http://127.0.0.1:5011" # URL for the attendance Flask app

    if "store attendance" in command:
        if last_uploaded_file and last_uploaded_file.get("filename", "").lower().endswith(('.xlsx', '.xls')):
            speak("Attempting to store the attendance file.")
            print(f"DEBUG: Storing attendance file: {last_uploaded_file.get('filename')}")
            file_path = last_uploaded_file["path"] # Use the saved file path

            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (last_uploaded_file["filename"], f, last_uploaded_file["mime_type"])}
                    response = requests.post(f"{attendance_flask_url}/store-attendance", files=files)
                
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                result = response.json()
                if result.get("status") == "success":
                    speak(result["message"])
                    print(f"INFO: {result['message']}")
                else:
                    speak(f"Failed to store attendance file: {result.get('error', 'Unknown error')}")
                    print(f"ERROR: Failed to store attendance file: {result}")
            except requests.exceptions.ConnectionError:
                speak("Could not connect to the attendance service. Please ensure the attendance application is running.")
                print("ERROR: Connection to attendance Flask app failed.")
            except requests.exceptions.RequestException as e:
                speak(f"Error during attendance storage request: {e}")
                print(f"ERROR: Attendance storage request failed: {e}")
            except json.JSONDecodeError:
                speak("Received invalid response from attendance storage service.")
                print(f"ERROR: JSON decoding error from attendance storage: {response.text}")
            except Exception as e:
                speak(f"An error occurred while storing the attendance file: {str(e)}")
                print(f"ERROR: Exception during store attendance: {e}")
            finally:
                last_uploaded_file = {} # Clear after attempt
        else:
            speak("Please upload an Excel attendance file first.")

    elif "update attendance" in command: # NEW: Handle "update attendance" command
        # Check if a file was uploaded and if it's an allowed type for signature detection
        if last_uploaded_file and \
           last_uploaded_file.get("filename", "").lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
            
            speak("Attempting to update the attendance file by detecting signatures from the uploaded document.")
            print(f"DEBUG: Updating attendance with data from: {last_uploaded_file['filename']}")
            file_path = last_uploaded_file["path"] # Use the saved file path

            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (last_uploaded_file['filename'], f, last_uploaded_file['mime_type'])} # Changed 'document' to 'file'
                    response = requests.post(f"{attendance_flask_url}/modify-attendance", files=files) # Changed to /modify-attendance
                
                response.raise_for_status()
                result = response.json()
                if result.get("status") == "success":
                    speak(result["message"])
                    print(f"INFO: {result['message']}")
                    # Optionally, display details about who was marked present/absent
                    if result.get("details"):
                        present_names = ", ".join(result["details"].get("names_marked_present", []))
                        absent_names = ", ".join(result["details"].get("names_marked_absent", []))
                        if present_names:
                            speak(f"Marked present: {present_names}.")
                        if absent_names:
                            speak(f"Marked absent: {absent_names}.")
                else:
                    speak(f"Failed to update attendance file: {result.get('error', 'Unknown error')}")
                    print(f"ERROR: Failed to update attendance file: {result}")
            except requests.exceptions.ConnectionError:
                speak("Could not connect to the attendance modification service. Please ensure the attendance application is running.")
                print("ERROR: Connection to attendance Flask app failed.")
            except requests.exceptions.RequestException as e:
                speak(f"Error during attendance modification request: {e}")
                print(f"ERROR: Attendance modification request failed: {e}")
            except json.JSONDecodeError:
                speak("Received invalid response from attendance modification service.")
                print(f"ERROR: JSON decoding error from attendance modification: {response.text}")
            except Exception as e:
                speak(f"An unexpected error occurred during attendance update: {e}")
                print(f"ERROR: General error during attendance update: {e}")
            finally:
                last_uploaded_file = {} # Clear after attempt
        else:
            speak("To update attendance, please first upload an image file (PNG, JPG, JPEG) or a PDF file containing names and signatures.")
            print("ERROR: No valid image or PDF file found in last_uploaded_file for attendance update.")

    elif "download attendance" in command:
        speak("Attempting to download the attendance file.")
        print("DEBUG: Downloading attendance file.")
        try:
            response = requests.get(f"{attendance_flask_url}/download-attendance")
            response.raise_for_status()

            # Check if the response is a file download (not JSON error)
            if 'content-disposition' in response.headers:
                # Extract filename from Content-Disposition header
                cd = response.headers.get('content-disposition')
                filename_match = re.findall(r'filename="([^"]+)"', cd)
                download_filename = filename_match[0] if filename_match else "attendance_report.xlsx" # Default name

                # Save the file to the UPLOAD_FOLDER
                download_path = os.path.join(UPLOAD_FOLDER, download_filename)
                with open(download_path, 'wb') as f:
                    f.write(response.content)

                # Now, use eel to prompt the user to download it via the browser
                # Encode the content to base64 for download via frontend
                file_data_base64 = base64.b64encode(response.content).decode('utf-8')

                if hasattr(eel, 'downloadCompletedFile') and callable(getattr(eel, 'downloadCompletedFile')):
                    eel.downloadCompletedFile(file_data_base64, download_filename)()
                    speak(f"Attendance file '{download_filename}' downloaded successfully.")
                    print(f"INFO: Attendance file '{download_filename}' downloaded successfully.")
                else:
                    print("WARNING: eel.downloadCompletedFile is not defined or not callable in the frontend.")
                    speak(f"Attendance file '{download_filename}' downloaded. Download functionality not available in UI.")
            else:
                # If no content-disposition, it might be an error JSON
                result = response.json()
                speak(f"Failed to download attendance file: {result.get('error', 'Unknown error')}")
                print(f"ERROR: Failed to download attendance file: {result}")

        except requests.exceptions.ConnectionError:
            speak("Error: Could not connect to the attendance download service. Please ensure the attendance application is running.")
            print(f"ERROR: Connection to attendance download service failed.")
        except requests.exceptions.RequestException as e:
            speak(f"Error during attendance download request: {e}")
            print(f"ERROR: Attendance download request failed: {e}")
        except json.JSONDecodeError:
            speak("Received invalid response from attendance download service.")
            print(f"ERROR: JSON decoding error from attendance download: {response.text if response else 'No response'}")
        except Exception as e:
            speak(f"An unexpected error occurred during attendance download: {e}")
            print(f"ERROR: General error during attendance download: {e}")
    else:
        speak("I'm not sure what you mean by that attendance command. Please say 'store attendance', 'download attendance', or 'update attendance'.")


# --- Process Command Function ---
def processCommand(c, source_input_text=None): # Added source_input_text parameter
    import re # Explicitly import re within the function to ensure it's bound locally

    global jarvis_active, is_listening, is_handling_complex_command, in_mcq_answer_mode

    command = c.lower().strip()
    print(f"Processing command: {command}")
    logging.info(f"Command received: {command}")
    eel.HideTyping()

    # --- Attendance Commands (NEW) ---
    if "store attendance" in command or "download attendance" in command or "update attendance" in command: # Added "update attendance"
        handle_attendance(command, input_text=source_input_text)
        return

    # --- Worksheet Commands (Prioritized) ---
    if "create level 1 worksheet" in command or \
       "create level 2 worksheet" in command or \
       "create level 3 worksheet" in command or \
       "create level 4 worksheet" in command or \
       "create worksheet" in command:
        if last_uploaded_file:
            handle_file_command(command, input_text=source_input_text) # Pass source_input_text
        else:
            speak("Please upload a file first using the GUI, then say 'create worksheet' or 'create level [1-4] worksheet'.")
        return

    # --- NEW: Lesson Plan Command ---
    if "plan lesson" in command or "generate lesson plan" in command:
        if last_uploaded_file:
            handle_file_command(command, input_text=source_input_text)
        else:
            speak("Please upload a file first using the GUI, then say 'plan lesson' or 'generate lesson plan'.")
        return

    # --- Other File-related Commands ---
    if "generate presentation from file" in command:
        handle_file_command(command, input_text=source_input_text) # Pass source_input_text
        return
    elif "generate questions" in command:
        handle_file_command(command, input_text=source_input_text) # Pass source_input_text
        return
    elif "solve" in command:
        handle_file_command(command, input_text=source_input_text) # Pass source_input_text
        return
    elif "get information" in command:
        # Extract language if present
        language_match = re.search(r"get information in (\w+)", command)
        language = "English"
        if language_match:
            language = language_match.group(1).capitalize()
            speak(f"Getting information in {language}.")
        
        handle_file_command(command, input_text=source_input_text, language=language) # Pass language
        return
    elif "analyze marks" in command: # NEW: Handle "analyze marks" command
        if last_uploaded_file and (last_uploaded_file["filename"].endswith(('.xlsx', '.xls'))):
            handle_file_command(command, input_text=source_input_text)
        else:
            speak("Please upload an Excel file first to analyze marks.")
        return
    elif last_uploaded_file and ("complete" in command or "summarize" in command or "analyze" in command):
        handle_file_command(command, input_text=source_input_text) # Pass source_input_text
        return

  
   # --- NEW: CREATE GOOGLE FORM ---
    elif "create google form" in command or "generate a form" in command:
        speak("Okay, let's create a Google Form.")
        form_title = None
        form_description = None
        form_topic = None

        # Try to extract topic from the command itself (after "generate a form about")
        match_form_command = re.search(r"generate(?: a)? form about (.+)", command, re.IGNORECASE)
        if match_form_command:
            form_topic = match_form_command.group(1).strip()
            # If topic is provided in the initial command, directly set title and description
            form_title = f"Form about {form_topic}"
            form_description = f"This form collects information related to {form_topic}."
            speak(f"I will create a form about {form_topic}. The title will be '{form_title}' and a default description will be used.")
        else:
            speak("What is the main topic or purpose of this form?")
            form_topic = source_input_text.strip() if source_input_text else listen_for_response().strip()
            if not form_topic:
                speak("No topic provided. Cannot create the form.")
                return

            speak("What would you like to title the form?")
            form_title = source_input_text.strip() if source_input_text else listen_for_response().strip()
            if not form_title:
                form_title = f"Form about {form_topic}"
                speak(f"No title provided, so I'll title it: {form_title}")

            speak("Please provide a brief description for the form.")
            form_description = source_input_text.strip() if source_input_text else listen_for_response().strip()
            if not form_description:
                form_description = f"This form collects information related to {form_topic}."
                speak(f"No description provided, so I'll use: {form_description}")

        speak("Generating questions for the form using AI. This might take a moment.")
        try:
            gemini_model = google_ai.GenerativeModel("gemini-2.0-flash")
            question_prompt = f"""
            Generate 5-7 diverse questions for a Google Form about \"{form_topic}\".
            For each question, specify its type (e.g., 'TEXT', 'PARAGRAPH_TEXT', 'MULTIPLE_CHOICE', 'CHECKBOX', 'DROPDOWN').
            If the type is 'MULTIPLE_CHOICE', 'CHECKBOX', or 'DROPDOWN', provide 3-5 relevant options.
            Ensure the output is a JSON array of objects, where each object has:
            - \"question_text\": string
            - \"type\": string (one of 'TEXT', 'PARAGRAPH_TEXT', 'MULTIPLE_CHOICE', 'CHECKBOX', 'DROPDOWN')
            - \"options\": array of strings (only if type is MULTIPLE_CHOICE, CHECKBOX, or DROPDOWN, otherwise omit or set to null)
            """

            gemini_response = gemini_model.generate_content(question_prompt)
            json_string = gemini_response.text.strip()

            if json_string.startswith("```json"):
                json_string = json_string[7:].strip()
            if json_string.endswith("```"):
                json_string = json_string[:-3].strip()

            questions_data = json.loads(json_string)
            print(f"DEBUG: Generated questions: {questions_data}")

            if not isinstance(questions_data, list):
                raise ValueError("Gemini response for questions is not a list.")
            for q in questions_data:
                if not isinstance(q, dict) or "question_text" not in q or "type" not in q:
                    raise ValueError("Each question must be an object with 'question_text' and 'type'.")

            form_url = create_google_form(
                form_title, form_description, questions_data, speak,
                form_topic=form_topic,
                get_credentials_func=get_google_credentials,
                all_scopes=SCOPES
            )

            if form_url:
                speak(f"Google Form '{form_title}' created successfully. Opening it in your browser.")
                webbrowser.open(form_url)
            else:
                speak("Sorry, I failed to create the Google Form.")

        except json.JSONDecodeError as e:
            speak(f"I had trouble generating questions for the form. The AI response was not in the correct format: {e}.")
            print(f"ERROR: JSON decoding error for form questions: {e}. Response: {gemini_response.text}")
        except ValueError as e:
            speak(f"The AI generated invalid question data: {e}. Please try again with a clearer topic.")
            print(f"ERROR: Invalid question data from Gemini: {e}")
        except Exception as e:
            speak(f"An unexpected error occurred while generating form questions: {e}.")
            print(f"ERROR: General error during form question generation: {e}")
        return
    # NEW: GENERATE AND CREATE GMAIL DRAFT
    elif "generate a mail about" in command or "send an email about" in command:
        speak("Okay, I can help you draft an email.")
        email_topic = None

        # Extract topic from the command
        match_email_command = re.search(r"(?:generate a mail about|send an email about)\s+(.+)", command, re.IGNORECASE)
        if match_email_command:
            email_topic = match_email_command.group(1).strip()
        else:
            speak("What is the topic of the email you want to generate?")
            email_topic = source_input_text.strip() if source_input_text else listen_for_response().strip()

        if not email_topic:
            speak("No topic provided. Cannot generate the email.")
            return

        speak(f"Drafting an email about {email_topic}...")
        try:
            # Generate email body using Gemini
            body = generate_email_body_with_gemini(subject=email_topic, context="", speak_func=speak)
            subject = email_topic

            if body:
                # Authenticate with Gmail
                creds = get_google_credentials()
                if not creds:
                    speak("Failed to authenticate with Google. Cannot create Gmail draft.")
                    return

                service = build('gmail', 'v1', credentials=creds)

                # Create the email message
                message = MIMEText(body)
                message['to'] = ''  # Leave empty
                message['from'] = get_current_user_email()
                message['subject'] = subject

                # Encode in base64
                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

                # Create draft
                draft_body = {'message': {'raw': raw_message}}
                draft = service.users().drafts().create(userId='me', body=draft_body).execute()

                speak(f"I have drafted the email with subject '{subject}'. Opening your Gmail drafts now.")
                webbrowser.open("https://mail.google.com/mail/u/0/#drafts")  # ✅ Best-possible link

            else:
                speak("Sorry, I couldn't generate the email content.")

        except Exception as e:
            speak(f"An unexpected error occurred while drafting the email: {e}")
            print(f"ERROR: {e}")
        return




    # --- OPEN COMMON WEBSITES ---
    websites = {
        "youtube": "youtube.com",
        "google": "google.com",
        "whatsapp web": "web.whatsapp.com",
        "instagram": "instagram.com",
        "facebook": "facebook.com",
        "twitter": "twitter.com",
        "linkedin": "linkedin.com",
        "github": "github.com"
    }

    for keyword, url in websites.items():
        if f"open {keyword}" in command:
            speak(f"Opening {keyword.title()}")
            webbrowser.open(f"https://{url}")
            return

     # --- WHATSAPP FEATURES ---
    if "whatsapp video call" in command:
        contact_query = command.replace("whatsapp video call", "").strip()
        if not contact_query:
            speak("Who would you like to WhatsApp video call?")
            contact_query = listen()
        if contact_query:
            jarvis_whatsapp_video_call(contact_query)
        else:
            speak("Sorry, I didn't get the contact name for the video call.")
        return

    elif "whatsapp call" in command:
        contact_query = command.replace("whatsapp call", "").strip()
        if not contact_query:
            speak("Who would you like to WhatsApp call?")
            contact_query = listen()
        if contact_query:
            jarvis_whatsapp_call(contact_query)
        else:
            speak("Sorry, I didn't get the contact name for the call.")
        return

    elif "send whatsapp message to " in command:
        # Split command into name and message
        parts = command.split("saying", 1)
        contact_query = parts[0].replace("send whatsapp message to", "").strip()
        message_text = parts[1].strip() if len(parts) == 2 else ""

        if not contact_query:
            speak("To whom would you like to send the WhatsApp message?")
            message_text = listen()
        if not message_text:
            speak("What message would you like to send?")
            message_text = listen()

        if contact_query and message_text:
            jarvis_whatsapp_message(contact_query, message_text)
        else:
            speak("Sorry, I need both a contact and a message to proceed.")
        return


    elif "set alarm" in c:
        handle_alarm_command(c)
        return


    elif "volume" in command or "sound" in command:
        if "mute" in command or "silence" in command or "sound off" in command:
            mute_volume()
            speak("Okay, I am now muted.")
        elif "unmute" in command or "sound on" in command:
            unmute_volume()
            speak("Okay, I am unmuted now.")
        elif "volume up" in command or "louder" in command or "increase sound" in command:
            increase_volume()
            speak("Okay, increasing volume.")
        elif "volume down" in command or "quieter" in command or "decrease sound" in command:
            lower_volume()
            speak("Okay, lowering volume.")
        return


    elif "generate image" in c or "create image" in c:
        global text_input_command
        topic = None

        # Extract topic from voice or text input
        if " of " in c:
            topic = c.split(" of ", 1)[1].strip()
        elif source_input_text and " of " in source_input_text: # Check source_input_text first for GUI input
            topic = source_input_text.split(" of ", 1)[1].strip()
        else:
            speak("What image do you want me to create?")
            # Prioritize voice input, then text input if voice is empty
            topic = listen()
            if not topic and source_input_text: # Fallback to source_input_text if voice is empty
                 topic = source_input_text.strip()

        if topic:
            speak(f"Generating an image for '{topic}'. This might take a moment.")
            try:
                saved_path = generate_image_pollinations(topic)

                if saved_path:
                    speak("Image has been generated successfully. Downloading it now.")
                    
                    # Ensure file exists
                    if os.path.exists(saved_path):
                        # Read file and convert to base64
                        with open(saved_path, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")

                        filename = os.path.basename(saved_path)

                        # Trigger download in browser
                        eel.downloadCompletedFile(encoded, filename)()
                        eel.showImage(f"data:image/png;base64,{encoded}")()  # also display
                    else:
                        speak("I couldn't find the saved image file. Please check my logs.")

            except Exception as e:
                print(f"⚠ Image generation error: {e}")
                speak("Something went wrong during image generation.")
        else:
            speak("I didn't catch that. Please provide a clear description for the image.")

        text_input_command = None

    # --- INTEGRATION OF OPEN_APP_BY_SEARCH ---
    elif "open" in command:
            parts = command.split("open ", 1)
            if len(parts) > 1:
                app_name_raw = parts[1].strip()
                
                app_to_open = ""
                if "chrome" in app_name_raw:
                    app_to_open = "chrome"
                elif "notepad" in app_name_raw:
                    app_to_open = "notepad"
                elif "code" in app_name_raw or "visual studio code" in app_name_raw:
                    app_to_open = "vs code"
                elif "calculator" in app_name_raw:
                    app_to_open = "calculator"
                elif "paint" in app_name_raw:
                    app_to_open = "paint"
                elif "settings" in app_name_raw:
                    app_to_open = "settings"
                else:
                    app_to_open = app_name_raw 
                
                if app_to_open:
                    open_app_by_search(app_to_open)
                else:
                    speak("I'm sorry, I couldn't identify the application name.")
            else:
                speak("What application do you want me to open?")

    # --- GOOGLE SEARCH ---
    elif "search" in command or "google" in command:
        search_query = command.replace("search", "").replace("google", "").strip()
        if not search_query:
            speak("What would you like to search for?")
            search_query = listen()
        if search_query:
            speak(f"Searching Google for {search_query}")
            webbrowser.open(f"https://www.google.com/search?q={quote(search_query)}")
        else:
            speak("Sorry, I didn't catch what you wanted to search for.")
        return

    elif "shut down" in c or "shutdown" in c:
        speak("Shutting down your system.")
        shutdown()

    elif "restart" in c or "reboot" in c:
        speak("Restarting your system.")
        restart()

    # --- YOUTUBE & NEWS ---
    elif "turn on youtube" in command:
        speak("Opening YouTube.")
        webbrowser.open("https://youtube.com")

    elif "play" in command :
        PlayYoutube(command)

    elif "news" in command:
        fetch_news()

    elif "next news" in command:
        fetch_next_news()

    # --- PHONE LINK / NOTIFICATIONS ---
    elif "open phone link" in command:
        speak("Opening Phone Link.")
        subprocess.Popen(['start', 'ms-phone-link:'], shell=True)

    elif "read notifications" in command:
        phone_link_window = find_phone_link_window()
        if phone_link_window:
            read_notifications(phone_link_window)
        else:
            speak("Phone Link window not found. Please ensure it's open.")

    elif "send reply" in command:
        speak("What do you want to reply?")
        reply_text = listen()
        if reply_text:
            phone_link_window = find_phone_link_window()
            if phone_link_window:
                send_reply(phone_link_window, reply_text)
            else:
                speak("Phone Link window not found. Please ensure it's open.")
        else:
            speak("No reply text provided.")


    # --- PRESENTATION ---
    elif "generate presentation on" in command:
        handle_presentation_command(command, speak)

    # --- NEW: SCHEDULE MEETING ---
    elif "schedule meeting" in command:
        is_handling_complex_command = True
        try:
            handle_scheduling_command(command, speak)
        finally:
            is_handling_complex_command = False
        return

    # --- NEW: ANSWER MCQ QUESTION ---
    elif "answer a multiple choice question" in command or "answer mod" in command:
        speak("Entering multiple-choice question answering mode. Please state your questions one by one. Say 'end answer' to exit this mode.")
        in_mcq_answer_mode = True
        return

    # --- SYSTEM CONTROL ---
    elif any(x in command for x in ["stop listening", "sleep"]):
        speak("Okay, I'm going to sleep now. You can wake me up by saying 'Jarvis'.")
        jarvis_active = False
        is_listening = False
        in_mcq_answer_mode = False
        eel.DisplayMessage("Jarvis is sleeping. Say 'Jarvis' to wake me up.")
        eel.HideSiriWave()
        try:
            eel.hideImage()()
        except Exception as e:
            print(f"Error hiding image on sleep: {e}")
        return
    
    elif "weather" in command:
        import re

        match = re.search(r"weather.*in (.+)", command)
        if match:
            raw_location = match.group(1).strip()
        else:
            raw_location = "Mumbai"

        city = raw_location.title()
        speak(f"Getting the weather in {city}")
        get_weather(city)
        return

    # --- DEFAULT AI PROCESSING ---
    else:
        speak("Thinking...")
        try:
            response_text = aiProcess(command)
            response_text = response_text.replace('*', '')
            speak(response_text)
        except Exception as e:
            speak("I am sorry, I am unable to process your request at the moment.")
            logging.error(f"Error in AI processing: {e}")


def parse_mcq_from_text(full_text: str):
    """
    Parses a combined string of question and options into a question and a list of options.
    This version is more robust in identifying options from natural language input.
    """
    full_text = full_text.strip()
    question = ""
    options = []

    # 1. Initial cleanup: remove common conversational prefixes from the start
    question_prefix_patterns = [
        r"general knowledge question for you",
        r"here is a question",
        r"i have a question for you",
        r"question for you",
        r"which planet is known as the red planet" # Specific to the user's example
    ]
    for prefix_pattern in question_prefix_patterns:
        full_text = re.sub(f"^{prefix_pattern}\\s*", "", full_text, flags=re.IGNORECASE).strip()

    # Define patterns for explicit option prefixes (e.g., "Option A:", "A.")
    explicit_option_prefixes_regex = r'(?i)\s*(?:Option\s+[A-Za-z][:.)]?|\b[A-Za-z][.)]?)\s*'

    # Define patterns for question ending phrases (e.g., "what's your answer")
    question_ending_phrases_regex = [
        r"what's your answer\s*$",
        r"what is your answer\s*$",
        r"which is the answer\s*$",
        r"what is your choice\s*$",
        r"what's your choice\s*$",
        r"what's your option\s*$",
        r"what is your option\s*$",
        r"(?:the\s+)?options\s+are[:\s]*", # Added to catch "the options are:"
        r"(?:the\s+)?choices\s+are[:\s]*" # Added to catch "the choices are:"
    ]

    # 2. Try to find an explicit question mark '?' first
    if '?' in full_text:
        question_part, options_part = full_text.split('?', 1)
        question = question_part.strip() + "?"
        remaining_text_for_options = options_part.strip()
    else:
        # 3. If no '?', try to find an explicit question ending phrase
        ending_phrase_match = None
        for pattern in question_ending_phrases_regex:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                ending_phrase_match = match
                break
        if ending_phrase_match:
            question_and_options_part = full_text[:ending_phrase_match.start()].strip()
            remaining_text_for_options = full_text[ending_phrase_match.end():].strip()
            question = question_and_options_part # Assume everything before the ending phrase is the question
        else:
            # 4. If no '?' and no ending phrase, assume the whole text is the question
            # and options are implicitly listed at the end.
            # This is a less reliable fallback.
            question = full_text
            remaining_text_for_options = "" # Will try to extract options from full_text later

    # 5. Extract options from the `remaining_text_for_options` or `full_text`
    # Prioritize explicit prefixes
    text_to_parse_options_from = remaining_text_for_options if remaining_text_for_options else full_text

    # Split by explicit option prefixes
    explicit_parts = re.split(explicit_option_prefixes_regex, text_to_parse_options_from)

    if len(explicit_parts) > 1:
        # If explicit prefixes found, the first part (if any) might be part of the question
        # or just leading text. The rest are options.
        if not question and explicit_parts[0].strip():
            question = explicit_parts[0].strip() + "?" # If question wasn't set, set it now
        options = [p.strip() for p in explicit_parts[1:] if p.strip()]
    else:
        # No explicit prefixes. Try to split by common conjunctions/separators and then by spaces.
        # This is the crucial part for natural language option identification.
        
        # Remove common short words that are unlikely to be options
        common_filler_words = r'\b(?:a|an|the|is|are|in|on|at|of|with|from|to|for|which|what|who|where|when|how|your|my|his|her|its|their|our|a|an|the|is|are|in|on|at|of|with|from|to|for)\b'
        cleaned_options_text = re.sub(common_filler_words, ' ', text_to_parse_options_from, flags=re.IGNORECASE).strip()
        
        # Split by commas, "or", "and"
        potential_options_list = re.split(r'\s*(?:,|\bor\b|\band\b)\s*', cleaned_options_text, flags=re.IGNORECASE)
        
        final_options = []
        for opt in potential_options_list:
            opt = opt.strip()
            if opt:
                # Heuristic: if it's a short phrase (more than 1 word, and length > 3), keep it.
                # Otherwise, if it's a single word, add it.
                if ' ' in opt and len(opt.split()) > 1 and len(opt) > 3:
                    final_options.append(opt)
                elif opt: # Single word options
                    final_options.append(opt)
        options = [o for o in final_options if o] # Filter out empty strings

    # Ensure options are unique and not empty
    options = list(dict.fromkeys(options)) # Remove duplicates while preserving order
    options = [o for o in options if o] # Remove any empty strings that might have snuck in

    return question, options


# New function to process an MCQ question when in dedicated mode
def process_mcq_question(full_question_text: str):
    """
    Handles the parsing and answering of a single MCQ question.
    """
    question, options = parse_mcq_from_text(full_question_text)
            
    if question and options:
        speak("I've received the question and options. Thinking about the answer...")
        print(f"DEBUG: Parsed Question: '{question}'")
        print(f"DEBUG: Parsed Options: {options}")
        chosen_answer = answer_mcq_question(question, options)
        if chosen_answer:
            speak(f"The answer is: {chosen_answer}")
        else:
            speak("I had trouble determining the answer. Please try again.")
    else:
        speak("I couldn't properly understand the question and options from what you said. Please try again with the suggested format.")
        print(f"DEBUG: Failed to parse. Question: '{question}', Options: {options}")


@eel.expose
def handle_command_from_frontend(command):
    """Function called by the frontend chatbox to process text commands."""
    global jarvis_active, is_listening, in_mcq_answer_mode
    # For text commands, we assume Jarvis is active and process them.
    # We don't want to start a *new* listening loop if one is already running
    # but we ensure the command is processed.
    eel.DisplayMessage(f"You: {command}")
    
    if in_mcq_answer_mode:
        if command.lower().strip() == "end answer":
            in_mcq_answer_mode = False
            speak("Exiting multiple-choice question answering mode. Returning to normal operations.")
        else:
            process_mcq_question(command)
    else:
        # Pass the command as source_input_text when it comes from the frontend
        processCommand(command, source_input_text=command) 

    # If Jarvis was told to sleep, adjust UI and state
    if not jarvis_active:
        eel.HideSiriWave()
        eel.DisplayMessage("Jarvis is sleeping. Say 'Jarvis' to wake me up.")
        try:
            eel.hideImage()()
        except Exception as e:
            print(f"Error hiding image after command processing: {e}")
    elif not is_listening and not in_mcq_answer_mode:
        eel.HideSiriWave()
        eel.DisplayMessage("Listening for 'Jarvis'...")
import threading
import eel
import os
import base64
from flask import Flask, request, jsonify

eel.init("www")

@eel.expose
def receive_file(filename, base64_data):
    print(f"[📎] Receiving file: {filename}")

    if "," in base64_data:
        base64_data = base64_data.split(",")[1]

    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)

    try:
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(base64_data))
        print(f"✅ File saved at: {save_path}")
        eel.DisplayMessage(f"File '{filename}' received and saved.")
    except Exception as e:
        print("❌ Error saving file:", e)
        eel.DisplayMessage("Failed to save file.")

@eel.expose
def listen_from_frontend():
    """
    Function called by the frontend MicBtn or hotword to initiate continuous listening.
    This function will now loop as long as Jarvis is active.
    """
    global jarvis_active, is_listening, is_handling_complex_command, is_speaking, in_mcq_answer_mode
    if is_listening:
        print("Already listening. Skipping new listening loop.")
        return

    jarvis_active = True
    is_listening = True
    eel.ShowSiriWave()
    eel.DisplayMessage("🎤 Listening for 'Jarvis'...")

    while jarvis_active:
        while is_speaking:
            time.sleep(0.1)

        if is_handling_complex_command:
            eel.DisplayMessage("⚙️ Processing a multi-step command...")
            eel.HideSiriWave()
            time.sleep(0.5)
            continue

        if in_mcq_answer_mode:
            speak("Please state your multiple-choice question, or say 'end answer' to exit this mode.")
            command = listen_for_response_answer()
            if command.lower().strip() == "end answer":
                in_mcq_answer_mode = False
                speak("Exiting multiple-choice question answering mode. Returning to normal operations.")
            elif command:
                eel.DisplayMessage(f"🎙️ You: {command}")
                eel.receiverText(command)
                process_mcq_question(command)
            else:
                speak("I didn't hear a question. Please try again or say 'end answer'.")
            time.sleep(0.5)
            continue

        command = listen()
        if command:
            eel.DisplayMessage(f"🎙️ You: {command}")   # Show in main Jarvis display
            eel.appendUserMessage(command)             # 👈 Blue right-side chat bubble
            processCommand(command)
        else:
            if not jarvis_active:
                eel.DisplayMessage("Jarvis is sleeping. Say 'Jarvis' to wake me up.")
            else:
                eel.DisplayMessage("Didn't catch that. Still listening...")

        time.sleep(0.5)

    is_listening = False
    eel.HideSiriWave()
    eel.DisplayMessage("💤 Jarvis is sleeping. Say 'Jarvis' to wake me up.")
    print("Jarvis is now sleeping.")


def hotword_listener_thread(q):
    global jarvis_active
    while True:
        try:
            message = q.get(timeout=1)
            if message == "activate_jarvis":
                if not jarvis_active:
                    print("Jarvis activated by hotword!")
                    speak("Yes, how can I help you?")
                    listen_from_frontend()
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in hotword listener thread: {e}")
        time.sleep(0.1)

def start(command_queue):
    global hotword_queue
    hotword_queue = command_queue

    speak("Initializing Jarvis...")

    eel.init("www")

    threading.Thread(target=hotword_listener_thread, args=(hotword_queue,), daemon=True).start()

    eel.start('index.html', size=(1000, 800), block=False)

    while True:
        eel.sleep(1.0)


peer_agent_app = Flask("peer_agent")

@peer_agent_app.route("/receive", methods=["POST"])
def receive_meeting_request():
    data = request.get_json()
    speak(f"Received a meeting proposal from {data.get('from')}")

    creds = get_google_calendar_credentials_main()
    if not creds:
        return jsonify({"status": "error", "reason": "No credentials"}), 403

    service = build("calendar", "v3", credentials=creds)
    busy = get_free_busy_slots(service, ["primary"], dt.datetime.utcnow(), dt.datetime.utcnow() + dt.timedelta(days=2))
    busy_times = busy['primary'].get('busy', [])

    def is_free(proposed_dt):
        return all(not (dt.datetime.fromisoformat(b['start']) <= proposed_dt < dt.datetime.fromisoformat(b['end'])) for b in busy_times)

    for proposed in data.get("proposed_times", []):
        proposed_dt = dt.datetime.fromisoformat(proposed)
        if is_free(proposed_dt):
            event = {
                'summary': data.get("topic"),
                'start': {'dateTime': proposed_dt.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': (proposed_dt + dt.timedelta(minutes=data.get("duration_minutes", 30))).isoformat(), 'timeZone': 'UTC'},
                'attendees': [{'email': data.get("from")}, {'email': get_current_user_email()}]
            }
            service.events().insert(calendarId="primary", body=event).execute()
            return jsonify({"status": "confirmed", "time": proposed_dt.isoformat()})

    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    end = now + dt.timedelta(days=3)
    slot = now.replace(hour=10, minute=0, second=0, microsecond=0)
    while slot < end:
        if is_free(slot):
            return jsonify({"status": "counter_proposal", "alternative_time": slot.isoformat()})
        slot += dt.timedelta(minutes=30)

    return jsonify({"status": "unavailable"})


def run_peer_agent_listener():
    peer_agent_app.run(port=5001, debug=False)

threading.Thread(target=run_peer_agent_listener, daemon=True).start()


from file_completion import app as file_completion_flask_app
from analyze import app as analyze_flask_app
from question_bot import app as question_bot_flask_app
from presentation import app as presentation_flask_app
from solve import app as solve_flask_app
from information import app as information_flask_app
from worksheet import app as worksheet_flask_app # Import the Flask app from worksheet.py
from marks_analysis import app as marks_analysis_flask_app # Import the Flask app from marks_analysis.py
from lesson_planner import app as lesson_planner_flask_app # NEW: Import the Flask app from lesson_planner.py
from attendance import app as attendance_flask_app # NEW: Import the Flask app from attendance.py

def run_file_completion_flask():
    file_completion_flask_app.run(port=5002, debug=False)

def run_analyze_flask():
    analyze_flask_app.run(port=5003, debug=False)

def run_question_bot_flask():
    question_bot_flask_app.run(port=5004, debug=False)

def run_presentation_flask():
    presentation_flask_app.run(port=5005, debug=False)

def run_solve_flask():
    solve_flask_app.run(port=5006, debug=False)

def run_information_flask():
    information_flask_app.run(port=5007, debug=False)

def run_worksheet_flask(): # Function to run the worksheet Flask app
    worksheet_flask_app.run(port=5008, debug=False) # Run on a new port, e.g., 5008

def run_marks_analysis_flask(): # Function to run the marks_analysis Flask app
    marks_analysis_flask_app.run(port=5009, debug=False) # Run on port 5009

def run_lesson_planner_flask(): # NEW: Function to run the lesson_planner Flask app
    lesson_planner_flask_app.run(port=5010, debug=False) # Run on port 5010

def run_attendance_flask(): # NEW: Function to run the attendance Flask app
    attendance_flask_app.run(port=5011, debug=False) # Run on port 5011

threading.Thread(target=run_file_completion_flask, daemon=True).start()
threading.Thread(target=run_analyze_flask, daemon=True).start()
threading.Thread(target=run_question_bot_flask, daemon=True).start()
threading.Thread(target=run_presentation_flask, daemon=True).start()
threading.Thread(target=run_solve_flask, daemon=True).start()
threading.Thread(target=run_information_flask, daemon=True).start()
threading.Thread(target=run_worksheet_flask, daemon=True).start() # Start the worksheet Flask app
threading.Thread(target=run_marks_analysis_flask, daemon=True).start() # Start the marks_analysis Flask app
threading.Thread(target=run_lesson_planner_flask, daemon=True).start() # NEW: Start the lesson_planner Flask app
threading.Thread(target=run_attendance_flask, daemon=True).start() # NEW: Start the attendance Flask app

if __name__ == "__main__":
    print("Run `run.py` to start Jarvis with hotword detection.")

    print("\n--- Jarvis AI Presentation Assistant (Google Slides) ---")
    print("Commands:")
    print("  'auth' - To authorize / re-authorize Google Slides API access.")
    print("  'generate presentation on [topic]' - To create a presentation.")
    print("  'generate presentation from file' - To create a presentation from an uploaded file.")
    print("  'schedule meeting' - To schedule a new meeting using the Agentic AI Scheduling Assistant.")
    print("  'solve' - To solve a problem from an uploaded file or text.")
    print("  'get information' - To retrieve information from an uploaded file or text.")
    print("  'create worksheet' - To create a worksheet from an uploaded file (all levels).")
    print("  'create level [1-4] worksheet' - To create a worksheet for a specific level from an uploaded file.")
    print("  'analyze marks' - To analyze marks from an uploaded Excel file and send WhatsApp messages.")
    print("  'create google form' - To create a new Google Form with AI-generated questions.")
    print("  'plan lesson' or 'generate lesson plan' - To generate a lesson plan from an uploaded file.") # NEW
    print("  'generate a mail about [topic]' or 'send an email about [topic]' - To draft an email and open it in your browser.") # NEW
    print("  'store attendance' - To store the last uploaded attendance file.") # NEW
    print("  'download attendance' - To download the stored attendance file.") # NEW
    print("  'update attendance' - To update the attendance file based on detected signatures and names.") # NEW
    print("  'quit' / 'exit' - To stop the assistant.")
    print("-----------------------------------------------------")

    while True:
        cmd = input("🗣️ Type your Jarvis command: ").strip()
        if cmd.lower() in ["quit", "exit"]:
            print("Exiting Jarvis Presentation Assistant. Goodbye!")
            break
        elif "auth" == cmd.lower():
            authenticate_google_slides(speak)
        elif "generate presentation on" in cmd.lower():
            handle_presentation_command(cmd, speak)
        elif "schedule meeting" == cmd.lower():
            handle_scheduling_command(cmd, speak)
        elif "generate presentation from file" in cmd.lower():
            if last_uploaded_file:
                handle_file_command(cmd)
            else:
                speak("Please upload a file first using the GUI, then say 'generate presentation from file'.")
        elif "solve" == cmd.lower():
            if last_uploaded_file:
                handle_file_command(cmd)
            else:
                speak("Please upload a file first using the GUI, then say 'solve'.")
        elif "get information" == cmd.lower():
            # Explicitly import re within this block as well for CLI input
            import re 
            # Extract language if present for CLI input
            language_match = re.search(r"get information in (\w+)", cmd)
            language = "English"
            if language_match:
                language = language_match.group(1).capitalize()
                speak(f"Getting information in {language}.")
            handle_file_command(cmd, language=language) # Pass language
        elif "create level 1 worksheet" in cmd.lower() or \
             "create level 2 worksheet" in cmd.lower() or \
             "create level 3 worksheet" in cmd.lower() or \
             "create level 4 worksheet" in cmd.lower() or \
             "create worksheet" in cmd.lower(): # Handle worksheet commands
            if last_uploaded_file:
                handle_file_command(cmd)
            else:
                speak("Please upload a file first using the GUI, then say 'create worksheet' or 'create level [1-4] worksheet'.")
        elif "analyze marks" in cmd.lower(): # Handle "analyze marks" command in main loop
            if last_uploaded_file and (last_uploaded_file["filename"].endswith(('.xlsx', '.xls'))):
                handle_file_command(cmd)
            else:
                speak("Please upload an Excel file first to analyze marks.")
        elif "create google form" in cmd.lower() or "generate a form" in cmd.lower(): # Handle Google Forms command
            processCommand(cmd) # Call processCommand to handle this
        elif "plan lesson" in cmd.lower() or "generate lesson plan" in cmd.lower(): # NEW: Handle lesson plan commands
            if last_uploaded_file:
                handle_file_command(cmd)
            else:
                speak("Please upload a file first using the GUI, then say 'plan lesson' or 'generate lesson plan'.")
        elif "generate a mail about" in cmd.lower() or "send an email about" in cmd.lower(): # NEW: Handle email generation
            processCommand(cmd) # Call processCommand to handle this
        elif "store attendance" in cmd.lower() or "download attendance" in cmd.lower() or "update attendance" in cmd.lower(): # NEW: Handle attendance commands
            handle_attendance(cmd)
        else:
            print("Unrecognized command. Please use 'auth', 'generate presentation on [topic]', 'generate presentation from file', 'schedule meeting', 'solve', 'get information', 'create worksheet', 'create level [1-4] worksheet', 'analyze marks', 'create google form', 'plan lesson', 'generate a mail about [topic]', 'store attendance', 'download attendance', 'update attendance', or 'quit'.")
