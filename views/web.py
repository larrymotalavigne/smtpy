import os
import secrets
import smtplib
from datetime import datetime, timedelta
from collections import defaultdict
from email.message import EmailMessage
import json

from fastapi import FastAPI, Request, Form, HTTPException, Depends, status, BackgroundTasks, Path, Body
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import selectinload
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
import dns.resolver
import stripe

from database.db import get_session, init_db
from database.models import Domain, Alias, ActivityLog, User, Invitation
from controllers.domain_controller import router as domain_router
from controllers.alias_controller import router as alias_router
from web.dns_check import check_dns_records

SECRET_KEY = os.environ.get("SMTPY_SECRET_KEY", "change-this-secret-key")
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 25))

STRIPE_TEST_API_KEY = os.environ.get("STRIPE_TEST_API_KEY", "sk_test_...")
STRIPE_BILLING_PORTAL_RETURN_URL = os.environ.get("STRIPE_BILLING_PORTAL_RETURN_URL", "http://localhost:8000/billing")
stripe.api_key = STRIPE_TEST_API_KEY

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.include_router(domain_router, prefix="/api")
app.include_router(alias_router, prefix="/api")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../web/static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../web/templates"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

@app.on_event("startup")
def on_startup():
    init_db()

@app.on_event("startup")
def create_default_admin():
    with get_session() as session:
        if not session.query(User).first():
            hashed = pwd_context.hash("password")
            user = User(
                username="admin",
                hashed_password=hashed,
                email=None,
                role="admin",
                is_active=True,
                email_verified=True
            )
            session.add(user)
            session.commit()
            print("\n\033[92mCreated default admin user: admin / password\033[0m\n")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def send_verification_email(to_email, token):
    msg = EmailMessage()
    msg["Subject"] = "Verify your email for smtpy"
    msg["From"] = "no-reply@smtpy.local"
    msg["To"] = to_email
    msg.set_content(f"Click to verify: http://localhost/verify-email?token={token}")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.send_message(msg)

def send_invitation_email(to_email, token):
    msg = EmailMessage()
    msg["Subject"] = "You're invited to smtpy"
    msg["From"] = "no-reply@smtpy.local"
    msg["To"] = to_email
    msg.set_content(f"You've been invited! Complete your registration: http://localhost/register?invite={token}")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.send_message(msg)

# --- Web routes (copied from web/app.py, update as needed) ---
# Example for login, register, dashboard, etc.
# All routes should use the new imports and structure

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("presentation.html", {"request": request})

@app.get("/invite-user", response_class=HTMLResponse)
def invite_user_get(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return templates.TemplateResponse("invite_user.html", {"request": request, "error": None})

@app.post("/invite-user", response_class=HTMLResponse)
def invite_user_post(request: Request, background_tasks: BackgroundTasks, email: str = Form(...)):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    with get_session() as session:
        if session.query(User).filter_by(email=email).first():
            return templates.TemplateResponse("invite_user.html", {"request": request, "error": "Email already registered."})
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=24)
        invitation = Invitation(email=email, token=token, expires_at=expires, invited_by=user.id)
        session.add(invitation)
        try:
            session.commit()
        except IntegrityError:
            return templates.TemplateResponse("invite_user.html", {"request": request, "error": "Invitation already sent."})
        background_tasks.add_task(send_invitation_email, email, token)
    return templates.TemplateResponse("invite_user.html", {"request": request, "error": "Invitation sent."})

@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request, invite: str = None):
    return templates.TemplateResponse("register.html", {"request": request, "error": None, "invite": invite})

@app.post("/register", response_class=HTMLResponse)
def register_post(request: Request, background_tasks: BackgroundTasks, username: str = Form(...), email: str = Form(""), password: str = Form(...), invite: str = Form("") ):
    email_val = email if email else None
    invite_val = invite if invite else None
    with get_session() as session:
        if invite_val:
            invitation = session.query(Invitation).filter_by(token=invite_val).first()
            if not invitation or invitation.expires_at < datetime.utcnow():
                return templates.TemplateResponse("register.html", {"request": request, "error": "Invalid or expired invitation.", "invite": invite_val})
            email_val = invitation.email
        if session.query(User).filter_by(username=username).first():
            return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists.", "invite": invite_val})
        if email_val and session.query(User).filter_by(email=email_val).first():
            return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered.", "invite": invite_val})
        token = secrets.token_urlsafe(32)
        user = User(username=username, email=email_val, hashed_password=hash_password(password), is_active=not invite_val, email_verified=bool(invite_val), verification_token=None if invite_val else token)
        session.add(user)
        if invite_val:
            session.delete(invitation)
        session.commit()
        if email_val and not invite_val:
            background_tasks.add_task(send_verification_email, email_val, token)
    if invite_val:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Account created. You can now log in."})
    return templates.TemplateResponse("register.html", {"request": request, "error": "Check your email to verify your account.", "invite": None})

@app.get("/verify-email", response_class=HTMLResponse)
def verify_email(request: Request, token: str):
    with get_session() as session:
        user = session.query(User).filter_by(verification_token=token).first()
        if not user:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid or expired token."})
        user.is_active = True
        user.email_verified = True
        user.verification_token = None
        session.commit()
    return templates.TemplateResponse("login.html", {"request": request, "error": "Email verified. You can now log in."})

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with get_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if not user or not pwd_context.verify(password, user.hashed_password):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
        request.session["user_id"] = user.id
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("presentation.html", {"request": request, "user": user})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        num_domains = session.query(Domain).count()
        num_aliases = session.query(Alias).count()
        recent_activity = session.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    user = get_current_user(request)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "num_domains": num_domains, "num_aliases": num_aliases, "recent_activity": recent_activity, "user": user}
    )

@app.get("/admin", response_class=HTMLResponse)
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
            dns_results = check_dns_records(domain.name)
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
    return templates.TemplateResponse("index.html", {"request": request, "title": "smtpy Admin", "domains": domain_statuses, "aliases": aliases, "user": user})

@app.post("/add-domain")
def add_domain(request: Request, name: str = Form(...), catch_all: str = Form(None)):
    require_login(request)
    with get_session() as session:
        domain = Domain(name=name, catch_all=catch_all)
        session.add(domain)
        session.commit()
        session.refresh(domain)
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/delete-domain")
def delete_domain(request: Request, domain_id: int = Form(...)):
    require_login(request)
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        session.delete(domain)
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/add-alias")
def add_alias(request: Request, local_part: str = Form(...), target: str = Form(...), domain_id: int = Form(...)):
    require_login(request)
    with get_session() as session:
        alias = Alias(local_part=local_part, target=target, domain_id=domain_id)
        session.add(alias)
        session.commit()
        session.refresh(alias)
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/delete-alias")
def delete_alias(request: Request, alias_id: int = Form(...)):
    require_login(request)
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        session.delete(alias)
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/edit-catchall")
def edit_catchall(request: Request, domain_id: int = Form(...), catch_all: str = Form("")):
    with get_session() as session:
        domain = session.query(Domain).get(domain_id)
        if domain:
            domain.catch_all = catch_all or None
            session.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/api/dns-check")
def api_dns_check(domain: str):
    return check_dns_records(domain)

@app.get("/dkim-public-key", response_class=PlainTextResponse)
def get_dkim_public_key(domain: str):
    if not domain:
        return "Please specify a domain."
    safe_domain = domain.replace('/', '').replace('..', '')
    path = os.path.join(os.path.dirname(__file__), "static", f"dkim-public-{safe_domain}.txt")
    if not os.path.exists(path):
        return f"DKIM public key for {domain} not found. Please generate and mount the key as dkim-public-{domain}.txt."
    with open(path) as f:
        return f.read()

@app.get("/api/activity-stats")
def activity_stats():
    with get_session() as session:
        cutoff = datetime.utcnow() - timedelta(days=30)
        logs = session.query(ActivityLog).filter(ActivityLog.timestamp >= cutoff.isoformat()).all()
        stats = defaultdict(lambda: {"forward": 0, "bounce": 0, "error": 0})
        for log in logs:
            # Parse timestamp to date
            date = log.timestamp[:10]  # YYYY-MM-DD
            stats[date][log.event_type] += 1
        # Sort by date
        sorted_stats = sorted(stats.items())
        return {
            "dates": [d for d, _ in sorted_stats],
            "forward": [v["forward"] for _, v in sorted_stats],
            "bounce": [v["bounce"] for _, v in sorted_stats],
            "error": [v["error"] for _, v in sorted_stats],
        }

@app.get("/users", response_class=HTMLResponse)
def user_management(request: Request):
    user = get_current_user(request)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    with get_session() as session:
        users = session.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "user": user})

@app.post("/users/edit")
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

@app.post("/users/delete")
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

@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_get(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request, "error": None})

@app.post("/forgot-password", response_class=HTMLResponse)
def forgot_password_post(request: Request, background_tasks: BackgroundTasks, email: str = Form(...)):
    with get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "If the email exists, a reset link will be sent."})
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
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.send_message(msg)
        background_tasks.add_task(send_reset_email, email, token)
    return templates.TemplateResponse("forgot_password.html", {"request": request, "error": "If the email exists, a reset link will be sent."})

@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_get(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "error": None, "token": token})

@app.post("/reset-password", response_class=HTMLResponse)
def reset_password_post(request: Request, token: str = Form(...), password: str = Form(...)):
    with get_session() as session:
        user = session.query(User).filter_by(password_reset_token=token).first()
        if not user or not user.password_reset_expiry or user.password_reset_expiry < datetime.utcnow():
            return templates.TemplateResponse("reset_password.html", {"request": request, "error": "Invalid or expired token.", "token": token})
        user.hashed_password = hash_password(password)
        user.password_reset_token = None
        user.password_reset_expiry = None
        session.commit()
    return templates.TemplateResponse("login.html", {"request": request, "error": "Password reset. You can now log in."})

@app.get("/domain-dns/{domain_id}", response_class=HTMLResponse)
def domain_dns_settings(request: Request, domain_id: int = Path(...)):
    with get_session() as session:
        domain = session.query(Domain).get(domain_id)
        if not domain:
            return RedirectResponse(url="/admin", status_code=303)
        # Example recommended values (customize as needed)
        mx_records = [
            {"type": "MX", "hostname": domain.name, "priority": 10, "value": f"mx1.{request.url.hostname}."},
            {"type": "MX", "hostname": domain.name, "priority": 20, "value": f"mx2.{request.url.hostname}."},
        ]
        spf_value = f"v=spf1 include:{request.url.hostname} ~all"
        dkim_selector = "mail"
        dkim_value = "(DKIM public key here)"  # TODO: fetch real key
        dmarc_value = "v=DMARC1; p=quarantine; rua=mailto:postmaster@%s" % domain.name
        return templates.TemplateResponse("domain_dns.html", {
            "request": request,
            "domain": domain,
            "mx_records": mx_records,
            "spf_value": spf_value,
            "dkim_selector": dkim_selector,
            "dkim_value": dkim_value,
            "dmarc_value": dmarc_value,
        })

@app.get("/api/dns-status/{domain_id}")
def api_dns_status(domain_id: int = Path(...)):
    import dns.resolver
    with get_session() as session:
        domain = session.query(Domain).get(domain_id)
        if not domain:
            return {"error": "Domain not found"}
        results = {}
        # MX
        try:
            mx_answers = dns.resolver.resolve(domain.name, "MX")
            results["mx"] = [str(r.exchange).rstrip(".") for r in mx_answers]
        except Exception as e:
            results["mx"] = []
        # SPF
        try:
            txt_answers = dns.resolver.resolve(domain.name, "TXT")
            spf = [r.strings[0].decode() for r in txt_answers if r.strings and r.strings[0].decode().startswith("v=spf1")]
            results["spf"] = spf
        except Exception as e:
            results["spf"] = []
        # DKIM
        try:
            dkim_name = f"mail._domainkey.{domain.name}"
            dkim_txt = dns.resolver.resolve(dkim_name, "TXT")
            dkim = [r.strings[0].decode() for r in dkim_txt if r.strings]
            results["dkim"] = dkim
        except Exception as e:
            results["dkim"] = []
        # DMARC
        try:
            dmarc_name = f"_dmarc.{domain.name}"
            dmarc_txt = dns.resolver.resolve(dmarc_name, "TXT")
            dmarc = [r.strings[0].decode() for r in dmarc_txt if r.strings]
            results["dmarc"] = dmarc
        except Exception as e:
            results["dmarc"] = []
        return results 

@app.get("/domain-aliases/{domain_id}", response_class=HTMLResponse)
def domain_aliases(request: Request, domain_id: int = Path(...)):
    with get_session() as session:
        domain = session.query(Domain).get(domain_id)
        if not domain:
            return RedirectResponse(url="/admin", status_code=303)
        return templates.TemplateResponse("domain_aliases.html", {"request": request, "domain": domain})

@app.get("/api/aliases/{domain_id}")
def api_list_aliases(domain_id: int = Path(...)):
    with get_session() as session:
        now = datetime.utcnow()
        aliases = session.query(Alias).filter_by(domain_id=domain_id).all()
        return [{"id": a.id, "local_part": a.local_part, "targets": a.targets, "expires_at": a.expires_at.isoformat() if a.expires_at else None} for a in aliases]

@app.post("/api/aliases/{domain_id}")
def api_add_alias(request: Request, domain_id: int = Path(...), local_part: str = Body(...), targets: str = Body(...), expires_at: str = Body(None)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        exp = datetime.fromisoformat(expires_at) if expires_at else None
        alias = Alias(local_part=local_part, targets=targets, domain_id=domain_id, expires_at=exp)
        session.add(alias)
        session.commit()
        return {"success": True, "id": alias.id}

@app.delete("/api/alias/{alias_id}")
def api_delete_alias(request: Request, alias_id: int = Path(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        alias = session.query(Alias).get(alias_id)
        if alias:
            session.delete(alias)
            session.commit()
            return {"success": True}
        return JSONResponse(status_code=404, content={"error": "Alias not found"}) 

@app.post("/api/alias-test/{alias_id}")
def api_test_alias(alias_id: int = Path(...)):
    with get_session() as session:
        alias = session.query(Alias).get(alias_id)
        if not alias:
            return JSONResponse(status_code=404, content={"error": "Alias not found"})
        # Simulate sending a test email (log only)
        print(f"Test email would be sent to {alias.target} for alias {alias.local_part}")
        return {"success": True, "message": f"Test email sent to {alias.target}"} 

@app.get("/billing", response_class=HTMLResponse)
def billing(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("billing.html", {"request": request, "user": user}) 

@app.post("/billing/stripe-portal")
def billing_stripe_portal(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    # Ensure user has a Stripe customer ID
    with get_session() as session:
        db_user = session.get(User, user.id)
        if not db_user.stripe_customer_id:
            # Create Stripe customer in test mode
            customer = stripe.Customer.create(email=db_user.email or f"user{db_user.id}@example.com")
            db_user.stripe_customer_id = customer.id
            session.commit()
        else:
            customer = stripe.Customer.retrieve(db_user.stripe_customer_id)
    # Create a billing portal session
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=STRIPE_BILLING_PORTAL_RETURN_URL
        )
        return RedirectResponse(url=portal_session.url, status_code=303)
    except Exception as e:
        return templates.TemplateResponse("billing.html", {"request": request, "user": user, "error": str(e)}) 

@app.post("/billing/checkout")
def billing_checkout(request: Request, plan: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    # Map plan to Stripe price ID (test mode)
    price_ids = {
        "basic": os.environ.get("STRIPE_BASIC_PRICE_ID", "price_1N..."),
        "pro": os.environ.get("STRIPE_PRO_PRICE_ID", "price_1N...")
    }
    price_id = price_ids.get(plan)
    if not price_id:
        return templates.TemplateResponse("billing.html", {"request": request, "user": user, "error": "Invalid plan selected."})
    # Ensure user has a Stripe customer ID
    with get_session() as session:
        db_user = session.get(User, user.id)
        if not db_user.stripe_customer_id:
            customer = stripe.Customer.create(email=db_user.email or f"user{db_user.id}@example.com")
            db_user.stripe_customer_id = customer.id
            session.commit()
        else:
            customer = stripe.Customer.retrieve(db_user.stripe_customer_id)
    # Create Stripe Checkout Session
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=os.environ.get("STRIPE_CHECKOUT_SUCCESS_URL", "http://localhost:8000/billing?success=1"),
            cancel_url=os.environ.get("STRIPE_CHECKOUT_CANCEL_URL", "http://localhost:8000/billing?canceled=1")
        )
        return RedirectResponse(url=checkout_session.url, status_code=303)
    except Exception as e:
        return templates.TemplateResponse("billing.html", {"request": request, "user": user, "error": str(e)})

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test")
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        print(f"Webhook error: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    # Handle subscription events
    if event["type"].startswith("customer.subscription."):
        data = event["data"]["object"]
        customer_id = data["customer"]
        status_val = data["status"]
        with get_session() as session:
            user = session.query(User).filter_by(stripe_customer_id=customer_id).first()
            if user:
                user.subscription_status = status_val
                session.commit()
    print(f"Received Stripe event: {event['type']}")
    return {"received": True} 