import os
import secrets
import smtplib
from datetime import datetime, timedelta, UTC
from email.message import EmailMessage

from fastapi import APIRouter, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from back.core.config import template_response
from back.api.controllers.main_controller import (
    invite_user_simple,
    register_user_simple,
    verify_email_simple,
    authenticate_simple,
)
from back.core.database.models import User
from back.core.utils.csrf import validate_csrf
from back.core.utils.db import adbDep
from back.core.utils.user import (
    get_current_user,
    send_invitation_email,
    hash_password,
    send_verification_email,
)

router = APIRouter(prefix="/user")


@router.get("/invite", response_class=HTMLResponse)
def invite_user_get(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return template_response(request, "invite_user.html", {"error": None})


@router.post("/invite", response_class=HTMLResponse)
async def invite_user_post(
        request: Request, background_tasks: BackgroundTasks, email: str = Form(...), db: adbDep = None
):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    from back.core.utils.error_handling import ValidationError

    try:
        result = await invite_user_simple(db, email=email, invited_by_id=user["id"])
    except ValidationError:
        return template_response(
            request,
            "invite_user.html",
            {"error": "Invitation already sent or email registered."},
        )
    background_tasks.add_task(send_invitation_email, email, result.get("token"))
    return template_response(request, "invite_user.html", {"error": "Invitation sent."})


@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request, invite: str = None):
    return template_response(request, "register.html", {"error": None, "invite": invite})


@router.post("/register", response_class=HTMLResponse)
async def register_post(
        request: Request,
        background_tasks: BackgroundTasks,
        username: str = Form(...),
        email: str = Form(""),
        password: str = Form(...),
        invite: str = Form(""),
        db: adbDep = None,
):
    from back.core.utils.error_handling import ValidationError

    try:
        result = await register_user_simple(
            db,
            username=username,
            password=password,
            email=(email or None),
            invite_token=(invite or None),
        )
    except ValidationError as e:
        msg = str(e) if str(e) else "Registration error"
        return template_response(
            request,
            "register.html",
            {"error": msg, "invite": (invite or None)},
        )
    if (email or None) and result.get("requires_verification"):
        background_tasks.add_task(send_verification_email, email, result.get("verification_token"))
    if invite:
        return template_response(
            request,
            "login.html",
            {"error": "Account created. You can now log in."},
        )
    return template_response(
        request,
        "register.html",
        {"error": "Check your email to verify your account.", "invite": None},
    )


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(request: Request, token: str, db: adbDep = None):
    ok = await verify_email_simple(db, token)
    if not ok:
        return template_response(
            request, "login.html", {"error": "Invalid or expired token."}
        )
    return template_response(
        request, "login.html", {"error": "Email verified. You can now log in."}
    )


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return template_response(request, "login.html", {})


@router.post("/login")
async def login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        csrf_token: str = Form(...),
        db: adbDep = None,
):
    # Validate CSRF token
    validate_csrf(request, csrf_token)

    user_id = await authenticate_simple(db, username=username, password=password)
    if not user_id:
        return template_response(request, "login.html", {"error": "Invalid credentials."})
    request.session["user_id"] = user_id
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def user_management(request: Request, db: adbDep):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    users = await db.execute(select(User))
    users_list = users.scalars().all()
    return request.app.TEMPLATES.TemplateResponse(
        "users.html", {"request": request, "users": users_list, "user": user}
    )


@router.post("/users/edit")
async def edit_user(
        request: Request, user_id: int = Form(...), email: str = Form(None), role: str = Form(...), db: adbDep = None
):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    u = await db.get(User, user_id)
    if u:
        u.email = email
        u.role = role
        await db.commit()
    return RedirectResponse(url="/users", status_code=303)


@router.post("/users/delete")
async def delete_user(request: Request, user_id: int = Form(...), db: adbDep = None):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    u = await db.get(User, user_id)
    if u:
        await db.delete(u)
        await db.commit()
    return RedirectResponse(url="/users", status_code=303)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_get(request: Request):
    return request.app.TEMPLATES.TemplateResponse(
        "forgot_password.html", {"request": request, "error": None}
    )


@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_post(
        request: Request, background_tasks: BackgroundTasks, email: str = Form(...), db: adbDep = None
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        return request.app.TEMPLATES.TemplateResponse(
            "forgot_password.html",
            {"request": request, "error": "If the email exists, a reset link will be sent."},
        )
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(UTC) + timedelta(hours=1)
    user.password_reset_token = token
    user.password_reset_expiry = expiry
    await db.commit()

    def send_reset_email(to_email, token):
        msg = EmailMessage()
        msg["Subject"] = "Password Reset for smtpy"
        msg["From"] = "no-reply@smtpy.local"
        msg["To"] = to_email
        msg.set_content(f"Reset your password: http://localhost/reset-password?token={token}")
        with smtplib.SMTP(
                os.environ.get("SMTP_HOST", "localhost"), int(os.environ.get("SMTP_PORT", 25))
        ) as s:
            s.send_message(msg)

    background_tasks.add_task(send_reset_email, email, token)
    return request.app.TEMPLATES.TemplateResponse(
        "forgot_password.html",
        {"request": request, "error": "If the email exists, a reset link will be sent."},
    )


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_get(request: Request, token: str):
    return request.app.TEMPLATES.TemplateResponse(
        "reset_password.html", {"request": request, "error": None, "token": token}
    )


@router.post("/reset-password", response_class=HTMLResponse)
async def reset_password_post(request: Request, token: str = Form(...), password: str = Form(...), db: adbDep = None):
    result = await db.execute(select(User).where(User.password_reset_token == token))
    user = result.scalars().first()
    if (
            not user
            or not user.password_reset_expiry
            or user.password_reset_expiry < datetime.now(UTC)
    ):
        return request.app.TEMPLATES.TemplateResponse(
            "reset_password.html",
            {"request": request, "error": "Invalid or expired token.", "token": token},
        )
    user.hashed_password = hash_password(password)
    user.password_reset_token = None
    user.password_reset_expiry = None
    await db.commit()
    return request.app.TEMPLATES.TemplateResponse(
        "login.html", {"request": request, "error": "Password reset. You can now log in."}
    )
