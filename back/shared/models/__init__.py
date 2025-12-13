"""Models package for SMTPy v2."""

from .base import Base, TimestampMixin
from .organization import Organization
from .user import User, UserRole, PasswordResetToken, EmailVerificationToken
from .user_preferences import UserPreferences
from .api_key import APIKey
from .session import Session
from .domain import Domain
from .message import Message, MessageStatus
from .event import Event
from .alias import Alias
from .activity_log import ActivityLog
from .forwarding_rule import ForwardingRule, RuleConditionType, RuleActionType
from .security_event import SecurityEvent, EventType, EventSeverity

__all__ = [
    "Base",
    "TimestampMixin",
    "Organization",
    "User",
    "UserRole",
    "PasswordResetToken",
    "EmailVerificationToken",
    "UserPreferences",
    "APIKey",
    "Session",
    "Domain",
    "Message",
    "MessageStatus",
    "Event",
    "Alias",
    "ActivityLog",
    "ForwardingRule",
    "RuleConditionType",
    "RuleActionType",
    "SecurityEvent",
    "EventType",
    "EventSeverity",
]
