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
from ..schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    OrganizationBilling,
)

# Router for billing
router = APIRouter(prefix="/billing", tags=["billing"])

# For now, we'll use a hardcoded organization_id
# In a real implementation, this would come from authentication/session
MOCK_ORGANIZATION_ID = 1


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
):
    """Create a Stripe checkout session for subscription purchase."""
    try:
        return await billing_controller.create_checkout_session(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
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
):
    """Get Stripe customer portal URL for subscription management."""
    try:
        return await billing_controller.create_customer_portal_session(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
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
):
    """Get comprehensive billing information for the organization."""
    try:
        billing_info = await billing_controller.get_organization_billing(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
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