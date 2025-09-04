"""Domain model for SMTPy v2."""

import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class DomainStatus(enum.Enum):
    """Domain verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class Domain(Base, TimestampMixin):
    """Domain model for email forwarding."""
    
    __tablename__ = "domains"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Domain details
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, doc="Domain name (e.g., example.com)"
    )
    
    # Organization relationship
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    
    # Verification status
    status: Mapped[DomainStatus] = mapped_column(
        Enum(DomainStatus), nullable=False, default=DomainStatus.PENDING
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, doc="Whether domain is active for forwarding"
    )
    
    # DNS records for verification
    mx_record_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="MX record verification status"
    )
    spf_record_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="SPF record verification status"
    )
    dkim_record_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="DKIM record verification status"
    )
    dmarc_record_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="DMARC record verification status"
    )
    
    # DNS record values (for reference)
    dkim_public_key: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="DKIM public key for verification"
    )
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Domain verification token"
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="domains", lazy="selectin"
    )
    
    @property
    def is_fully_verified(self) -> bool:
        """Check if all DNS records are verified."""
        return (
            self.mx_record_verified and 
            self.spf_record_verified and 
            self.dkim_record_verified and 
            self.dmarc_record_verified
        )
    
    def __repr__(self) -> str:
        return f"<Domain(id={self.id}, name='{self.name}', status='{self.status.value}')>"