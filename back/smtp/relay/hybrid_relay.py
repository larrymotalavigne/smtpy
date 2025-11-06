"""
Hybrid SMTP Relay Service

Combines direct SMTP delivery with optional external relay fallback.

Strategy:
1. Try direct delivery first (self-hosted)
2. If direct delivery fails, optionally fall back to external relay (Gmail/SendGrid)
3. Sign all emails with DKIM before sending
"""

import asyncio
import logging
from email.message import EmailMessage
from typing import List, Dict, Optional
from enum import Enum

from .direct_smtp import get_direct_smtp_service, DirectSMTPService
from .relay_service import get_relay_service, SMTPRelayService, EmailPriority
from .dkim_signer import sign_email

from shared.core.config import SETTINGS

logger = logging.getLogger(__name__)


class DeliveryMode(Enum):
    """Email delivery mode"""
    DIRECT_ONLY = "direct"           # Only use direct SMTP
    RELAY_ONLY = "relay"             # Only use external relay
    HYBRID = "hybrid"                 # Try direct first, fallback to relay
    SMART = "smart"                   # Choose best method per recipient


class HybridRelayService:
    """
    Hybrid relay service that intelligently routes emails.

    Features:
    - Direct SMTP delivery (self-hosted, no external dependencies)
    - External relay fallback (Gmail/SendGrid for difficult deliveries)
    - DKIM signing for all outbound emails
    - Automatic mode selection
    - Comprehensive logging and statistics
    """

    def __init__(
        self,
        mode: DeliveryMode = DeliveryMode.DIRECT_ONLY,
        enable_dkim: bool = True
    ):
        """
        Initialize hybrid relay service.

        Args:
            mode: Delivery mode (direct/relay/hybrid/smart)
            enable_dkim: Enable DKIM signing
        """
        self.mode = mode
        self.enable_dkim = enable_dkim

        # Check if external relay is configured
        self.has_relay = bool(
            getattr(SETTINGS, 'SMTP_USER', None) and
            getattr(SETTINGS, 'SMTP_PASSWORD', None)
        )

        # Force direct-only if no relay configured
        if not self.has_relay and mode != DeliveryMode.DIRECT_ONLY:
            logger.warning(
                f"External relay not configured, forcing mode to DIRECT_ONLY "
                f"(was {mode.value})"
            )
            self.mode = DeliveryMode.DIRECT_ONLY

        # Services
        self._direct_service: Optional[DirectSMTPService] = None
        self._relay_service: Optional[SMTPRelayService] = None

        # Statistics
        self.stats = {
            "direct_sent": 0,
            "direct_failed": 0,
            "relay_sent": 0,
            "relay_failed": 0,
            "dkim_signed": 0,
            "dkim_unsigned": 0
        }

        logger.info(
            f"HybridRelayService initialized: mode={mode.value}, "
            f"dkim={enable_dkim}, has_relay={self.has_relay}"
        )

    def _get_direct_service(self) -> DirectSMTPService:
        """Get or create direct SMTP service"""
        if self._direct_service is None:
            self._direct_service = get_direct_smtp_service()
        return self._direct_service

    async def _get_relay_service(self) -> Optional[SMTPRelayService]:
        """Get or create relay service"""
        if not self.has_relay:
            return None

        if self._relay_service is None:
            self._relay_service = await get_relay_service()

        return self._relay_service

    async def _sign_message(
        self,
        message: EmailMessage,
        mail_from: str
    ) -> EmailMessage:
        """Sign message with DKIM if enabled"""
        if not self.enable_dkim:
            self.stats["dkim_unsigned"] += 1
            return message

        try:
            signed_message = await sign_email(message, mail_from)
            self.stats["dkim_signed"] += 1
            return signed_message
        except Exception as e:
            logger.error(f"DKIM signing failed: {e}")
            self.stats["dkim_unsigned"] += 1
            return message

    async def _send_direct(
        self,
        message: EmailMessage,
        recipients: List[str],
        mail_from: str
    ) -> Dict[str, bool]:
        """Send via direct SMTP"""
        service = self._get_direct_service()

        results = await service.send_email_bulk(message, recipients, mail_from)

        # Update statistics
        for recipient, success in results.items():
            if success:
                self.stats["direct_sent"] += 1
            else:
                self.stats["direct_failed"] += 1

        return results

    async def _send_relay(
        self,
        message: EmailMessage,
        recipients: List[str],
        mail_from: str,
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> Dict[str, bool]:
        """Send via external relay"""
        relay = await self._get_relay_service()
        if not relay:
            logger.error("Relay service not available")
            return {recipient: False for recipient in recipients}

        results = {}
        for recipient in recipients:
            success = await relay.send(message, [recipient], mail_from, priority)
            results[recipient] = success

            if success:
                self.stats["relay_sent"] += 1
            else:
                self.stats["relay_failed"] += 1

        return results

    async def send(
        self,
        message: EmailMessage,
        recipients: List[str],
        mail_from: str = "noreply@smtpy.fr",
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> Dict[str, bool]:
        """
        Send email using hybrid delivery strategy.

        Args:
            message: Email message to send
            recipients: List of recipient email addresses
            mail_from: Sender email address
            priority: Priority level (only used for relay mode)

        Returns:
            Dict mapping recipient email to delivery success status
        """
        if not recipients:
            return {}

        # Sign message with DKIM
        signed_message = await self._sign_message(message, mail_from)

        # Route based on mode
        if self.mode == DeliveryMode.DIRECT_ONLY:
            return await self._send_direct(signed_message, recipients, mail_from)

        elif self.mode == DeliveryMode.RELAY_ONLY:
            return await self._send_relay(signed_message, recipients, mail_from, priority)

        elif self.mode == DeliveryMode.HYBRID:
            # Try direct first
            results = await self._send_direct(signed_message, recipients, mail_from)

            # Find failed deliveries
            failed_recipients = [
                recipient for recipient, success in results.items()
                if not success
            ]

            if failed_recipients:
                logger.info(
                    f"Direct delivery failed for {len(failed_recipients)} recipients, "
                    f"trying relay fallback"
                )

                # Try relay for failed recipients
                relay_results = await self._send_relay(
                    signed_message,
                    failed_recipients,
                    mail_from,
                    priority
                )

                # Update results with relay attempts
                results.update(relay_results)

            return results

        elif self.mode == DeliveryMode.SMART:
            # Smart mode: analyze recipient domain and choose best method
            # For now, same as hybrid mode
            # Future: maintain reputation scores per domain, route accordingly
            return await self._send_relay(signed_message, recipients, mail_from, priority)

        else:
            logger.error(f"Unknown delivery mode: {self.mode}")
            return {recipient: False for recipient in recipients}

    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        stats = {**self.stats, "mode": self.mode.value}

        # Add direct service stats if available
        if self._direct_service:
            direct_stats = self._direct_service.get_stats()
            stats["direct_service"] = direct_stats

        # Add relay service stats if available
        if self._relay_service:
            relay_stats = self._relay_service.get_stats()
            stats["relay_service"] = relay_stats

        return stats


# Global instance
_hybrid_relay: Optional[HybridRelayService] = None


def get_hybrid_relay(
    mode: Optional[DeliveryMode] = None,
    enable_dkim: Optional[bool] = None
) -> HybridRelayService:
    """
    Get or create the global hybrid relay instance.

    Args:
        mode: Delivery mode (if not set, uses configuration or auto-detects)
        enable_dkim: Enable DKIM signing (if not set, uses configuration)

    Returns:
        HybridRelayService instance
    """
    global _hybrid_relay

    if _hybrid_relay is None:
        # Determine mode from configuration
        if mode is None:
            # Get mode from config
            mode_str = getattr(SETTINGS, 'SMTP_DELIVERY_MODE', 'direct').lower()

            # Map string to enum
            mode_map = {
                'direct': DeliveryMode.DIRECT_ONLY,
                'relay': DeliveryMode.RELAY_ONLY,
                'hybrid': DeliveryMode.HYBRID,
                'smart': DeliveryMode.SMART
            }

            mode = mode_map.get(mode_str, DeliveryMode.DIRECT_ONLY)

            # If mode requires relay but none configured, force DIRECT_ONLY
            has_relay = bool(
                getattr(SETTINGS, 'SMTP_USER', None) and
                getattr(SETTINGS, 'SMTP_PASSWORD', None)
            )

            if not has_relay and mode in [DeliveryMode.RELAY_ONLY, DeliveryMode.HYBRID, DeliveryMode.SMART]:
                logger.warning(
                    f"SMTP_DELIVERY_MODE is '{mode_str}' but no relay credentials configured. "
                    f"Forcing mode to 'direct'"
                )
                mode = DeliveryMode.DIRECT_ONLY

        # Get DKIM setting from config if not specified
        if enable_dkim is None:
            enable_dkim = getattr(SETTINGS, 'SMTP_ENABLE_DKIM', True)

        _hybrid_relay = HybridRelayService(mode=mode, enable_dkim=enable_dkim)

    return _hybrid_relay


async def send_email_hybrid(
    message: EmailMessage,
    recipients: List[str],
    mail_from: str = "noreply@smtpy.fr",
    priority: EmailPriority = EmailPriority.NORMAL
) -> Dict[str, bool]:
    """
    Convenience function to send email via hybrid relay.

    Args:
        message: Email message to send
        recipients: List of recipient email addresses
        mail_from: Sender email address
        priority: Priority level

    Returns:
        Dict mapping recipient to delivery success status
    """
    relay = get_hybrid_relay()
    return await relay.send(message, recipients, mail_from, priority)
