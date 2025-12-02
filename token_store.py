import json
import os
from datetime import datetime, timedelta # Import datetime and timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_FILE = "token.json" # Changed to match your usage in refresh_token and authenticate_and_save_token


def save_token(token_data):
    """Saves the token data along with the timestamp of last authentication."""
    token_data['last_authenticated_at'] = datetime.now().isoformat() # Store ISO formatted datetime
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=4) # Use indent for readability


def load_token():
    """Loads the token data."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            # Convert the stored 'last_authenticated_at' back to datetime object
            if 'last_authenticated_at' in data:
                data['last_authenticated_at'] = datetime.fromisoformat(data['last_authenticated_at'])
            return data
    return None


def refresh_token():
    """
    Refreshes the token if it has expired or if a year has passed since last authentication.
    """
    try:
        token_data = load_token() # Use load_token to get the full data, including timestamp

        if not token_data:
            print("❌ No token found. Please authenticate.")
            authenticate_and_save_token()
            return

        # Check if 1 year has passed since last authentication
        # We'll re-load the creds object within this function
        last_auth_time = token_data.get('last_authenticated_at')
        if last_auth_time:
            one_year_ago = datetime.now() - timedelta(days=365) # Approximately 1 year
            if last_auth_time < one_year_ago:
                print("⏳ More than one year has passed since last full authentication. Forcing re-authentication.")
                # Force re-authentication by deleting the token file
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                authenticate_and_save_token()
                return # Exit after re-authentication

        # Create credentials object from the loaded token data
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data.get("refresh_token"), # Use .get() for safety
            token_uri=token_data["token_uri"],
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=token_data["scopes"],
        )

        # Refresh the token if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("🔄 Access Token refreshed successfully!")

            # Save the updated token back to token.json
            # We'll save the whole creds object and then re-add our custom timestamp
            creds_json = json.loads(creds.to_json())
            creds_json['last_authenticated_at'] = datetime.now().isoformat() # Update timestamp on refresh
            with open(TOKEN_FILE, "w") as token_file:
                json.dump(creds_json, token_file, indent=4)
        elif not creds.expired:
            print("✅ Access Token is still valid.")
        elif not creds.refresh_token:
            print("❌ Refresh token is missing or invalid. Re-authenticating.")
            # If refresh token is missing, force re-authentication
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            authenticate_and_save_token()

    except Exception as e:
        print(f"❌ Error during token refresh/check: {e}")
        print("Attempting full re-authentication as a fallback...")
        # As a fallback, try to re-authenticate
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        authenticate_and_save_token()


def authenticate_and_save_token():
    """
    Authenticates the user and saves the token to token.json.
    """
    SCOPES = ["https://www.googleapis.com/auth/contacts.readonly"]
    # Ensure the client_secrets.json path is correct for your system
    CLIENT_SECRET_PATH = r"C:\Users\Anvay Uparkar\Python\JARVIS\client_secret_133871116699-teh8o91k85noal3nid1tkr1o6j3kbfce.apps.googleusercontent.com.json"

    if not os.path.exists(CLIENT_SECRET_PATH):
        print(f"ERROR: Client secret file not found at {CLIENT_SECRET_PATH}")
        print("Please ensure your client_secret_*.json file is in the correct location.")
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_PATH,
            SCOPES,
        )
        creds = flow.run_local_server(port=0)

        # Convert credentials to JSON and add our custom timestamp
        creds_json = json.loads(creds.to_json())
        save_token(creds_json) # Use our save_token to add the timestamp
        print("✅ Authentication successful. Token saved.")
        return creds
    except Exception as e:
        print(f"❌ Error during initial authentication: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    # Simulate a scenario where the token might exist or not
    # For testing, you might want to delete token.json manually first
    # os.remove(TOKEN_FILE) # Uncomment to force a fresh auth every time for testing

    print("\n--- Initial Load/Auth Check ---")
    current_token_data = load_token()
    if not current_token_data:
        print("No token found, starting authentication process...")
        authenticate_and_save_token()
    else:
        print("Token already exists. Checking validity...")

    print("\n--- Refreshing Token (or re-authenticating if needed) ---")
    refresh_token()

    # You can inspect the token.json file to see the 'last_authenticated_at' field
    print("\n--- Current Token Details (after refresh/auth) ---")
    final_token_data = load_token()
    if final_token_data:
        print(f"Token present: {final_token_data['token'][:20]}...")
        print(f"Refresh token present: {'refresh_token' in final_token_data}")
        print(f"Last Authenticated: {final_token_data.get('last_authenticated_at')}")
    else:
        print("No token available after operations.")