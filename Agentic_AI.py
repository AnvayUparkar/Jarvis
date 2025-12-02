# # scheduling_assistant.py - Agentic AI Scheduling Assistant

# import os
# import json
# import datetime
# from datetime import date, timedelta
# import functools
# import re

# import google.generativeai as google_ai
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# from google.auth.transport.requests import Request

# # --- Configuration ---
# # Your Google Cloud Console project's credentials.json file path
# GOOGLE_CREDENTIALS_FILE = 'credentials.json'
# # File to store user's Google API token
# GOOGLE_TOKEN_FILE = 'calendar_token.json'

# # Google Calendar API Scopes: Read/write access to calendar events
# SCOPES = ['[https://www.googleapis.com/auth/calendar.events](https://www.googleapis.com/auth/calendar.events)']

# # Configure Gemini API
# # IMPORTANT: Replace with your actual Gemini API Key or set it as an environment variable
# # It's recommended to use environment variables for production.
# # Example: export GEN_AI_API_KEY="YOUR_API_KEY_HERE"
# try:
#     GEN_AI_API_KEY = os.environ.get("GEN_AI_API_KEY", "") # Fallback to empty string if not set
#     if not GEN_AI_API_KEY:
#         # Fallback if environment variable is not set. For demonstration only, not recommended for prod.
#         print("WARNING: GEN_AI_API_KEY not found in environment variables. Using placeholder. Please set it for production.")
#         GEN_AI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" # <<< REPLACE THIS WITH YOUR ACTUAL API KEY

#     google_ai.configure(api_key=GEN_AI_API_KEY)
# except Exception as e:
#     print(f"❌ Error configuring Gemini API: {e}. Please check your GEN_AI_API_KEY.")
#     exit(1) # Exit if API is not configured

# # --- Utility Functions ---

# def print_message(message, level="info"):
#     """Prints messages with formatting based on level."""
#     if level == "info":
#         print(f"ℹ️ {message}")
#     elif level == "success":
#         print(f"✅ {message}")
#     elif level == "warning":
#         print(f"⚠️ {message}")
#     elif level == "error":
#         print(f"❌ {message}")
#     elif level == "agent":
#         print(f"🤖 Agent: {message}")
#     else:
#         print(message)

# def retry_on_exception(retries=3, delay=2, exceptions=(Exception,)):
#     """Decorator to retry a function on specified exceptions."""
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             for i in range(retries):
#                 try:
#                     return func(*args, **kwargs)
#                 except exceptions as e:
#                     print_message(f"Attempt {i + 1}/{retries} failed: {e}", "warning")
#                     if i < retries - 1:
#                         import time
#                         time.sleep(delay)
#             raise # Re-raise the last exception if all retries fail
#         return wrapper
#     return decorator

# # --- Google Calendar API Authentication ---

# @retry_on_exception(retries=2, delay=5, exceptions=(HttpError,))
# def get_google_calendar_credentials():
#     """
#     Handles Google OAuth2.0 authentication for Google Calendar API.
#     Attempts to load existing credentials or performs a new authorization flow if needed.
#     Ensures all required SCOPES are covered.
#     """
#     creds = None
#     if os.path.exists(GOOGLE_TOKEN_FILE):
#         print_message("Attempting to load Google Calendar credentials from calendar_token.json...")
#         try:
#             creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
#             print_message("Google Calendar credentials loaded.", "success")

#             # IMPORTANT: Check if all *currently required* SCOPES are covered by the loaded credentials
#             if not all(s in creds.scopes for s in SCOPES):
#                 print_message("Loaded credentials do not cover all required scopes. Forcing re-authentication.", "warning")
#                 creds = None
            
#         except Exception as e:
#             print_message(f"Error loading credentials from calendar_token.json: {e}. Re-authenticating.", "error")
#             creds = None

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             print_message("Google Calendar credentials expired, attempting to refresh...")
#             try:
#                 creds.refresh(Request())
#                 print_message("Google Calendar credentials refreshed successfully.", "success")
#                 if not all(s in creds.scopes for s in SCOPES):
#                     print_message("Refreshed credentials still do not cover all required scopes. Initiating new authentication flow.", "warning")
#                     creds = None
#             except Exception as e:
#                 print_message(f"Error refreshing credentials: {e}. Initiating new authentication flow.", "error")
#                 creds = None
        
#         if not creds:
#             print_message("Initiating new Google Calendar authentication flow...")
#             try:
#                 flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
#                 creds = flow.run_local_server(port=0)
#                 print_message("Google Calendar authentication completed.", "success")
#             except Exception as e:
#                 print_message(f"Error during Google Calendar authentication flow: {e}. Ensure '{GOOGLE_CREDENTIALS_FILE}' is valid and present and that you have enabled 'Google Calendar API' in Google Cloud Console.", "error")
#                 return None
            
#             try:
#                 with open(GOOGLE_TOKEN_FILE, 'w') as token:
#                     token.write(creds.to_json())
#                 print_message("Google Calendar credentials saved to calendar_token.json.", "success")
#             except Exception as e:
#                 print_message(f"Error saving credentials to calendar_token.json: {e}", "error")
                
#     return creds

# # --- Google Calendar API Interactions ---

# @retry_on_exception(retries=3, delay=2, exceptions=(HttpError,))
# def get_free_busy_slots(service, participant_emails, start_time: datetime, end_time: datetime):
#     """
#     Fetches free/busy information for a list of participants within a specified time range.
#     Times should be timezone-aware (UTC recommended).
#     """
#     print_message(f"Checking free/busy for {len(participant_emails)} participants from {start_time.isoformat()} to {end_time.isoformat()}...")
    
#     # The timezone needs to be consistent, UTC is a good default for API calls.
#     # Convert naive datetime objects to timezone-aware UTC if they aren't already.
#     if start_time.tzinfo is None:
#         start_time = start_time.replace(tzinfo=datetime.timezone.utc)
#     if end_time.tzinfo is None:
#         end_time = end_time.replace(tzinfo=datetime.timezone.utc)

#     items = [{"id": email} for email in participant_emails]
    
#     body = {
#         "timeMin": start_time.isoformat(),
#         "timeMax": end_time.isoformat(),
#         "items": items
#     }
    
#     try:
#         response = service.freebusy().query(body=body).execute()
#         print_message("Free/busy information fetched.", "success")
#         return response['calendars']
#     except HttpError as error:
#         print_message(f"Failed to fetch free/busy information: {error}", "error")
#         raise
#     except Exception as e:
#         print_message(f"An unexpected error occurred while fetching free/busy: {e}", "error")
#         raise

# @retry_on_exception(retries=3, delay=2, exceptions=(HttpError,))
# def create_calendar_event(service, event_details: dict):
#     """
#     Creates a new event on the user's Google Calendar.
#     `event_details` should be a dictionary following Google Calendar API's Event resource format.
#     """
#     print_message(f"Attempting to create event: '{event_details.get('summary', 'No Title')}'...")
#     try:
#         event = service.events().insert(calendarId='primary', body=event_details).execute()
#         print_message(f"Event created: {event.get('htmlLink')}", "success")
#         return event
#     except HttpError as error:
#         print_message(f"Failed to create event: {error}", "error")
#         raise
#     except Exception as e:
#         print_message(f"An unexpected error occurred while creating event: {e}", "error")
#         raise

# @retry_on_exception(retries=3, delay=2, exceptions=(HttpError,))
# def update_calendar_event(service, event_id: str, updated_details: dict):
#     """
#     Updates an existing event on the user's Google Calendar.
#     """
#     print_message(f"Attempting to update event {event_id}...")
#     try:
#         event = service.events().update(calendarId='primary', eventId=event_id, body=updated_details).execute()
#         print_message(f"Event updated: {event.get('htmlLink')}", "success")
#         return event
#     except HttpError as error:
#         print_message(f"Failed to update event: {error}", "error")
#         raise
#     except Exception as e:
#         print_message(f"An unexpected error occurred while updating event: {e}", "error")
#         raise

# # --- Agentic Logic with Gemini ---

# def get_gemini_model():
#     """Initializes and returns the Gemini Pro model."""
#     try:
#         model = google_ai.GenerativeModel("gemini-2.0-flash") # Using gemini-2.0-flash for faster responses
#         return model
#     except Exception as e:
#         print_message(f"Failed to load Gemini model: {e}", "error")
#         raise

# def generate_negotiation_message(gemini_model, meeting_title: str, current_slot: str, proposed_new_slot: str, conflict_reason: str):
#     """
#     Uses Gemini to generate a polite reschedule request message.
#     """
#     prompt = f"""
#     You are an AI scheduling assistant. Your goal is to draft a polite and professional message to reschedule a meeting.

#     Meeting Title: "{meeting_title}"
#     Current Proposed Slot: "{current_slot}"
#     Proposed New Slot: "{proposed_new_slot}"
#     Reason for conflict (internal to you, for context): "{conflict_reason}"

#     Please write a polite, concise, and professional email or message body that:
#     1. Acknowledges the current proposed slot.
#     2. Explains that there is a conflict.
#     3. Proposes the new slot.
#     4. Asks for confirmation or alternative if the new slot doesn't work.
    
#     Do NOT include salutations or closings (e.g., "Hi,", "Sincerely,"). Focus only on the core message.
#     """
#     print_message(f"Generating negotiation message for '{meeting_title}'...", "agent")
#     try:
#         response = gemini_model.generate_content(prompt)
#         return response.text.strip()
#     except Exception as e:
#         print_message(f"Failed to generate negotiation message with Gemini: {e}", "error")
#         return "Apologies, I encountered an issue while generating the reschedule message. Can we discuss alternative times for this meeting?"

# def parse_agent_response_for_slot(response_text: str):
#     """
#     (Simulated) Parses a human/agent's response to a negotiation, looking for acceptance or new proposals.
#     In a real system, this would be more sophisticated.
#     Returns (True, None) for acceptance, (False, new_datetime) for a new proposal, or (False, None) for rejection/no clear path.
#     """
#     response_text_lower = response_text.lower()
#     if "yes" in response_text_lower or "confirm" in response_text_lower or "works for me" in response_text_lower:
#         print_message("Agent accepted the proposal.", "agent")
#         return True, None
    
#     # Simple regex to find a new time. This is very basic for demonstration.
#     time_match = re.search(r'(\d{1,2}(:\d{2})?)\s*(am|pm)?\s*(on|for)?\s*(\w+)?\s*(\d{1,2})?\s*(th|nd|rd|st)?', response_text_lower)
#     if time_match:
#         # This parsing would need to be much more robust for real-world use.
#         print_message("Agent proposed a new time (simplified parsing).", "agent")
#         # For simplicity, we'll just indicate a new proposal without parsing the exact datetime
#         return False, "NEW_PROPOSED_TIME" 

#     print_message("Agent did not clearly accept or propose new time.", "agent")
#     return False, None

# def find_optimal_slot_and_negotiate(
#     calendar_service,
#     gemini_model,
#     meeting_title: str,
#     participants: list[str],
#     duration_minutes: int,
#     start_search_date: date,
#     end_search_date: date,
#     preferred_start_time_of_day: str = "09:00", # HH:MM string
#     preferred_end_time_of_day: str = "17:00" # HH:MM string
# ):
#     """
#     Orchestrates the process of finding optimal meeting slots and simulating negotiation.
#     """
#     print_message(f"Initiating scheduling for: '{meeting_title}' with {', '.join(participants)}", "agent")

#     # Define working hours for all participants (simplified to a fixed range for this example)
#     PREFERRED_START_HOUR = int(preferred_start_time_of_day.split(":")[0])
#     PREFERRED_END_HOUR = int(preferred_end_time_of_day.split(":")[0])

#     # Add yourself (the primary calendar user) to participants if not already included
#     # This requires getting the primary calendar's email, which is not directly available
#     # from 'service' object without an extra API call or config.
#     # For now, assume the user's primary calendar is handled by the API key's owner.
    
#     all_participants = list(set(participants + ['primary'])) # 'primary' refers to the authenticated user's calendar

#     current_date = start_search_date
#     while current_date <= end_search_date:
#         print_message(f"Searching for slots on {current_date.strftime('%Y-%m-%d')}...", "agent")
        
#         # Define search window for the current day
#         day_start = datetime.combine(current_date, datetime.time(PREFERRED_START_HOUR, 0, 0))
#         day_end = datetime.combine(current_date, datetime.time(PREFERRED_END_HOUR, 0, 0))

#         # Ensure times are timezone-aware (UTC is a good default for API calls)
#         day_start = day_start.replace(tzinfo=datetime.timezone.utc)
#         day_end = day_end.replace(tzinfo=datetime.timezone.utc)

#         free_busy_info = {}
#         try:
#             # Fetch free/busy for the current day for all participants
#             free_busy_info = get_free_busy_slots(calendar_service, all_participants, day_start, day_end)
#         except Exception as e:
#             print_message(f"Could not get free/busy for {current_date}: {e}", "warning")
#             current_date += timedelta(days=1)
#             continue

#         # Convert busy times to a list of (start, end) tuples for easier processing
#         busy_slots_per_person = {}
#         for email, calendar_data in free_busy_info.items():
#             busy_slots_per_person[email] = []
#             for busy_period in calendar_data.get('busy', []):
#                 start = datetime.fromisoformat(busy_period['start']).astimezone(datetime.timezone.utc)
#                 end = datetime.fromisoformat(busy_period['end']).astimezone(datetime.timezone.utc)
#                 busy_slots_per_person[email].append((start, end))
        
#         # Find common free slots
#         potential_slots = []
#         slot_start_time = day_start
#         while slot_start_time + timedelta(minutes=duration_minutes) <= day_end:
#             slot_end_time = slot_start_time + timedelta(minutes=duration_minutes)
#             is_free_for_all = True
            
#             for email in all_participants:
#                 for busy_start, busy_end in busy_slots_per_person.get(email, []):
#                     # Check for overlap: (slot_start < busy_end) and (slot_end > busy_start)
#                     if slot_start_time < busy_end and slot_end_time > busy_start:
#                         is_free_for_all = False
#                         break
#                 if not is_free_for_all:
#                     break
            
#             if is_free_for_all:
#                 potential_slots.append((slot_start_time, slot_end_time))
#                 # Move to the end of this found slot to avoid tiny overlaps
#                 slot_start_time = slot_end_time 
#             else:
#                 # Move forward by a smaller increment if current slot is busy
#                 slot_start_time += timedelta(minutes=15) # Check every 15 minutes
        
#         if potential_slots:
#             # For simplicity, take the first available slot
#             chosen_start, chosen_end = potential_slots[0]
#             print_message(f"Found a potential slot: {chosen_start.isoformat()} - {chosen_end.isoformat()}", "success")
            
#             # Simulate confirmation with user
#             print_message(f"Should I propose this slot: {chosen_start.isoformat()} to {chosen_end.isoformat()}?", "agent")
#             user_confirm = input("Confirm? (yes/no/propose alternative): ").lower().strip()

#             if user_confirm == "yes":
#                 event_body = {
#                     'summary': meeting_title,
#                     'start': {
#                         'dateTime': chosen_start.isoformat(),
#                         'timeZone': 'UTC', # Store in UTC
#                     },
#                     'end': {
#                         'dateTime': chosen_end.isoformat(),
#                         'timeZone': 'UTC', # Store in UTC
#                     },
#                     'attendees': [{'email': email} for email in participants],
#                     'reminders': {
#                         'useDefault': True,
#                     },
#                 }
#                 created_event = create_calendar_event(calendar_service, event_body)
#                 if created_event:
#                     print_message(f"Meeting '{meeting_title}' confirmed for {chosen_start.isoformat()}!", "success")
#                     return created_event
#                 else:
#                     print_message("Failed to create event after confirmation.", "error")
#                     return None
#             elif user_confirm == "propose alternative":
#                 # This would ideally prompt for *which* alternative the user wants
#                 print_message("Okay, let's look for other options or you can provide a specific one.", "info")
#                 # For this demo, we will simply continue search or exit this iteration
#             else:
#                 print_message("Proposal cancelled. Searching next day.", "info")

#         current_date += timedelta(days=1)

#     print_message("No optimal slots found within the search range.", "warning")
#     return None

# # --- Main Application Logic ---

# def main():
#     print("\n--- Agentic AI Scheduling Assistant ---")
#     print_message("Please ensure you have enabled 'Google Calendar API' in Google Cloud Console and downloaded 'credentials.json'.")
#     print_message("Also, ensure your Gemini API key is set as an environment variable (GEN_AI_API_KEY) or directly in the script.")

#     calendar_service = None
#     try:
#         creds = get_google_calendar_credentials()
#         if creds:
#             calendar_service = build('calendar', 'v3', credentials=creds)
#             print_message("Google Calendar service initialized.", "success")
#         else:
#             print_message("Could not get Google Calendar credentials. Exiting.", "error")
#             return
#     except Exception as e:
#         print_message(f"Initialization error for Google Calendar: {e}", "error")
#         return

#     gemini_model = None
#     try:
#         gemini_model = get_gemini_model()
#         print_message("Gemini model initialized.", "success")
#     except Exception as e:
#         print_message(f"Initialization error for Gemini: {e}", "error")
#         return

#     while True:
#         print("\n--- Main Menu ---")
#         print("1. Schedule a new meeting")
#         print("2. Exit")
#         choice = input("Enter your choice: ").strip()

#         if choice == '1':
#             meeting_title = input("Enter meeting title: ").strip()
#             participant_emails_str = input("Enter participant emails (comma-separated): ").strip()
#             participant_emails = [email.strip() for email in participant_emails_str.split(',') if email.strip()]

#             if not participant_emails:
#                 print_message("No participants entered. Returning to menu.", "warning")
#                 continue

#             try:
#                 duration_minutes = int(input("Enter meeting duration in minutes (e.g., 60): ").strip())
#             except ValueError:
#                 print_message("Invalid duration. Must be a number.", "error")
#                 continue

#             search_start_date_str = input("Enter search start date (YYYY-MM-DD, e.g., 2025-07-01): ").strip()
#             search_end_date_str = input("Enter search end date (YYYY-MM-DD, e.g., 2025-07-30): ").strip()

#             try:
#                 search_start_date = datetime.strptime(search_start_date_str, '%Y-%m-%d').date()
#                 search_end_date = datetime.strptime(search_end_date_str, '%Y-%m-%d').date()
#             except ValueError:
#                 print_message("Invalid date format. Please use YYYY-MM-DD.", "error")
#                 continue
            
#             preferred_start_time = input("Enter preferred start time of day (HH:MM, e.g., 09:00, leave blank for default 09:00): ").strip() or "09:00"
#             preferred_end_time = input("Enter preferred end time of day (HH:MM, e.g., 17:00, leave blank for default 17:00): ").strip() or "17:00"


#             find_optimal_slot_and_negotiate(
#                 calendar_service,
#                 gemini_model,
#                 meeting_title,
#                 participant_emails,
#                 duration_minutes,
#                 search_start_date,
#                 search_end_date,
#                 preferred_start_time,
#                 preferred_end_time
#             )

#         elif choice == '2':
#             print_message("Exiting Agentic AI Scheduling Assistant. Goodbye!", "info")
#             break
#         else:
#             print_message("Invalid choice. Please try again.", "warning")

# if __name__ == "__main__":
#     main()
