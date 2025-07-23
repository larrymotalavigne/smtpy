import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Request, Form, Path, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from controllers.dns_controller import check_dns_records

from config import template_response
from utils.db import get_session
from utils.user import get_current_user
from utils.csrf import validate_csrf
from database.models import Domain, Alias, ActivityLog

router = APIRouter(
    prefix="/domain",
)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        num_domains = session.query(Domain).count()
        num_aliases = session.query(Alias).count()
        recent_activity = session.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    return template_response(
        request,
        "dashboard.html",
        {"num_domains": num_domains, "num_aliases": num_aliases, "recent_activity": recent_activity, "user": user}
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        domains = session.query(Domain).all()
        aliases = session.query(Alias).all()
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
    return template_response(request, "index.html", {"title": "smtpy Admin", "domains": domain_statuses,
                                                     "aliases": aliases, "user": user})


@router.post("/")
def add_domain(request: Request, name: str = Form(...), catch_all: str = Form(None), csrf_token: str = Form(...)):
    # Validate CSRF token
    validate_csrf(request, csrf_token)
    
    # Check authentication
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")
    
    with get_session() as session:
        domain = Domain(name=name, catch_all=catch_all, owner_id=user.id)
        session.add(domain)
        session.commit()
        session.refresh(domain)
    return RedirectResponse(url="/admin", status_code=303)


@router.delete("/")
def delete_domain(request: Request, domain_id: int = Form(...), csrf_token: str = Form(...)):
    # Validate CSRF token
    validate_csrf(request, csrf_token)
    
    # Check authentication
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")
    
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        # Check ownership (admin can delete any domain)
        if user.role != "admin" and domain.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: You can only delete your own domains")
        
        session.delete(domain)
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/edit-catchall")
def edit_catchall(request: Request, domain_id: int = Form(...), catch_all: str = Form(""), csrf_token: str = Form(...)):
    # Validate CSRF token
    validate_csrf(request, csrf_token)
    
    # Check authentication
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")
    
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        # Check ownership (admin can edit any domain)
        if user.role != "admin" and domain.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: You can only edit your own domains")
        
        domain.catch_all = catch_all or None
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/dns-check")
def api_dns_check(domain: str):
    return check_dns_records(domain)


@router.get("/dkim-public-key", response_class=PlainTextResponse)
def get_dkim_public_key(domain: str):
    if not domain:
        return "Please specify a domain."
    safe_domain = domain.replace('/', '').replace('..', '')
    path = os.path.join(os.path.dirname(__file__), "../web/static", f"dkim-public-{safe_domain}.txt")
    if not os.path.exists(path):
        return f"DKIM public key for {domain} not found. Please generate and mount the key as dkim-public-{domain}.txt."
    with open(path) as f:
        return f.read()


@router.get("/activity-stats")
def activity_stats():
    with get_session() as session:
        cutoff = datetime.utcnow() - timedelta(days=30)
        logs = session.query(ActivityLog).filter(ActivityLog.timestamp >= cutoff.isoformat()).all()
        stats = defaultdict(lambda: {"forward": 0, "bounce": 0, "error": 0})
        for log in logs:
            date = log.timestamp[:10]
            stats[date][log.event_type] += 1
        sorted_stats = sorted(stats.items())
        return {
            "dates": [d for d, _ in sorted_stats],
            "forward": [v["forward"] for _, v in sorted_stats],
            "bounce": [v["bounce"] for _, v in sorted_stats],
            "error": [v["error"] for _, v in sorted_stats],
        }


@router.get("/domain-dns/{domain_id}", response_class=HTMLResponse)
def domain_dns_settings(request: Request, domain_id: int = Path(...)):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            return RedirectResponse(url="/admin", status_code=303)
        mx_records = [
            {"type": "MX", "hostname": domain.name, "priority": 10, "value": f"mx1.{request.url.hostname}."},
            {"type": "MX", "hostname": domain.name, "priority": 20, "value": f"mx2.{request.url.hostname}."},
        ]
        spf_value = f"v=spf1 include:{request.url.hostname} ~all"
        dkim_selector = "mail"
        dkim_value = "(DKIM public key here)"
        dmarc_value = "v=DMARC1; p=quarantine; rua=mailto:postmaster@%s" % domain.name
        return request.app.TEMPLATES.TemplateResponse("domain_dns.html", {
            "request": request,
            "domain": domain,
            "mx_records": mx_records,
            "spf_value": spf_value,
            "dkim_selector": dkim_selector,
            "dkim_value": dkim_value,
            "dmarc_value": dmarc_value,
        })


@router.get("/dns-status/{domain_id}")
def api_dns_status(domain_id: int = Path(...)):
    import dns.resolver
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            return {"error": "Domain not found"}
        results = {}
        try:
            mx_answers = dns.resolver.resolve(domain.name, "MX")
            results["mx"] = [str(r.exchange).rstrip(".") for r in mx_answers]
        except Exception as e:
            results["mx"] = []
        try:
            txt_answers = dns.resolver.resolve(domain.name, "TXT")
            spf = [r.strings[0].decode() for r in txt_answers if r.strings and r.strings[0].decode().startswith("v=spf1")]
            results["spf"] = spf
        except Exception as e:
            results["spf"] = []
        try:
            dkim_name = f"mail._domainkey.{domain.name}"
            dkim_txt = dns.resolver.resolve(dkim_name, "TXT")
            dkim = [r.strings[0].decode() for r in dkim_txt if r.strings]
            results["dkim"] = dkim
        except Exception as e:
            results["dkim"] = []
        try:
            dmarc_name = f"_dmarc.{domain.name}"
            dmarc_txt = dns.resolver.resolve(dmarc_name, "TXT")
            dmarc = [r.strings[0].decode() for r in dmarc_txt if r.strings]
            results["dmarc"] = dmarc
        except Exception as e:
            results["dmarc"] = []
        return results


@router.get("/domain-aliases/{domain_id}", response_class=HTMLResponse)
def domain_aliases(request: Request, domain_id: int = Path(...)):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            return RedirectResponse(url="/admin", status_code=303)
        return request.app.TEMPLATES.TemplateResponse("domain_aliases.html", {"request": request, "domain": domain})


@router.get("/domains", response_model=List[dict])
def list_domains():
    with get_session() as session:
        domains = session.query(Domain).all()
        return [domain.__dict__ for domain in domains]


@router.post("/domains", response_model=dict)
def create_domain(domain: dict):
    with get_session() as session:
        db_domain = Domain(name=domain["name"], catch_all=domain.get("catch_all"))
        session.add(db_domain)
        session.commit()
        session.refresh(db_domain)
        return db_domain.__dict__


@router.get("/domains/{domain_id}", response_model=dict)
def get_domain(domain_id: int):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return domain.__dict__


@router.delete("/domains/{domain_id}")
def delete_domain(domain_id: int):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        session.delete(domain)
        session.commit()
        return {"ok": True}
