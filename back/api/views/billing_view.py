"""Billing view layer for SMTPy v2 (billing endpoints only).

Split from the original monolithic billing_view into separate modules:
- billing_view.py: /billing endpoints
- subscriptions_view.py: /subscriptions endpoints
- webhooks_view.py: /webhooks endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import billing_controller
from ..core.db import get_db
from ..schemas.common import ErrorResponse
from ..views.auth_view import get_current_user
from ..schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    OrganizationBilling,
    SubscriptionResponse,
)

# Router for billing
router = APIRouter(prefix="/billing", tags=["billing"])


@router.post(
    "/checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create checkout session",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_checkout_session(
    checkout_request: CheckoutSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a Stripe checkout session for subscription purchase."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        return await billing_controller.create_checkout_session(
            db=db,
            organization_id=organization_id,
            checkout_request=checkout_request,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.get(
    "/customer-portal",
    response_model=CustomerPortalResponse,
    summary="Get customer portal URL",
    responses={
        400: {"model": ErrorResponse, "description": "Organization does not have a Stripe customer"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_customer_portal(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get Stripe customer portal URL for subscription management."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        return await billing_controller.create_customer_portal_session(
            db=db,
            organization_id=organization_id,
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer portal session",
        )


@router.get(
    "/organization",
    response_model=OrganizationBilling,
    summary="Get organization billing information",
    responses={
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_organization_billing(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get comprehensive billing information for the organization."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        billing_info = await billing_controller.get_organization_billing(
            db=db,
            organization_id=organization_id,
        )

        if not billing_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        return billing_info
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch billing information",
        )


@router.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Get current subscription",
    responses={
        404: {"model": ErrorResponse, "description": "Organization or subscription not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current subscription details for the organization."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        subscription = await billing_controller.get_subscription(
            db=db,
            organization_id=organization_id,
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found",
            )

        return subscription
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription",
        )


@router.get(
    "/plans",
    summary="Get available subscription plans",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_plans():
    """Get list of available subscription plans."""
    # Return hardcoded plans for now - in production, these could come from Stripe or database
    return {
        "success": True,
        "data": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "1 domain",
                    "10 aliases",
                    "100 emails/month",
                    "Basic support"
                ],
                "limits": {
                    "domains": 1,
                    "aliases": 10,
                    "emails_per_month": 100
                }
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": 999,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "5 domains",
                    "100 aliases",
                    "10,000 emails/month",
                    "Priority support"
                ],
                "limits": {
                    "domains": 5,
                    "aliases": 100,
                    "emails_per_month": 10000
                }
            },
            {
                "id": "professional",
                "name": "Professional",
                "price": 2999,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Unlimited domains",
                    "Unlimited aliases",
                    "100,000 emails/month",
                    "Premium support",
                    "Custom DKIM keys"
                ],
                "limits": {
                    "domains": -1,
                    "aliases": -1,
                    "emails_per_month": 100000
                }
            }
        ]
    }


@router.get(
    "/usage-limits",
    summary="Get current usage and limits",
    responses={
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_usage_limits(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current usage and subscription limits for the organization."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=400, detail="No organization found for user")

    try:
        # Get current usage from billing info
        billing_info = await billing_controller.get_organization_billing(
            db=db,
            organization_id=organization_id,
        )

        if not billing_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Determine limits based on subscription plan (from billing_info.subscription)
        plan_id = "free"
        if billing_info.subscription and billing_info.subscription.status == "active":
            plan_id = getattr(billing_info.subscription, "plan_id", "free")

        # Map plan to limits (should match /plans endpoint)
        limits_map = {
            "free": {"domains": 1, "aliases": 10, "emails_per_month": 100},
            "starter": {"domains": 5, "aliases": 100, "emails_per_month": 10000},
            "professional": {"domains": -1, "aliases": -1, "emails_per_month": 100000},
        }

        limits = limits_map.get(plan_id, limits_map["free"])

        # Use actual field names from OrganizationBilling schema
        return {
            "success": True,
            "data": {
                "usage": {
                    "domains": billing_info.domains_count,
                    "aliases": 0,  # Not tracked in current schema
                    "emails_this_month": billing_info.messages_count,
                },
                "limits": limits,
                "percentage": {
                    "domains": (billing_info.domains_count / limits["domains"] * 100) if limits["domains"] > 0 else 0,
                    "aliases": 0,  # Not tracked
                    "emails": (billing_info.messages_count / limits["emails_per_month"] * 100) if limits["emails_per_month"] > 0 else 0,
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch usage limits: {str(e)}",
        )