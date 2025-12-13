"""Security event model for tracking mail server security incidents."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, DateTime, Text, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class EventType(str, Enum):
    """Types of security events."""
    PREGREET_VIOLATION = "pregreet_violation"
    AUTH_FAILURE = "auth_failure"
    REJECTION = "rejection"
    DNSBL_HIT = "dnsbl_hit"
    SPAM_DETECTED = "spam_detected"
    MALWARE_DETECTED = "malware_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class EventSeverity(str, Enum):
    """Severity levels for security events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(Base, TimestampMixin):
    """Security event detected in mail server logs.

    Tracks security incidents like:
    - PREGREET violations (spam bots)
    - Failed authentication attempts
    - Email rejections
    - DNS blocklist hits
    - Spam/malware detections
    """

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Event identification
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of security event (pregreet_violation, auth_failure, etc.)"
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        default=EventSeverity.MEDIUM.value,
        doc="Severity level (low, medium, high, critical)"
    )

    # Source information
    ip_address: Mapped[str] = mapped_column(
        String(45),  # IPv6 max length
        nullable=False,
        index=True,
        doc="Source IP address of the event"
    )

    port: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Source port number if available"
    )

    # Event details
    service: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="postfix",
        doc="Service that generated the event (postfix, dovecot, rspamd, etc.)"
    )

    details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed description of the security event"
    )

    # Timestamp (when the event occurred in the logs, may differ from created_at)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When the event actually occurred"
    )

    # Action taken
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Action taken in response to the event (blocked, rate-limited, etc.)"
    )

    # Additional event metadata (JSON-serializable string)
    event_metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional event metadata as JSON string"
    )

    # Indexes for common queries
    __table_args__ = (
        Index('idx_security_events_timestamp', 'event_timestamp'),
        Index('idx_security_events_ip_type', 'ip_address', 'event_type'),
        Index('idx_security_events_severity_timestamp', 'severity', 'event_timestamp'),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "ip_address": self.ip_address,
            "port": self.port,
            "service": self.service,
            "details": self.details,
            "event_timestamp": self.event_timestamp.isoformat() if self.event_timestamp else None,
            "action_taken": self.action_taken,
            "event_metadata": self.event_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<SecurityEvent(id={self.id}, type={self.event_type}, "
            f"severity={self.severity}, ip={self.ip_address})>"
        )
