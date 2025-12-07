"""API Key model for SMTPy v2."""

import bcrypt
import secrets
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, Column
from sqlalchemy.orm import Mapped, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class APIKey(Base, TimestampMixin):
    """API Key for programmatic access."""

    __tablename__ = "api_keys"

    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to user
    user_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User ID"
    )

    # API key details
    name: Mapped[str] = Column(
        String(100), nullable=False, doc="User-defined name for the key"
    )
    key_hash: Mapped[str] = Column(
        String(255), nullable=False, doc="Hashed API key (bcrypt)"
    )
    prefix: Mapped[str] = Column(
        String(16), nullable=False, index=True, doc="Key prefix for identification (e.g., smtpy_sk_abc12345)"
    )

    # Status and usage
    is_active: Mapped[bool] = Column(
        Boolean, nullable=False, default=True, doc="Is API key active"
    )
    last_used_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True, doc="Last time key was used"
    )

    # Expiration (optional)
    expires_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True, doc="Optional expiration timestamp"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys", lazy="selectin")

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """
        Generate a new API key.

        Returns:
            tuple: (full_key, key_hash, prefix)
                - full_key: The complete API key to return to user (only shown once)
                - key_hash: Bcrypt hash to store in database
                - prefix: First 16 chars for identification
        """
        # Generate random key: smtpy_sk_{32 random chars}
        random_part = secrets.token_urlsafe(32)
        full_key = f"smtpy_sk_{random_part}"

        # Extract prefix (first 16 chars including smtpy_sk_)
        prefix = full_key[:16]

        # Hash the full key
        salt = bcrypt.gensalt()
        key_hash = bcrypt.hashpw(full_key.encode('utf-8'), salt).decode('utf-8')

        return full_key, key_hash, prefix

    def verify_key(self, key: str) -> bool:
        """Verify an API key against the stored hash."""
        try:
            return bcrypt.checkpw(key.encode('utf-8'), self.key_hash.encode('utf-8'))
        except Exception:
            return False

    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)."""
        if not self.is_active:
            return False

        if self.expires_at:
            from datetime import timezone
            return self.expires_at > datetime.now(timezone.utc)

        return True

    def to_dict(self, include_key: bool = False) -> dict:
        """Convert API key to dictionary for API responses."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "prefix": self.prefix,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Never include the full key or hash in normal responses
        # The full key is only returned once during creation

        return data
