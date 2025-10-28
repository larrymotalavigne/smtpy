"""Billing database operations for SMTPy v2."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.organization import Organization, SubscriptionStatus
from shared.models.event import BillingWebhookEvent


async def get_organization_by_id(db: AsyncSession, organization_id: int) -> Optional[Organization]:
    """Get organization by ID with billing information."""
    stmt = (
        select(Organization)
        .where(Organization.id == organization_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_organization_by_stripe_customer_id(
    db: AsyncSession, 
    stripe_customer_id: str
) -> Optional[Organization]:
    """Get organization by Stripe customer ID."""
    stmt = (
        select(Organization)
        .where(Organization.stripe_customer_id == stripe_customer_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_organization_by_stripe_subscription_id(
    db: AsyncSession, 
    stripe_subscription_id: str
) -> Optional[Organization]:
    """Get organization by Stripe subscription ID."""
    stmt = (
        select(Organization)
        .where(Organization.stripe_subscription_id == stripe_subscription_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_organization_stripe_customer(
    db: AsyncSession,
    organization_id: int,
    stripe_customer_id: str
) -> Optional[Organization]:
    """Update organization with Stripe customer ID."""
    stmt = (
        update(Organization)
        .where(Organization.id == organization_id)
        .values(stripe_customer_id=stripe_customer_id)
        .returning(Organization)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_org = result.scalar_one_or_none()
    if updated_org:
        await db.refresh(updated_org)
    return updated_org


async def update_organization_subscription(
    db: AsyncSession,
    organization_id: int,
    stripe_subscription_id: str,
    subscription_status: SubscriptionStatus,
    current_period_end: datetime,
    plan_price_id: str
) -> Optional[Organization]:
    """Update organization subscription information."""
    stmt = (
        update(Organization)
        .where(Organization.id == organization_id)
        .values(
            stripe_subscription_id=stripe_subscription_id,
            subscription_status=subscription_status,
            current_period_end=current_period_end,
            plan_price_id=plan_price_id
        )
        .returning(Organization)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_org = result.scalar_one_or_none()
    if updated_org:
        await db.refresh(updated_org)
    return updated_org


async def update_subscription_status(
    db: AsyncSession,
    stripe_subscription_id: str,
    subscription_status: SubscriptionStatus,
    current_period_end: Optional[datetime] = None
) -> Optional[Organization]:
    """Update subscription status and period end."""
    updates = {"subscription_status": subscription_status}
    if current_period_end:
        updates["current_period_end"] = current_period_end
    
    stmt = (
        update(Organization)
        .where(Organization.stripe_subscription_id == stripe_subscription_id)
        .values(**updates)
        .returning(Organization)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_org = result.scalar_one_or_none()
    if updated_org:
        await db.refresh(updated_org)
    return updated_org


async def clear_subscription_data(
    db: AsyncSession,
    organization_id: int
) -> Optional[Organization]:
    """Clear subscription data for an organization."""
    stmt = (
        update(Organization)
        .where(Organization.id == organization_id)
        .values(
            stripe_subscription_id=None,
            subscription_status=None,
            current_period_end=None,
            plan_price_id=None
        )
        .returning(Organization)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_org = result.scalar_one_or_none()
    if updated_org:
        await db.refresh(updated_org)
    return updated_org


async def create_webhook_event(
    db: AsyncSession,
    event_id: str,
    event_type: str
) -> BillingWebhookEvent:
    """Create a webhook event record for deduplication."""
    webhook_event = BillingWebhookEvent(
        event_id=event_id,
        event_type=event_type
    )
    db.add(webhook_event)
    await db.commit()
    await db.refresh(webhook_event)
    return webhook_event


async def get_webhook_event(
    db: AsyncSession,
    event_id: str
) -> Optional[BillingWebhookEvent]:
    """Check if webhook event already exists."""
    stmt = (
        select(BillingWebhookEvent)
        .where(BillingWebhookEvent.event_id == event_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def mark_webhook_event_processed(
    db: AsyncSession,
    event_id: str
) -> Optional[BillingWebhookEvent]:
    """Mark webhook event as successfully processed."""
    stmt = (
        update(BillingWebhookEvent)
        .where(BillingWebhookEvent.event_id == event_id)
        .values(processed=True)
        .returning(BillingWebhookEvent)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


async def get_active_subscriptions_count(db: AsyncSession) -> int:
    """Get count of organizations with active subscriptions."""
    stmt = (
        select(func.count(Organization.id))
        .where(
            Organization.subscription_status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_subscriptions_by_status(
    db: AsyncSession,
    status: SubscriptionStatus
) -> list[Organization]:
    """Get organizations by subscription status."""
    stmt = (
        select(Organization)
        .where(Organization.subscription_status == status)
        .order_by(Organization.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_organizations_with_expiring_subscriptions(
    db: AsyncSession,
    before_date: datetime
) -> list[Organization]:
    """Get organizations with subscriptions expiring before a given date."""
    stmt = (
        select(Organization)
        .where(
            Organization.current_period_end <= before_date,
            Organization.subscription_status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        )
        .order_by(Organization.current_period_end.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_domains_for_organization(db: AsyncSession, organization_id: int) -> int:
    """Count domains for billing usage tracking."""
    from shared.models.domain import Domain
    
    stmt = (
        select(func.count(Domain.id))
        .where(Domain.organization_id == organization_id)
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def count_messages_for_organization(
    db: AsyncSession, 
    organization_id: int,
    since_date: Optional[datetime] = None
) -> int:
    """Count messages for billing usage tracking."""
    from shared.models.message import Message
    from shared.models.domain import Domain
    
    stmt = (
        select(func.count(Message.id))
        .join(Domain, Message.domain_id == Domain.id)
        .where(Domain.organization_id == organization_id)
    )
    
    if since_date:
        stmt = stmt.where(Message.created_at >= since_date)
    
    result = await db.execute(stmt)
    return result.scalar() or 0