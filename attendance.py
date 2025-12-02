# attendance.py

import os
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import pytesseract # For OCR
from PIL import Image # For image processing
from io import BytesIO # To handle image data in memory

# For PDF processing (install: pip install PyMuPDF)
try:
    import fitz # PyMuPDF
except ImportError:
    fitz = None
    print("WARNING: PyMuPDF (fitz) not installed. PDF processing for attendance update will not be available.")

try:
    # Attempt to set a common default path or rely on system PATH
    # This path might need to be adjusted based on the user's Tesseract installation
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
except Exception as e:
    print(f"WARNING: pytesseract configuration failed. OCR functionality may be limited. Error: {e}")

    
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "www/uploaded_files"
# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    """A simple root route to confirm the Flask service is running."""
    return "Flask Attendance service is running!", 200

@app.route("/store-attendance", methods=["POST"])
def store_attendance():
    """
    Handles the upload and storage of an attendance Excel file.
    The uploaded file will be saved as 'attendance.xls' or 'attendance.xlsx'
    in the UPLOAD_FOLDER, overwriting any existing file with the same name.
    """
    print("DEBUG: /store-attendance endpoint hit.")
    if 'file' not in request.files:
        print("ERROR: No 'file' part in the request for /store-attendance.")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        print("ERROR: No selected file for /store-attendance.")
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Secure the original filename to extract its extension
        original_filename_secured = secure_filename(file.filename)
        _, file_extension = os.path.splitext(original_filename_secured)

        # Check for allowed extensions
        if file_extension.lower() not in ('.xlsx', '.xls'):
            print(f"ERROR: Unsupported file type '{file_extension}' for /store-attendance. Only .xlsx and .xls are supported.")
            return jsonify({"error": "Unsupported file type. Only .xlsx and .xls are supported."}), 400

        # Define the standardized target filename for storage
        # This will be either 'attendance.xls' or 'attendance.xlsx'
        target_filename = "attendance" + file_extension.lower()
        filepath = os.path.join(UPLOAD_FOLDER, target_filename)

        try:
            # Save the uploaded file, overwriting if it exists
            file.save(filepath)
            print(f"DEBUG: Attendance file saved to {filepath}")
            return jsonify({"status": "success", "message": f"Attendance file '{target_filename}' stored successfully."}), 200
        except Exception as e:
            print(f"ERROR: Failed to store attendance file {target_filename}: {e}")
            return jsonify({"error": f"Failed to store attendance file: {str(e)}"}), 500

@app.route("/download-attendance", methods=["GET"])
def download_attendance():
    """
    Handles the download of the stored attendance Excel file.
    It attempts to find 'attendance.xlsx' first, then 'attendance.xls'.
    """
    print("DEBUG: /download-attendance endpoint hit.")
    
    # Define potential file paths for the attendance file
    filepath_xlsx = os.path.join(UPLOAD_FOLDER, "attendance.xlsx")
    filepath_xls = os.path.join(UPLOAD_FOLDER, "attendance.xls")
    
    # Check if attendance.xlsx exists
    if os.path.exists(filepath_xlsx):
        print(f"DEBUG: Serving attendance.xlsx from {filepath_xlsx}")
        # Serve the file for download
        return send_from_directory(UPLOAD_FOLDER, "attendance.xlsx", as_attachment=True)
    # If not, check if attendance.xls exists
    elif os.path.exists(filepath_xls):
        print(f"DEBUG: Serving attendance.xls from {filepath_xls}")
        # Serve the file for download
        return send_from_directory(UPLOAD_FOLDER, "attendance.xls", as_attachment=True)
    else:
        # If neither file is found, return an error
        print(f"ERROR: No attendance file found in {UPLOAD_FOLDER}")
        return jsonify({"error": "Attendance file not found. Please upload it first."}), 404

def extract_text_from_image(image_bytes):
    """Extracts text from image bytes using Tesseract OCR."""
    print("DEBUG: Attempting to extract text from image.")
    try:
        img = Image.open(BytesIO(image_bytes))
        # Use a more robust configuration for Tesseract if needed, e.g., specifying language
        text = pytesseract.image_to_string(img, config='--psm 6') # psm 6 for single uniform block of text
        print(f"DEBUG: Successfully extracted text from image. Length: {len(text)}.")
        return text
    except pytesseract.TesseractNotFoundError:
        print("ERROR: Tesseract is not installed or not found in your PATH. Cannot extract text from image.")
        return None
    except Exception as e:
        print(f"ERROR: Failed to extract text from image: {e}")
        return None

def extract_text_from_pdf(pdf_bytes):
    """Extracts text from PDF bytes using PyMuPDF."""
    print("DEBUG: Attempting to extract text from PDF.")
    if not fitz:
        print("ERROR: PyMuPDF (fitz) is not installed. Cannot process PDF.")
        return None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        print(f"DEBUG: Successfully extracted text from PDF. Length: {len(text)}.")
        return text
    except Exception as e:
        print(f"ERROR: Failed to extract text from PDF: {e}")
        return None

def simulate_signature_detection(text_content, name):
    """
    Simulates signature detection based on keywords in the extracted text.
    This is a placeholder for actual computer vision signature detection.
    It checks if the name is present near "signature" or "signed by".
    """
    print(f"DEBUG: Simulating signature detection for name: '{name}'.")
    if not text_content:
        print("DEBUG: No text content provided for signature simulation.")
        return False

    # Normalize text and name for comparison
    text_content_lower = text_content.lower()
    name_lower = name.lower()

    # Heuristic 1: Look for "signature" or "signed by" near the name
    signature_keywords = ["signature", "signed by", "sign here", "approved by", "present", "attended"]
    
    for keyword in signature_keywords:
        # Check if the keyword is present
        if keyword in text_content_lower:
            # Find the index of the keyword
            keyword_index = text_content_lower.find(keyword)
            # Define a search window around the keyword (e.g., 50 characters before and after)
            search_start = max(0, keyword_index - 50)
            search_end = min(len(text_content_lower), keyword_index + 50)
            search_area = text_content_lower[search_start:search_end]

            # Check if the name is present in this search area
            if name_lower in search_area:
                print(f"DEBUG: Signature simulated for '{name}' near keyword '{keyword}'.")
                return True
    
    # Heuristic 2: Simple check if the name appears anywhere in the document
    # and we assume if the document is for attendance, their presence implies signature.
    # This is a very weak heuristic and should be replaced by actual signature detection.
    if name_lower in text_content_lower:
        print(f"DEBUG: Name '{name}' found in document. Assuming implied signature for demo.")
        return True # For demonstration, if name is found, assume they signed.

    print(f"DEBUG: No signature simulated for '{name}'.")
    return False


@app.route("/modify-attendance", methods=["POST"])
def modify_attendance():
    """
    Receives an uploaded file (image or PDF), extracts text using OCR,
    and then simulates signature detection to update the attendance.xlsx/.xls file.
    """
    print("DEBUG: /modify-attendance endpoint hit.")

    if 'file' not in request.files: # Changed from 'document' to 'file' to match main.py's send
        print("ERROR: No 'file' part in the request for /modify-attendance.")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file'] # Changed from 'document' to 'file'
    if file.filename == '':
        print("ERROR: No selected file for /modify-attendance.")
        return jsonify({"error": "No selected file"}), 400

    if not file:
        print("ERROR: No file uploaded for /modify-attendance.")
        return jsonify({"error": "No file uploaded."}), 400

    filename = secure_filename(file.filename)
    file_extension = os.path.splitext(filename)[1].lower()
    file_bytes = file.read() # Read file content into bytes

    text_content = None
    try:
        if file_extension in ('.png', '.jpg', '.jpeg'):
            text_content = extract_text_from_image(file_bytes)
        elif file_extension == '.pdf':
            if fitz:
                text_content = extract_text_from_pdf(file_bytes)
            else:
                print("ERROR: PyMuPDF not installed. Cannot process PDF files for signature detection.")
                return jsonify({"error": "PyMuPDF not installed. Cannot process PDF files for signature detection."}), 400
        else:
            print(f"ERROR: Unsupported file type '{file_extension}' for attendance modification.")
            return jsonify({"error": "Unsupported file type for attendance modification. Please upload an image (.png, .jpg, .jpeg) or a PDF (.pdf) file."}), 400
    except Exception as e:
        print(f"CRITICAL ERROR: Exception during text extraction: {e}")
        return jsonify({"error": f"Failed to extract text from the uploaded file: {str(e)}. Ensure OCR tools are correctly set up."}), 500

    if text_content is None:
        print("ERROR: Text content is None after extraction attempt.")
        return jsonify({"error": "Failed to extract text from the uploaded file. Cannot proceed with attendance update. Ensure Tesseract is installed and configured correctly."}), 500
    
    print(f"DEBUG: Extracted text (first 500 chars): {text_content[:500]}...")


    # --- LOAD AND MODIFY ATTENDANCE FILE ---
    attendance_filepath = None
    if os.path.exists(os.path.join(UPLOAD_FOLDER, "attendance.xlsx")):
        attendance_filepath = os.path.join(UPLOAD_FOLDER, "attendance.xlsx")
    elif os.path.exists(os.path.join(UPLOAD_FOLDER, "attendance.xls")):
        attendance_filepath = os.path.join(UPLOAD_FOLDER, "attendance.xls")
    
    if not attendance_filepath:
        print(f"ERROR: Attendance file (attendance.xlsx or attendance.xls) not found in {UPLOAD_FOLDER}.")
        return jsonify({"error": "Attendance file (attendance.xlsx or attendance.xls) not found. Please upload it first."}), 404

    try:
        # Read the attendance file
        df = pd.read_excel(attendance_filepath)
        print(f"DEBUG: Loaded attendance file from {attendance_filepath}")

        # Get the current date to use as the column header
        today_date = datetime.now().strftime('%Y-%m-%d') # Format:YYYY-MM-DD
        print(f"DEBUG: Current date for attendance column: {today_date}")

        # Ensure the attendance column for today's date exists
        if today_date not in df.columns:
            df[today_date] = '' # Initialize with empty strings if not present
            print(f"DEBUG: Created new column '{today_date}' for today's attendance.")

        # Determine the name column more robustly
        name_column = None
        for col in df.columns:
            if col.lower() == 'name':
                name_column = col
                break
        if name_column is None and len(df.columns) > 0:
            name_column = df.columns[0] # Fallback to the first column if no 'name' column found
            print(f"WARNING: No 'name' column found. Using first column '{name_column}' as the name column.")
        elif name_column is None:
            print("ERROR: No columns found in the attendance file. Cannot process.")
            return jsonify({"error": "Attendance file is empty or has no recognizable name column."}), 400

        print(f"DEBUG: Using '{name_column}' as the name column for attendance updates.")
        
        updated_count = 0
        names_marked_present = []
        names_marked_absent = []

        for index, row in df.iterrows():
            # Convert name to string and lowercase for case-insensitive comparison
            df_name = str(row[name_column]).strip()
            print(f"DEBUG: Processing name: '{df_name}'")

            # Simulate signature detection for each name
            if simulate_signature_detection(text_content, df_name):
                df.at[index, today_date] = 'P'
                names_marked_present.append(df_name)
                updated_count += 1
                print(f"DEBUG: Marked '{df_name}' as Present.")
            else:
                df.at[index, today_date] = 'A'
                names_marked_absent.append(df_name)
                updated_count += 1
                print(f"DEBUG: Marked '{df_name}' as Absent.")

        # Save the modified DataFrame back to the Excel file
        df.to_excel(attendance_filepath, index=False)
        print(f"DEBUG: Attendance file updated and saved to {attendance_filepath}")

        return jsonify({
            "status": "success",
            "message": f"Attendance file modified successfully. {updated_count} entries updated for {today_date}.",
            "details": {
                "date_column_updated": today_date,
                "names_marked_present": names_marked_present,
                "names_marked_absent": names_marked_absent
            }
        }), 200

    except FileNotFoundError:
        print(f"ERROR: Attendance file not found at {attendance_filepath}")
        return jsonify({"error": "Attendance file not found. Please upload it first."}), 404
    except pd.errors.EmptyDataError:
        print(f"ERROR: Attendance file at {attendance_filepath} is empty.")
        return jsonify({"error": "Attendance file is empty. Please ensure it contains data."}), 400
    except KeyError as ke:
        print(f"ERROR: Missing expected column in attendance file: {ke}")
        return jsonify({"error": f"Missing expected column in attendance file: {ke}. Ensure your Excel file has a 'Name' column or names in the first column."}), 400
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to modify attendance file: {e}")
        return jsonify({"error": f"Failed to modify attendance file: {str(e)}"}), 500

if __name__ == "__main__":
    # Run the Flask app on a different port to avoid conflicts with other services
    app.run(port=5011, debug=True)
