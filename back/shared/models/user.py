"""User model for SMTPy v2."""

import enum
import bcrypt
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Integer, String, DateTime, ForeignKey, Column
from sqlalchemy.orm import Mapped, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .organization import Organization


class UserRole(enum.Enum):
    """User role enum."""
    ADMIN = "admin"
    USER = "user"


class User(Base, TimestampMixin):
    """User model with authentication."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # User credentials
    username: Mapped[str] = Column(
        String(50), nullable=False, unique=True, index=True, doc="Unique username"
    )
    email: Mapped[str] = Column(
        String(320), nullable=False, unique=True, index=True, doc="User email address"
    )
    password_hash: Mapped[str] = Column(
        String(255), nullable=False, doc="Hashed password (bcrypt)"
    )

    # User status
    is_active: Mapped[bool] = Column(
        Boolean, nullable=False, default=True, doc="Is user account active"
    )
    is_verified: Mapped[bool] = Column(
        Boolean, nullable=False, default=False, doc="Is email verified"
    )
    role: Mapped[UserRole] = Column(
        Enum(UserRole), nullable=False, default=UserRole.USER, doc="User role"
    )

    # Organization relationship
    organization_id: Mapped[Optional[int]] = Column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated organization ID"
    )

    # Login tracking
    last_login: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True, doc="Last successful login timestamp"
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="users", lazy="selectin"
    )

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary for API responses."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "role": self.role.value,
            "organization_id": self.organization_id,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_sensitive:
            data["password_hash"] = self.password_hash

        return data


class PasswordResetToken(Base):
    """Password reset token model."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = Column(
        String(255), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = Column(
        DateTime(timezone=True), nullable=False, index=True
    )
    used: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")

    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        from datetime import datetime, timezone
        return not self.used and self.expires_at > datetime.now(timezone.utc)


class EmailVerificationToken(Base):
    """Email verification token model."""

    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = Column(
        String(255), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = Column(
        DateTime(timezone=True), nullable=False
    )
    used: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")

    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        from datetime import datetime, timezone
        return not self.used and self.expires_at > datetime.now(timezone.utc)
