import os
from typing import List, Optional

from fastapi import APIRouter, Request, Form, Path, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from sqlalchemy import select
from pydantic import BaseModel

from config import template_response
from controllers import domain_controller
from controllers.dns_controller import check_dns_records
from controllers.domain_controller import (
    list_domains_simple,
    create_domain_simple,
    get_domain_simple,
    delete_domain_simple,
    update_domain_catchall,
    get_dns_status_simple,
    activity_stats_simple,
)
from database.models import Domain, Alias, ActivityLog
from utils.csrf import validate_csrf
from utils.db import adbDep
from utils.user import require_login, get_current_user

router = APIRouter(
    prefix="/domain",
)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: adbDep):
    user = require_login(request)

    num_domains = await domain_controller.get_domain_count(db)
    num_aliases = db.query(Alias).count()
    recent_activity = (
        db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(10).all()
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
async def admin_panel(request: Request, db: adbDep):
    user = require_login(request)
    
    domains_result = await db.execute(select(Domain).where(Domain.is_deleted == False))
    domains = domains_result.scalars().all()
    aliases_result = await db.execute(select(Alias).where(Alias.is_deleted == False))
    aliases = aliases_result.scalars().all()
    
    domain_statuses = []
    for domain in domains:
        dns_results = check_dns_records(domain.name)
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


@router.post("/")
async def add_domain(
        request: Request,
        name: str = Form(...),
        catch_all: str = Form(None),
        csrf_token: str = Form(...),
        db: adbDep = None,
):
    # Validate CSRF token
    validate_csrf(request, csrf_token)

    # Check authentication
    user = require_login(request)

    # Delegate to controller
    await create_domain_simple(db, name=name, owner_id=user["id"], catch_all=catch_all)
    return RedirectResponse(url="/admin", status_code=303)


@router.delete("/")
async def delete_domain(
        request: Request, domain_id: int = Form(...), csrf_token: str = Form(...), db: adbDep = None
):
    # Validate CSRF token
    validate_csrf(request, csrf_token)

    # Check authentication
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    domain = await get_domain_simple(db, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    # Check ownership (admin can delete any domain)
    if user.role != "admin" and domain.get("owner_id") != user.id:
        raise HTTPException(
            status_code=403, detail="Access denied: You can only delete your own domains"
        )
    await delete_domain_simple(db, domain_id)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/edit-catchall")
async def edit_catchall(
        request: Request,
        domain_id: int = Form(...),
        catch_all: str = Form(""),
        csrf_token: str = Form(...),
        db: adbDep = None,
):
    # Validate CSRF token
    validate_csrf(request, csrf_token)

    # Check authentication
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    domain = await get_domain_simple(db, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    # Check ownership (admin can edit any domain)
    if user.role != "admin" and domain.get("owner_id") != user.id:
        raise HTTPException(
            status_code=403, detail="Access denied: You can only edit your own domains"
        )
    await update_domain_catchall(db, domain_id, catch_all or None)
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/dns-check")
def api_dns_check(domain: str):
    return check_dns_records(domain)


@router.get("/dkim-public-key", response_class=PlainTextResponse)
def get_dkim_public_key(domain: str):
    if not domain:
        return "Please specify a domain."
    safe_domain = domain.replace("/", "").replace("..", "")
    path = os.path.join(
        os.path.dirname(__file__), "../web/static", f"dkim-public-{safe_domain}.txt"
    )
    if not os.path.exists(path):
        return f"DKIM public key for {domain} not found. Please generate and mount the key as dkim-public-{domain}.txt."
    with open(path) as f:
        return f.read()


@router.get("/activity-stats")
async def activity_stats(db: adbDep = None):
    return await activity_stats_simple(db)


@router.get("/domain-dns/{domain_id}", response_class=HTMLResponse)
async def domain_dns_settings(request: Request, domain_id: int = Path(...), db: adbDep = None):
    user = require_login(request)
    domain = await get_domain_simple(db, domain_id)
    if not domain:
        return RedirectResponse(url="/admin", status_code=303)
    # Ownership check (admin can access any domain)
    if user["role"] != "admin" and domain.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    mx_records = [
        {
            "type": "MX",
            "hostname": domain["name"],
            "priority": 10,
            "value": f"mx1.{request.url.hostname}.",
        },
        {
            "type": "MX",
            "hostname": domain["name"],
            "priority": 20,
            "value": f"mx2.{request.url.hostname}.",
        },
    ]
    spf_value = f"v=spf1 include:{request.url.hostname} ~all"
    dkim_selector = "mail"
    dkim_value = "(DKIM public key here)"
    dmarc_value = "v=DMARC1; p=quarantine; rua=mailto:postmaster@%s" % domain["name"]
    return request.app.TEMPLATES.TemplateResponse(
        "domain_dns.html",
        {
            "request": request,
            "domain": domain,
            "mx_records": mx_records,
            "spf_value": spf_value,
            "dkim_selector": dkim_selector,
            "dkim_value": dkim_value,
            "dmarc_value": dmarc_value,
        },
    )


@router.get("/dns-status/{domain_id}")
async def api_dns_status(domain_id: int = Path(...), db: adbDep = None):
    results = await get_dns_status_simple(db, domain_id)
    if results is None:
        return {"error": "Domain not found"}
    return results


@router.get("/domain-aliases/{domain_id}", response_class=HTMLResponse)
async def domain_aliases(request: Request, domain_id: int = Path(...), db: adbDep = None):
    user = require_login(request)
    domain = await get_domain_simple(db, domain_id)
    if not domain:
        return RedirectResponse(url="/admin", status_code=303)
    if user["role"] != "admin" and domain.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return template_response(request, "domain_aliases.html", {"domain": domain})


@router.get("/domains", response_model=List[dict])
async def list_domains(db: adbDep = None):
    return await list_domains_simple(db)


class DomainCreate(BaseModel):
    name: str
    catch_all: Optional[str] = None


@router.post("/domains", response_model=dict)
async def create_domain_api(request: Request, domain: DomainCreate, db: adbDep = None):
    user = require_login(request)
    created = await create_domain_simple(
        db, name=domain.name, owner_id=user["id"], catch_all=domain.catch_all
    )
    return created


@router.get("/domains/{domain_id}", response_model=dict)
async def get_domain_api(domain_id: int, db: adbDep = None):
    domain = await get_domain_simple(db, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.delete("/domains/{domain_id}")
async def delete_domain_api(domain_id: int, db: adbDep = None):
    ok = await delete_domain_simple(db, domain_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Domain not found")
    return {"ok": True}
