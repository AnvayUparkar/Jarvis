#!/usr/bin/env python3
"""
Quick OAuth Flow Trigger for Google Contacts
This script will delete any existing token.json and start a fresh OAuth flow
"""

import os
from get_google_contacts import get_google_contacts

def main():
    print("=" * 60)
    print("🔐 Google OAuth Authentication Flow")
    print("=" * 60)
    
    # Delete existing token if present
    if os.path.exists('token.json'):
        print("\n🗑️  Removing old token.json...")
        os.remove('token.json')
        print("✅ Old token deleted")
    
    print("\n🔄 Starting fresh OAuth flow...")
    print("⏳ A browser window will open for you to authenticate")
    print("📱 Please grant permissions when prompted\n")
    
    # This will trigger the OAuth flow
    contacts = get_google_contacts()
    
    print("\n" + "=" * 60)
    if contacts:
        print(f"✅ SUCCESS! Retrieved {len(contacts)} contacts")
        print("🎉 Your Google OAuth token has been saved to token.json")
    else:
        print("⚠️  No contacts found or authentication was cancelled")
    print("=" * 60)

if __name__ == '__main__':
    main()
