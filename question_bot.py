# question_bot_app.py
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

# Try to set Tesseract command, handle if pytesseract or tesseract are missing
try:
    # Attempt to set a common default path or rely on system PATH
    # This line might need to be customized based on your Tesseract installation
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Uncomment and modify for your system
    pass # If already in PATH or configured elsewhere, no need to set here
except Exception as e:
    print(f"WARNING: pytesseract configuration failed. OCR functionality may be limited. Error: {e}")


app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "www/uploaded_files"
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
        # if not pytesseract.pytesseract.tesseract_cmd:
        #     print("WARNING: Tesseract command not set. OCR may fail.")
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except pytesseract.TesseractNotFoundError:
        print("ERROR: Tesseract OCR is not installed or not found in PATH. Image text extraction will fail.")
        return ""
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
    return "Flask Question Bot service is running!", 200

@app.route("/generate-questions", methods=["POST"])
def generate_questions_endpoint():
    print("DEBUG: /generate-questions endpoint hit (with file).")
    if not request.json:
        print("ERROR: Request must be JSON.")
        return jsonify({"error": "Request must be JSON"}), 400

    filename = request.json.get("filename")
    base64_file_data = request.json.get("file_data")
    mime_type = request.json.get("mime_type") # Get MIME type from frontend

    if not filename or not base64_file_data or not mime_type:
        print("ERROR: Missing filename, file_data, or mime_type in request.")
        return jsonify({"error": "Missing filename, file_data, or mime_type"}), 400

    if model is None:
        return jsonify({"error": "Gemini API model is not configured. Please check your API key."}), 500

    temp_uploaded_filepath = None
    try:
        # Decode the base64 data and save it as a temporary file
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
            # For image input, send both inline_data and text prompt
            gemini_input_parts.append({
                "inline_data": { # Changed from "inlineData" to "inline_data"
                    "mime_type": mime_type, # Changed from "mimeType" to "mime_type"
                    "data": base64_file_data # Use original base64 data for Gemini
                }
            })
            # Add a text part to guide Gemini, referencing the extracted text
            # This helps Gemini if OCR is poor or to confirm the content type
            gemini_input_parts.append({
                "text": f"Generate questions based on the content of this image, which appears to be a syllabus or document. The extracted text from the image is:\n\n{extracted_text if extracted_text else 'No legible text was extracted by OCR. Please analyze the image content directly.'}"
            })
            print(f"DEBUG: Processed image and extracted text (length: {len(extracted_text)}).")
        else:
            return jsonify({"error": "Unsupported file type. Only .docx, .pdf, .png, .jpg, .jpeg are supported."}), 400
        
        # If text content is empty for non-image files, it might be an issue.
        # For images, we rely on the image itself even if OCR fails.
        if not extracted_text and not mime_type.startswith("image/"):
             print("WARNING: No text extracted from the document/PDF. This might result in poor question generation.")
             # Consider returning an error here or sending a different prompt to Gemini if no text is vital

        # Craft the prompt to generate questions from the syllabus
        # This part of the prompt will be appended to the input parts for Gemini
        question_prompt_template = """
        You are a question generation bot. Your task is to create a set of diverse and challenging questions based on the provided syllabus or document content.
        The questions should cover various topics and assess understanding at different levels (e.g., recall, application, analysis).

        You MUST generate Multiple Choice Questions (MCQ). Each MCQ question should have exactly 4 options. One of these options must be the correct answer.

        Provide the questions in a JSON array format. Each item in the array should be an object with the following structure:
        {
            "question": "The question text",
            "type": "Multiple Choice",
            "difficulty": "e.g., Easy, Medium, Hard",
            "topic": "The topic from the syllabus the question relates to (if identifiable)",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "The correct option (e.g., 'Option A' or the full text of the correct option)"
        }

        Please generate at least 5 questions.
        """
        
        # Determine how to add the question prompt to Gemini's input parts
        if mime_type.startswith("image/"):
            # For images, append the question_prompt_template to the existing text part for the image
            gemini_input_parts[1]["text"] += "\n\n" + question_prompt_template
        else:
            # For text-based documents (DOCX, PDF), add the question_prompt_template as a new text part
            gemini_input_parts.append({"text": question_prompt_template})

        print(f"DEBUG: Sending prompt to Generative Model. Number of parts: {len(gemini_input_parts)}")

        response = model.generate_content(gemini_input_parts)
        gemini_response_text = response.text
        print("DEBUG: Received response from Generative Model.")

        # Attempt to parse Gemini's response as JSON
        try:
            # Clean up potential markdown formatting from Gemini's JSON response
            if gemini_response_text.startswith("```json"):
                gemini_response_text = gemini_response_text[7:].strip()
            if gemini_response_text.endswith("```"):
                gemini_response_text = gemini_response_text[:-3].strip()

            questions_data = json.loads(gemini_response_text)
            if not isinstance(questions_data, list):
                raise ValueError("Expected a JSON array of questions.")

            # Basic validation for each question object
            for q in questions_data:
                if not all(k in q for k in ["question", "type", "difficulty"]):
                    raise ValueError("Each question object must contain 'question', 'type', and 'difficulty' fields.")
                
                # Validate MCQ specific fields if type is "Multiple Choice"
                if q.get("type") == "Multiple Choice":
                    if "options" not in q or not isinstance(q["options"], list) or len(q["options"]) != 4:
                        raise ValueError("MCQ type questions must have an 'options' array with 4 items.")
                    if "correct_answer" not in q or not isinstance(q["correct_answer"], str):
                        raise ValueError("MCQ type questions must have a 'correct_answer' string.")

            return jsonify({"questions": questions_data}), 200

        except json.JSONDecodeError as e:
            print(f"ERROR: Gemini response is not valid JSON: {e}. Raw response: {gemini_response_text[:500]}...")
            return jsonify({"error": "Failed to parse questions from model. Response was not valid JSON.", "raw_response": gemini_response_text}), 500
        except ValueError as e:
            print(f"ERROR: Invalid structure in Gemini response: {e}. Raw response: {gemini_response_text[:500]}...")
            return jsonify({"error": f"Invalid structure in generated questions: {e}", "raw_response": gemini_response_text}), 500

    except Exception as e:
        print(f"ERROR: An error occurred during question generation: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if temp_uploaded_filepath and os.path.exists(temp_uploaded_filepath):
            os.remove(temp_uploaded_filepath)
            print(f"DEBUG: Cleaned up temporary uploaded file: {temp_uploaded_filepath}")

@app.route("/generate-questions-no-file", methods=["POST"])
def generate_questions_no_file_endpoint():
    print("DEBUG: /generate-questions-no-file endpoint hit.")
    
    # Ensure request.json is a dictionary before trying to get "topic"
    # If request.json is None or not a dict, default topic to None.
    # This change handles cases where the request body might be empty or non-JSON.
    topic = request.json.get("topic") if request.json and isinstance(request.json, dict) else None

    if model is None:
        return jsonify({"error": "Gemini API model is not configured. Please check your API key."}), 500

    try:
        # Craft the prompt to generate questions based on the provided topic
        if topic:
            question_prompt = f"""
            You are a question generation bot. Your task is to create a set of diverse and challenging questions based on the topic: "{topic}".
            The questions should cover various sub-topics and assess understanding at different levels (e.g., recall, application, analysis).
            """
        else:
            # Default to general knowledge questions if no topic is provided in the JSON payload.
            # The 'main.py' is responsible for asking the user for a topic.
            question_prompt = """
            You are a question generation bot. Your task is to create a set of diverse and challenging general knowledge questions.
            The questions should cover various topics and assess understanding at different levels (e.g., history, science, arts, geography, current events).
            """
        
        question_prompt += """
        You MUST generate Multiple Choice Questions (MCQ). Each MCQ question should have exactly 4 options. One of these options must be the correct answer.

        Provide the questions in a JSON array format. Each item in the array should be an object with the following structure:
        {
            "question": "The question text",
            "type": "Multiple Choice",
            "difficulty": "e.g., Easy, Medium, Hard",
            "topic": "The specific sub-topic the question relates to (if identifiable)",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "The correct option (e.g., 'Option A' or the full text of the correct option)"
        }

        Please generate at least 5 questions.
        """
        
        print(f"DEBUG: Sending prompt to Generative Model. Topic: {topic if topic else 'General Knowledge'}")
        response = model.generate_content(question_prompt)
        gemini_response_text = response.text
        print("DEBUG: Received response from Generative Model.")

        # Attempt to parse Gemini's response as JSON
        try:
            # Clean up potential markdown formatting from Gemini's JSON response
            if gemini_response_text.startswith("```json"):
                gemini_response_text = gemini_response_text[7:].strip()
            if gemini_response_text.endswith("```"):
                gemini_response_text = gemini_response_text[:-3].strip()

            questions_data = json.loads(gemini_response_text)
            if not isinstance(questions_data, list):
                raise ValueError("Expected a JSON array of questions.")

            # Basic validation for each question object
            for q in questions_data:
                if not all(k in q for k in ["question", "type", "difficulty"]):
                    raise ValueError("Each question object must contain 'question', 'type', and 'difficulty' fields.")
                
                # Validate MCQ specific fields if type is "Multiple Choice"
                if q.get("type") == "Multiple Choice":
                    if "options" not in q or not isinstance(q["options"], list) or len(q["options"]) != 4:
                        raise ValueError("MCQ type questions must have an 'options' array with 4 items.")
                    if "correct_answer" not in q or not isinstance(q["correct_answer"], str):
                        raise ValueError("MCQ type questions must have a 'correct_answer' string.")

            return jsonify({"questions": questions_data}), 200

        except json.JSONDecodeError as e:
            print(f"ERROR: Gemini response is not valid JSON: {e}. Raw response: {gemini_response_text[:500]}...")
            return jsonify({"error": "Failed to parse questions from model. Response was not valid JSON.", "raw_response": gemini_response_text}), 500
        except ValueError as e:
            print(f"ERROR: Invalid structure in Gemini response: {e}. Raw response: {gemini_response_text[:500]}...")
            return jsonify({"error": f"Invalid structure in generated questions: {e}", "raw_response": gemini_response_text}), 500

    except Exception as e:
        print(f"ERROR: An error occurred during question generation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5004, debug=True) # Changed port to 5004 for consistency with main.py integration
