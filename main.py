from mysql.connector import IntegrityError, errorcode
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pwdlib import PasswordHash

from database import get_connection, initialise_database


# Project folder
BASE_DIR = Path(__file__).resolve().parent

# Create the database table if it does not already exist.
initialise_database()

# Password hashing tool
password_hasher = PasswordHash.recommended()

# FastAPI application
app = FastAPI(
    title="Cybersecurity Knowledge Retrieval and AI Learning System"
)


# Homepage
@app.get("/", response_class=FileResponse)
def home():
    return FileResponse(BASE_DIR / "home.html")


# Question-submission page
@app.get("/learn", response_class=FileResponse)
def learning_page():
    return FileResponse(BASE_DIR / "index.html")


# Question input validation
class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


# Receive a question and return a test response.
@app.post("/ask")
def ask_question(data: QuestionRequest):
    return {
        "question": data.question,
        "answer": "Your question has been received."
    }


# Registration input validation
class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    password: str = Field(
        min_length=8,
        max_length=128
    )


# Register a new student account.
@app.post("/register", status_code=201)
def register_user(data: RegisterRequest):
    username = data.username.lower()
    password_hash = password_hasher.hash(data.password)

    connection = get_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)

    try:
        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            """,
            (username, password_hash)
        )

        connection.commit()

        return {
            "message": "Account created successfully.",
            "user_id": cursor.lastrowid,
            "username": username,
            "role": "student"
        }

    except IntegrityError as error:
        connection.rollback()

        if error.errno == errorcode.ER_DUP_ENTRY:
            raise HTTPException(
                status_code=409,
                detail="This username is already taken."
            ) from error

        raise

    finally:
        cursor.close()
        connection.close()
@app.get("/signup", response_class=FileResponse)
def registration_page():
    return FileResponse(BASE_DIR / "register.html")
@app.get("/login", response_class=FileResponse)
def login_page():
    return FileResponse(BASE_DIR / "login.html")
import secrets

from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware


# Keep the login state in a signed browser cookie.
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    session_cookie="cybersecurity_session",
    max_age=3600,
    same_site="strict",
    https_only=False
)


# Used to make password checking consistent for unknown users.
DUMMY_PASSWORD_HASH = password_hasher.hash(
    secrets.token_urlsafe(32)
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=1, max_length=128)


@app.post("/api/login")
def login_user(data: LoginRequest, request: Request):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)

    try:
        cursor.execute(
            """
            SELECT id, username, password_hash
            FROM users
            WHERE username = %s
            """,
            (data.username.lower(),)
        )
        user = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    stored_hash = (
        user["password_hash"]
        if user is not None
        else DUMMY_PASSWORD_HASH
    )

    password_matches = password_hasher.verify(
        data.password,
        stored_hash
    )

    if user is None or not password_matches:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password."
        )

    request.session.clear()
    request.session["user_id"] = user["id"]

    return {
        "message": "Logged in successfully.",
        "username": user["username"]
    }


@app.get("/api/me")
def current_user(request: Request):
    user_id = request.session.get("user_id")

    if user_id is None:
        return {"authenticated": False}

    connection = get_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)

    try:
        cursor.execute(
            """
            SELECT id, username, role
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if user is None:
        request.session.clear()
        return {"authenticated": False}

    return {
        "authenticated": True,
        "username": user["username"],
        "role": user["role"]
    }


@app.post("/api/logout")
def logout_user(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully."}

from seed_knowledge import seed_knowledge
from knowledge import router as knowledge_router

seed_knowledge()
app.include_router(knowledge_router)

import logging
import time


activity_logger = logging.getLogger("uvicorn.error")


@app.middleware("http")
async def show_operation_feedback(request: Request, call_next):
    started = time.perf_counter()

    operation_names = {
        ("GET", "/"): "Open homepage",
        ("GET", "/signup"): "Open registration page",
        ("POST", "/register"): "Register account",
        ("GET", "/login"): "Open login page",
        ("POST", "/api/login"): "Log in",
        ("POST", "/api/logout"): "Log out",
        ("GET", "/api/me"): "Check login status",
        ("GET", "/learn"): "Open question page",
        ("POST", "/ask"): "Submit question",
        ("GET", "/topics"): "Open knowledge topic directory",
        ("GET", "/api/topics"): "Load topic catalogue",
        ("GET", "/api/articles"): "Search knowledge library",
        ("GET", "/topics/networking"): "Open networking topic",
        ("GET", "/api/topics/networking"): "Search networking resources"
    }

    operation = operation_names.get(
        (request.method, request.url.path),
        f"{request.method} {request.url.path}"
    )

    try:
        response = await call_next(request)

    except Exception:
        activity_logger.error(
            "[ACTION] %s | ERROR: server exception",
            operation
        )
        raise

    result_names = {
        200: "SUCCESS",
        201: "CREATED",
        401: "LOGIN REQUIRED OR INCORRECT CREDENTIALS",
        403: "ACCESS DENIED",
        404: "NOT FOUND",
        409: "ALREADY EXISTS",
        422: "INVALID INPUT"
    }

    result = result_names.get(
        response.status_code,
        "SUCCESS" if response.status_code < 400 else "FAILED"
    )

    elapsed = round((time.perf_counter() - started) * 1000)

    activity_logger.info(
        "[ACTION] %s | %s | HTTP %s | %s ms",
        operation,
        result,
        response.status_code,
        elapsed
    )

    return response

   