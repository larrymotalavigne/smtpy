import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from fastapi import APIRouter, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.context import CryptContext

from database.models import User, Invitation
from utils.db import get_session
from utils.user import get_current_user, send_invitation_email, hash_password, send_verification_email

router = APIRouter(prefix="/user")


@router.get("/invite", response_class=HTMLResponse)
def invite_user_get(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return request.app.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": None})


@router.post("/invite", response_class=HTMLResponse)
def invite_user_post(request: Request, background_tasks: BackgroundTasks, email: str = Form(...)):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    with get_session() as session:
        if session.query(User).filter_by(email=email).first():
            return request.app.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": "Email already registered."})
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=24)
        invitation = Invitation(email=email, token=token, expires_at=expires, invited_by=user.id)
        session.add(invitation)
        try:
            session.commit()
        except Exception:
            return request.app.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": "Invitation already sent."})
        background_tasks.add_task(send_invitation_email, email, token)
    return request.app.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": "Invitation sent."})


@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request, invite: str = None):
    return request.app.TEMPLATES.TemplateResponse("register.html", {"request": request, "error": None, "invite": invite})


@router.post("/register", response_class=HTMLResponse)
def register_post(request: Request, background_tasks: BackgroundTasks, username: str = Form(...), email: str = Form(""),
                  password: str = Form(...), invite: str = Form("")):
    email_val = email if email else None
    invite_val = invite if invite else None
    with get_session() as session:
        if invite_val:
            invitation = session.query(Invitation).filter_by(token=invite_val).first()
            if not invitation or invitation.expires_at < datetime.utcnow():
                return request.app.TEMPLATES.TemplateResponse("register.html",
                                                              {"request": request, "error": "Invalid or expired invitation.",
                                                               "invite": invite_val})
            email_val = invitation.email
        if session.query(User).filter_by(username=username).first():
            return request.app.TEMPLATES.TemplateResponse("register.html",
                                                          {"request": request, "error": "Username already exists.", "invite": invite_val})
        if email_val and session.query(User).filter_by(email=email_val).first():
            return request.app.TEMPLATES.TemplateResponse("register.html",
                                                          {"request": request, "error": "Email already registered.", "invite": invite_val})
        token = secrets.token_urlsafe(32)
        user = User(username=username, email=email_val, hashed_password=hash_password(password), is_active=not invite_val,
                    email_verified=bool(invite_val), verification_token=None if invite_val else token)
        session.add(user)
        if invite_val:
            session.delete(invitation)
        session.commit()
        if email_val and not invite_val:
            background_tasks.add_task(send_verification_email, email_val, token)
    if invite_val:
        return request.app.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Account created. You can now log in."})
    return request.app.TEMPLATES.TemplateResponse("register.html",
                                                  {"request": request, "error": "Check your email to verify your account.", "invite": None})


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email(request: Request, token: str):
    with get_session() as session:
        user = session.query(User).filter_by(verification_token=token).first()
        if not user:
            return request.app.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Invalid or expired token."})
        user.is_active = True
        user.email_verified = True
        user.verification_token = None
        session.commit()
    return request.app.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Email verified. You can now log in."})


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return request.app.TEMPLATES.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with get_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if not user or not CryptContext(schemes=["bcrypt"]).verify(password, user.hashed_password):
            return request.app.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
        request.session["user_id"] = user.id
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/users", response_class=HTMLResponse)
def user_management(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    with get_session() as session:
        users = session.query(User).all()
    return request.app.TEMPLATES.TemplateResponse("users.html", {"request": request, "users": users, "user": user})


@router.post("/users/edit")
def edit_user(request: Request, user_id: int = Form(...), email: str = Form(None), role: str = Form(...)):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    with get_session() as session:
        u = session.get(User, user_id)
        if u:
            u.email = email
            u.role = role
            session.commit()
    return RedirectResponse(url="/users", status_code=303)


@router.post("/users/delete")
def delete_user(request: Request, user_id: int = Form(...)):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    with get_session() as session:
        u = session.get(User, user_id)
        if u:
            session.delete(u)
            session.commit()
    return RedirectResponse(url="/users", status_code=303)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_get(request: Request):
    return request.app.TEMPLATES.TemplateResponse("forgot_password.html", {"request": request, "error": None})


@router.post("/forgot-password", response_class=HTMLResponse)
def forgot_password_post(request: Request, background_tasks: BackgroundTasks, email: str = Form(...)):
    with get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return request.app.TEMPLATES.TemplateResponse("forgot_password.html",
                                                          {"request": request, "error": "If the email exists, a reset link will be sent."})
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=1)
        user.password_reset_token = token
        user.password_reset_expiry = expiry
        session.commit()

        def send_reset_email(to_email, token):
            msg = EmailMessage()
            msg["Subject"] = "Password Reset for smtpy"
            msg["From"] = "no-reply@smtpy.local"
            msg["To"] = to_email
            msg.set_content(f"Reset your password: http://localhost/reset-password?token={token}")
            with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"), int(os.environ.get("SMTP_PORT", 25))) as s:
                s.send_message(msg)

        background_tasks.add_task(send_reset_email, email, token)
    return request.app.TEMPLATES.TemplateResponse("forgot_password.html",
                                                  {"request": request, "error": "If the email exists, a reset link will be sent."})


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_get(request: Request, token: str):
    return request.app.TEMPLATES.TemplateResponse("reset_password.html", {"request": request, "error": None, "token": token})


@router.post("/reset-password", response_class=HTMLResponse)
def reset_password_post(request: Request, token: str = Form(...), password: str = Form(...)):
    with get_session() as session:
        user = session.query(User).filter_by(password_reset_token=token).first()
        if not user or not user.password_reset_expiry or user.password_reset_expiry < datetime.utcnow():
            return request.app.TEMPLATES.TemplateResponse("reset_password.html",
                                                          {"request": request, "error": "Invalid or expired token.", "token": token})
        user.hashed_password = hash_password(password)
        user.password_reset_token = None
        user.password_reset_expiry = None
        session.commit()
    return request.app.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Password reset. You can now log in."})
