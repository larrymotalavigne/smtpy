"""Stripe service functions for SMTPy v2."""

import stripe
from typing import Dict, Any, Optional

from shared.core.config import SETTINGS

# Initialize Stripe with API key
stripe.api_key = SETTINGS.STRIPE_API_KEY


async def create_or_get_customer(email: str, name: str) -> str:
    """
    Create a new Stripe customer or get existing one by email.
    
    Args:
        email: Customer email address
        name: Customer name
        
    Returns:
        Stripe customer ID
    """
    try:
        # First try to find existing customer by email
        customers = stripe.Customer.list(email=email, limit=1)
        
        if customers.data:
            return customers.data[0].id
        
        # Create new customer if none exists
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={
                "source": "smtpy-v2"
            }
        )
        
        return customer.id
        
    except stripe.error.StripeError as e:
        raise ValueError(f"Failed to create or get Stripe customer: {str(e)}")


async def create_checkout_session(
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a Stripe checkout session.
    
    Args:
        customer_id: Stripe customer ID
        price_id: Stripe price ID
        success_url: URL to redirect to on successful payment
        cancel_url: URL to redirect to on cancelled payment
        metadata: Optional metadata to attach to the session
        
    Returns:
        Dictionary containing session URL and ID
    """
    try:
        session_metadata = metadata or {}
        session_metadata.update({
            "source": "smtpy-v2"
        })
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=session_metadata,
            allow_promotion_codes=True,
            billing_address_collection="auto",
            customer_update={
                "address": "auto",
                "name": "auto"
            }
        )
        
        return {
            "url": session.url,
            "session_id": session.id
        }
        
    except stripe.error.StripeError as e:
        raise ValueError(f"Failed to create checkout session: {str(e)}")


async def create_portal_session(customer_id: str, return_url: str) -> Dict[str, str]:
    """
    Create a Stripe customer portal session.
    
    Args:
        customer_id: Stripe customer ID
        return_url: URL to return to from the portal
        
    Returns:
        Dictionary containing portal URL
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        
        return {
            "url": session.url
        }
        
    except stripe.error.StripeError as e:
        raise ValueError(f"Failed to create portal session: {str(e)}")


async def verify_webhook(payload: bytes, sig_header: str) -> Dict[str, Any]:
    """
    Verify Stripe webhook signature and parse event.
    
    Args:
        payload: Raw webhook payload
        sig_header: Stripe signature header
        
    Returns:
        Parsed webhook event
        
    Raises:
        ValueError: If signature verification fails
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, SETTINGS.STRIPE_WEBHOOK_SECRET
        )
        return event
        
    except ValueError as e:
        raise ValueError(f"Invalid payload: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        raise ValueError(f"Invalid signature: {str(e)}")


async def fetch_subscription(subscription_id: str) -> Dict[str, Any]:
    """
    Fetch subscription details from Stripe.
    
    Args:
        subscription_id: Stripe subscription ID
        
    Returns:
        Subscription data dictionary
    """
    try:
        subscription = stripe.Subscription.retrieve(
            subscription_id,
            expand=["latest_invoice", "customer", "items.data.price"]
        )
        
        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "canceled_at": subscription.canceled_at,
            "customer_id": subscription.customer,
            "items": [
                {
                    "price_id": item.price.id,
                    "price_amount": item.price.unit_amount,
                    "price_currency": item.price.currency,
                    "price_interval": item.price.recurring.interval if item.price.recurring else None,
                }
                for item in subscription.items.data
            ],
            "latest_invoice": {
                "id": subscription.latest_invoice.id if subscription.latest_invoice else None,
                "status": subscription.latest_invoice.status if subscription.latest_invoice else None,
                "amount_paid": subscription.latest_invoice.amount_paid if subscription.latest_invoice else 0,
            } if subscription.latest_invoice else None,
        }
        
    except stripe.error.StripeError as e:
        raise ValueError(f"Failed to fetch subscription: {str(e)}")


async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
    """
    Cancel or schedule cancellation of a subscription.
    
    Args:
        subscription_id: Stripe subscription ID
        at_period_end: Whether to cancel at period end or immediately
        
    Returns:
        Updated subscription data
    """
    try:
        if at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            subscription = stripe.Subscription.delete(subscription_id)
        
        return {
            "id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "canceled_at": subscription.canceled_at,
            "current_period_end": subscription.current_period_end,
        }
        
    except stripe.error.StripeError as e:
        raise ValueError(f"Failed to cancel subscription: {str(e)}")


async def resume_subscription(subscription_id: str) -> Dict[str, Any]:
    """
    Resume a subscription that was set to cancel at period end.
    
    Args:
        subscription_id: Stripe subscription ID
        
    Returns:
        Updated subscription data
    """
    try:
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False
        )
        
        return {
            "id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "current_period_end": subscription.current_period_end,
        }
        
    except stripe.error.StripeError as e:
        raise ValueError(f"Failed to resume subscription: {str(e)}")


async def get_customer(customer_id: str) -> Dict[str, Any]:
    """
    Get customer details from Stripe.
    
    Args:
        customer_id: Stripe customer ID
        
    Returns:
        Customer data dictionary
    """
    try:
        customer = stripe.Customer.retrieve(customer_id)
        
        return {
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "created": customer.created,
            "metadata": customer.metadata,
        }
        
    except stripe.error.StripeError as e:
        raise ValueError(f"Failed to get customer: {str(e)}")