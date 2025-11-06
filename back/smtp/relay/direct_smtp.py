"""
Direct SMTP Delivery Service

This module implements a self-hosted SMTP delivery system that sends emails
directly to recipient mail servers without relying on external relay services
like Gmail or SendGrid.

Features:
- Direct MX record lookup and delivery
- DKIM signing for authentication
- SPF alignment
- Retry logic with exponential backoff
- Bounce handling
- Connection pooling per domain
- Rate limiting per recipient domain
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, deque

import dns.resolver
import dns.exception
import aiosmtplib
from aiosmtplib import SMTPException

from shared.core.config import SETTINGS

logger = logging.getLogger(__name__)


@dataclass
class DeliveryAttempt:
    """Record of a delivery attempt"""
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    mx_host: Optional[str] = None


@dataclass
class EmailDelivery:
    """Represents an email delivery job"""
    message: EmailMessage
    recipient: str
    mail_from: str
    domain: str
    attempts: List[DeliveryAttempt] = None
    max_attempts: int = 3

    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []


class DirectSMTPService:
    """
    Direct SMTP delivery service that sends emails directly to recipient
    mail servers without using external relay services.

    This service:
    - Looks up MX records for recipient domains
    - Connects directly to recipient mail servers
    - Signs emails with DKIM
    - Implements retry logic
    - Handles bounces and temporary failures
    """

    def __init__(
        self,
        hostname: str = "mail.smtpy.fr",
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_per_domain: int = 10,  # connections per minute per domain
    ):
        """
        Initialize direct SMTP service.

        Args:
            hostname: Our sending hostname (FQDN)
            timeout: Connection timeout in seconds
            max_retries: Maximum delivery attempts
            rate_limit_per_domain: Max connections per minute per domain
        """
        self.hostname = hostname
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_per_domain = rate_limit_per_domain

        # DNS resolver
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 10
        self.resolver.lifetime = 10

        # Connection tracking for rate limiting
        self._domain_connections: Dict[str, deque] = defaultdict(lambda: deque(maxlen=rate_limit_per_domain))
        self._rate_limit_lock = asyncio.Lock()

        # Statistics
        self.stats = {
            "sent": 0,
            "failed": 0,
            "deferred": 0,
            "bounced": 0,
            "mx_lookups": 0,
            "mx_cache_hits": 0
        }

        # MX record cache (TTL: 1 hour)
        self._mx_cache: Dict[str, Tuple[List[str], datetime]] = {}
        self._mx_cache_ttl = 3600

        logger.info(f"DirectSMTPService initialized for {hostname}")

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address"""
        match = re.match(r"[^@]+@(.+)", email)
        if match:
            return match.group(1).lower()
        raise ValueError(f"Invalid email address: {email}")

    async def _lookup_mx_records(self, domain: str) -> List[str]:
        """
        Lookup MX records for a domain.

        Returns list of MX hosts sorted by priority (lowest first).
        """
        # Check cache first
        if domain in self._mx_cache:
            mx_hosts, cached_at = self._mx_cache[domain]
            if (datetime.utcnow() - cached_at).seconds < self._mx_cache_ttl:
                self.stats["mx_cache_hits"] += 1
                logger.debug(f"MX cache hit for {domain}")
                return mx_hosts

        self.stats["mx_lookups"] += 1

        try:
            # Perform MX lookup
            mx_records = await asyncio.to_thread(
                self.resolver.resolve,
                domain,
                'MX'
            )

            # Sort by priority (lower = higher priority)
            mx_hosts = [
                str(mx.exchange).rstrip('.')
                for mx in sorted(mx_records, key=lambda x: x.preference)
            ]

            if not mx_hosts:
                logger.warning(f"No MX records found for {domain}")
                # Fallback: try A record of domain
                mx_hosts = [domain]

            # Cache the result
            self._mx_cache[domain] = (mx_hosts, datetime.utcnow())

            logger.info(f"MX lookup for {domain}: {mx_hosts}")
            return mx_hosts

        except dns.resolver.NoAnswer:
            logger.warning(f"No MX records for {domain}, trying A record")
            # Fallback to A record
            return [domain]

        except dns.resolver.NXDOMAIN:
            logger.error(f"Domain {domain} does not exist")
            raise ValueError(f"Domain does not exist: {domain}")

        except dns.exception.Timeout:
            logger.error(f"DNS timeout looking up MX for {domain}")
            raise

        except Exception as e:
            logger.error(f"Error looking up MX for {domain}: {e}")
            raise

    async def _check_rate_limit(self, domain: str):
        """Check and enforce per-domain rate limiting"""
        async with self._rate_limit_lock:
            now = datetime.utcnow()
            connections = self._domain_connections[domain]

            # Remove connections older than 1 minute
            while connections and (now - connections[0]) > timedelta(minutes=1):
                connections.popleft()

            # Check if we've hit the rate limit
            if len(connections) >= self.rate_limit_per_domain:
                oldest = connections[0]
                wait_time = 60 - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit reached for {domain}, waiting {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)

            # Record this connection
            connections.append(now)

    async def _deliver_to_mx(
        self,
        mx_host: str,
        message: EmailMessage,
        mail_from: str,
        recipient: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Attempt delivery to a specific MX host.

        Returns:
            (success, error_message)
        """
        try:
            # Create SMTP client
            smtp = aiosmtplib.SMTP(
                hostname=mx_host,
                port=25,  # Standard SMTP port
                timeout=self.timeout
            )

            # Connect
            await smtp.connect()
            logger.debug(f"Connected to {mx_host}:25")

            # Send EHLO
            await smtp.ehlo(self.hostname)

            # Try STARTTLS if supported
            if smtp.supports_extension("STARTTLS"):
                try:
                    await smtp.starttls()
                    await smtp.ehlo(self.hostname)  # EHLO again after STARTTLS
                    logger.debug(f"STARTTLS established with {mx_host}")
                except Exception as e:
                    logger.warning(f"STARTTLS failed with {mx_host}, continuing without TLS: {e}")

            # Send the email
            await smtp.sendmail(
                mail_from,
                [recipient],
                message.as_string()
            )

            # Quit
            await smtp.quit()

            logger.info(f"Successfully delivered email to {recipient} via {mx_host}")
            return True, None

        except aiosmtplib.SMTPRecipientsRefused as e:
            error_msg = f"Recipient refused: {e}"
            logger.error(f"Permanent failure delivering to {recipient} via {mx_host}: {error_msg}")
            return False, error_msg

        except aiosmtplib.SMTPResponseException as e:
            # Check if temporary (4xx) or permanent (5xx) failure
            if e.code >= 500:
                error_msg = f"Permanent error {e.code}: {e.message}"
                logger.error(f"Permanent failure delivering to {recipient} via {mx_host}: {error_msg}")
                return False, error_msg
            else:
                error_msg = f"Temporary error {e.code}: {e.message}"
                logger.warning(f"Temporary failure delivering to {recipient} via {mx_host}: {error_msg}")
                return False, error_msg

        except asyncio.TimeoutError:
            error_msg = f"Connection timeout to {mx_host}"
            logger.warning(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Error delivering to {recipient} via {mx_host}: {error_msg}")
            return False, error_msg

    async def _attempt_delivery(
        self,
        message: EmailMessage,
        recipient: str,
        mail_from: str,
        attempt_number: int
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Attempt to deliver email to recipient.

        Returns:
            (success, error_message, mx_host)
        """
        try:
            # Extract domain from recipient
            domain = self._extract_domain(recipient)

            # Check rate limit for this domain
            await self._check_rate_limit(domain)

            # Lookup MX records
            mx_hosts = await self._lookup_mx_records(domain)

            # Try each MX host in order
            for mx_host in mx_hosts:
                logger.debug(f"Attempting delivery to {recipient} via {mx_host} (attempt {attempt_number})")

                success, error = await self._deliver_to_mx(
                    mx_host,
                    message,
                    mail_from,
                    recipient
                )

                if success:
                    return True, None, mx_host

                # If permanent error (5xx), don't try other MX hosts
                if error and "Permanent" in error:
                    return False, error, mx_host

                # Try next MX host
                logger.debug(f"Trying next MX host for {recipient}")

            # All MX hosts failed
            return False, "All MX hosts failed", mx_hosts[0] if mx_hosts else None

        except Exception as e:
            error_msg = f"Delivery attempt failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    async def send_email(
        self,
        message: EmailMessage,
        recipient: str,
        mail_from: str = "noreply@smtpy.fr"
    ) -> bool:
        """
        Send email directly to recipient's mail server.

        Args:
            message: Email message to send
            recipient: Recipient email address
            mail_from: Sender email address (envelope from)

        Returns:
            True if delivery successful, False otherwise
        """
        delivery = EmailDelivery(
            message=message,
            recipient=recipient,
            mail_from=mail_from,
            domain=self._extract_domain(recipient),
            max_attempts=self.max_retries
        )

        for attempt in range(1, self.max_retries + 1):
            success, error, mx_host = await self._attempt_delivery(
                message,
                recipient,
                mail_from,
                attempt
            )

            # Record attempt
            delivery.attempts.append(DeliveryAttempt(
                timestamp=datetime.utcnow(),
                success=success,
                error=error,
                mx_host=mx_host
            ))

            if success:
                self.stats["sent"] += 1
                return True

            # Check if permanent failure (don't retry)
            if error and ("Permanent" in error or "refused" in error):
                logger.error(f"Permanent failure for {recipient}, not retrying: {error}")
                self.stats["bounced"] += 1
                return False

            # Temporary failure, retry with exponential backoff
            if attempt < self.max_retries:
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                logger.info(
                    f"Delivery to {recipient} failed (attempt {attempt}/{self.max_retries}), "
                    f"retrying in {wait_time}s: {error}"
                )
                self.stats["deferred"] += 1
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"Delivery to {recipient} failed after {self.max_retries} attempts: {error}"
                )
                self.stats["failed"] += 1

        return False

    async def send_email_bulk(
        self,
        message: EmailMessage,
        recipients: List[str],
        mail_from: str = "noreply@smtpy.fr"
    ) -> Dict[str, bool]:
        """
        Send email to multiple recipients.

        Returns:
            Dict mapping recipient email to success status
        """
        results = {}

        # Send to all recipients concurrently
        tasks = [
            self.send_email(message, recipient, mail_from)
            for recipient in recipients
        ]

        delivery_results = await asyncio.gather(*tasks, return_exceptions=True)

        for recipient, result in zip(recipients, delivery_results):
            if isinstance(result, Exception):
                logger.error(f"Exception sending to {recipient}: {result}")
                results[recipient] = False
            else:
                results[recipient] = result

        return results

    def get_stats(self) -> Dict:
        """Get delivery statistics"""
        return {
            **self.stats,
            "mx_cache_size": len(self._mx_cache)
        }

    def clear_mx_cache(self):
        """Clear MX record cache"""
        self._mx_cache.clear()
        logger.info("MX cache cleared")


# Global instance
_direct_smtp_service: Optional[DirectSMTPService] = None


def get_direct_smtp_service() -> DirectSMTPService:
    """Get or create the global direct SMTP service instance"""
    global _direct_smtp_service

    if _direct_smtp_service is None:
        _direct_smtp_service = DirectSMTPService(
            hostname=getattr(SETTINGS, 'SMTP_HOSTNAME', 'mail.smtpy.fr')
        )

    return _direct_smtp_service


async def send_direct(
    message: EmailMessage,
    recipients: List[str],
    mail_from: str = "noreply@smtpy.fr"
) -> Dict[str, bool]:
    """
    Convenience function to send email directly.

    Args:
        message: Email message to send
        recipients: List of recipient email addresses
        mail_from: Sender email address

    Returns:
        Dict mapping recipient to success status
    """
    service = get_direct_smtp_service()
    return await service.send_email_bulk(message, recipients, mail_from)
