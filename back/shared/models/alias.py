"""Alias model for email forwarding."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from .base import Base, TimestampMixin


class Alias(Base, TimestampMixin):
    """Email alias model for forwarding emails to target addresses."""

    __tablename__ = "aliases"

    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # Domain relationship
    domain_id: Mapped[int] = Column(
        Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )

    # Alias details
    local_part: Mapped[str] = Column(
        String(255), nullable=False, doc="Local part of the email (before @)"
    )

    # Target addresses (comma-separated)
    targets: Mapped[str] = Column(
        Text, nullable=False, doc="Comma-separated list of target email addresses"
    )

    # Status flags
    is_deleted: Mapped[bool] = Column(Boolean, nullable=False, default=False)

    # Expiration
    expires_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True, doc="Optional expiration timestamp"
    )

    # Relationships
    domain: Mapped["Domain"] = relationship("Domain", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Alias(id={self.id}, local_part='{self.local_part}', domain_id={self.domain_id})>"
