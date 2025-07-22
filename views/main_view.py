import secrets
from datetime import datetime, timedelta
from sqlite3 import IntegrityError

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Form
from fastapi.responses import HTMLResponse
from passlib.context import CryptContext
from sqlalchemy.orm import selectinload
from starlette.responses import RedirectResponse

from config import SETTINGS
from controllers import dns_controller
from database.models import User, Invitation, Domain, Alias, ActivityLog
from utils.db import get_session
from utils.user import get_current_user, send_invitation_email, hash_password, send_verification_email

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    return SETTINGS.TEMPLATES.TemplateResponse("presentation.html", {"request": request})


@router.get("/invite", response_class=HTMLResponse)
def invite_user_get(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return SETTINGS.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": None})


@router.post("/invite-user", response_class=HTMLResponse)
def invite_user_post(request: Request, background_tasks: BackgroundTasks, email: str = Form(...)):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    with get_session() as session:
        if session.query(User).filter_by(email=email).first():
            return SETTINGS.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": "Email already registered."})
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=24)
        invitation = Invitation(email=email, token=token, expires_at=expires, invited_by=user.id)
        session.add(invitation)
        try:
            session.commit()
        except IntegrityError:
            return SETTINGS.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": "Invitation already sent."})
        background_tasks.add_task(send_invitation_email, email, token)
    return SETTINGS.TEMPLATES.TemplateResponse("invite_user.html", {"request": request, "error": "Invitation sent."})


@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request, invite: str = None):
    return SETTINGS.TEMPLATES.TemplateResponse("register.html", {"request": request, "error": None, "invite": invite})


@router.post("/register", response_class=HTMLResponse)
def register_post(request: Request, background_tasks: BackgroundTasks, username: str = Form(...), email: str = Form(""),
                  password: str = Form(...), invite: str = Form("")):
    email_val = email if email else None
    invite_val = invite if invite else None
    with get_session() as session:
        if invite_val:
            invitation = session.query(Invitation).filter_by(token=invite_val).first()
            if not invitation or invitation.expires_at < datetime.utcnow():
                return SETTINGS.TEMPLATES.TemplateResponse("register.html",
                                                  {"request": request, "error": "Invalid or expired invitation.", "invite": invite_val})
            email_val = invitation.email
        if session.query(User).filter_by(username=username).first():
            return SETTINGS.TEMPLATES.TemplateResponse("register.html",
                                              {"request": request, "error": "Username already exists.", "invite": invite_val})
        if email_val and session.query(User).filter_by(email=email_val).first():
            return SETTINGS.TEMPLATES.TemplateResponse("register.html",
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
        return SETTINGS.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Account created. You can now log in."})
    return SETTINGS.TEMPLATES.TemplateResponse("register.html",
                                      {"request": request, "error": "Check your email to verify your account.", "invite": None})


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email(request: Request, token: str):
    with get_session() as session:
        user = session.query(User).filter_by(verification_token=token).first()
        if not user:
            return SETTINGS.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Invalid or expired token."})
        user.is_active = True
        user.email_verified = True
        user.verification_token = None
        session.commit()
    return SETTINGS.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Email verified. You can now log in."})


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return SETTINGS.TEMPLATES.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with get_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if not user or not pwd_context.verify(password, user.hashed_password):
            return SETTINGS.TEMPLATES.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
        request.session["user_id"] = user.id
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    user = get_current_user(request)
    return SETTINGS.TEMPLATES.TemplateResponse("presentation.html", {"request": request, "user": user})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        num_domains = session.query(Domain).count()
        num_aliases = session.query(Alias).count()
        recent_activity = session.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    user = get_current_user(request)
    return SETTINGS.TEMPLATES.TemplateResponse(
        "dashboard.html",
        {"request": request, "num_domains": num_domains, "num_aliases": num_aliases, "recent_activity": recent_activity, "user": user}
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        domains = session.query(Domain).options(selectinload(Domain.aliases)).all()
        aliases = session.query(Alias).all()
        # Prepare domain status for onboarding checklist
        domain_statuses = []
        for domain in domains:
            dns_results = dns_controller.check_dns_records(domain.name)
            verified = dns_results.get('spf', {}).get('status') == 'valid'
            mx_valid = False
            try:
                import dns.resolver
                answers = dns.resolver.resolve(domain.name, 'MX')
                mx_valid = any(answers)
            except Exception:
                mx_valid = False
            domain_statuses.append({
                'id': domain.id,
                'name': domain.name,
                'catch_all': domain.catch_all,
                'verified': verified,
                'mx_valid': mx_valid,
                'spf_valid': dns_results.get('spf', {}).get('status') == 'valid',
                'dkim_valid': dns_results.get('dkim', {}).get('status') == 'valid',
                'dmarc_valid': dns_results.get('dmarc', {}).get('status') == 'valid'
            })
    user = get_current_user(request)
    return SETTINGS.TEMPLATES.TemplateResponse("index.html",
                                      {"request": request, "title": "smtpy Admin", "domains": domain_statuses, "aliases": aliases,
                                       "user": user})
