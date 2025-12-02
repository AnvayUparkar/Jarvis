# marks_analysis.py
import os
import pandas as pd
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from urllib.parse import quote # Import quote for URL encoding
import json
# Removed subprocess, webbrowser, time as they are not suitable for a backend service directly controlling desktop UI

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
        # In a production environment, you might want to exit or raise an exception here.

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

def whatsApp(mobile_no, message, flag, name):
    """
    This 'whatsApp' function is for the Flask backend service.
    It SIMULATES the WhatsApp action by printing to the console.
    Actual desktop automation (opening WhatsApp, sending messages) must be done
    by the client-side script (e.g., main.py) using libraries like pyautogui.
    """
    jarvis_message = ""
    encoded_message = quote(message)
    
    # WhatsApp Desktop URI scheme
    whatsapp_desktop_uri = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
    
    # WhatsApp Web URL
    whatsapp_web_url = f"https://web.whatsapp.com/send?phone={mobile_no}&text={encoded_message}"

    if flag == 'message':
        jarvis_message = f"Message drafted for {name} ({mobile_no})."
        print(f"\n--- SIMULATED WhatsApp Message Drafted ---")
        print(f"To: {name} ({mobile_no})")
        print(f"Message: {message}")
        print(f"WhatsApp Desktop URI (for client): {whatsapp_desktop_uri}")
        print(f"WhatsApp Web URL (for client): {whatsapp_web_url}")
        print(f"Status: {jarvis_message}")
        
    elif flag == 'call' or flag == 'video_call':
        jarvis_message = f"WhatsApp {flag} prepared for {name} ({mobile_no})."
        print(f"\n--- SIMULATED WhatsApp {flag.capitalize()} Prepared ---")
        print(f"To: {name} ({mobile_no})")
        print(f"Status: {jarvis_message}")
        print("This action needs to be initiated by the client-side script.")

    else:
        print("Invalid WhatsApp action requested (backend simulation).")
        return

    print(f"-----------------------------------")


def analyze_marks_and_draft_messages(excel_file_path):
    """
    Analyzes student marks from an Excel file, identifies students with low marks,
    drafts complaint messages using Gemini, and prepares them for sending.
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file_path)

        # Ensure required columns exist
        required_columns = ['Name', 'Marks', 'Phone_Number']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Excel file must contain columns: {', '.join(required_columns)}")

        low_marks_students = []
        messages_to_send = [] # This list will be returned

        # Identify students with marks less than 10 out of 20
        # Assuming 'Marks' column contains numerical values
        for index, row in df.iterrows():
            student_name = row['Name']
            marks = row['Marks']
            # Ensure phone number is treated as string and remove any non-digit characters if necessary
            phone_number = str(row['Phone_Number']).strip()
            # Basic formatting for phone number (e.g., add +91 if it's a 10-digit Indian number)
            if len(phone_number) == 10 and phone_number.isdigit():
                phone_number = '+91' + phone_number
            elif not phone_number.startswith('+'):
                print(f"WARNING: Phone number '{phone_number}' for {student_name} does not start with '+' and is not a 10-digit number. It might be invalid for WhatsApp.")


            if pd.isna(marks): # Handle cases where marks might be missing
                print(f"WARNING: Marks missing for student {student_name}. Skipping.")
                continue

            # Assuming total marks are 20, check if less than 10
            if marks < 10:
                low_marks_students.append({
                    "name": student_name,
                    "marks": marks,
                    "phone_number": phone_number
                })

        if not low_marks_students:
            return {"status": "success", "message": "No students found with marks less than 10.", "messages_to_send": []}

        # Draft messages for students with low marks using Gemini
        for student in low_marks_students:
            student_name = student['name']
            student_marks = student['marks']
            student_phone = student['phone_number']

            if model is None:
                print(f"ERROR: Skipping message generation for {student_name} due to missing Gemini API model.")
                messages_to_send.append({
                    "student_name": student_name,
                    "phone_number": student_phone,
                    "message": f"Dear {student_name}, your marks are {student_marks}. (Message generation skipped due to API error)."
                })
                continue

            prompt = f"""
            Draft a formal complaint message for a student named {student_name} who scored {student_marks} out of 20 in a recent assessment.
            The message should be polite but firm, express concern about the low score, and encourage them to improve.
            It should be suitable for sending via WhatsApp.
            Start with "Dear {student_name}," and include their marks.
            Do not include any placeholders like [Your Name] or [Course Name].
            """
            print(f"DEBUG: Drafting message for {student_name} with marks {student_marks}...")
            response = model.generate_content(prompt)
            complaint_message = response.text.strip()
            print(f"DEBUG: Message drafted for {student_name}.")

            messages_to_send.append({
                "student_name": student_name,
                "phone_number": student_phone,
                "message": complaint_message
            })

        # The backend service will return the messages, not send them directly
        # The client (main.py) will then handle the actual desktop WhatsApp sending.
        return {
            "status": "success",
            "low_marks_students_count": len(low_marks_students),
            "messages_to_send": messages_to_send # Return the list of messages
        }

    except FileNotFoundError:
        return {"status": "error", "message": f"Excel file not found at {excel_file_path}", "messages_to_send": []}
    except ValueError as e:
        return {"status": "error", "message": str(e), "messages_to_send": []}
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during analysis: {e}")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}", "messages_to_send": []}

@app.route("/", methods=["GET"])
def home():
    """A simple root route to confirm the Flask service is running."""
    return "Flask Marks Analysis service is running!", 200

@app.route("/analyze-marks", methods=["POST"])
def analyze_marks_endpoint():
    print("DEBUG: /analyze-marks endpoint hit.")
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        if not filename.endswith(('.xlsx', '.xls')):
            return jsonify({"error": "Unsupported file type. Only .xlsx and .xls are supported."}), 400

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            file.save(filepath)
            print(f"DEBUG: File saved to {filepath}")
            result = analyze_marks_and_draft_messages(filepath)
            return jsonify(result), 200
        except Exception as e:
            print(f"ERROR: Failed to process file {filename}: {e}")
            return jsonify({"error": f"Failed to process file: {str(e)}"}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"DEBUG: Cleaned up temporary uploaded file: {filepath}")

if __name__ == "__main__":
    app.run(port=5009, debug=True) # Changed port to 5009
