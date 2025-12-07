"""User preferences model for SMTPy v2."""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, String, Integer, ForeignKey, Column
from sqlalchemy.orm import Mapped, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class UserPreferences(Base, TimestampMixin):
    """User notification and UI preferences."""

    __tablename__ = "user_preferences"

    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to user (one-to-one relationship)
    user_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="User ID"
    )

    # Email notification preferences
    email_on_new_message: Mapped[bool] = Column(
        Boolean, nullable=False, default=True, doc="Send email on new message received"
    )
    email_on_domain_verified: Mapped[bool] = Column(
        Boolean, nullable=False, default=True, doc="Send email on domain verification"
    )
    email_on_quota_warning: Mapped[bool] = Column(
        Boolean, nullable=False, default=True, doc="Send email when quota reaches 80%"
    )
    email_weekly_summary: Mapped[bool] = Column(
        Boolean, nullable=False, default=False, doc="Send weekly activity summary"
    )

    # UI preferences
    theme: Mapped[str] = Column(
        String(20), nullable=False, default="light", doc="UI theme (light/dark/auto)"
    )
    language: Mapped[str] = Column(
        String(10), nullable=False, default="en", doc="Preferred language code"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences", lazy="selectin")

    def to_dict(self) -> dict:
        """Convert preferences to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_on_new_message": self.email_on_new_message,
            "email_on_domain_verified": self.email_on_domain_verified,
            "email_on_quota_warning": self.email_on_quota_warning,
            "email_weekly_summary": self.email_weekly_summary,
            "theme": self.theme,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
