"""Session tracking model for SMTPy v2."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any

from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, Column, JSON
from sqlalchemy.orm import Mapped, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Session(Base, TimestampMixin):
    """User session tracking for security and management."""

    __tablename__ = "sessions"

    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to user
    user_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User ID"
    )

    # Session details
    session_token: Mapped[str] = Column(
        String(255), nullable=False, unique=True, index=True, doc="Session token (hashed cookie value)"
    )

    # Device and location info
    device_info: Mapped[Optional[dict[str, Any]]] = Column(
        JSON, nullable=True, doc="Device information (browser, OS, etc.)"
    )
    ip_address: Mapped[Optional[str]] = Column(
        String(45), nullable=True, doc="IP address (supports IPv4 and IPv6)"
    )
    location: Mapped[Optional[str]] = Column(
        String(255), nullable=True, doc="Approximate location (city, country)"
    )

    # Activity tracking
    last_activity_at: Mapped[datetime] = Column(
        DateTime(timezone=True), nullable=False, doc="Last request timestamp"
    )

    # Expiration
    expires_at: Mapped[datetime] = Column(
        DateTime(timezone=True), nullable=False, doc="Session expiration timestamp"
    )

    # Status
    is_active: Mapped[bool] = Column(
        Boolean, nullable=False, default=True, doc="Is session active"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions", lazy="selectin")

    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)."""
        if not self.is_active:
            return False

        from datetime import timezone
        return self.expires_at > datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert session to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_info": self.device_info,
            "ip_address": self.ip_address,
            "location": self.location,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
