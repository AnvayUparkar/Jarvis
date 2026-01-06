import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

def get_google_contacts():
    """
    Fetches all contacts from the user's Google Contacts.

    Returns:
        list: A list of contact dictionaries. Each dictionary represents a contact.
              Returns an empty list if there are no contacts or if an error occurs.
    """
    creds = None
    if os.path.exists('token.json'):
        print("✅ Found existing token.json file.")
    else:
        print("❌ token.json file not found. Starting OAuth flow...")
    
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json',
                                                          ['https://www.googleapis.com/auth/contacts.readonly'])
        except Exception as e:
            print(f"⚠️ Error loading token: {e}")
            if 'invalid_grant' in str(e):
                print("🔄 Token is invalid. Clearing for re-authentication...")
                os.remove('token.json')
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                with open('token.json', 'w') as token:
                    print("💾 Saving refreshed credentials to token.json...")
                    token.write(creds.to_json())
            except Exception as e:
                print(f"⚠️ Failed to refresh token: {e}")
                if 'invalid_grant' in str(e):
                    print("🔄 Refresh token is invalid. Clearing for re-authentication...")
                    if os.path.exists('token.json'):
                        os.remove('token.json')
                    creds = None
        
        if not creds or not creds.valid:
            print("🔑 No valid credentials found. Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_133871116699-cn0a6i1lja1n9gkos0f3kr6sia0jej55.apps.googleusercontent.com.json',
                ['https://www.googleapis.com/auth/contacts.readonly'])
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                print("💾 Saving new credentials to token.json...")
                token.write(creds.to_json())

    try:
        print("📞 Fetching Google Contacts...")
        service = build('people', 'v1', credentials=creds)
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,phoneNumbers').execute()
        connections = results.get('connections', [])
        print(f"✅ Retrieved {len(connections)} contacts.")
        return connections

    except Exception as error:
        print(f"❌ An error occurred while accessing contacts: {error}")
        if 'invalid_grant' in str(error):
            print("⚠️ Token is invalid. Please re-authenticate.")
            if os.path.exists('token.json'):
                os.remove('token.json')
        return []

def get_contact_number(name_to_search):
    try:
        creds = None
        
        # Try to load existing token
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/contacts.readonly'])
            
            # Check if token is expired and refresh if needed
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
                # Save the refreshed token
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
        
        # If no valid credentials, trigger OAuth flow
        if not creds or not creds.valid:
            print("🔑 No valid credentials found. Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_133871116699-cn0a6i1lja1n9gkos0f3kr6sia0jej55.apps.googleusercontent.com.json',
                ['https://www.googleapis.com/auth/contacts.readonly'])
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                print("💾 Saving new credentials to token.json...")
                token.write(creds.to_json())
        
        service = build('people', 'v1', credentials=creds)
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,phoneNumbers').execute()
        connections = results.get('connections', [])

        for person in connections:
            names = person.get('names', [])
            phone_numbers = person.get('phoneNumbers', [])
            if names and phone_numbers:
                name = names[0].get('displayName').lower()
                if name_to_search.lower() in name:
                    number = phone_numbers[0].get('value').replace(" ", "").replace("-", "").replace("+", "")
                    print(f"✅ Found number for {name}: {number}")
                    return number
        print("❌ Contact not found.")
        return None
    except Exception as e:
        print(f"❌ Error fetching contact: {e}")
        # If it's an invalid_grant error, delete the corrupted token
        if 'invalid_grant' in str(e):
            print("⚠️ Token is invalid. Clearing token.json for re-authentication...")
            if os.path.exists('token.json'):
                os.remove('token.json')
            print("🔑 Please try again to trigger a fresh OAuth flow.")
        return None

if __name__ == '__main__':
    contacts = get_google_contacts()
    if not contacts:
        print('No contacts found.')
    else:
        print(f'Found {len(contacts)} contacts:')
        for contact in contacts:
            names = contact.get('names', [])
            if names:
                name = names[0].get('displayName')
                print(f'Name: {name}')
            else:
                print(f'Name: No name found')
            phone_numbers = contact.get('phoneNumbers', [])
            if phone_numbers:
                phone_number = phone_numbers[0].get('value')
                print(f'  Phone Number: {phone_number}')
            else:
                print(f'  Phone Number: No phone number found')
            print('---')
        print('Contacts fetched successfully!')