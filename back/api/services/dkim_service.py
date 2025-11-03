"""DKIM key generation and management service."""

import base64
import logging
from typing import Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class DKIMService:
    """Service for DKIM key generation and management."""

    @staticmethod
    def generate_dkim_keypair(key_size: int = 2048) -> Tuple[str, str]:
        """Generate a DKIM RSA keypair.

        Args:
            key_size: RSA key size in bits (2048 recommended, 1024 minimum)

        Returns:
            Tuple of (private_key_pem, public_key_base64)
            - private_key_pem: PEM-encoded private key for email signing
            - public_key_base64: Base64-encoded public key for DNS TXT record
        """
        if key_size < 1024:
            raise ValueError("DKIM key size must be at least 1024 bits")

        logger.info(f"Generating DKIM keypair with {key_size}-bit RSA key")

        # Generate RSA private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        # Export private key as PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        # Extract public key
        public_key = private_key.public_key()

        # Export public key in SubjectPublicKeyInfo format (DER)
        public_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Base64 encode the public key (without PEM headers) for DNS
        public_base64 = base64.b64encode(public_der).decode('utf-8')

        logger.info("DKIM keypair generated successfully")

        return private_pem, public_base64

    @staticmethod
    def format_dkim_public_key_for_dns(public_key_base64: str) -> str:
        """Format a public key for DNS TXT record.

        Args:
            public_key_base64: Base64-encoded public key

        Returns:
            Formatted DKIM DNS record value (v=DKIM1; k=rsa; p=...)
        """
        return f"v=DKIM1; k=rsa; p={public_key_base64}"

    @staticmethod
    def validate_dkim_public_key(public_key_base64: str) -> bool:
        """Validate that a public key is properly formatted.

        Args:
            public_key_base64: Base64-encoded public key

        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to decode the base64
            decoded = base64.b64decode(public_key_base64)
            # Should be at least 200 bytes for a 1024-bit key
            if len(decoded) < 200:
                return False
            return True
        except Exception as e:
            logger.error(f"Invalid DKIM public key: {e}")
            return False

    @staticmethod
    def split_dns_record(dns_value: str, max_length: int = 255) -> list[str]:
        """Split a long DNS TXT record into chunks.

        Some DNS providers have a 255-character limit per TXT record string.
        This splits long DKIM records into multiple quoted strings.

        Args:
            dns_value: The DNS TXT record value
            max_length: Maximum length per chunk

        Returns:
            List of record chunks

        Example:
            >>> split_dns_record('v=DKIM1; k=rsa; p=VERY_LONG_KEY...')
            ['v=DKIM1; k=rsa; p=VERY_LONG', 'KEY...']
        """
        if len(dns_value) <= max_length:
            return [dns_value]

        chunks = []
        remaining = dns_value

        while remaining:
            # Take max_length characters
            chunk = remaining[:max_length]
            chunks.append(chunk)
            remaining = remaining[max_length:]

        return chunks

    @staticmethod
    def get_dkim_selector() -> str:
        """Get the DKIM selector to use.

        The selector is used in the DNS record subdomain:
        {selector}._domainkey.example.com

        Returns:
            DKIM selector string (default: 'default')
        """
        # For now, use a fixed selector
        # In production, you might want to support multiple selectors
        # for key rotation (e.g., 'default', 'default2', etc.)
        return "default"

    @staticmethod
    def format_dns_hostname(selector: str, domain: str) -> str:
        """Format the DNS hostname for DKIM TXT record.

        Args:
            selector: DKIM selector (e.g., 'default')
            domain: Domain name (e.g., 'example.com')

        Returns:
            Full DNS hostname (e.g., 'default._domainkey.example.com')
        """
        return f"{selector}._domainkey.{domain}"
