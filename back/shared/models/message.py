"""Message model for SMTPy v2."""

import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, Column
from sqlalchemy.orm import Mapped, relationship

from . import Domain
from .base import Base, TimestampMixin


class MessageStatus(enum.Enum):
    """Message processing status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"
    REJECTED = "REJECTED"


class Message(Base, TimestampMixin):
    """Email message model for tracking forwarded messages."""
    
    __tablename__ = "messages"
    
    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    
    # Message identifiers
    message_id: Mapped[str] = Column(
        String(255), nullable=False, unique=True, doc="Unique message ID"
    )
    thread_id: Mapped[Optional[str]] = Column(
        String(255), nullable=True, doc="Thread ID for message grouping"
    )
    
    # Domain relationship
    domain_id: Mapped[int] = Column(
        Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )
    
    # Email addresses
    sender_email: Mapped[str] = Column(
        String(320), nullable=False, doc="Original sender email address"
    )
    recipient_email: Mapped[str] = Column(
        String(320), nullable=False, doc="Original recipient email address"
    )
    forwarded_to: Mapped[Optional[str]] = Column(
        String(320), nullable=True, doc="Email address message was forwarded to"
    )
    
    # Message content
    subject: Mapped[Optional[str]] = Column(
        String(500), nullable=True, doc="Email subject line"
    )
    body_preview: Mapped[Optional[str]] = Column(
        Text, nullable=True, doc="Preview of email body content"
    )
    
    # Processing status
    status: Mapped[MessageStatus] = Column(
        Enum(MessageStatus), nullable=False, default=MessageStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = Column(
        Text, nullable=True, doc="Error message if processing failed"
    )
    
    # Message size and attachments
    size_bytes: Mapped[Optional[int]] = Column(
        Integer, nullable=True, doc="Message size in bytes"
    )
    has_attachments: Mapped[bool] = Column(
        Boolean, nullable=False, default=False, doc="Whether message has attachments"
    )
    
    # Relationships
    domain: Mapped["Domain"] = relationship("Domain", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, message_id='{self.message_id}', status='{self.status.value}')>"