# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity (teacher sign-in required)                  |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity (teacher sign-in required)             |
| POST   | `/auth/login`                                                      | Sign in as a teacher                                                |
| GET    | `/auth/session`                                                    | Get the current teacher session                                     |
| POST   | `/auth/logout`                                                     | Sign out                                                            |

## Teacher Access

Teacher accounts are configured in a local `teachers.json` file. Start by copying `teachers.example.json` to `teachers.json`; the local file is git-ignored and should not be committed. The JSON stores a per-teacher salt and a PBKDF2-SHA256 password hash, not a plaintext password.

Generate a teacher record with Python, then add the printed object to the `teachers` array in `teachers.json`:

```sh
python -c 'import getpass, hashlib, json, secrets; username=input("Username: "); password=getpass.getpass("Password: "); salt=secrets.token_bytes(16); print(json.dumps({"username": username, "salt": salt.hex(), "password_hash": hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000).hex()}, indent=2))'
```

Teacher sessions use an HTTP-only, SameSite=Strict cookie and expire after eight hours. Set `SESSION_COOKIE_SECURE=1` when serving the app over HTTPS. Sessions are held in memory and are cleared when the server restarts.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
