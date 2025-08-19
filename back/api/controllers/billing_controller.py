"""Billing controller for Stripe billing operations."""

import logging
import os
from datetime import datetime, UTC
from typing import Dict, Any, Optional

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from back.core.config import SETTINGS
from back.core.database.billing_database import (
    db_get_user_by_stripe_customer_id,
    db_set_user_stripe_customer_id,
    db_update_user_subscription_status,
)
from back.core.database.models import User, ActivityLog
from back.core.utils.db import get_db
from back.core.utils.error_handling import (
    ValidationError,
    ResourceNotFoundError,
)


def log_activity(event_type: str, details: Dict[str, Any]) -> None:
    """Log activity to the database."""
    try:
        with get_db() as session:
            activity_log = ActivityLog(
                event_type=event_type,
                timestamp=datetime.now(UTC),
                details=str(details),
                status="success"
            )
            session.add(activity_log)
            session.commit()
    except Exception as e:
        logging.error(f"Failed to log activity: {e}")


def get_by_id_or_404(session, model_class, record_id: int):
    """Get a record by ID or raise an error if not found."""
    record = session.get(model_class, record_id)
    if not record:
        raise ResourceNotFoundError(f"{model_class.__name__} with id {record_id} not found")
    return record


def get_or_create_stripe_customer(user_id: int) -> str:
    """Get or create a Stripe customer for a user.

    Args:
        user_id: ID of the user

    Returns:
        Stripe customer ID

    Raises:
        ResourceNotFoundError: If user not found
    """
    try:
        with get_db() as session:
            user = get_by_id_or_404(session, User, user_id, session)

            if not user.stripe_customer_id:
                # Create new Stripe customer
                customer = stripe.Customer.create(email=user.email or f"user{user.id}@example.com")
                db_set_user_stripe_customer_id(session, user, customer.id)

                log_activity(
                    "stripe_customer_created",
                    {"user_id": user_id, "customer_id": customer.id, "email": user.email},
                )
            else:
                # Retrieve existing customer
                customer = stripe.Customer.retrieve(user.stripe_customer_id)

            return customer.id

    except ResourceNotFoundError:
        raise
    except Exception as e:
        logging.error(f"Failed to get/create Stripe customer for user {user_id}: {e}")
        raise


def create_billing_portal_session(user_id: int) -> str:
    """Create a Stripe billing portal session.

    Args:
        user_id: ID of the user

    Returns:
        Billing portal session URL

    Raises:
        ResourceNotFoundError: If user not found
    """
    try:
        customer_id = get_or_create_stripe_customer(user_id)

        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id, return_url=SETTINGS.STRIPE_BILLING_PORTAL_RETURN_URL
        )

        log_activity(
            "billing_portal_session_created",
            {"user_id": user_id, "customer_id": customer_id, "session_url": portal_session.url},
        )

        return portal_session.url

    except Exception as e:
        logging.error(f"Failed to create billing portal session for user {user_id}: {e}")
        raise


def create_checkout_session(user_id: int, plan: str) -> str:
    """Create a Stripe checkout session.

    Args:
        user_id: ID of the user
        plan: Plan name (basic, pro, etc.)

    Returns:
        Checkout session URL

    Raises:
        ResourceNotFoundError: If user not found
        ValidationError: If invalid plan
    """
    try:
        # Validate plan
        price_ids = {
            "basic": os.environ.get("STRIPE_BASIC_PRICE_ID", "price_1N..."),
            "pro": os.environ.get("STRIPE_PRO_PRICE_ID", "price_1N..."),
        }

        price_id = price_ids.get(plan)
        if not price_id:
            raise ValidationError(f"Invalid plan: {plan}")

        customer_id = get_or_create_stripe_customer(user_id)

        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=os.environ.get(
                "STRIPE_CHECKOUT_SUCCESS_URL", "http://localhost:8000/billing?success=1"
            ),
            cancel_url=os.environ.get(
                "STRIPE_CHECKOUT_CANCEL_URL", "http://localhost:8000/billing?canceled=1"
            ),
        )

        log_activity(
            "checkout_session_created",
            {
                "user_id": user_id,
                "customer_id": customer_id,
                "plan": plan,
                "price_id": price_id,
                "session_url": checkout_session.url,
            },
        )

        return checkout_session.url

    except (ResourceNotFoundError, ValidationError):
        raise
    except Exception as e:
        logging.error(f"Failed to create checkout session for user {user_id}, plan {plan}: {e}")
        raise


def handle_webhook_event(payload: bytes, signature: str) -> Dict[str, Any]:
    """Handle Stripe webhook events.

    Args:
        payload: Raw webhook payload
        signature: Stripe signature header

    Returns:
        Dictionary containing processing results

    Raises:
        ValidationError: If webhook validation fails
    """
    try:
        endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test")

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(payload, signature, endpoint_secret)
        except Exception as e:
            logging.error(f"Webhook signature verification failed: {e}")
            raise ValidationError(f"Invalid webhook signature: {e}")

        # Process subscription events
        if event["type"].startswith("customer.subscription."):
            return _handle_subscription_event(event)

        # Log unhandled events
        log_activity(
            "webhook_event_received",
            {"event_type": event["type"], "event_id": event.get("id"), "handled": False},
        )

        return {"received": True, "handled": False, "event_type": event["type"]}

    except ValidationError:
        raise
    except Exception as e:
        logging.error(f"Failed to handle webhook event: {e}")
        raise


def _handle_subscription_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle subscription-related webhook events.

    Args:
        event: Stripe webhook event

    Returns:
        Dictionary containing processing results
    """
    try:
        data = event["data"]["object"]
        customer_id = data["customer"]
        status = data["status"]

        with get_db() as session:
            user = db_get_user_by_stripe_customer_id(session, customer_id)

            if user:
                old_status = user.subscription_status
                db_update_user_subscription_status(session, user, status)

                log_activity(
                    "subscription_status_updated",
                    {
                        "user_id": user.id,
                        "customer_id": customer_id,
                        "old_status": old_status,
                        "new_status": status,
                        "event_type": event["type"],
                        "event_id": event.get("id"),
                    },
                )

                return {
                    "received": True,
                    "handled": True,
                    "event_type": event["type"],
                    "user_id": user.id,
                    "status_updated": True,
                }
            else:
                logging.warning(f"No user found for Stripe customer {customer_id}")

                log_activity(
                    "subscription_event_no_user",
                    {
                        "customer_id": customer_id,
                        "status": status,
                        "event_type": event["type"],
                        "event_id": event.get("id"),
                    },
                )

                return {
                    "received": True,
                    "handled": False,
                    "event_type": event["type"],
                    "error": "User not found",
                }

    except Exception as e:
        logging.error(f"Failed to handle subscription event: {e}")
        raise


def get_user_billing_info(user_id: int) -> Dict[str, Any]:
    """Get billing information for a user.

    Args:
        user_id: ID of the user

    Returns:
        Dictionary containing billing information

    Raises:
        ResourceNotFoundError: If user not found
    """
    try:
        with get_db() as session:
            user = get_by_id_or_404(session, User, user_id, session)

            billing_info = {
                "user_id": user_id,
                "has_stripe_customer": bool(user.stripe_customer_id),
                "stripe_customer_id": user.stripe_customer_id,
                "subscription_status": user.subscription_status,
            }

            # Get additional Stripe info if customer exists
            if user.stripe_customer_id:
                try:
                    customer = stripe.Customer.retrieve(user.stripe_customer_id)
                    subscriptions = stripe.Subscription.list(customer=user.stripe_customer_id)

                    billing_info.update(
                        {
                            "customer_email": customer.email,
                            "customer_created": customer.created,
                            "active_subscriptions": len(subscriptions.data),
                            "subscriptions": [
                                {
                                    "id": sub.id,
                                    "status": sub.status,
                                    "current_period_start": sub.current_period_start,
                                    "current_period_end": sub.current_period_end,
                                    "plan_name": sub.items.data[0].price.nickname
                                    if sub.items.data
                                    else None,
                                }
                                for sub in subscriptions.data
                            ],
                        }
                    )
                except Exception as e:
                    logging.warning(
                        f"Failed to retrieve Stripe info for customer {user.stripe_customer_id}: {e}"
                    )
                    billing_info["stripe_error"] = str(e)

            log_activity(
                "billing_info_retrieved",
                {"user_id": user_id, "has_stripe_customer": billing_info["has_stripe_customer"]},
            )

            return billing_info

    except ResourceNotFoundError:
        raise
    except Exception as e:
        logging.error(f"Failed to get billing info for user {user_id}: {e}")
        raise


def cancel_subscription(user_id: int, subscription_id: str) -> Dict[str, Any]:
    """Cancel a user's subscription.

    Args:
        user_id: ID of the user
        subscription_id: Stripe subscription ID

    Returns:
        Dictionary containing cancellation results

    Raises:
        ResourceNotFoundError: If user not found
        PermissionError: If user doesn't own the subscription
    """
    try:
        with get_db() as session:
            user = get_by_id_or_404(session, User, user_id, session)

            if not user.stripe_customer_id:
                raise ValidationError("User has no Stripe customer")

            # Verify subscription belongs to user
            subscription = stripe.Subscription.retrieve(subscription_id)
            if subscription.customer != user.stripe_customer_id:
                raise PermissionError("Subscription does not belong to user")

            # Cancel subscription
            canceled_subscription = stripe.Subscription.delete(subscription_id)

            log_activity(
                "subscription_canceled",
                {
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "customer_id": user.stripe_customer_id,
                    "canceled_at": canceled_subscription.canceled_at,
                },
            )

            return {
                "canceled": True,
                "subscription_id": subscription_id,
                "canceled_at": canceled_subscription.canceled_at,
                "status": canceled_subscription.status,
            }

    except (ResourceNotFoundError, PermissionError, ValidationError):
        raise
    except Exception as e:
        logging.error(
            f"Failed to cancel subscription {subscription_id} for user {user_id}: {e}"
        )
        raise


# ---- Thin async billing operations for views (function-style) ----
# annotations future import not needed here


async def get_or_create_customer(session: AsyncSession, user_id: int) -> str:
    """Get or create a Stripe customer for a user and return the customer ID."""
    user = await session.get(User, user_id)
    if not user:
        raise ResourceNotFoundError("User not found")
    if not user.stripe_customer_id:
        # Create customer in Stripe (Stripe SDK is sync)
        customer = stripe.Customer.create(email=user.email or f"user{user.id}@example.com")
        await db_set_user_stripe_customer_id(session, user, customer.id)
        return customer.id
    else:
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        return customer.id


async def create_billing_portal(session: AsyncSession, user_id: int) -> str:
    """Create a billing portal session and return its URL."""
    customer_id = await get_or_create_customer(session, user_id)
    portal_session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=SETTINGS.STRIPE_BILLING_PORTAL_RETURN_URL,
    )
    return portal_session.url


async def create_checkout(session: AsyncSession, user_id: int, plan: str) -> str:
    """Create a checkout session for the provided plan and return its URL."""
    price_ids = {
        "basic": os.environ.get("STRIPE_BASIC_PRICE_ID", "price_1N..."),
        "pro": os.environ.get("STRIPE_PRO_PRICE_ID", "price_1N..."),
    }
    price_id = price_ids.get(plan)
    if not price_id:
        raise ValidationError(f"Invalid plan: {plan}")
    customer_id = await get_or_create_customer(session, user_id)
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=os.environ.get(
            "STRIPE_CHECKOUT_SUCCESS_URL", "http://localhost:8000/billing?success=1"
        ),
        cancel_url=os.environ.get(
            "STRIPE_CHECKOUT_CANCEL_URL", "http://localhost:8000/billing?canceled=1"
        ),
    )
    return checkout_session.url


async def handle_webhook(
        session: AsyncSession, payload: bytes, signature: Optional[str]
) -> Dict[str, Any]:
    """Validate and process a Stripe webhook payload."""
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test")
    try:
        event = stripe.Webhook.construct_event(payload, signature, endpoint_secret)
    except Exception as e:
        raise ValidationError(f"Invalid webhook signature: {e}")

    handled = False
    if event.get("type", "").startswith("customer.subscription."):
        data = event["data"]["object"]
        customer_id = data["customer"]
        status_val = data["status"]
        user = await db_get_user_by_stripe_customer_id(session, customer_id)
        if user:
            await db_update_user_subscription_status(session, user, status_val)
            handled = True

    return {"received": True, "handled": handled, "event_type": event.get("type")}
