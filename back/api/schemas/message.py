"""Message schemas for SMTPy v2."""

from typing import Optional

from pydantic import Field

from shared.models.message import MessageStatus
from .common import BaseSchema, TimestampSchema


class MessageResponse(TimestampSchema):
    """Schema for message response."""
    
    id: int = Field(..., description="Message ID")
    message_id: str = Field(..., description="Unique message ID")
    thread_id: Optional[str] = Field(None, description="Thread ID for message grouping")
    
    # Domain relationship
    domain_id: int = Field(..., description="Domain ID")
    
    # Email addresses
    sender_email: str = Field(..., description="Original sender email address")
    recipient_email: str = Field(..., description="Original recipient email address")
    forwarded_to: Optional[str] = Field(None, description="Email address message was forwarded to")
    
    # Message content
    subject: Optional[str] = Field(None, description="Email subject line")
    body_preview: Optional[str] = Field(None, description="Preview of email body content")
    
    # Processing status
    status: MessageStatus = Field(..., description="Message processing status")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    
    # Message size and attachments
    size_bytes: Optional[int] = Field(None, description="Message size in bytes")
    has_attachments: bool = Field(..., description="Whether message has attachments")


class MessageList(TimestampSchema):
    """Schema for message list response."""
    
    id: int = Field(..., description="Message ID")
    message_id: str = Field(..., description="Unique message ID")
    sender_email: str = Field(..., description="Original sender email address")
    recipient_email: str = Field(..., description="Original recipient email address")
    subject: Optional[str] = Field(None, description="Email subject line")
    status: MessageStatus = Field(..., description="Message processing status")
    size_bytes: Optional[int] = Field(None, description="Message size in bytes")
    has_attachments: bool = Field(..., description="Whether message has attachments")


class MessageStats(BaseSchema):
    """Schema for message statistics."""
    
    total_messages: int = Field(..., description="Total number of messages")
    delivered_messages: int = Field(..., description="Number of delivered messages")
    failed_messages: int = Field(..., description="Number of failed messages")
    pending_messages: int = Field(..., description="Number of pending messages")
    total_size_bytes: int = Field(..., description="Total size of all messages in bytes")
    
    @property
    def delivery_rate(self) -> float:
        """Calculate delivery rate as percentage."""
        if self.total_messages == 0:
            return 0.0
        return (self.delivered_messages / self.total_messages) * 100


class MessageFilter(BaseSchema):
    """Schema for message filtering parameters."""
    
    domain_id: Optional[int] = Field(None, description="Filter by domain ID")
    status: Optional[MessageStatus] = Field(None, description="Filter by message status")
    sender_email: Optional[str] = Field(None, description="Filter by sender email")
    recipient_email: Optional[str] = Field(None, description="Filter by recipient email")
    has_attachments: Optional[bool] = Field(None, description="Filter by attachment presence")
    date_from: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")