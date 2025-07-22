import os

import stripe
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from database.models import User
from utils.db import get_session

router = APIRouter()


@router.get("/billing", response_class=HTMLResponse)
def billing(request: Request):
    user = request.session.get("user_id")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return request.app.TEMPLATES.TemplateResponse("billing.html", {"request": request, "user": user})


@router.post("/billing/stripe-portal")
def billing_stripe_portal(request: Request):
    user = request.session.get("user_id")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        db_user = session.get(User, user.id)
        if not db_user.stripe_customer_id:
            customer = stripe.Customer.create(email=db_user.email or f"user{db_user.id}@example.com")
            db_user.stripe_customer_id = customer.id
            session.commit()
        else:
            customer = stripe.Customer.retrieve(db_user.stripe_customer_id)
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=SETTINGS.STRIPE_BILLING_PORTAL_RETURN_URL
        )
        return RedirectResponse(url=portal_session.url, status_code=303)
    except Exception as e:
        return request.app.TEMPLATES.TemplateResponse("billing.html", {"request": request, "user": user, "error": str(e)})


@router.post("/billing/checkout")
def billing_checkout(request: Request, plan: str = Form(...)):
    user = request.session.get("user_id")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    price_ids = {
        "basic": os.environ.get("STRIPE_BASIC_PRICE_ID", "price_1N..."),
        "pro": os.environ.get("STRIPE_PRO_PRICE_ID", "price_1N...")
    }
    price_id = price_ids.get(plan)
    if not price_id:
        return request.app.TEMPLATES.TemplateResponse("billing.html", {"request": request, "user": user, "error": "Invalid plan selected."})
    with get_session() as session:
        db_user = session.get(User, user.id)
        if not db_user.stripe_customer_id:
            customer = stripe.Customer.create(email=db_user.email or f"user{db_user.id}@example.com")
            db_user.stripe_customer_id = customer.id
            session.commit()
        else:
            customer = stripe.Customer.retrieve(db_user.stripe_customer_id)
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
        return request.app.TEMPLATES.TemplateResponse("billing.html", {"request": request, "user": user, "error": str(e)})


@router.post("/stripe/webhook")
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
