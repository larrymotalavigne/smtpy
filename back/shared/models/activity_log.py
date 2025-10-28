"""ActivityLog model for tracking email forwarding activity."""

from sqlalchemy import Column, Integer, String, Text

from .base import Base, TimestampMixin


class ActivityLog(Base, TimestampMixin):
    """Activity log model for tracking email forwarding events."""

    __tablename__ = "activity_logs"

    # Primary key
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # Event details
    event_type: str = Column(
        String(50), nullable=False, doc="Type of event (forward, bounce, error, etc.)"
    )

    # Email details
    sender: str = Column(String(255), nullable=False, doc="Sender email address")
    recipient: str = Column(String(255), nullable=False, doc="Recipient email address")
    subject: str = Column(String(500), nullable=False, doc="Email subject")

    # Status
    status: str = Column(
        String(50), nullable=False, doc="Status of the event (success, failed, etc.)"
    )

    # Additional information
    message: str = Column(Text, nullable=True, doc="Additional message or error details")

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, event_type='{self.event_type}', status='{self.status}')>"
