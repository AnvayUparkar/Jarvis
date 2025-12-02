import os
import uuid
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from docx import Document
from werkzeug.utils import secure_filename
import json
import base64
from PIL import Image # Import Pillow for image processing
import pytesseract # Import pytesseract for OCR
import PyPDF2 # Import PyPDF2 for PDF text extraction

# Google API specific imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import webbrowser # For opening the presentation URL in a browser
import sys # For path manipulation
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# --- API Key Configuration ---
# IMPORTANT: Replace "" with your actual Gemini API key.
# If you are using an apikey.py file, ensure GEN_AI_API_KEY is correctly defined there.
# Example: GEN_AI_API_KEY = "YOUR_API_KEY_HERE"
try:
    from apikey import GEN_AI_API_KEY
    if not GEN_AI_API_KEY:
        raise ValueError("GEN_AI_API_KEY is empty in apikey.py. Please provide your API key.")
except ImportError:
    print("WARNING: apikey.py not found. Please set your API key directly in this file.")
    # If apikey.py is not used, set your API key directly here:
    GEN_AI_API_KEY = os.getenv("GEMINI_API_KEY", "") # Fallback to environment variable or empty string

    if not GEN_AI_API_KEY:
        print("CRITICAL ERROR: GEMINI_API_KEY is not set. Please set it in apikey.py or as an environment variable.")
        # You might want to exit or raise an exception here in a production environment
        # For development, we'll let it proceed but note the issue.


# --- Tesseract OCR Configuration ---
# IMPORTANT: You must install Tesseract OCR on your system.
# Download from: https://tesseract-ocr.github.io/tessdoc/Installation.html
# After installation, set the path to your tesseract executable if it's not in your system's PATH.
# Example for Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Example for Linux/macOS (often in PATH, but if not, find its location):
# pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract' # Or similar path

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    print("WARNING: pytesseract not found. Notification reading may not work.")
except Exception as e:
    print(f"WARNING: Tesseract OCR setup failed: {e}. Notification reading may not work.")



app = Flask(__name__)
CORS(app)

# Separate upload folder for presentations to keep things organized
UPLOAD_FOLDER = "www/uploaded_presentation_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure Gemini AI model
if GEN_AI_API_KEY:
    try:
        genai.configure(api_key=GEN_AI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to configure Gemini API with provided key: {e}")
        model = None # Set model to None if configuration fails
else:
    print("CRITICAL ERROR: Gemini API key is missing. Model will not be available.")
    model = None # Ensure model is None if API key is missing


# --- Google Slides API Configuration ---
GOOGLE_CREDENTIALS_FILE = 'credentials3.json'
GOOGLE_TOKEN_FILE = 'token.json' # Active configuration for storing token
GOOGLE_CALENDAR_TOKEN_FILE = 'calendar_token.json' # Not used in this file but kept for consistency

SCOPES = [
    'https://www.googleapis.com/auth/calendar.freebusy',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/contacts.readonly',
    'openid'
]
SCOPES = list(set(SCOPES)) # Remove duplicates to ensure clean scope list


# --- Google Slides API Authentication ---
def get_google_credentials():
    """
    Handles Google OAuth2.0 authentication for Google Slides and Drive APIs.
    Attempts to load existing credentials or performs a new authorization flow if needed.
    Ensures all required SCOPES are covered.
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
                print(f"❌ Error saving credentials to token.json: {e}")
                
    return creds

# --- Gemini Function to Get Slide Content ---
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
    For the content of each slide, provide at least 5-7 comprehensive bullet points. Each bullet point should be a comprehensive and self-contained explanation, providing significant detail and directly elaborating on the slide's heading. Think of each bullet as a mini-paragraph summarizing a key aspect.
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
        model = genai.GenerativeModel("gemini-2.0-flash") 
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
def create_google_presentation(topic, slides_content, speak, use_template=False, template_id=None):
    """
    Creates a new Google Slides presentation and populates it with content.
    Optionally copies an existing Google Slides template presentation.
    'speak' is passed to allow this module to use Jarvis's voice output.
    
    Args:
        topic (str): The main topic of the presentation.
        slides_content (list): A list of dictionaries, each representing a slide's content.
        speak (function): A function to provide voice output (e.g., Jarvis's speak function).
        use_template (bool): If True, attempts to use a Google Slides template.
        template_id (str, optional): The ID of the Google Slides presentation to use as a template.
                                     This MUST be a Google Slides ID, not a local file path (e.g., PDF, PPTX).
                                     If a local file is intended as a content source, it should be processed
                                     separately to extract text for Gemini.
    """
    creds = get_google_credentials()
    if not creds:
        speak("Failed to authenticate with Google. Cannot create presentation.")
        print("❌ Failed to get Google credentials. Cannot create presentation.")
        return None

    try:
        slides_service = build('slides', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds) # Initialize Drive service

        presentation_id = None
        presentation_title = f"{topic} - Jarvis Generated Presentation"

        if use_template and template_id:
            try:
                # Copy the template presentation from Google Drive
                copy_body = {
                    'name': presentation_title
                }
                copied_file = drive_service.files().copy(
                    fileId=template_id,
                    body=copy_body
                ).execute()
                presentation_id = copied_file.get('id')
                speak(f"Copied template and creating presentation titled {presentation_title}.")
                print(f"✅ Copied Google Slides template (ID: {template_id}) to new presentation with ID: {presentation_id}")

                # Get all existing slide IDs from the copied presentation to delete them
                # This ensures a clean slate for new content while preserving the template's theme/background.
                existing_presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
                existing_slide_ids = [s['objectId'] for s in existing_presentation.get('slides', [])]
                
                requests_batch = []
                for slide_obj_id in existing_slide_ids:
                    requests_batch.append({
                        'deleteObject': {
                            'objectId': slide_obj_id
                        }
                    })
                if requests_batch:
                    slides_service.presentations().batchUpdate(
                        presentationId=presentation_id,
                        body={'requests': requests_batch}
                    ).execute()
                    print(f"Deleted {len(existing_slide_ids)} existing slides from the copied template to prepare for new content.")

            except HttpError as err:
                print(f"❌ Drive API Error when copying template: {err}")
                speak(f"Failed to copy template: {err.resp.status}. Please ensure the template ID is correct and you have permissions to access it.")
                return None
            except Exception as e:
                print(f"❌ An unexpected error occurred while copying template: {e}")
                speak("I encountered an issue while copying the template.")
                return None
        else:
            # Create a new blank presentation if no template is used or provided
            body = {
                'title': presentation_title
            }
            presentation = slides_service.presentations().create(body=body).execute()
            presentation_id = presentation.get('presentationId')
            speak(f"Creating a new blank presentation titled {presentation_title}.")
            print(f"✅ Created new blank presentation with ID: {presentation_id}")

            # Delete the default first slide if it's a new blank presentation
            initial_presentation_get = slides_service.presentations().get(presentationId=presentation_id).execute()
            initial_slide_id = initial_presentation_get['slides'][0]['objectId'] if initial_presentation_get['slides'] else None
            
            requests_batch = [] # Initialize requests_batch for new blank presentation
            if initial_slide_id:
                requests_batch.append({
                    'deleteObject': {
                        'objectId': initial_slide_id
                    }
                })
                print(f"Added request to delete default initial slide: {initial_slide_id}")
            else:
                print("No default initial slide found to delete.")

        # Now, add the main Title Slide and content slides to the chosen presentation_id
        
        # Add the main Title Slide (first slide of the presentation)
        main_title_slide_id = str(uuid.uuid4())
        main_title_textbox_id = str(uuid.uuid4())

        requests_batch.append({
            'createSlide': {
                'objectId': main_title_slide_id,
                'slideLayoutReference': {
                    'predefinedLayout': 'TITLE'
                }
            }
        })
        
        requests_batch.append({
            'createShape': {
                'objectId': main_title_textbox_id,
                'shapeType': 'TEXT_BOX', 
                'elementProperties': {
                    'pageObjectId': main_title_slide_id,
                    'size': {
                        'width': {'magnitude': 9000000, 'unit': 'EMU'},
                        'height': {'magnitude': 1000000, 'unit': 'EMU'}
                    },
                    'transform': {
                        'scaleX': 1, 'scaleY': 1, 'shearX': 0, 'shearY': 0, 'translateX': 500000, 'translateY': 1000000, 'unit': 'EMU'
                    }
                }
            }
        })

        requests_batch.append({
            'insertText': {
                'objectId': main_title_textbox_id,
                'insertionIndex': 0,
                'text': presentation_title
            }
        })
        
        # Add content slides based on Gemini's output
        for i, slide in enumerate(slides_content):
            current_slide_id = str(uuid.uuid4())
            title_textbox_id = str(uuid.uuid4())
            body_textbox_id = str(uuid.uuid4())

            requests_batch.append({
                'createSlide': {
                    'objectId': current_slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'BLANK'
                    }
                }
            })

            requests_batch.append({
                'createShape': {
                    'objectId': title_textbox_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': current_slide_id,
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

            # --- FIX: Support both 'heading'/'content' and 'title'/'content_points' slide formats ---
            slide_title = slide.get("heading") or slide.get("title") or f"Slide {i+1}"
            slide_content = slide.get("content") or slide.get("content_points") or []

            requests_batch.append({
                'insertText': {
                    'objectId': title_textbox_id,
                    'insertionIndex': 0,
                    'text': slide_title
                }
            })
            
            requests_batch.append({
                'createShape': {
                    'objectId': body_textbox_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': current_slide_id,
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

            content_text = "\n".join([f"• {item}" for item in slide_content])
            requests_batch.append({
                'insertText': {
                    'objectId': body_textbox_id,
                    'insertionIndex': 0,
                    'text': content_text
                }
            })
            
            if slide_content and isinstance(slide_content, list):
                requests_batch.append({
                    'createParagraphBullets': {
                        'objectId': body_textbox_id,
                        'textRange': {'type': 'ALL'},
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                })

        if requests_batch:
            slides_service.presentations().batchUpdate(
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
            # In a real Jarvis integration, you would typically get use_template and template_id
            # from user input or a more complex command parsing.
            # For this example, we'll assume no template is used when called via handle_presentation_command.
            url = create_google_presentation(topic, slides_content, speak)
            if url:
                speak("Google Slides presentation generated successfully. Opening it in your browser.")
                # Note: In a Flask app context, you typically wouldn't open a browser directly.
                # This would be handled by the frontend receiving the URL.
                webbrowser.open(url) 
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


def extract_text_from_docx(file_path):
    """
    Extracts all text from a .docx file.
    """
    try:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"ERROR: Could not extract text from DOCX {file_path}: {e}")
        return ""

def extract_text_from_image(image_path):
    """
    Extracts text from an image file using OCR (pytesseract).
    """
    try:
        # Ensure Tesseract OCR command is set if needed
        if not pytesseract.pytesseract.tesseract_cmd:
            print("WARNING: Tesseract command not set. OCR may fail.")
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except pytesseract.TesseractNotFoundError:
        print("ERROR: Tesseract OCR is not installed or not found in PATH. Image text extraction will fail.")
    except Exception as e:
        print(f"ERROR: Could not perform OCR on image {image_path}: {e}")
        return ""

def extract_text_from_pdf(file_path):
    """
    Extracts all text from a PDF file.
    """
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or "" # extract_text() might return None
        return text
    except Exception as e:
        print(f"ERROR: Could not extract text from PDF {file_path}: {e}")
        return ""

@app.route("/", methods=["GET"])
def home():
    """A simple root route to confirm the Flask service is running."""
    return "Flask Presentation Bot service is running!", 200

@app.route("/generate-presentation-from-file", methods=["POST"])
def generate_presentation_from_file_endpoint():
    print("DEBUG: /generate-presentation-from-file endpoint hit (with file).")
    if not request.json:
        print("ERROR: Request must be JSON.")
        return jsonify({"error": "Request must be JSON"}), 400

    filename = request.json.get("filename")
    base64_file_data = request.json.get("file_data")
    mime_type = request.json.get("mime_type")
    
    # New parameters for template functionality
    use_template = request.json.get("use_template", False)
    template_id = request.json.get("template_id")

    if not filename or not base64_file_data or not mime_type:
        print("ERROR: Missing filename, file_data, or mime_type in request.")
        return jsonify({"error": "Missing filename, file_data, or mime_type"}), 400

    if model is None:
        return jsonify({"error": "Gemini API model is not configured. Please check your API key."}), 500

    temp_uploaded_filepath = None
    try:
        file_bytes = base64.b64decode(base64_file_data)
        unique_filename = f"{uuid.uuid4()}_{secure_filename(filename)}"
        temp_uploaded_filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(temp_uploaded_filepath, "wb") as f:
            f.write(file_bytes)
        print(f"DEBUG: Temporary file saved at: {temp_uploaded_filepath}")

        extracted_text = ""
        gemini_input_parts = []

        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            extracted_text = extract_text_from_docx(temp_uploaded_filepath)
            gemini_input_parts.append({"text": extracted_text})
            print("DEBUG: Extracted text from DOCX.")
        elif mime_type == "application/pdf":
            extracted_text = extract_text_from_pdf(temp_uploaded_filepath)
            gemini_input_parts.append({"text": extracted_text})
            print("DEBUG: Extracted text from PDF.")
        elif mime_type.startswith("image/"):
            extracted_text = extract_text_from_image(temp_uploaded_filepath)
            gemini_input_parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64_file_data
                }
            })
            gemini_input_parts.append({
                "text": f"Generate a presentation outline based on the content of this image, which appears to be a document. The extracted text from the image is:\n\n{extracted_text if extracted_text else 'No legible text was extracted by OCR. Please analyze the image content directly.'}"
            })
            # Fix: Avoid len(None) error
            print(f"DEBUG: Processed image and extracted text (length: {len(extracted_text) if extracted_text is not None else 0}).")
        else:
            return jsonify({"error": "Unsupported file type. Only .docx, .pdf, .png, .jpg, .jpeg are supported."}), 400
        
        if not extracted_text and not mime_type.startswith("image/"):
            print("WARNING: No text extracted from the document/PDF. This might result in poor presentation generation.")

        presentation_prompt_template = """
        You are a presentation outline generation bot. Your task is to create a structured presentation outline based on the provided document content.
        The outline should include a title and a series of slides, each with a title, key content points, and optional speaker notes.

        For each slide, ensure that every content_point is a comprehensive, self-contained, and detailed explanation. Each point should be several sentences long, providing significant detail and directly elaborating on the slide's title. Avoid generic or vague points; make each bullet a mini-paragraph summarizing a key aspect.

        Provide the presentation outline in a JSON object format. The object should have the following structure:
        {
            "title": "Overall Presentation Title",
            "slides": [
                {
                    "slide_number": 1,
                    "title": "Slide 1 Title",
                    "content_points": [
                        "A detailed, multi-sentence explanation for key point 1 of slide 1, directly related to the slide title.",
                        "Another detailed, self-contained explanation for key point 2 of slide 1."
                    ],
                    "notes": "Speaker notes for slide 1 (optional)"
                },
                {
                    "slide_number": 2,
                    "title": "Slide 2 Title",
                    "content_points": [
                        "A detailed, multi-sentence explanation for key point 1 of slide 2.",
                        "Another detailed, self-contained explanation for key point 2 of slide 2."
                    ],
                    "notes": "Speaker notes for slide 2 (optional)"
                }
                // ... more slides
            ]
        }

        Please generate at least 3-5 slides, covering the main sections or topics of the document. Do not include any text or markdown outside the JSON object.
        """
        
        if mime_type.startswith("image/"):
            gemini_input_parts[1]["text"] += "\n\n" + presentation_prompt_template
        else:
            gemini_input_parts.append({"text": presentation_prompt_template})

        print(f"DEBUG: Sending prompt to Generative Model. Number of parts: {len(gemini_input_parts)}")

        response = model.generate_content(gemini_input_parts)
        gemini_response_text = response.text
        print("DEBUG: Received response from Generative Model.")

        try:
            if gemini_response_text.startswith("```json"):
                gemini_response_text = gemini_response_text[7:].strip()
            if gemini_response_text.endswith("```"):
                gemini_response_text = gemini_response_text[:-3].strip()

            presentation_data = json.loads(gemini_response_text)
            if not isinstance(presentation_data, dict):
                raise ValueError("Expected a JSON object for presentation data.")
            if "title" not in presentation_data or "slides" not in presentation_data:
                raise ValueError("Presentation data must contain 'title' and 'slides' fields.")
            if not isinstance(presentation_data["slides"], list):
                raise ValueError("'slides' field must be a JSON array.")

            for slide in presentation_data["slides"]:
                if not all(k in slide for k in ["slide_number", "title", "content_points"]):
                    raise ValueError("Each slide object must contain 'slide_number', 'title', and 'content_points' fields.")
                if not isinstance(slide["content_points"], list):
                    raise ValueError("'content_points' field in a slide must be a list.")
                if "notes" in slide and not isinstance(slide["notes"], str):
                    raise ValueError("'notes' field in a slide must be a string if present.")

            # Call create_google_presentation with template parameters
            # Placeholder for 'speak' function, assuming it's available in the Flask context or mocked
            # In a real Jarvis integration, 'speak' would come from the main Jarvis loop.
            # For a standalone Flask app, you might remove 'speak' or pass a dummy function.
            def dummy_speak(text):
                print(f"SPEAK: {text}")

            url = create_google_presentation(
                presentation_data["title"], 
                presentation_data["slides"], 
                dummy_speak, # Pass dummy_speak or actual speak function
                use_template=use_template, 
                template_id=template_id
            )

            if url:
                return jsonify({"presentation_url": url}), 200
            else:
                return jsonify({"error": "Failed to create Google Slides presentation."}), 500

        except json.JSONDecodeError as e:
            print(f"ERROR: Gemini response is not valid JSON: {e}. Raw response: {gemini_response_text[:500]}...")
            return jsonify({"error": "Failed to parse presentation from model. Response was not valid JSON.", "raw_response": gemini_response_text}), 500
        except ValueError as e:
            print(f"ERROR: Invalid structure in Gemini response: {e}. Raw response: {gemini_response_text[:500]}...")
            return jsonify({"error": f"Invalid structure in generated presentation: {e}", "raw_response": gemini_response_text}), 500

    except Exception as e:
        print(f"ERROR: An error occurred during presentation generation: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if temp_uploaded_filepath and os.path.exists(temp_uploaded_filepath):
            os.remove(temp_uploaded_filepath)
            print(f"DEBUG: Cleaned up temporary uploaded file: {temp_uploaded_filepath}")

if __name__ == "__main__":
    app.run(port=5005, debug=True)
