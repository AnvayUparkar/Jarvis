import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the import
import_statement = "from google_auth_helpers import get_google_credentials, get_current_user_email, GOOGLE_TOKEN_FILE, GOOGLE_CALENDAR_TOKEN_FILE, SCOPES, GOOGLE_CREDENTIALS_FILE\n"
if "from google_auth_helpers import" not in content:
    # insert after "from google.oauth2.credentials import Credentials"
    content = content.replace(
        "from google.oauth2.credentials import Credentials\n",
        f"from google.oauth2.credentials import Credentials\n{import_statement}"
    )

# 2. Remove GOOGLE_CREDENTIALS_FILE and SCOPES block
pattern1 = r"(?s)# Using a single credentials file.*?print\(f\".*?Error configuring Gemini API.*?\"\)\n\n\n"
# Wait, let's just remove the block from # Using a single credentials file to SCOPES = list(set(SCOPES))
pattern1_alt = r"(?s)# Using a single credentials file.*?SCOPES = list\(set\(SCOPES\)\)\n"
content = re.sub(pattern1_alt, "", content)

# 3. Remove get_google_credentials
pattern2 = r"(?s)# --- Google API Authentication \(Unified\) ---.*?def get_google_credentials\(\):.*?print\(\"DEBUG: No credentials loaded\.\"\)\n"
content = re.sub(pattern2, "", content)

# 4. Remove get_current_user_email
pattern3 = r"(?s)# --- NEW FUNCTION: get_current_user_email ---.*?def get_current_user_email\(\):.*?return None\n"
content = re.sub(pattern3, "", content)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done updating main.py")
