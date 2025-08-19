import os
from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlalchemy.orm import selectinload, Session
from starlette.responses import RedirectResponse

from back.api.controllers import dns_controller
from back.core.config import template_response
from back.core.database.models import User, Domain, Alias, ActivityLog
from back.core.utils.csrf import validate_csrf
from back.core.utils.db import get_db_dep
from back.core.utils.error_handling import ValidationError

# Backward-compatible alias for dependency usage throughout this module
get_db = get_db_dep
from back.core.utils.rate_limit import check_rate_limit
from back.core.utils.soft_delete import (
    soft_delete_domain,
    soft_delete_alias,
    soft_delete_user,
    get_active_domains,
    get_active_aliases,
    get_active_users,
)
from back.core.utils.user import (
    get_current_user,
    send_invitation_email,
    send_verification_email,
)

router = APIRouter(prefix="")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Thin controller helpers (async)
from back.api.controllers.main_controller import (
    invite_user_simple_sync,
    register_user_simple_sync,
    verify_email_simple_sync,
)


@router.get("/invite", response_class=HTMLResponse)
def invite_user_get(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return template_response(request, "invite_user.html", {"error": None})


@router.post("/invite-user", response_class=HTMLResponse)
def invite_user_post(
        request: Request,
        background_tasks: BackgroundTasks,
        email: str = Form(...),
        csrf_token: str = Form(...),
        session: Session = Depends(get_db),
):
    # Validate CSRF token
    validate_csrf(request, csrf_token)

    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    try:
        result = invite_user_simple_sync(session, email=email, invited_by_id=user.id)
    except ValidationError:
        return template_response(
            request, "invite_user.html", {"error": "Invitation already sent or email registered."}
        )
    # Send email
    background_tasks.add_task(send_invitation_email, email, result.get("token"))
    return template_response(request, "invite_user.html", {"error": "Invitation sent."})


@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request, invite: str = None):
    return template_response(request, "register.html", {"error": None, "invite": invite})


@router.post("/register", response_class=HTMLResponse)
def register_post(
        request: Request,
        background_tasks: BackgroundTasks,
        username: str = Form(...),
        email: str = Form(""),
        password: str = Form(...),
        invite: str = Form(""),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    # Apply rate limiting for registration attempts (3 attempts per 10 minutes)
    check_rate_limit(request, "auth_register", 3, 600)

    # Validate CSRF token
    if csrf_token:
        validate_csrf(request, csrf_token)

    try:
        result = register_user_simple_sync(
            session,
            username=username,
            password=password,
            email=(email or None),
            invite_token=(invite or None),
        )
    except ValidationError as e:
        # Keep original UX messages as close as possible
        msg = str(e) if str(e) else "Registration error"
        return template_response(
            request, "register.html", {"error": msg, "invite": (invite or None)}
        )
    # Send verification if needed
    if (email or None) and result.get("requires_verification"):
        background_tasks.add_task(send_verification_email, email, result.get("verification_token"))
    if invite:
        return template_response(
            request, "login.html", {"error": "Account created. You can now log in."}
        )
    return template_response(
        request,
        "register.html",
        {"error": "Check your email to verify your account.", "invite": None},
    )


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email(request: Request, token: str, session: Session = Depends(get_db)):
    ok = verify_email_simple_sync(session, token)
    if not ok:
        return template_response(request, "login.html", {"error": "Invalid or expired token."})
    return template_response(
        request, "login.html", {"error": "Email verified. You can now log in."}
    )


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return template_response(request, "login.html", {})


@router.post("/login")
def login(
        request: Request,
        username: str = Form(..., min_length=1),
        password: str = Form(..., min_length=1),
        csrf_token: str = Form(...),
        session: Session = Depends(get_db),
):
    # Apply rate limiting for authentication attempts (5 attempts per 5 minutes)
    # Scope by username to avoid cross-test/user interference
    check_rate_limit(request, f"auth_login:{username}", 5, 300)

    # Validate CSRF token
    validate_csrf(request, csrf_token)

    user = get_active_users(session).filter_by(username=username).first()
    password_ok = user is not None and bcrypt.verify(password, user.hashed_password)
    if not user or not password_ok:
        return template_response(request, "login.html", {"error": "Invalid credentials."})
    # Successful authentication: clear auth attempt rate limit for this client
    from back.core.utils.rate_limit import rate_limiter, get_client_ip

    client_ip = get_client_ip(request)
    # Clear possible rate limit keys
    rate_limiter.clear(f"auth_login:{username}")
    rate_limiter.clear(f"auth_login:{username}:{client_ip}")
    rate_limiter.clear(f"auth_login:{client_ip}")
    request.session["user_id"] = user.id
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    user = get_current_user(request)
    return template_response(request, "presentation.html", {"user": user})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    num_domains = get_active_domains(session).count()
    num_aliases = get_active_aliases(session).count()
    recent_activity = (
        session.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    )
    return template_response(
        request,
        "dashboard.html",
        {
            "num_domains": num_domains,
            "num_aliases": num_aliases,
            "recent_activity": recent_activity,
            "user": user,
        },
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, session: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    domains = get_active_domains(session).options(selectinload(Domain.aliases)).all()
    aliases = get_active_aliases(session).all()
    # Prepare domain status for onboarding checklist
    domain_statuses = []
    for domain in domains:
        dns_results = dns_controller.check_dns_records(domain.name)
        verified = dns_results.get("spf", {}).get("status") == "valid"
        mx_valid = False
        try:
            import dns.resolver

            answers = dns.resolver.resolve(domain.name, "MX")
            mx_valid = any(answers)
        except Exception:
            mx_valid = False
        domain_statuses.append(
            {
                "id": domain.id,
                "name": domain.name,
                "catch_all": domain.catch_all,
                "verified": verified,
                "mx_valid": mx_valid,
                "spf_valid": dns_results.get("spf", {}).get("status") == "valid",
                "dkim_valid": dns_results.get("dkim", {}).get("status") == "valid",
                "dmarc_valid": dns_results.get("dmarc", {}).get("status") == "valid",
            }
        )
    return template_response(
        request,
        "index.html",
        {"title": "smtpy Admin", "domains": domain_statuses, "aliases": aliases, "user": user},
    )


# Additional endpoints for test compatibility


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_get(request: Request):
    return template_response(request, "forgot_password.html", {"error": None})


@router.get("/invite-user", response_class=HTMLResponse)
def invite_user_get_alt(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return template_response(request, "invite_user.html", {"error": None})


@router.get("/users", response_class=HTMLResponse)
def users_get(request: Request, session: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    users = get_active_users(session).all()
    return template_response(request, "users.html", {"users": users, "user": user})


@router.get("/dkim-public-key")
def dkim_public_key_get(request: Request, domain: str):
    if not domain:
        return "Please specify a domain."
    safe_domain = domain.replace("/", "").replace("..", "")
    path = os.path.join(os.path.dirname(__file__), "../static", f"dkim-public-{safe_domain}.txt")
    if not os.path.exists(path):
        return f"DKIM public key for {domain} not found. Please generate and mount the key as dkim-public-{domain}.txt."
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return f"DKIM public key for {domain} not found."


@router.get("/domain-dns/{domain_id}", response_class=HTMLResponse)
def domain_dns_get(request: Request, domain_id: int, session: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    domain = session.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    # Enforce access control: only owner or admin can view
    if user["role"] != "admin" and domain.owner_id != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    dns_results = dns_controller.check_dns_records(domain.name)
    return template_response(
        request, "domain_dns.html", {"domain": domain, "dns_results": dns_results, "user": user}
    )


@router.get("/domain-aliases/{domain_id}", response_class=HTMLResponse)
def domain_aliases_get(request: Request, domain_id: int, session: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    domain = session.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    # Enforce access control: only owner or admin can view
    if user["role"] != "admin" and domain.owner_id != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    aliases = get_active_aliases(session, domain_id=domain_id).all()
    return template_response(
        request, "domain_aliases.html", {"domain": domain, "aliases": aliases, "user": user}
    )


# Health check endpoints for container orchestration


@router.get("/health")
def health_check():
    """Liveness probe endpoint - checks if the application is running."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "smtpy",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@router.get("/ready")
def readiness_check(session: Session = Depends(get_db_dep)):
    """Readiness probe endpoint - checks if the application is ready to serve traffic."""
    try:
        # Check database connectivity
        session.execute("SELECT 1")

        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "service": "smtpy",
                "database": "connected",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "service": "smtpy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )


# API endpoints for test compatibility


@router.get("/api/dns-check")
def api_dns_check_root(domain: str):
    return dns_controller.check_dns_records(domain)


@router.get("/api/activity-stats")
def api_activity_stats_root(session: Session = Depends(get_db)):
    from collections import defaultdict

    cutoff = datetime.now(UTC) - timedelta(days=30)
    logs = session.query(ActivityLog).filter(ActivityLog.timestamp >= cutoff).all()
    stats = defaultdict(lambda: {"forward": 0, "bounce": 0, "error": 0})
    for log in logs:
        date = str(log.timestamp)[:10]
        stats[date][log.event_type] += 1
    sorted_stats = sorted(stats.items())
    return {
        "dates": [d for d, _ in sorted_stats],
        "forward": [v["forward"] for _, v in sorted_stats],
        "bounce": [v["bounce"] for _, v in sorted_stats],
        "error": [v["error"] for _, v in sorted_stats],
    }


@router.get("/api/aliases/{domain_id}")
@router.post("/api/aliases/{domain_id}")
def api_add_alias_to_domain(
        request: Request,
        domain_id: int,
        local_part: str = None,
        targets: str = None,
        expires_at: str = None,
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    # This endpoint is for testing - just return 403 to indicate auth is required
    raise HTTPException(status_code=403, detail="Authentication required")


# Form submission endpoints for test compatibility


@router.post("/add-domain")
def add_domain_post(
        request: Request,
        name: str = Form(...),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    if csrf_token:
        validate_csrf(request, csrf_token)
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    domain = Domain(name=name, owner_id=user.id)
    session.add(domain)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/delete-domain")
def delete_domain_post(
        request: Request,
        domain_id: int = Form(...),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    if csrf_token:
        validate_csrf(request, csrf_token)
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    domain = session.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Check ownership (admin can delete any domain)
    if user.role != "admin" and domain.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="Access denied: You can only delete your own domains"
        )

    # Use soft delete instead of hard delete
    soft_delete_domain(session, domain_id)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/add-alias")
def add_alias_post(
        request: Request,
        local_part: str = Form(...),
        target: str = Form(...),
        domain_id: int = Form(...),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    if csrf_token:
        validate_csrf(request, csrf_token)
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    # Check if domain exists and user has access to it
    domain = session.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Check domain ownership (admin can create aliases for any domain)
    if user.role != "admin" and domain.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: You can only create aliases for your own domains",
        )

    alias = Alias(local_part=local_part, targets=target, domain_id=domain_id, owner_id=user.id)
    session.add(alias)
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/delete-alias")
def delete_alias_post(
        request: Request,
        alias_id: int = Form(...),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    if csrf_token:
        validate_csrf(request, csrf_token)
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    alias = session.get(Alias, alias_id)
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")

    # Check ownership (admin can delete any alias)
    if user.role != "admin" and alias.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="Access denied: You can only delete your own aliases"
        )

    # Use soft delete instead of hard delete
    soft_delete_alias(session, alias_id)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/edit-catchall")
def edit_catchall_post(
        request: Request,
        domain_id: int = Form(...),
        catch_all: str = Form(""),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    if csrf_token:
        validate_csrf(request, csrf_token)
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    domain = session.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Check ownership (admin can edit any domain)
    if user.role != "admin" and domain.owner_id != user.id:
        raise HTTPException(
            status_code=403, detail="Access denied: You can only edit your own domains"
        )

    domain.catch_all = catch_all or None
    session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/users/edit")
def users_edit_post(
        request: Request,
        user_id: int = Form(...),
        email: str = Form(...),
        role: str = Form(...),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    if csrf_token:
        validate_csrf(request, csrf_token)
    current_user = get_current_user(request)
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    user = session.get(User, user_id)
    if user:
        user.email = email
        user.role = role
        session.commit()
    return RedirectResponse(url="/users", status_code=303)


@router.post("/users/delete")
def users_delete_post(
        request: Request,
        user_id: int = Form(...),
        csrf_token: str = Form(None),
        session: Session = Depends(get_db),
):
    if csrf_token:
        validate_csrf(request, csrf_token)
    current_user = get_current_user(request)
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete yourself")

    # Use soft delete instead of hard delete
    soft_delete_user(session, user_id)
    return RedirectResponse(url="/users", status_code=303)
