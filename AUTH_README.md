# Authentication System Documentation

This document explains the secure authentication system connected to `login.html`.

## Prerequisites

The authentication system uses `bcrypt` for secure password hashing. You must install it:

```bash
pip install bcrypt
```

## Backend Structure

### 1. database.py
- **Purpose**: Manages the SQLite database connection (`db.sqlite` created in project root).
- **Schema**: Creates a `users` table if it doesn't exist.
  - `id`: Auto-incrementing primary key.
  - `username`: Unique username.
  - `email`: Unique email address.
  - `password_hash`: Bcrypt hashed password (never plain text).
  - `created_at`: Timestamp.

### 2. auth.py
- **Purpose**: Contains the authentication logic and exposes functions to the frontend via Eel.
- **Functions**:
  - `user_register(username, email, password)`:
    - Checks for duplicate username/email.
    - Hashes password using `bcrypt`.
    - Inserts into `users` table.
    - Returns JSON: `{"success": true/false, "message": "..."}`.
  - `user_login(username, password)`:
    - Fetches user by username.
    - Verifies password hash using `bcrypt.checkpw`.
    - Returns JSON success/failure.

### 3. main.py
- **Integration**:
  - Imports `database` and `auth` modules.
  - Calls `database.init_db()` on startup (in `start()` function) to ensure the table exists.
  - Changed start page from `home.html` to `login.html`.

## Frontend Integration (login.html)

The existing `login.html` connects to the backend using `eel`:

1.  **Registration**:
    ```javascript
    eel.user_register(username, email, password)(function(response){
        if(response.success) {
            // Handle success
        } else {
            alert(response.message);
        }
    });
    ```

2.  **Login**:
    ```javascript
    eel.user_login(username, password)(function(response){
        if(response.success) {
            window.location.href = "home.html"; // Redirects on success
        } else {
            alert(response.message);
        }
    });
    ```

## Security Features
- **SQL Injection Prevention**: Uses parameterized queries (`?` placeholders) in all SQL operations.
- **Secure Hashing**: Uses `bcrypt` with salt (handled automatically) for passwords.
- **Input Validation**: usage of try-except blocks and explicit checks for empty fields.
