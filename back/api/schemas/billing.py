"""Billing schemas for SMTPy v2."""

from datetime import datetime
from typing import Optional

from pydantic import Field, HttpUrl

from ..models.organization import SubscriptionStatus
from .common import BaseSchema


class CheckoutSessionRequest(BaseSchema):
    """Schema for creating checkout session."""
    
    price_id: str = Field(..., description="Stripe price ID")
    success_url: Optional[HttpUrl] = Field(None, description="Success URL override")
    cancel_url: Optional[HttpUrl] = Field(None, description="Cancel URL override")


class CheckoutSessionResponse(BaseSchema):
    """Schema for checkout session response."""
    
    url: HttpUrl = Field(..., description="Stripe checkout session URL")
    session_id: str = Field(..., description="Stripe checkout session ID")


class CustomerPortalResponse(BaseSchema):
    """Schema for customer portal response."""
    
    url: HttpUrl = Field(..., description="Stripe customer portal URL")


class SubscriptionResponse(BaseSchema):
    """Schema for subscription details."""
    
    id: Optional[str] = Field(None, description="Stripe subscription ID")
    status: Optional[SubscriptionStatus] = Field(None, description="Subscription status")
    current_period_end: Optional[datetime] = Field(None, description="Current period end date")
    plan_price_id: Optional[str] = Field(None, description="Current plan price ID")
    cancel_at_period_end: bool = Field(default=False, description="Whether subscription will cancel at period end")
    
    # Computed fields
    is_active: bool = Field(..., description="Whether subscription is currently active")
    days_until_renewal: Optional[int] = Field(None, description="Days until next renewal")
    
    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIALING if self.status else False
    
    @property
    def needs_payment(self) -> bool:
        """Check if subscription needs payment attention."""
        return self.status in [
            SubscriptionStatus.PAST_DUE, 
            SubscriptionStatus.UNPAID,
            SubscriptionStatus.INCOMPLETE
        ] if self.status else False


class SubscriptionUpdateRequest(BaseSchema):
    """Schema for subscription update requests."""
    
    cancel_at_period_end: Optional[bool] = Field(None, description="Cancel subscription at period end")


class WebhookEventRequest(BaseSchema):
    """Schema for Stripe webhook event."""
    
    # This will be validated by Stripe's signature verification
    # The actual event data will be extracted from the raw request
    pass


class BillingStats(BaseSchema):
    """Schema for billing statistics."""
    
    total_revenue: float = Field(..., description="Total revenue")
    active_subscriptions: int = Field(..., description="Number of active subscriptions")
    trial_subscriptions: int = Field(..., description="Number of trial subscriptions")
    canceled_subscriptions: int = Field(..., description="Number of canceled subscriptions")
    mrr: float = Field(..., description="Monthly recurring revenue")
    
    
class PlanInfo(BaseSchema):
    """Schema for plan information."""
    
    price_id: str = Field(..., description="Stripe price ID")
    name: str = Field(..., description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    amount: int = Field(..., description="Plan amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    interval: str = Field(..., description="Billing interval (month, year)")
    features: list[str] = Field(default_factory=list, description="Plan features list")


class OrganizationBilling(BaseSchema):
    """Schema for organization billing information."""
    
    organization_id: int = Field(..., description="Organization ID")
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    subscription: Optional[SubscriptionResponse] = Field(None, description="Current subscription")
    billing_email: str = Field(..., description="Billing email address")
    
    # Usage information
    domains_count: int = Field(..., description="Number of domains")
    messages_count: int = Field(..., description="Number of messages this month")
    
    # Plan limits (if applicable)
    plan_domain_limit: Optional[int] = Field(None, description="Plan domain limit")
    plan_message_limit: Optional[int] = Field(None, description="Plan message limit")
    
    @property
    def approaching_limits(self) -> bool:
        """Check if organization is approaching plan limits."""
        if self.plan_domain_limit and self.domains_count >= self.plan_domain_limit * 0.8:
            return True
        if self.plan_message_limit and self.messages_count >= self.plan_message_limit * 0.8:
            return True
        return False