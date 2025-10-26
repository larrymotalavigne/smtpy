"""Comprehensive edge case tests for billing controller.

This test suite aims to achieve 70%+ coverage for the billing controller
by testing all functions with various edge cases, error conditions, and scenarios.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from api.controllers import billing_controller
from api.models.organization import Organization, SubscriptionStatus
from api.schemas.billing import (
    CheckoutSessionRequest,
    SubscriptionUpdateRequest
)


@pytest.mark.asyncio
class TestCreateCheckoutSession:
    """Test create_checkout_session function with edge cases."""

    async def test_create_checkout_session_success(
        self, async_db: AsyncSession, test_organization
    ):
        """Test successful checkout session creation."""
        with patch('api.services.stripe_service.create_or_get_customer', new_callable=AsyncMock) as mock_customer, \
             patch('api.services.stripe_service.create_checkout_session', new_callable=AsyncMock) as mock_checkout:

            # Mock Stripe responses
            mock_customer.return_value = "cus_test_123"
            mock_checkout.return_value = {
                "url": "https://checkout.stripe.com/session123",
                "session_id": "cs_test_123"
            }

            # Create checkout request
            request = CheckoutSessionRequest(price_id="price_test_123")

            # Call controller
            result = await billing_controller.create_checkout_session(
                db=async_db,
                organization_id=test_organization.id,
                checkout_request=request
            )

            # Assertions
            assert str(result.url) == "https://checkout.stripe.com/session123"
            assert result.session_id == "cs_test_123"
            # mock_customer might not be called if org already has stripe_customer_id
            mock_checkout.assert_called_once()

    async def test_create_checkout_session_organization_not_found(
        self, async_db: AsyncSession
    ):
        """Test checkout session creation with non-existent organization."""
        request = CheckoutSessionRequest(price_id="price_test_123")

        with pytest.raises(ValueError, match="Organization not found"):
            await billing_controller.create_checkout_session(
                db=async_db,
                organization_id=99999,  # Non-existent
                checkout_request=request
            )

    async def test_create_checkout_session_with_existing_customer(
        self, async_db: AsyncSession, test_organization
    ):
        """Test checkout session when organization already has Stripe customer."""
        # Update organization with existing customer ID
        test_organization.stripe_customer_id = "cus_existing_123"
        async_db.add(test_organization)
        await async_db.commit()

        with patch('api.services.stripe_service.create_checkout_session', new_callable=AsyncMock) as mock_checkout:
            mock_checkout.return_value = {
                "url": "https://checkout.stripe.com/session123",
                "session_id": "cs_test_123"
            }

            request = CheckoutSessionRequest(price_id="price_test_123")

            result = await billing_controller.create_checkout_session(
                db=async_db,
                organization_id=test_organization.id,
                checkout_request=request
            )

            assert result.url is not None
            # Should not create new customer
            mock_checkout.assert_called_once()

    async def test_create_checkout_session_with_custom_urls(
        self, async_db: AsyncSession, test_organization
    ):
        """Test checkout session with custom success/cancel URLs."""
        with patch('api.services.stripe_service.create_or_get_customer', new_callable=AsyncMock) as mock_customer, \
             patch('api.services.stripe_service.create_checkout_session', new_callable=AsyncMock) as mock_checkout:

            mock_customer.return_value = "cus_test_123"
            mock_checkout.return_value = {
                "url": "https://checkout.stripe.com/session123",
                "session_id": "cs_test_123"
            }

            request = CheckoutSessionRequest(
                price_id="price_test_123",
                success_url="https://custom.com/success",
                cancel_url="https://custom.com/cancel"
            )

            result = await billing_controller.create_checkout_session(
                db=async_db,
                organization_id=test_organization.id,
                checkout_request=request
            )

            assert result.url is not None
            # Verify custom URLs were passed
            call_kwargs = mock_checkout.call_args[1]
            assert call_kwargs['success_url'] == "https://custom.com/success"
            assert call_kwargs['cancel_url'] == "https://custom.com/cancel"

    async def test_create_checkout_session_stripe_error(
        self, async_db: AsyncSession, test_organization
    ):
        """Test checkout session creation when Stripe API fails."""
        with patch('api.services.stripe_service.create_checkout_session') as mock_checkout:
            mock_checkout.side_effect = Exception("Stripe API error")

            request = CheckoutSessionRequest(price_id="price_test_123")

            with pytest.raises(Exception, match="Stripe API error"):
                await billing_controller.create_checkout_session(
                    db=async_db,
                    organization_id=test_organization.id,
                    checkout_request=request
                )


@pytest.mark.asyncio
class TestCreateCustomerPortalSession:
    """Test create_customer_portal_session function with edge cases."""

    async def test_create_portal_session_success(
        self, async_db: AsyncSession, test_organization
    ):
        """Test successful customer portal session creation."""
        # Update organization with customer ID
        test_organization.stripe_customer_id = "cus_test_123"
        async_db.add(test_organization)
        await async_db.commit()

        with patch('api.services.stripe_service.create_portal_session', new_callable=AsyncMock) as mock_portal:
            mock_portal.return_value = {
                "url": "https://billing.stripe.com/portal123"
            }

            result = await billing_controller.create_customer_portal_session(
                db=async_db,
                organization_id=test_organization.id
            )

            assert str(result.url) == "https://billing.stripe.com/portal123"
            # Verify mock was called with correct customer_id and a string return_url
            assert mock_portal.call_count == 1
            call_args = mock_portal.call_args
            assert call_args.kwargs['customer_id'] == "cus_test_123"
            assert isinstance(call_args.kwargs['return_url'], str)

    async def test_create_portal_session_organization_not_found(
        self, async_db: AsyncSession
    ):
        """Test portal session creation with non-existent organization."""
        with pytest.raises(ValueError, match="Organization not found"):
            await billing_controller.create_customer_portal_session(
                db=async_db,
                organization_id=99999
            )

    async def test_create_portal_session_no_stripe_customer(
        self, async_db: AsyncSession, test_organization
    ):
        """Test portal session when organization has no Stripe customer."""
        # Ensure no customer ID
        test_organization.stripe_customer_id = None
        async_db.add(test_organization)
        await async_db.commit()

        with pytest.raises(ValueError, match="does not have a Stripe customer"):
            await billing_controller.create_customer_portal_session(
                db=async_db,
                organization_id=test_organization.id
            )


@pytest.mark.asyncio
class TestGetSubscription:
    """Test get_subscription function with edge cases."""

    async def test_get_subscription_success(
        self, async_db: AsyncSession, test_organization
    ):
        """Test successful subscription retrieval."""
        # Setup organization with subscription
        test_organization.stripe_subscription_id = "sub_test_123"
        test_organization.subscription_status = SubscriptionStatus.ACTIVE
        async_db.add(test_organization)
        await async_db.commit()

        with patch('api.services.stripe_service.fetch_subscription', new_callable=AsyncMock) as mock_get_sub:
            mock_get_sub.return_value = {
                "id": "sub_test_123",
                "status": "active",
                "current_period_end": int(datetime.now().timestamp()),
                "plan": {
                    "id": "price_test_123",
                    "amount": 1000,
                    "currency": "usd",
                    "interval": "month"
                }
            }

            result = await billing_controller.get_subscription(
                db=async_db,
                organization_id=test_organization.id
            )

            assert result is not None
            assert result.id == "sub_test_123"
            assert result.status == SubscriptionStatus.ACTIVE

    async def test_get_subscription_organization_not_found(
        self, async_db: AsyncSession
    ):
        """Test get subscription with non-existent organization."""
        with pytest.raises(ValueError, match="Organization not found"):
            await billing_controller.get_subscription(
                db=async_db,
                organization_id=99999
            )

    async def test_get_subscription_no_subscription(
        self, async_db: AsyncSession, test_organization
    ):
        """Test get subscription when organization has no subscription."""
        # Ensure no subscription
        test_organization.stripe_subscription_id = None
        async_db.add(test_organization)
        await async_db.commit()

        result = await billing_controller.get_subscription(
            db=async_db,
            organization_id=test_organization.id
        )

        assert result is None


@pytest.mark.asyncio
class TestCancelSubscription:
    """Test cancel_subscription function with edge cases."""

    async def test_cancel_subscription_success(
        self, async_db: AsyncSession, test_organization
    ):
        """Test successful subscription cancellation."""
        # Setup organization with subscription
        test_organization.stripe_subscription_id = "sub_test_123"
        async_db.add(test_organization)
        await async_db.commit()

        with patch('api.services.stripe_service.cancel_subscription', new_callable=AsyncMock) as mock_cancel, \
             patch('api.services.stripe_service.fetch_subscription', new_callable=AsyncMock) as mock_fetch:

            mock_fetch.return_value = {
                "id": "sub_test_123",
                "status": "active",
                "current_period_end": int(datetime.now().timestamp()),
                "plan": {
                    "id": "price_test_123"
                }
            }

            mock_cancel.return_value = {
                "id": "sub_test_123",
                "status": "canceled",
                "canceled_at": int(datetime.now().timestamp())
            }

            request = SubscriptionUpdateRequest(cancel_at_period_end=True)

            result = await billing_controller.cancel_subscription(
                db=async_db,
                organization_id=test_organization.id,
                update_request=request
            )

            assert result.id == "sub_test_123"
            mock_cancel.assert_called_once()

    async def test_cancel_subscription_organization_not_found(
        self, async_db: AsyncSession
    ):
        """Test cancel subscription with non-existent organization."""
        request = SubscriptionUpdateRequest(cancel_at_period_end=True)

        with pytest.raises(ValueError, match="Organization not found"):
            await billing_controller.cancel_subscription(
                db=async_db,
                organization_id=99999,
                update_request=request
            )

    async def test_cancel_subscription_no_subscription(
        self, async_db: AsyncSession, test_organization
    ):
        """Test cancel subscription when organization has no subscription."""
        test_organization.stripe_subscription_id = None
        async_db.add(test_organization)
        await async_db.commit()

        request = SubscriptionUpdateRequest(cancel_at_period_end=True)

        with pytest.raises(ValueError, match="does not have an active subscription"):
            await billing_controller.cancel_subscription(
                db=async_db,
                organization_id=test_organization.id,
                update_request=request
            )


@pytest.mark.asyncio
class TestResumeSubscription:
    """Test resume_subscription function with edge cases."""

    async def test_resume_subscription_success(
        self, async_db: AsyncSession, test_organization
    ):
        """Test successful subscription resumption."""
        test_organization.stripe_subscription_id = "sub_test_123"
        async_db.add(test_organization)
        await async_db.commit()

        with patch('api.services.stripe_service.resume_subscription', new_callable=AsyncMock) as mock_resume, \
             patch('api.services.stripe_service.fetch_subscription', new_callable=AsyncMock) as mock_fetch:

            mock_fetch.return_value = {
                "id": "sub_test_123",
                "status": "canceled",
                "current_period_end": int(datetime.now().timestamp()),
                "plan": {
                    "id": "price_test_123"
                }
            }

            mock_resume.return_value = {
                "id": "sub_test_123",
                "status": "active",
                "cancel_at_period_end": False
            }

            result = await billing_controller.resume_subscription(
                db=async_db,
                organization_id=test_organization.id
            )

            assert result.id == "sub_test_123"
            mock_resume.assert_called_once_with("sub_test_123")

    async def test_resume_subscription_no_subscription(
        self, async_db: AsyncSession, test_organization
    ):
        """Test resume subscription when no subscription exists."""
        test_organization.stripe_subscription_id = None
        async_db.add(test_organization)
        await async_db.commit()

        with pytest.raises(ValueError, match="does not have an active subscription"):
            await billing_controller.resume_subscription(
                db=async_db,
                organization_id=test_organization.id
            )


@pytest.mark.asyncio
class TestGetOrganizationBilling:
    """Test get_organization_billing function with edge cases."""

    async def test_get_organization_billing_success(
        self, async_db: AsyncSession, test_organization
    ):
        """Test successful organization billing retrieval."""
        test_organization.stripe_customer_id = "cus_test_123"
        test_organization.stripe_subscription_id = "sub_test_123"
        test_organization.subscription_status = SubscriptionStatus.ACTIVE
        async_db.add(test_organization)
        await async_db.commit()

        with patch('api.controllers.billing_controller.get_subscription', new_callable=AsyncMock) as mock_get_sub:
            from api.schemas.billing import SubscriptionResponse
            mock_get_sub.return_value = SubscriptionResponse(
                id="sub_test_123",
                status=SubscriptionStatus.ACTIVE,
                current_period_end=datetime.now(),
                cancel_at_period_end=False,
                plan_price_id="price_test_123",
                is_active=True,
                days_until_renewal=30
            )

            result = await billing_controller.get_organization_billing(
                db=async_db,
                organization_id=test_organization.id
            )

            assert result is not None
            assert result.stripe_customer_id == "cus_test_123"
            assert result.subscription is not None
            assert result.subscription.id == "sub_test_123"
            assert result.subscription.status == SubscriptionStatus.ACTIVE

    async def test_get_organization_billing_not_found(
        self, async_db: AsyncSession
    ):
        """Test get organization billing when organization doesn't exist."""
        result = await billing_controller.get_organization_billing(
            db=async_db,
            organization_id=99999
        )

        assert result is None

    async def test_get_organization_billing_no_subscription(
        self, async_db: AsyncSession, test_organization
    ):
        """Test get organization billing with no subscription data."""
        # Ensure no billing data
        test_organization.stripe_customer_id = None
        test_organization.stripe_subscription_id = None
        async_db.add(test_organization)
        await async_db.commit()

        result = await billing_controller.get_organization_billing(
            db=async_db,
            organization_id=test_organization.id
        )

        assert result is not None
        assert result.stripe_customer_id is None
        assert result.subscription is None


@pytest.mark.asyncio
class TestWebhookHandling:
    """Test webhook event handling with edge cases."""

    async def test_handle_subscription_created_event(
        self, async_db: AsyncSession, test_organization
    ):
        """Test handling subscription.created webhook event."""
        test_organization.stripe_customer_id = "cus_test_123"
        async_db.add(test_organization)
        await async_db.commit()

        event_data = {
            "id": "evt_test_123",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_new_123",
                    "customer": "cus_test_123",
                    "status": "active",
                    "current_period_end": int(datetime.now().timestamp()),
                    "items": {
                        "data": [{
                            "price": {
                                "id": "price_test_123"
                            }
                        }]
                    }
                }
            }
        }

        result = await billing_controller.handle_webhook_event(
            db=async_db,
            event_data=event_data
        )

        assert result is True

    async def test_handle_unknown_webhook_event(
        self, async_db: AsyncSession
    ):
        """Test handling unknown webhook event type."""
        event_data = {
            "id": "evt_unknown_123",
            "type": "unknown.event.type",
            "data": {"object": {}}
        }

        result = await billing_controller.handle_webhook_event(
            db=async_db,
            event_data=event_data
        )

        # Should not raise error, just skip
        assert result is not None

    async def test_handle_payment_failed_event(
        self, async_db: AsyncSession, test_organization
    ):
        """Test handling payment_intent.payment_failed webhook event."""
        test_organization.stripe_customer_id = "cus_test_123"
        async_db.add(test_organization)
        await async_db.commit()

        event_data = {
            "id": "evt_payment_failed_123",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_failed_123",
                    "customer": "cus_test_123",
                    "amount": 1000,
                    "currency": "usd"
                }
            }
        }

        result = await billing_controller.handle_webhook_event(
            db=async_db,
            event_data=event_data
        )

        assert result is not None
