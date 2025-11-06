"""
DKIM Email Signing Service

Handles DKIM (DomainKeys Identified Mail) signing for outbound emails
to improve deliverability and prevent spoofing.
"""

import logging
from email.message import EmailMessage
from typing import Optional

import dkim

from shared.core.db import get_db
from shared.models import Domain

logger = logging.getLogger(__name__)


class DKIMSigner:
    """
    DKIM signing service for email authentication.

    Signs outbound emails with DKIM signatures using domain-specific private keys.
    """

    def __init__(self, default_selector: str = "smtpy"):
        """
        Initialize DKIM signer.

        Args:
            default_selector: Default DKIM selector to use
        """
        self.default_selector = default_selector

    async def get_domain_dkim_key(self, domain_name: str) -> Optional[tuple]:
        """
        Get DKIM private key and selector for a domain.

        Returns:
            (private_key, selector) or None if not found
        """
        try:
            async with get_db() as session:
                from sqlalchemy import select

                query = select(Domain).where(
                    Domain.name == domain_name,
                    Domain.is_deleted == False
                )
                result = await session.execute(query)
                domain = result.scalar_one_or_none()

                if domain and domain.dkim_private_key:
                    return (
                        domain.dkim_private_key,
                        domain.dkim_selector or self.default_selector
                    )

                return None

        except Exception as e:
            logger.error(f"Error fetching DKIM key for {domain_name}: {e}")
            return None

    def sign_message(
        self,
        message: EmailMessage,
        private_key: str,
        selector: str,
        domain: str
    ) -> EmailMessage:
        """
        Sign an email message with DKIM.

        Args:
            message: Email message to sign
            private_key: DKIM private key in PEM format
            selector: DKIM selector
            domain: Sending domain

        Returns:
            Signed email message
        """
        try:
            # Convert message to bytes
            message_bytes = message.as_bytes()

            # Sign the message
            signature = dkim.sign(
                message=message_bytes,
                selector=selector.encode(),
                domain=domain.encode(),
                privkey=private_key.encode(),
                include_headers=[
                    b'from',
                    b'to',
                    b'subject',
                    b'date',
                    b'message-id',
                    b'content-type'
                ]
            )

            # Add DKIM signature header
            # The signature includes "DKIM-Signature: ", so we need to extract just the value
            signature_value = signature.decode().split(':', 1)[1].strip()
            message['DKIM-Signature'] = signature_value

            logger.info(f"DKIM signature added for domain {domain} (selector: {selector})")
            return message

        except Exception as e:
            logger.error(f"DKIM signing failed for {domain}: {e}")
            # Return unsigned message rather than failing
            return message

    async def sign_message_auto(
        self,
        message: EmailMessage,
        mail_from: str
    ) -> EmailMessage:
        """
        Automatically sign message using domain's DKIM key.

        Args:
            message: Email message to sign
            mail_from: Sender email address (used to lookup domain)

        Returns:
            Signed email message (or unsigned if no key found)
        """
        try:
            # Extract domain from mail_from
            domain = mail_from.split('@')[-1] if '@' in mail_from else None
            if not domain:
                logger.warning(f"Could not extract domain from {mail_from}")
                return message

            # Get DKIM key for domain
            dkim_data = await self.get_domain_dkim_key(domain)
            if not dkim_data:
                logger.debug(f"No DKIM key found for {domain}, sending unsigned")
                return message

            private_key, selector = dkim_data

            # Sign the message
            return self.sign_message(message, private_key, selector, domain)

        except Exception as e:
            logger.error(f"Auto DKIM signing failed: {e}")
            return message


# Global instance
_dkim_signer: Optional[DKIMSigner] = None


def get_dkim_signer() -> DKIMSigner:
    """Get or create the global DKIM signer instance"""
    global _dkim_signer

    if _dkim_signer is None:
        _dkim_signer = DKIMSigner()

    return _dkim_signer


async def sign_email(message: EmailMessage, mail_from: str) -> EmailMessage:
    """
    Convenience function to sign an email.

    Args:
        message: Email message to sign
        mail_from: Sender email address

    Returns:
        Signed email message
    """
    signer = get_dkim_signer()
    return await signer.sign_message_auto(message, mail_from)
