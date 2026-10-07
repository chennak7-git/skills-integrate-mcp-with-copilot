"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from pydantic import BaseModel

current_dir = Path(__file__).parent
teachers_file = Path(os.environ.get("TEACHERS_FILE", current_dir / "teachers.json"))
session_cookie = "teacher_session"
session_ttl_seconds = 8 * 60 * 60
session_cookie_secure = os.environ.get("SESSION_COOKIE_SECURE", "").lower() in {
    "1",
    "true",
    "yes",
}
password_iterations = 310_000
teacher_sessions: dict[str, tuple[str, float]] = {}

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


class TeacherCredentials(BaseModel):
    username: str
    password: str


def authenticate_teacher(username: str, password: str) -> bool:
    try:
        teacher_data = json.loads(teachers_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=503, detail="Teacher sign-in is unavailable") from error

    teachers = teacher_data.get("teachers") if isinstance(teacher_data, dict) else None
    if not isinstance(teachers, list):
        raise HTTPException(status_code=503, detail="Teacher sign-in is unavailable")

    for teacher in teachers:
        if not isinstance(teacher, dict) or teacher.get("username") != username:
            continue
        try:
            salt = bytes.fromhex(teacher["salt"])
            expected_hash = teacher["password_hash"]
            if not isinstance(expected_hash, str):
                continue
            actual_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, password_iterations
            ).hex()
        except (KeyError, TypeError, ValueError):
            continue
        if hmac.compare_digest(actual_hash, expected_hash):
            return True
    return False


def require_teacher(request: Request) -> str:
    token = request.cookies.get(session_cookie)
    session = teacher_sessions.get(token) if token else None
    if session is None:
        raise HTTPException(status_code=401, detail="Teacher sign-in required")

    username, expires_at = session
    if expires_at <= time.time():
        teacher_sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Teacher session expired")
    return username


@app.post("/auth/login")
def teacher_login(credentials: TeacherCredentials, response: Response):
    if not authenticate_teacher(credentials.username, credentials.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    teacher_sessions[token] = (credentials.username, time.time() + session_ttl_seconds)
    response.set_cookie(
        session_cookie,
        token,
        max_age=session_ttl_seconds,
        httponly=True,
        secure=session_cookie_secure,
        samesite="strict",
        path="/",
    )
    return {"message": "Signed in", "username": credentials.username}


@app.get("/auth/session")
def get_teacher_session(request: Request):
    try:
        return {"authenticated": True, "username": require_teacher(request)}
    except HTTPException as error:
        if error.status_code == 401:
            return {"authenticated": False}
        raise


@app.post("/auth/logout")
def teacher_logout(request: Request, response: Response):
    token = request.cookies.get(session_cookie)
    if token:
        teacher_sessions.pop(token, None)
    response.delete_cookie(
        session_cookie,
        httponly=True,
        secure=session_cookie_secure,
        samesite="strict",
        path="/",
    )
    return {"message": "Signed out"}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup", dependencies=[Depends(require_teacher)])
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister", dependencies=[Depends(require_teacher)])
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
