import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Using a single credentials file for all Google APIs for consistency
GOOGLE_CREDENTIALS_FILE = 'client_secret_798986409322-mhuifnus25qs6clsoejlhdsah7f4o6hl.apps.googleusercontent.com.json'
GOOGLE_TOKEN_FILE = 'token.json'
GOOGLE_CALENDAR_TOKEN_FILE = 'calendar_token.json'

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
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'openid'
]
SCOPES = list(set(SCOPES))

def get_google_credentials(allow_interaction=True):
    """
    Handles Google OAuth2.0 authentication for all Google APIs used by Jarvis.
    Attempts to load existing credentials from token.json or performs a new
    authorization flow if needed (and allowed). Ensures all required SCOPES are covered.
    """
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        print("Attempting to load Google credentials from token.json...")
        try:
            creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
            print("Google credentials loaded from token.json.")

            if not all(s in creds.scopes for s in SCOPES):
                print("Loaded credentials do not cover all required scopes. Forcing re-authentication.")
                creds = None
        except Exception as e:
            print(f"Error loading credentials from token.json: {e}. Re-authenticating.")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Google credentials expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                print("Google credentials refreshed successfully.")
                if not all(s in creds.scopes for s in SCOPES):
                    print("Refreshed credentials still do not cover all required scopes. Initiating new authentication flow.")
                    creds = None
            except Exception as e:
                print(f"Error refreshing credentials: {e}. Initiating new authentication flow.")
                creds = None
        
        if not creds:
            if not allow_interaction:
                print("Valid Google credentials not found and allow_interaction is False. Skipping auth flow.")
                return None
                
            print("Initiating new Google authentication flow...")
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                print("Google authentication completed.")
            except Exception as e:
                print(f"Error during Google authentication flow: {e}. Ensure '{GOOGLE_CREDENTIALS_FILE}' is valid and present.")
                return None
            
            try:
                with open(GOOGLE_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("Google credentials saved to token.json.")
            except Exception as e:
                print(f"Error saving credentials to token.json: {e}")
                
    if creds:
        print(f"DEBUG: Scopes currently loaded in credentials: {sorted(list(creds.scopes))}")
    else:
        print("DEBUG: No credentials loaded.")
        
    return creds

def get_current_user_email(allow_interaction=True):
    """
    Retrieves the primary email address of the currently authenticated Google user.
    """
    creds = get_google_credentials(allow_interaction=allow_interaction)
    if not creds:
        print("Failed to authenticate with Google. Cannot retrieve current user email.")
        return None

    try:
        service = build('people', 'v1', credentials=creds)
        profile = service.people().get(resourceName='people/me', personFields='emailAddresses').execute()
        
        email_addresses = profile.get('emailAddresses', [])
        if email_addresses:
            for email_entry in email_addresses:
                if email_entry.get('metadata', {}).get('primary'):
                    return email_entry['value']
            if email_addresses:
                return email_addresses[0]['value']
        
        print("No email address found for the current user.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching contact email: {e}")
        return None
