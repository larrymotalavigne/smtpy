"""Event models for SMTPy v2."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class EventType(enum.Enum):
    """System event types."""
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    DOMAIN_CREATED = "domain_created"
    DOMAIN_VERIFIED = "domain_verified"
    DOMAIN_DELETED = "domain_deleted"
    MESSAGE_FORWARDED = "message_forwarded"
    MESSAGE_BOUNCED = "message_bounced"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"


class Event(Base, TimestampMixin):
    """System event tracking model."""
    
    __tablename__ = "events"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Event details
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType), nullable=False, doc="Type of event"
    )
    event_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="JSON data associated with the event"
    )
    
    # Organization relationship (optional)
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True
    )
    
    # Additional metadata
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="User identifier if applicable"
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Resource identifier (domain ID, message ID, etc.)"
    )
    
    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type='{self.event_type.value}', org_id={self.organization_id})>"


class BillingWebhookEvent(Base):
    """Stripe webhook event deduplication table."""
    
    __tablename__ = "billing_webhook_events"
    
    # Primary key - using Stripe event ID
    event_id: Mapped[str] = mapped_column(
        String(255), primary_key=True, doc="Stripe event ID"
    )
    
    # Timestamp
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        nullable=False,
        doc="When webhook was received"
    )
    
    # Event metadata
    event_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Stripe event type"
    )
    processed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="Whether event was processed successfully"
    )
    
    def __repr__(self) -> str:
        return f"<BillingWebhookEvent(event_id='{self.event_id}', type='{self.event_type}')>"