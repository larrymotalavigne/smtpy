"""Webhooks view layer for SMTPy v2.

Currently handles Stripe webhooks under /webhooks/stripe.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..controllers import billing_controller
from shared.core.db import get_db
from ..services import stripe_service
from ..schemas.common import ErrorResponse

# Router for webhooks
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/stripe",
    status_code=status.HTTP_200_OK,
    summary="Handle Stripe webhook",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid webhook signature or payload"},
        500: {"model": ErrorResponse, "description": "Webhook processing failed"},
    },
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
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
                detail="Missing Stripe signature header",
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
            detail=f"Webhook verification failed: {str(e)}",
        )
    except Exception as e:
        # Other processing errors
        print(f"Webhook processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )
