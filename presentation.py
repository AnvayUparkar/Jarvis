import os
import uuid
import json
import base64
import sys
import webbrowser
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import google.generativeai as genai

# Document Processing Imports
from docx import Document
from PIL import Image
import pytesseract
import PyPDF2

# Google API Imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---

# API Key Setup
try:
    from apikey import GEN_AI_API_KEY
    if not GEN_AI_API_KEY:
        raise ValueError("GEN_AI_API_KEY is empty in apikey.py.")
except ImportError:
    print("WARNING: apikey.py not found. Using environment variable or empty string.")
    GEN_AI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEN_AI_API_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY is not set.")

# Enable/Disable Styling
ENABLE_NANO_BANANA = True  

# Tesseract Setup
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    print("WARNING: Tesseract OCR configuration might be incorrect.")

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "www/uploaded_presentation_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure Gemini
if GEN_AI_API_KEY:
    genai.configure(api_key=GEN_AI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

# --- Google Slides API Config ---
GOOGLE_CREDENTIALS_FILE = 'credentials3.json'
GOOGLE_TOKEN_FILE = 'token.json'
SCOPES = [
    'https://www.googleapis.com/auth/calendar.freebusy',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# --- HELPER: Google Authentication ---
def get_google_credentials():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(GOOGLE_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Auth Error: {e}")
                return None
    return creds

# --- HELPER: Gemini Content Generation (With Theme Detection) ---
def get_slide_content(topic, speak):
    """
    Generates presentation slide content AND selects a visual theme using Google Gemini.
    Returns: (theme_string, slides_list)
    """
    prompt = f"""Create a 6-slide presentation about {topic}.
    
    1. Analyze the topic to decide the Visual Theme:
       - If it is about AI, Coding, Cyber Security, Gaming, Space, or Future Tech, choose "TECH_DARK".
       - If it is about Business, Finance, Education, History, or General topics, choose "PROFESSIONAL_LIGHT".
    
    2. For each slide, provide a descriptive heading and 5-7 detailed content bullet points.

    3. Provide ONLY JSON in the following format:
    {{
        "theme": "TECH_DARK" or "PROFESSIONAL_LIGHT",
        "slides": [
            {{"heading": "Slide 1 Title", "content": ["Point 1...", "Point 2..."]}},
            ...
        ]
    }}
    """
    print(f"🧠 Asking Gemini for content and theme on: {topic}")
    speak(f"Thinking about content and visual style for {topic}...")
    try:
        response = model.generate_content(prompt)
        json_string = response.text.strip()
        
        # Clean markdown if present
        if json_string.startswith("```json"):
            json_string = json_string[7:].strip()
        if json_string.endswith("```"):
            json_string = json_string[:-3].strip()

        data = json.loads(json_string)
        
        theme = data.get("theme", "PROFESSIONAL_LIGHT")
        slides = data.get("slides", [])[:6]
        
        return theme, slides

    except Exception as e:
        print(f"❌ Error parsing JSON from Gemini: {e}")
        speak("I had trouble understanding the content from Gemini.")
        return "PROFESSIONAL_LIGHT", None

# --- NANO BANANA VISUAL ENHANCEMENT LAYER ---
def apply_nano_banana_style(slide_id, title_id, body_id, theme="PROFESSIONAL_LIGHT", is_title_slide=False):
    """
    Generates Google Slides API requests based on the selected theme.
    """
    requests = []

    # --- DEFINE PALETTES BASED ON THEME ---
    if theme == "TECH_DARK":
        # Style: Futuristic, AI, Dark Mode (Deep Navy / Neon)
        bg_color = {'red': 0.05, 'green': 0.08, 'blue': 0.15} # Deep Midnight Blue
        title_color = {'red': 1.0, 'green': 1.0, 'blue': 1.0} # White
        body_color = {'red': 0.9, 'green': 0.9, 'blue': 0.95} # Off-White
        accent_color = {'red': 0.0, 'green': 0.8, 'blue': 1.0} # Neon Cyan
        accent_alpha = 0.8
        font_title = 'Montserrat'
        font_body = 'Roboto'
    else: 
        # Style: Business, Clean, Professional (Light Mode)
        bg_color = {'red': 1.0, 'green': 1.0, 'blue': 1.0} # Pure White
        title_color = {'red': 0.1, 'green': 0.1, 'blue': 0.3} # Dark Navy Text
        body_color = {'red': 0.25, 'green': 0.25, 'blue': 0.25} # Dark Grey Text
        accent_color = {'red': 0.1, 'green': 0.2, 'blue': 0.5} # Professional Blue
        accent_alpha = 1.0
        font_title = 'Arial'
        font_body = 'Open Sans'

    # 1. VISUALS: Background Color
    requests.append({
        'updatePageProperties': {
            'objectId': slide_id,
            'pageProperties': {
                'pageBackgroundFill': {
                    'propertyState': 'RENDERED',
                    'solidFill': {
                        'color': {'rgbColor': bg_color}
                    }
                }
            },
            'fields': 'pageBackgroundFill'
        }
    })

    # 2. SHAPES: Accent Sidebar/Shape
    accent_shape_id = f"accent_{slide_id}"
    requests.append({
        'createShape': {
            'objectId': accent_shape_id,
            'shapeType': 'RECTANGLE',
            'elementProperties': {
                'pageObjectId': slide_id,
                'size': {
                    'width': {'magnitude': 150000, 'unit': 'EMU'}, 
                    'height': {'magnitude': 6000000, 'unit': 'EMU'} 
                },
                'transform': {
                    'scaleX': 1, 'scaleY': 1,
                    'translateX': 350000, 'translateY': 0, 'unit': 'EMU'
                }
            }
        }
    })
    
    # --- FIX IS HERE: alpha moved inside solidFill ---
    requests.append({
        'updateShapeProperties': {
            'objectId': accent_shape_id,
            'shapeProperties': {
                'shapeBackgroundFill': {
                    'solidFill': {
                        'color': {'rgbColor': accent_color},
                        'alpha': accent_alpha  # Correct placement
                    }
                },
                'outline': {'propertyState': 'NOT_RENDERED'}
            },
            'fields': 'shapeBackgroundFill,outline'
        }
    })

    # 3. TYPOGRAPHY: Styling
    requests.append({
        'updateTextStyle': {
            'objectId': title_id,
            'style': {
                'foregroundColor': {'opaqueColor': {'rgbColor': title_color}},
                'bold': True,
                'fontFamily': font_title, 
                'fontSize': {'magnitude': 42 if is_title_slide else 32, 'unit': 'PT'}
            },
            'fields': 'foregroundColor,bold,fontFamily,fontSize'
        }
    })

    if body_id:
        requests.append({
            'updateTextStyle': {
                'objectId': body_id,
                'style': {
                    'foregroundColor': {'opaqueColor': {'rgbColor': body_color}},
                    'fontFamily': font_body,
                    'fontSize': {'magnitude': 14, 'unit': 'PT'}
                },
                'fields': 'foregroundColor,fontFamily,fontSize'
            }
        })

    return requests
# --- CORE: Create Presentation Function ---
def create_google_presentation(topic, slides_content, speak, theme="PROFESSIONAL_LIGHT"):
    """
    Creates a new Google Slides presentation and populates it with content.
    Applies Nano Banana styling based on the theme.
    """
    creds = get_google_credentials()
    if not creds:
        speak("Failed to authenticate with Google.")
        return None

    try:
        service = build('slides', 'v1', credentials=creds)
        
        presentation_title = f"{topic} - Jarvis Generated ({theme})"
        body = {'title': presentation_title}
        presentation = service.presentations().create(body=body).execute()
        presentation_id = presentation.get('presentationId')
        speak(f"Creating a {theme.lower().replace('_', ' ')} style presentation titled {presentation_title}.")

        requests_batch = []

        # 1. Delete default slide
        initial = service.presentations().get(presentationId=presentation_id).execute()
        if initial.get('slides'):
            requests_batch.append({'deleteObject': {'objectId': initial['slides'][0]['objectId']}})

        # --- MAIN TITLE SLIDE ---
        main_title_slide_id = str(uuid.uuid4())
        main_title_textbox_id = str(uuid.uuid4())

        # A. Create Slide
        requests_batch.append({
            'createSlide': {
                'objectId': main_title_slide_id,
                'slideLayoutReference': {'predefinedLayout': 'BLANK'}
            }
        })

        # B. Create Text Box (MUST happen before styling)
        requests_batch.append({
            'createShape': {
                'objectId': main_title_textbox_id,
                'shapeType': 'TEXT_BOX', 
                'elementProperties': {
                    'pageObjectId': main_title_slide_id,
                    'size': {'width': {'magnitude': 8000000, 'unit': 'EMU'}, 'height': {'magnitude': 2000000, 'unit': 'EMU'}},
                    'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 750000, 'translateY': 2500000, 'unit': 'EMU'}
                }
            }
        })
        
        # C. Insert Text
        requests_batch.append({
            'insertText': {'objectId': main_title_textbox_id, 'insertionIndex': 0, 'text': presentation_title}
        })

        # D. Apply Styling (Now safe because objects exist)
        if ENABLE_NANO_BANANA:
            requests_batch.extend(apply_nano_banana_style(
                main_title_slide_id, main_title_textbox_id, None, theme=theme, is_title_slide=True
            ))

        # --- CONTENT SLIDES ---
        for i, slide in enumerate(slides_content):
            current_slide_id = str(uuid.uuid4())
            title_textbox_id = str(uuid.uuid4())
            body_textbox_id = str(uuid.uuid4())

            # A. Create Slide
            requests_batch.append({
                'createSlide': {
                    'objectId': current_slide_id,
                    'slideLayoutReference': {'predefinedLayout': 'BLANK'}
                }
            })

            # B. Create Title Box
            requests_batch.append({
                'createShape': {
                    'objectId': title_textbox_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': current_slide_id,
                        'size': {'width': {'magnitude': 8500000, 'unit': 'EMU'}, 'height': {'magnitude': 1000000, 'unit': 'EMU'}},
                        'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 550000, 'translateY': 350000, 'unit': 'EMU'}
                    }
                }
            })
            slide_title = slide.get("heading") or f"Slide {i+1}"
            requests_batch.append({
                'insertText': {'objectId': title_textbox_id, 'insertionIndex': 0, 'text': slide_title}
            })
            
            # C. Create Body Box
            requests_batch.append({
                'createShape': {
                    'objectId': body_textbox_id,
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': current_slide_id,
                        'size': {'width': {'magnitude': 8500000, 'unit': 'EMU'}, 'height': {'magnitude': 4000000, 'unit': 'EMU'}},
                        'transform': {'scaleX': 1, 'scaleY': 1, 'translateX': 550000, 'translateY': 1500000, 'unit': 'EMU'}
                    }
                }
            })
            content_text = "\n".join([f"• {item}" for item in slide.get("content", [])])
            requests_batch.append({
                'insertText': {'objectId': body_textbox_id, 'insertionIndex': 0, 'text': content_text}
            })
            
            if content_text:
                requests_batch.append({
                    'createParagraphBullets': {
                        'objectId': body_textbox_id,
                        'textRange': {'type': 'ALL'},
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                })

            # D. Apply Styling (Now safe because objects exist)
            if ENABLE_NANO_BANANA:
                requests_batch.extend(apply_nano_banana_style(
                    current_slide_id, title_textbox_id, body_textbox_id, theme=theme
                ))

        # Execute
        if requests_batch:
            service.presentations().batchUpdate(
                presentationId=presentation_id, body={'requests': requests_batch}
            ).execute()
            print(f"✅ Slides created successfully with {theme} theme.")
        
        return f"https://docs.google.com/presentation/d/{presentation_id}/edit"

    except Exception as e:
        print(f"❌ Error creating presentation: {e}")
        speak("I encountered an issue while creating the presentation.")
        return None
    
# --- COMMAND HANDLER (CLI/Voice) ---
def handle_presentation_command(command, speak):
    """
    Processes a command to generate and create a presentation with auto-theme detection.
    """
    if "generate presentation on" in command.lower():
        topic = command.lower().replace("generate presentation on", "").strip()
        if not topic:
            speak("Please specify a topic.")
            return

        # Get Theme AND Content
        theme, slides_content = get_slide_content(topic, speak)
        
        if slides_content:
            print(f"🎨 Creating {theme} style presentation for: {topic}")
            url = create_google_presentation(topic, slides_content, speak, theme=theme)
            if url:
                speak("Presentation generated successfully. Opening it now.")
                webbrowser.open(url) 
            else:
                speak("Sorry, I failed to create the presentation.")
        else:
            speak("Sorry, I could not generate content from Gemini.")

# --- UTILITIES: File Extraction ---
def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception:
        return ""

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception:
        return ""

# --- FLASK ENDPOINTS ---
@app.route("/", methods=["GET"])
def home():
    return "Flask Presentation Bot (With Dynamic Themes) is running!", 200

@app.route("/generate-presentation-from-file", methods=["POST"])
def generate_presentation_from_file_endpoint():
    if not request.json:
        return jsonify({"error": "Request must be JSON"}), 400

    filename = request.json.get("filename")
    base64_file_data = request.json.get("file_data")
    mime_type = request.json.get("mime_type")
    use_template = request.json.get("use_template", False)
    template_id = request.json.get("template_id")

    if not all([filename, base64_file_data, mime_type]):
        return jsonify({"error": "Missing file data"}), 400

    if not model:
        return jsonify({"error": "Gemini not configured"}), 500

    temp_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{secure_filename(filename)}")
    
    try:
        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(base64_file_data))

        extracted_text = ""
        gemini_input_parts = []

        if "wordprocessingml" in mime_type:
            extracted_text = extract_text_from_docx(temp_path)
            gemini_input_parts.append({"text": extracted_text})
        elif "pdf" in mime_type:
            extracted_text = extract_text_from_pdf(temp_path)
            gemini_input_parts.append({"text": extracted_text})
        elif mime_type.startswith("image/"):
            extracted_text = extract_text_from_image(temp_path)
            gemini_input_parts.append({
                "inline_data": {"mime_type": mime_type, "data": base64_file_data}
            })
            gemini_input_parts.append({"text": f"Extracted text: {extracted_text}"})
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        # Prompt with Theme Detection
        prompt = """
        You are a presentation bot. 
        1. Analyze the document. 
           - If it is Technical/AI/Future/Science, set "theme" to "TECH_DARK".
           - Otherwise, set "theme" to "PROFESSIONAL_LIGHT".

        2. Provide output as JSON:
        {
            "title": "Presentation Title",
            "theme": "TECH_DARK" or "PROFESSIONAL_LIGHT",
            "slides": [
                {
                    "slide_number": 1, 
                    "title": "Title", 
                    "content_points": ["Point 1", "Point 2"]
                }
            ]
        }
        Generate at least 3-5 slides.
        """
        
        gemini_input_parts.append({"text": prompt})
        response = model.generate_content(gemini_input_parts)
        
        resp_text = response.text.strip()
        if resp_text.startswith("```json"): resp_text = resp_text[7:].strip()
        if resp_text.endswith("```"): resp_text = resp_text[:-3].strip()
        
        data = json.loads(resp_text)
        
        # Extract Theme
        theme = data.get("theme", "PROFESSIONAL_LIGHT")
        
        def dummy_speak(text): print(f"API SPEAK: {text}")

        url = create_google_presentation(
            data["title"], 
            data["slides"], 
            dummy_speak, 
            theme=theme,
            use_template=use_template, 
            template_id=template_id
        )

        if url:
            return jsonify({"presentation_url": url, "theme_used": theme}), 200
        else:
            return jsonify({"error": "Failed to create slides"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    app.run(port=5005, debug=True)