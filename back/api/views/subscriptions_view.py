"""Subscriptions view layer for SMTPy v2.

Provides endpoints under /subscriptions for retrieving and managing
organization subscription state.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import billing_controller
from shared.core.db import get_db
from ..schemas.common import ErrorResponse
from ..schemas.billing import (
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)

# Router for subscriptions
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# For now, we'll use a hardcoded organization_id
# In a real implementation, this would come from authentication/session
MOCK_ORGANIZATION_ID = 1


@router.get(
    "/me",
    response_model=SubscriptionResponse,
    summary="Get current subscription",
    responses={
        404: {"model": ErrorResponse, "description": "Organization or subscription not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription details for the organization."""
    try:
        subscription = await billing_controller.get_subscription(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
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


@router.patch(
    "/cancel",
    response_model=SubscriptionResponse,
    summary="Cancel subscription",
    responses={
        400: {"model": ErrorResponse, "description": "No active subscription or invalid request"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def cancel_subscription(
    update_request: SubscriptionUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cancel or schedule cancellation of the current subscription."""
    try:
        updated_subscription = await billing_controller.cancel_subscription(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            update_request=update_request,
        )

        if not updated_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription to cancel",
            )

        return updated_subscription
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
            detail="Failed to cancel subscription",
        )


@router.patch(
    "/resume",
    response_model=SubscriptionResponse,
    summary="Resume subscription",
    responses={
        400: {"model": ErrorResponse, "description": "No active subscription or invalid request"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def resume_subscription(
    db: AsyncSession = Depends(get_db),
):
    """Resume a subscription that was set to cancel at period end."""
    try:
        updated_subscription = await billing_controller.resume_subscription(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
        )

        if not updated_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No subscription to resume",
            )

        return updated_subscription
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
            detail="Failed to resume subscription",
        )
