"""Organization model for SMTPy v2."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class SubscriptionStatus(enum.Enum):
    """Subscription status enum."""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class Organization(Base, TimestampMixin):
    """Organization model with billing integration."""
    
    __tablename__ = "organizations"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Organization details
    name: Mapped[str] = mapped_column(String(255), nullable=False, doc="Organization name")
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, doc="Organization primary email"
    )
    
    # Stripe billing integration
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, doc="Stripe customer ID"
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, doc="Stripe subscription ID"
    )
    subscription_status: Mapped[Optional[SubscriptionStatus]] = mapped_column(
        Enum(SubscriptionStatus), nullable=True, default=None, doc="Current subscription status"
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Current billing period end date"
    )
    plan_price_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Stripe price ID for current plan"
    )
    
    # Relationships
    domains: Mapped[list["Domain"]] = relationship(
        "Domain", back_populates="organization", lazy="selectin", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', email='{self.email}')>"