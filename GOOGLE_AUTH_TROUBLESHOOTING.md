# Google Authentication Troubleshooting Guide

## Error: `invalid_grant: Bad Request`

This error occurs when your Google OAuth token is invalid, expired, or has been revoked. The updated code now handles this automatically.

### What the Fix Does

The updated `get_google_contacts.py` now includes:

1. **Token Validation**: Checks if the token exists and is valid before use
2. **Automatic Token Refresh**: Attempts to refresh expired tokens automatically
3. **Invalid Token Detection**: Detects `invalid_grant` errors and clears the corrupted token
4. **Automatic Re-authentication**: Triggers OAuth flow when token is invalid
5. **Error Logging**: Provides clear messages about what's happening

### Quick Fix Steps

#### Option 1: Automatic (Recommended)
Just try to use the contact/WhatsApp feature again. The code will now:
- Detect the invalid token
- Delete the corrupted `token.json` file
- Trigger a fresh OAuth authentication flow
- Save the new valid token

#### Option 2: Manual Reset
1. Delete the `token.json` file from your JARVIS folder
2. Try the WhatsApp contact feature again
3. A browser window will open asking you to authenticate with Google
4. Grant permissions when prompted
5. A new valid `token.json` will be created

### When to Use Each Option

**Use Automatic (Option 1) if:**
- This is your first time seeing this error
- You want the system to handle re-authentication automatically

**Use Manual (Option 2) if:**
- You want full control over the authentication process
- You need to revoke permissions first from Google Account settings
- The automatic method doesn't work

### Why This Error Happens

1. **Token Expiration**: Google tokens expire after some time
2. **Revoked Permissions**: You revoked permissions in Google Account settings
3. **Multiple OAuth Apps**: Using credentials from different Google projects
4. **Password Change**: Changing your Google password invalidates tokens
5. **Account Security Issues**: Google revoked the token for security reasons

### Preventing This Error

1. **Keep Credentials Updated**: Re-authenticate every 3-6 months
2. **Use One Credentials File**: Only use one `client_secret_*.json` file
3. **Don't Share Tokens**: Keep your `token.json` file private
4. **Monitor Permissions**: Regularly check Google Account security settings

### Still Having Issues?

If the error persists after trying the above:

1. **Clear All Tokens and Credentials**:
   ```
   Delete: token.json
   Keep: Only ONE client_secret_*.json file
   ```

2. **Revoke Permissions**:
   - Go to https://myaccount.google.com/permissions
   - Find "JARVIS" or "Jarvis"
   - Click "Remove Access"
   - Try again

3. **Check Credentials File**:
   - Make sure the path in `get_google_contacts.py` is correct:
   ```python
   r'C:\Users\Anvay Uparkar\Python\JARVIS\jarvis_ai\client_secret_133871116699-teh8o91k85noal3nid1tkr1o6j3kbfce.apps.googleusercontent.com.json'
   ```

4. **Verify Google API Enabled**:
   - Go to https://console.cloud.google.com
   - Ensure "People API" is enabled for your project
   - Check your project ID matches your credentials file

### Contact Features Affected

This fix improves:
- ✅ "Send WhatsApp message to [contact]"
- ✅ "Call [contact] on WhatsApp"
- ✅ "Video call [contact] on WhatsApp"
- ✅ Any feature that fetches contacts from Google Contacts

### Code Changes

**Before**: Only caught exceptions without recovery
```python
except Exception as e:
    print(f"❌ Error fetching contact: {e}")
    return None
```

**After**: Detects invalid tokens and triggers re-authentication
```python
except Exception as e:
    print(f"❌ Error fetching contact: {e}")
    if 'invalid_grant' in str(e):
        print("⚠️ Token is invalid. Clearing token.json for re-authentication...")
        if os.path.exists('token.json'):
            os.remove('token.json')
        print("🔑 Please try again to trigger a fresh OAuth flow.")
    return None
```

### Testing Your Fix

After clearing the token, test with:
1. Start JARVIS
2. Say: "Call [contact name] on WhatsApp"
3. You should see browser authentication window
4. Grant permissions
5. JARVIS will now find and call the contact

Good luck! 🚀
