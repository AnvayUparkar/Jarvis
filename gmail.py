# gmail.py
import json
import google.generativeai as google_ai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Placeholder speak function
def speak_placeholder(text):
    print(f"Gmail Integration: {text}")

# Load Gemini API key
try:
    from apikey import api_data as GEN_AI_API_KEY
except ImportError:
    print("Error: apikey.py not found or GEN_AI_API_KEY not defined.")
    GEN_AI_API_KEY = "YOUR_GEMINI_API_KEY"

# Configure Gemini
try:
    google_ai.configure(api_key=GEN_AI_API_KEY)
except Exception as e:
    print(f"❌ Gemini configuration failed: {e}")

# Generate email body using Gemini (no recipient in prompt)
def generate_email_body_with_gemini(subject: str, context: str = "", speak_func=None):
    if speak_func is None:
        speak_func = speak_placeholder

    prompt = f"""
    Write a polite and professional email.
    Subject: {subject}
    Context: {context if context else 'No specific context provided.'}
    Avoid addressing the recipient directly.
    Just return the email body only.
    """

    speak_func(f"Generating email body for subject: {subject}")
    print(f"🧠 Gemini generating email body for: {subject}")

    try:
        model = google_ai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        speak_func("AI couldn't generate the email content.")
        print(f"❌ Gemini error while generating email: {e}")
        return "Hi,\n\n[Email content could not be generated. Please try again later.]\n\nRegards."

# Send email using Gmail API
def send_email(subject: str, recipient: str, body_text: str, get_credentials_func=None, speak_func=None):
    if speak_func is None:
        speak_func = speak_placeholder

    if get_credentials_func is None:
        speak_func("Authentication function missing. Cannot send email.")
        return False

    creds = get_credentials_func()
    if not creds or 'https://www.googleapis.com/auth/gmail.send' not in creds.scopes:
        speak_func("Insufficient Gmail permissions. Please re-authenticate.")
        print("❌ Gmail scope missing.")
        return False
    if 'https://www.googleapis.com/auth/gmail.compose' not in creds.scopes:
        speak_func("Gmail draft permission was not granted. Please re-authenticate Jarvis.")
        return


    try:
        service = build('gmail', 'v1', credentials=creds)
        message = {
            'raw': create_raw_email(recipient, subject, body_text)
        }
        send_response = service.users().messages().send(userId='me', body=message).execute()
        speak_func("Email sent successfully.")
        print(f"✅ Email sent. Message ID: {send_response['id']}")
        return True
    except HttpError as error:
        speak_func(f"Gmail API error: {error.resp.status}")
        print(f"❌ Gmail API error: {error}")
        return False
    except Exception as e:
        speak_func(f"Error while sending email: {e}")
        print(f"❌ Unexpected error: {e}")
        return False

# Helper to create raw email in base64
def create_raw_email(to: str, subject: str, message_text: str):
    import base64
    from email.mime.text import MIMEText

    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw
