"""Billing controller for SMTPy v2."""

from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.config import SETTINGS
from shared.models.organization import SubscriptionStatus
from ..database import billing_database
from ..services import stripe_service
from ..schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
    OrganizationBilling
)


async def create_checkout_session(
    db: AsyncSession,
    organization_id: int,
    checkout_request: CheckoutSessionRequest
) -> CheckoutSessionResponse:
    """Create a Stripe checkout session for an organization."""
    # Get organization
    organization = await billing_database.get_organization_by_id(db, organization_id)
    if not organization:
        raise ValueError("Organization not found")
    
    # Create or get Stripe customer
    customer_id = organization.stripe_customer_id
    if not customer_id:
        customer_id = await stripe_service.create_or_get_customer(
            email=organization.email,
            name=organization.name
        )
        
        # Update organization with customer ID
        await billing_database.update_organization_stripe_customer(
            db, organization_id, customer_id
        )
    
    # Determine URLs
    success_url = str(checkout_request.success_url) if checkout_request.success_url else SETTINGS.STRIPE_SUCCESS_URL
    cancel_url = str(checkout_request.cancel_url) if checkout_request.cancel_url else SETTINGS.STRIPE_CANCEL_URL
    
    # Create checkout session
    session_data = await stripe_service.create_checkout_session(
        customer_id=customer_id,
        price_id=checkout_request.price_id,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "organization_id": str(organization_id),
            "price_id": checkout_request.price_id
        }
    )
    
    return CheckoutSessionResponse(
        url=session_data["url"],
        session_id=session_data["session_id"]
    )


async def create_customer_portal_session(
    db: AsyncSession,
    organization_id: int
) -> CustomerPortalResponse:
    """Create a Stripe customer portal session."""
    # Get organization
    organization = await billing_database.get_organization_by_id(db, organization_id)
    if not organization:
        raise ValueError("Organization not found")
    
    if not organization.stripe_customer_id:
        raise ValueError("Organization does not have a Stripe customer")
    
    # Create portal session
    portal_data = await stripe_service.create_portal_session(
        customer_id=organization.stripe_customer_id,
        return_url=SETTINGS.STRIPE_PORTAL_RETURN_URL
    )
    
    return CustomerPortalResponse(url=portal_data["url"])


async def get_subscription(
    db: AsyncSession,
    organization_id: int
) -> Optional[SubscriptionResponse]:
    """Get current subscription for an organization."""
    # Get organization
    organization = await billing_database.get_organization_by_id(db, organization_id)
    if not organization:
        raise ValueError("Organization not found")
    
    if not organization.stripe_subscription_id:
        return None
    
    # Get subscription from Stripe
    try:
        subscription_data = await stripe_service.fetch_subscription(
            organization.stripe_subscription_id
        )
    except ValueError:
        # Subscription no longer exists in Stripe, clear local data
        await billing_database.clear_subscription_data(db, organization_id)
        return None
    
    # Calculate days until renewal
    days_until_renewal = None
    if organization.current_period_end:
        days_until_renewal = (organization.current_period_end - datetime.now()).days
        if days_until_renewal < 0:
            days_until_renewal = 0
    
    is_active = organization.subscription_status in [
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.TRIALING
    ] if organization.subscription_status else False
    
    return SubscriptionResponse(
        id=organization.stripe_subscription_id,
        status=organization.subscription_status,
        current_period_end=organization.current_period_end,
        plan_price_id=organization.plan_price_id,
        cancel_at_period_end=subscription_data.get("cancel_at_period_end", False),
        is_active=is_active,
        days_until_renewal=days_until_renewal
    )


async def cancel_subscription(
    db: AsyncSession,
    organization_id: int,
    update_request: SubscriptionUpdateRequest
) -> Optional[SubscriptionResponse]:
    """Cancel or schedule cancellation of a subscription."""
    # Get organization
    organization = await billing_database.get_organization_by_id(db, organization_id)
    if not organization:
        raise ValueError("Organization not found")
    
    if not organization.stripe_subscription_id:
        raise ValueError("Organization does not have an active subscription")
    
    # Cancel subscription in Stripe
    at_period_end = update_request.cancel_at_period_end or True
    await stripe_service.cancel_subscription(
        subscription_id=organization.stripe_subscription_id,
        at_period_end=at_period_end
    )
    
    # If canceling immediately, update status in database
    if not at_period_end:
        await billing_database.update_subscription_status(
            db=db,
            stripe_subscription_id=organization.stripe_subscription_id,
            subscription_status=SubscriptionStatus.CANCELED
        )
    
    # Return updated subscription
    return await get_subscription(db, organization_id)


async def resume_subscription(
    db: AsyncSession,
    organization_id: int
) -> Optional[SubscriptionResponse]:
    """Resume a subscription that was set to cancel at period end."""
    # Get organization
    organization = await billing_database.get_organization_by_id(db, organization_id)
    if not organization:
        raise ValueError("Organization not found")
    
    if not organization.stripe_subscription_id:
        raise ValueError("Organization does not have an active subscription")
    
    # Resume subscription in Stripe
    await stripe_service.resume_subscription(organization.stripe_subscription_id)
    
    # Return updated subscription
    return await get_subscription(db, organization_id)


async def handle_webhook_event(
    db: AsyncSession,
    event_data: Dict[str, Any]
) -> bool:
    """Handle Stripe webhook event and update database accordingly."""
    event_id = event_data["id"]
    event_type = event_data["type"]
    
    # Check if event already processed
    existing_event = await billing_database.get_webhook_event(db, event_id)
    if existing_event:
        return existing_event.processed
    
    # Record webhook event
    await billing_database.create_webhook_event(db, event_id, event_type)
    
    try:
        # Process different event types
        if event_type in [
            "checkout.session.completed",
            "invoice.payment_succeeded"
        ]:
            await _handle_subscription_created_or_updated(db, event_data)
        
        elif event_type in [
            "customer.subscription.updated",
            "customer.subscription.deleted"
        ]:
            await _handle_subscription_status_changed(db, event_data)
        
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(db, event_data)
        
        # Mark as processed
        await billing_database.mark_webhook_event_processed(db, event_id)
        return True
        
    except Exception as e:
        # Log error but don't mark as processed so it can be retried
        print(f"Error processing webhook {event_id}: {str(e)}")
        return False


async def _handle_subscription_created_or_updated(
    db: AsyncSession,
    event_data: Dict[str, Any]
) -> None:
    """Handle subscription creation or update events."""
    if event_data["type"] == "checkout.session.completed":
        session = event_data["data"]["object"]
        customer_id = session["customer"]
        subscription_id = session["subscription"]
    else:  # invoice.payment_succeeded
        invoice = event_data["data"]["object"]
        customer_id = invoice["customer"]
        subscription_id = invoice["subscription"]
    
    if not subscription_id:
        return
    
    # Get organization by customer ID
    organization = await billing_database.get_organization_by_stripe_customer_id(
        db, customer_id
    )
    if not organization:
        return
    
    # Get subscription details from Stripe
    subscription_data = await stripe_service.fetch_subscription(subscription_id)
    
    # Convert timestamps
    period_end = datetime.fromtimestamp(subscription_data["current_period_end"])
    
    # Map Stripe status to our enum
    status_mapping = {
        "active": SubscriptionStatus.ACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.UNPAID,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        "paused": SubscriptionStatus.PAUSED,
    }
    
    subscription_status = status_mapping.get(
        subscription_data["status"], 
        SubscriptionStatus.ACTIVE
    )
    
    # Get price ID from subscription items
    price_id = None
    if subscription_data["items"]:
        price_id = subscription_data["items"][0]["price_id"]
    
    # Update organization subscription
    await billing_database.update_organization_subscription(
        db=db,
        organization_id=organization.id,
        stripe_subscription_id=subscription_id,
        subscription_status=subscription_status,
        current_period_end=period_end,
        plan_price_id=price_id or ""
    )


async def _handle_subscription_status_changed(
    db: AsyncSession,
    event_data: Dict[str, Any]
) -> None:
    """Handle subscription status change events."""
    subscription = event_data["data"]["object"]
    subscription_id = subscription["id"]
    
    # Map Stripe status to our enum
    status_mapping = {
        "active": SubscriptionStatus.ACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.UNPAID,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        "paused": SubscriptionStatus.PAUSED,
    }
    
    subscription_status = status_mapping.get(
        subscription["status"], 
        SubscriptionStatus.ACTIVE
    )
    
    period_end = None
    if subscription.get("current_period_end"):
        period_end = datetime.fromtimestamp(subscription["current_period_end"])
    
    # Update subscription status
    await billing_database.update_subscription_status(
        db=db,
        stripe_subscription_id=subscription_id,
        subscription_status=subscription_status,
        current_period_end=period_end
    )


async def _handle_payment_failed(
    db: AsyncSession,
    event_data: Dict[str, Any]
) -> None:
    """Handle payment failure events."""
    invoice = event_data["data"]["object"]
    subscription_id = invoice.get("subscription")
    
    if subscription_id:
        # Update subscription status to past due
        await billing_database.update_subscription_status(
            db=db,
            stripe_subscription_id=subscription_id,
            subscription_status=SubscriptionStatus.PAST_DUE
        )


async def get_organization_billing(
    db: AsyncSession,
    organization_id: int
) -> Optional[OrganizationBilling]:
    """Get comprehensive billing information for an organization."""
    # Get organization
    organization = await billing_database.get_organization_by_id(db, organization_id)
    if not organization:
        return None
    
    # Get current subscription
    subscription = await get_subscription(db, organization_id)
    
    # Get usage counts
    domains_count = await billing_database.count_domains_for_organization(db, organization_id)
    
    # Get messages count for current month
    from datetime import datetime
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    messages_count = await billing_database.count_messages_for_organization(
        db, organization_id, since_date=current_month_start
    )
    
    return OrganizationBilling(
        organization_id=organization.id,
        stripe_customer_id=organization.stripe_customer_id,
        subscription=subscription,
        billing_email=organization.email,
        domains_count=domains_count,
        messages_count=messages_count,
        plan_domain_limit=None,  # Would be determined by plan
        plan_message_limit=None  # Would be determined by plan
    )