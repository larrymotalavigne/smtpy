"""Forwarding rule model for conditional email forwarding."""

import enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .alias import Alias


class RuleConditionType(enum.Enum):
    """Type of condition to evaluate."""
    SENDER_CONTAINS = "SENDER_CONTAINS"
    SENDER_EQUALS = "SENDER_EQUALS"
    SENDER_DOMAIN = "SENDER_DOMAIN"
    SUBJECT_CONTAINS = "SUBJECT_CONTAINS"
    SUBJECT_EQUALS = "SUBJECT_EQUALS"
    SIZE_GREATER_THAN = "SIZE_GREATER_THAN"
    SIZE_LESS_THAN = "SIZE_LESS_THAN"
    HAS_ATTACHMENTS = "HAS_ATTACHMENTS"


class RuleActionType(enum.Enum):
    """Action to take when condition matches."""
    FORWARD = "FORWARD"  # Forward to different address
    BLOCK = "BLOCK"      # Reject the email
    REDIRECT = "REDIRECT"  # Forward to alternative address(es)


class ForwardingRule(Base, TimestampMixin):
    """Conditional forwarding rules for aliases."""

    __tablename__ = "forwarding_rules"

    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # Alias relationship
    alias_id: Mapped[int] = Column(
        Integer, ForeignKey("aliases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Rule ordering (lower priority = evaluated first)
    priority: Mapped[int] = Column(
        Integer, nullable=False, default=100, doc="Rule evaluation order (lower = first)"
    )

    # Rule name/description
    name: Mapped[str] = Column(
        String(255), nullable=False, doc="User-friendly rule name"
    )
    description: Mapped[Optional[str]] = Column(
        Text, nullable=True, doc="Optional rule description"
    )

    # Condition
    condition_type: Mapped[RuleConditionType] = Column(
        Enum(RuleConditionType), nullable=False, doc="Type of condition to evaluate"
    )
    condition_value: Mapped[str] = Column(
        Text, nullable=False, doc="Value to match against (e.g., 'example.com', 'spam', '1048576')"
    )

    # Action
    action_type: Mapped[RuleActionType] = Column(
        Enum(RuleActionType), nullable=False, doc="Action to take when condition matches"
    )
    action_value: Mapped[Optional[str]] = Column(
        Text, nullable=True, doc="Email address(es) for FORWARD/REDIRECT actions (comma-separated)"
    )

    # Status
    is_active: Mapped[bool] = Column(
        Boolean, nullable=False, default=True, doc="Whether rule is active"
    )

    # Statistics
    match_count: Mapped[int] = Column(
        Integer, nullable=False, default=0, doc="Number of times rule has matched"
    )

    # Relationships
    alias: Mapped["Alias"] = relationship("Alias", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ForwardingRule(id={self.id}, name='{self.name}', alias_id={self.alias_id})>"

    def to_dict(self) -> dict:
        """Convert rule to dictionary for API responses."""
        return {
            "id": self.id,
            "alias_id": self.alias_id,
            "priority": self.priority,
            "name": self.name,
            "description": self.description,
            "condition_type": self.condition_type.value,
            "condition_value": self.condition_value,
            "action_type": self.action_type.value,
            "action_value": self.action_value,
            "is_active": self.is_active,
            "match_count": self.match_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
