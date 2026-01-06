# Google Authentication Setup for JARVIS

## Overview
This document explains how Google OAuth authentication has been integrated into your JARVIS application's home.html page.

## Features Implemented

### 1. Google Sign-In Button
- Added Google OAuth library to home.html
- Integrated Google Sign-In button on the login modal
- User can authenticate directly with their Google account

### 2. Backend Authentication Functions
Added three new Eel-exposed functions in main.py:

#### `authenticate_with_google_token(google_token)`
- **Purpose**: Verifies Google JWT token received from frontend
- **Parameters**: Google token from Google Sign-In
- **Returns**: Success/failure status with user info
- **How it works**:
  1. Validates the JWT token using Google's public certificates
  2. Extracts user email and name
  3. Stores authenticated user info globally
  4. Returns success response with user details

#### `get_authenticated_user_info()`
- **Purpose**: Retrieves current authenticated user info
- **Parameters**: None
- **Returns**: Dictionary with authentication status, name, and email
- **Used for**: Checking login status, displaying user name in navbar

#### `logout_user()`
- **Purpose**: Logs out the current user
- **Parameters**: None
- **Returns**: Success/failure status
- **How it works**: Clears all stored user authentication data

### 3. Frontend Callback Function
**`handleGoogleSignIn(response)` in home.html**
- Receives response from Google Sign-In
- Extracts JWT token
- Sends token to backend for verification
- Displays success/error messages
- Updates UI with user info

## File Changes

### home.html
**Added:**
- Google OAuth script library
- Google Sign-In button with configuration
- `handleGoogleSignIn()` callback function
- Integration with existing login modal

**Locations:**
- Line 12: Added Google OAuth script tag
- Lines 1105-1120: Added Google Sign-In button and styling
- After line 1378: Added handleGoogleSignIn() callback function

### main.py
**Added:**
- New imports for Google token verification:
  - `from google.oauth2 import id_token`
  - `import certifi`
  - `from google.auth.transport.requests import Request as GoogleRequest`
  
- Global variable `authenticated_user` dictionary to store user state

- Three new @eel.expose functions:
  1. `authenticate_with_google_token()`
  2. `get_authenticated_user_info()`
  3. `logout_user()`

**Location:** After line 967 (after continous_listen_loop function)

## Configuration

### Google OAuth Client ID
The following Client ID is used (already configured in home.html):
```
133871116699-cn0a6i1lja1n9gkos0f3kr6sia0jej55.apps.googleusercontent.com
```

This must match the Google Cloud project credentials configured in Google Cloud Console.

## How It Works

### Login Flow
1. User clicks Google Sign-In button
2. Google OAuth dialog opens
3. User authenticates with Google account
4. Google returns JWT token to frontend
5. Frontend sends token to `authenticate_with_google_token()`
6. Backend validates token and stores user info
7. Frontend receives success response
8. UI updates to show user is logged in
9. User can proceed to assistant

### Authentication Check
- When user navigates to assistant, `get_authenticated_user_info()` is called
- If not authenticated, user is redirected to login page
- If authenticated, user info is displayed in navbar

### Logout
- User clicks logout button
- `logout_user()` is called on backend
- All user data is cleared
- User is redirected to login page

## Usage

### For Users
1. Go to home page
2. Click "Login" button
3. Click "Sign in with Google" button
4. Authenticate with your Google account
5. You're now logged in and can access all features

### For Developers
To verify user authentication status in Python:
```python
# Check if user is authenticated
if authenticated_user["authenticated"]:
    user_email = authenticated_user["email"]
    user_name = authenticated_user["name"]
    # Use these in your application
```

To require authentication in a function:
```python
@eel.expose
def some_feature():
    if not authenticated_user["authenticated"]:
        return {"success": False, "message": "Please login first"}
    
    # Feature code here
    return {"success": True}
```

## Security Considerations

1. **Token Validation**: Google tokens are validated server-side
2. **Secure Storage**: User info stored in memory, cleared on logout
3. **CORS**: Google Sign-In handles CORS configuration
4. **HTTPS**: For production, ensure HTTPS is used for token transmission

## Troubleshooting

### "Backend connection not available"
- Ensure main.py is running
- Check that Eel server is active on http://127.0.0.1:8000

### Google Sign-In button not appearing
- Check that Google OAuth script is loaded: `<script src="https://accounts.google.com/gsi/client" async defer></script>`
- Verify Client ID is correct in g_id_onload element

### Token validation fails
- Verify Client ID matches your Google Cloud project
- Check that Google OAuth library is imported in main.py
- Ensure certifi package is installed

### User info not persisting
- User authentication is session-based (in-memory)
- On server restart, users will need to re-authenticate
- For persistent login, implement database storage

## Future Enhancements

1. **Database Integration**: Store user credentials and sessions
2. **Refresh Token**: Handle Google token refresh
3. **User Roles**: Add role-based access control
4. **Multi-Account**: Support multiple Google accounts
5. **Profile Info**: Store and display user profile picture
6. **OAuth Scopes**: Request additional Google service scopes as needed

## Related Files
- `main.py` - Backend authentication logic
- `www/home.html` - Frontend UI and Google Sign-In button
- `run.py` - Application launcher (ensures main.py runs)

## Dependencies
- `google-auth` - For Google token validation
- `google-auth-httplib2` - For HTTPS requests
- `certifi` - For SSL certificate validation
- `eel` - For frontend-backend communication

All dependencies should be in your requirements.txt
