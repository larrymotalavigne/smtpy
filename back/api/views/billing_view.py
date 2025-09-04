"""Billing view layer for SMTPy v2."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import billing_controller
from ..core.db import get_db
from ..services import stripe_service
from ..schemas.common import ErrorResponse
from ..schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
    OrganizationBilling
)

# Create router
billing_router = APIRouter(prefix="/billing", tags=["billing"])
subscriptions_router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
webhooks_router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# For now, we'll use a hardcoded organization_id
# In a real implementation, this would come from authentication/session
MOCK_ORGANIZATION_ID = 1


@billing_router.post(
    "/checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create checkout session",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_checkout_session(
    checkout_request: CheckoutSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe checkout session for subscription purchase."""
    try:
        return await billing_controller.create_checkout_session(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            checkout_request=checkout_request
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@billing_router.get(
    "/customer-portal",
    response_model=CustomerPortalResponse,
    summary="Get customer portal URL",
    responses={
        400: {"model": ErrorResponse, "description": "Organization does not have a Stripe customer"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_customer_portal(
    db: AsyncSession = Depends(get_db)
):
    """Get Stripe customer portal URL for subscription management."""
    try:
        return await billing_controller.create_customer_portal_session(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer portal session"
        )


@billing_router.get(
    "/organization",
    response_model=OrganizationBilling,
    summary="Get organization billing information",
    responses={
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_organization_billing(
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive billing information for the organization."""
    try:
        billing_info = await billing_controller.get_organization_billing(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not billing_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return billing_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch billing information"
        )


@subscriptions_router.get(
    "/me",
    response_model=SubscriptionResponse,
    summary="Get current subscription",
    responses={
        404: {"model": ErrorResponse, "description": "Organization or subscription not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db)
):
    """Get current subscription details for the organization."""
    try:
        subscription = await billing_controller.get_subscription(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        return subscription
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription"
        )


@subscriptions_router.patch(
    "/cancel",
    response_model=SubscriptionResponse,
    summary="Cancel subscription",
    responses={
        400: {"model": ErrorResponse, "description": "No active subscription or invalid request"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def cancel_subscription(
    update_request: SubscriptionUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Cancel or schedule cancellation of the current subscription."""
    try:
        updated_subscription = await billing_controller.cancel_subscription(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID,
            update_request=update_request
        )
        
        if not updated_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription to cancel"
            )
        
        return updated_subscription
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@subscriptions_router.patch(
    "/resume",
    response_model=SubscriptionResponse,
    summary="Resume subscription",
    responses={
        400: {"model": ErrorResponse, "description": "No active subscription or invalid request"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def resume_subscription(
    db: AsyncSession = Depends(get_db)
):
    """Resume a subscription that was set to cancel at period end."""
    try:
        updated_subscription = await billing_controller.resume_subscription(
            db=db,
            organization_id=MOCK_ORGANIZATION_ID
        )
        
        if not updated_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No subscription to resume"
            )
        
        return updated_subscription
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume subscription"
        )


@webhooks_router.post(
    "/stripe",
    status_code=status.HTTP_200_OK,
    summary="Handle Stripe webhook",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid webhook signature or payload"},
        500: {"model": ErrorResponse, "description": "Webhook processing failed"}
    }
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint verifies the webhook signature and processes the event
    to update subscription and billing information in the database.
    """
    try:
        # Get raw payload and signature header
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature", "")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature header"
            )
        
        # Verify webhook signature and parse event
        event_data = await stripe_service.verify_webhook(payload, sig_header)
        
        # Process the webhook event
        processed = await billing_controller.handle_webhook_event(db, event_data)
        
        if not processed:
            # Event was not processed successfully, but we don't want to return an error
            # to Stripe as this could cause webhook retries. Log the issue instead.
            print(f"Warning: Webhook event {event_data.get('id')} was not processed successfully")
        
        return {"received": True, "processed": processed}
        
    except ValueError as e:
        # Signature verification failed or invalid payload
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook verification failed: {str(e)}"
        )
    except Exception as e:
        # Other processing errors
        print(f"Webhook processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# Combine all routers
def get_billing_routers():
    """Get all billing-related routers."""
    return [billing_router, subscriptions_router, webhooks_router]