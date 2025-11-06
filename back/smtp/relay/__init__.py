"""SMTP Relay Service Module"""

from .relay_service import (
    SMTPRelayService,
    EmailPriority,
    EmailJob,
    get_relay_service,
    send_email
)

__all__ = [
    'SMTPRelayService',
    'EmailPriority',
    'EmailJob',
    'get_relay_service',
    'send_email'
]
