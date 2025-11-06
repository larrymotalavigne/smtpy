"""SMTP Relay Service Module

Provides multiple email delivery options:
- Direct SMTP: Self-hosted delivery directly to recipient MX servers
- External Relay: Delivery via Gmail/SendGrid/etc
- Hybrid: Direct with relay fallback
"""

from .relay_service import (
    SMTPRelayService,
    EmailPriority,
    EmailJob,
    get_relay_service,
    send_email
)

from .direct_smtp import (
    DirectSMTPService,
    get_direct_smtp_service,
    send_direct
)

from .dkim_signer import (
    DKIMSigner,
    get_dkim_signer,
    sign_email as sign_email_dkim
)

from .hybrid_relay import (
    HybridRelayService,
    DeliveryMode,
    get_hybrid_relay,
    send_email_hybrid
)

__all__ = [
    # External relay (Gmail/SendGrid)
    'SMTPRelayService',
    'EmailPriority',
    'EmailJob',
    'get_relay_service',
    'send_email',

    # Direct SMTP (self-hosted)
    'DirectSMTPService',
    'get_direct_smtp_service',
    'send_direct',

    # DKIM signing
    'DKIMSigner',
    'get_dkim_signer',
    'sign_email_dkim',

    # Hybrid relay (recommended)
    'HybridRelayService',
    'DeliveryMode',
    'get_hybrid_relay',
    'send_email_hybrid',
]
