import os
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException
from fastapi.requests import Request
from passlib.context import CryptContext
from starlette import status

from database.models import User
from utils.db import get_session


# Utility functions (should be imported from a shared module if possible)
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with get_session() as session:
        user = session.get(User, user_id)
        return user


def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


def hash_password(password: str) -> str:
    return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)


def send_verification_email(to_email, token):
    msg = EmailMessage()
    msg["Subject"] = "Verify your email for smtpy"
    msg["From"] = "no-reply@smtpy.local"
    msg["To"] = to_email
    msg.set_content(f"Click to verify: http://localhost/verify-email?token={token}")
    with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"), int(os.environ.get("SMTP_PORT", 25))) as s:
        s.send_message(msg)


def send_invitation_email(to_email, token):
    msg = EmailMessage()
    msg["Subject"] = "You're invited to smtpy"
    msg["From"] = "no-reply@smtpy.local"
    msg["To"] = to_email
    msg.set_content(f"You've been invited! Complete your registration: http://localhost/register?invite={token}")
    with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"), int(os.environ.get("SMTP_PORT", 25))) as s:
        s.send_message(msg)
