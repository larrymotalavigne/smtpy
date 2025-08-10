from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from config import template_response
from utils.csrf import validate_csrf
from utils.user import require_login

from controllers.billing_controller import (
    create_billing_portal,
    create_checkout,
    handle_webhook,
)
from utils.db import adbDep

router = APIRouter(prefix="")


@router.get("/billing", response_class=HTMLResponse)
async def billing(request: Request):
    user = require_login(request)
    return template_response(request, "billing.html", {"user": user})


@router.post("/billing/stripe-portal")
async def billing_stripe_portal(request: Request, db: adbDep = None):
    user = require_login(request)
    try:
        url = await create_billing_portal(db, user["id"])
        return RedirectResponse(url=url, status_code=303)
    except Exception as e:
        return template_response(request, "billing.html", {"user": user, "error": str(e)})


@router.post("/billing/checkout")
async def billing_checkout(request: Request, plan: str = Form(...), db: adbDep = None):
    user = require_login(request)
    try:
        url = await create_checkout(db, user["id"], plan)
        return RedirectResponse(url=url, status_code=303)
    except Exception as e:
        return template_response(request, "billing.html", {"user": user, "error": str(e)})


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: adbDep = None):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        result = await handle_webhook(db, payload, sig_header)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
