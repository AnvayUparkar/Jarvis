
import os
import atexit
import json
import msal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIGURATION (PLACEHOLDERS - REPLACE WITH YOUR AZURE APP DETAILS) ===
# TODO: Move sensitive data to .env
CLIENT_ID = "ba1b3da0-d628-4175-a821-b70e3b077a71"
TENANT_ID = "common" # or your specific tenant ID
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Scopes required for the application
SCOPES = [
    "User.Read",
    "EduAssignments.ReadWrite",
    "EduRoster.Read"
]

# Token Cache Path
CACHE_DIR = Path(__file__).parent.parent / ".msal_cache"
CACHE_FILE = CACHE_DIR / "token_cache.bin"

class TeamsAuth:
    """
    Handles Microsoft Teams OAuth2 Delegated Authentication.
    Uses MSAL PublicClientApplication (Device Code Flow or Interactive).
    """
    def __init__(self):
        self.cache = msal.SerializableTokenCache()
        self._load_cache()
        
        # Auto-save cache on exit
        atexit.register(self._save_cache)

        self.app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            token_cache=self.cache
        )

    def _load_cache(self):
        """Load token cache from disk if it exists."""
        if CACHE_FILE.exists():
            try:
                self.cache.deserialize(CACHE_FILE.read_text())
                logger.info("Token cache loaded.")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {e}")

    def _save_cache(self):
        """Save token cache to disk."""
        if self.cache.has_state_changed:
            try:
                CACHE_DIR.mkdir(exist_ok=True)
                CACHE_FILE.write_text(self.cache.serialize())
                logger.info("Token cache saved.")
            except Exception as e:
                logger.warning(f"Failed to save token cache: {e}")

    def acquire_token(self):
        """
        Acquire a token interactively or silently.
        Returns the access token or raises an exception.
        """
        accounts = self.app.get_accounts()
        result = None

        if accounts:
            # Try silent acquisition
            logger.info(f"Found account: {accounts[0]['username']}")
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])

        if not result:
            # No suitable token in cache, let's get a new one
            logger.info("No suitable token found in cache. Starting interactive auth...")
            
            # Interactive Flow (Opens Browser) - Best for Desktop Apps
            try:
                result = self.app.acquire_token_interactive(scopes=SCOPES)
            except Exception as e:
                logger.error(f"Interactive auth failed: {e}")
                # Fallback to Device Code Flow if interactive fails (e.g. headless)
                flow = self.app.initiate_device_flow(scopes=SCOPES)
                if "user_code" not in flow:
                    raise Exception("Failed to create device flow")
                
                print(flow["message"])
                result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            logger.info("Token acquired successfully.")
            return result["access_token"]
        else:
            error_description = result.get("error_description", "Unknown error")
            logger.error(f"Authentication failed: {error_description}")
            raise Exception(f"Authentication failed: {error_description}")

    def get_headers(self):
        """Get Authorization headers for Requests."""
        token = self.acquire_token()
        return {"Authorization": "Bearer " + token}

# Singleton instance
_teams_auth = None

def get_auth_client():
    global _teams_auth
    if _teams_auth is None:
        _teams_auth = TeamsAuth()
    return _teams_auth

if __name__ == "__main__":
    # Test authentication
    try:
        auth = get_auth_client()
        token = auth.acquire_token()
        print("Success! Access Token (truncated):", token[:20] + "...")
    except Exception as e:
        print(f"Error: {e}")
