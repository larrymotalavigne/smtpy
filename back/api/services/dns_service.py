"""DNS verification service for domain validation."""

import logging
from typing import Optional
import dns.resolver
import dns.exception

logger = logging.getLogger(__name__)


class DNSService:
    """Service for verifying DNS records."""

    def __init__(self, timeout: float = 10.0):
        """Initialize DNS service.

        Args:
            timeout: DNS query timeout in seconds
        """
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout

    def verify_mx_record(self, domain: str, expected_mx: str) -> bool:
        """Verify MX record points to expected mail server.

        Args:
            domain: Domain name to check (e.g., "example.com")
            expected_mx: Expected MX hostname (e.g., "mail.smtpy.fr" or "mail.smtpy.fr.")

        Returns:
            True if MX record matches expected value, False otherwise
        """
        try:
            # Normalize expected MX (remove trailing dot for comparison)
            expected_mx_normalized = expected_mx.rstrip('.')

            # Query MX records
            mx_records = self.resolver.resolve(domain, 'MX')

            # Check if any MX record matches expected value
            for mx in mx_records:
                mx_host = str(mx.exchange).rstrip('.')
                logger.info(f"Found MX record for {domain}: {mx_host} (priority: {mx.preference})")

                if mx_host == expected_mx_normalized:
                    logger.info(f"MX record verified for {domain}")
                    return True

            logger.warning(f"MX record not found for {domain}. Expected: {expected_mx_normalized}")
            return False

        except dns.resolver.NoAnswer:
            logger.warning(f"No MX records found for {domain}")
            return False
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
            return False
        except dns.exception.Timeout:
            logger.error(f"DNS query timeout for {domain}")
            return False
        except Exception as e:
            logger.error(f"Error verifying MX record for {domain}: {e}")
            return False

    def verify_spf_record(self, domain: str, expected_include: str) -> bool:
        """Verify SPF record includes expected domain.

        Args:
            domain: Domain name to check
            expected_include: Expected include domain (e.g., "smtpy.fr")

        Returns:
            True if SPF record includes expected domain, False otherwise
        """
        try:
            # Query TXT records
            txt_records = self.resolver.resolve(domain, 'TXT')

            # Find SPF record
            for record in txt_records:
                txt_value = ''.join([s.decode('utf-8') if isinstance(s, bytes) else s for s in record.strings])

                if txt_value.startswith('v=spf1'):
                    logger.info(f"Found SPF record for {domain}: {txt_value}")

                    # Check if it includes expected domain
                    if f"include:{expected_include}" in txt_value:
                        logger.info(f"SPF record verified for {domain}")
                        return True
                    else:
                        logger.warning(f"SPF record found but does not include {expected_include}")
                        return False

            logger.warning(f"No SPF record found for {domain}")
            return False

        except dns.resolver.NoAnswer:
            logger.warning(f"No TXT records found for {domain}")
            return False
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
            return False
        except dns.exception.Timeout:
            logger.error(f"DNS query timeout for {domain}")
            return False
        except Exception as e:
            logger.error(f"Error verifying SPF record for {domain}: {e}")
            return False

    def verify_dkim_record(
        self,
        domain: str,
        selector: str = "default",
        expected_public_key: Optional[str] = None
    ) -> bool:
        """Verify DKIM record exists and optionally matches expected public key.

        Args:
            domain: Domain name to check
            selector: DKIM selector (default: "default")
            expected_public_key: Expected public key (base64) to match against (optional)

        Returns:
            True if DKIM record exists and matches expected key (if provided), False otherwise
        """
        try:
            # DKIM record is at selector._domainkey.domain
            dkim_domain = f"{selector}._domainkey.{domain}"

            # Query TXT records
            txt_records = self.resolver.resolve(dkim_domain, 'TXT')

            # Find DKIM record
            for record in txt_records:
                txt_value = ''.join([s.decode('utf-8') if isinstance(s, bytes) else s for s in record.strings])

                if 'v=DKIM1' in txt_value:
                    logger.info(f"Found DKIM record for {domain} (selector: {selector}): {txt_value[:100]}...")

                    # If expected_public_key is provided, validate it matches
                    if expected_public_key:
                        # Extract public key from DKIM record
                        # Format: v=DKIM1; k=rsa; p=<base64_key>
                        dns_public_key = self._extract_dkim_public_key(txt_value)

                        if not dns_public_key:
                            logger.warning(f"DKIM record found but could not extract public key from: {txt_value}")
                            return False

                        # Normalize both keys (remove whitespace) for comparison
                        dns_key_normalized = dns_public_key.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
                        expected_key_normalized = expected_public_key.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

                        if dns_key_normalized != expected_key_normalized:
                            logger.warning(
                                f"DKIM public key mismatch for {domain}. "
                                f"DNS key (first 50 chars): {dns_key_normalized[:50]}..., "
                                f"Expected key (first 50 chars): {expected_key_normalized[:50]}..."
                            )
                            return False

                        logger.info(f"DKIM record verified with matching public key for {domain}")

                    return True

            logger.warning(f"No DKIM record found for {domain} (selector: {selector})")
            return False

        except dns.resolver.NoAnswer:
            logger.warning(f"No DKIM record found for {dkim_domain}")
            return False
        except dns.resolver.NXDOMAIN:
            logger.warning(f"DKIM domain {dkim_domain} does not exist")
            return False
        except dns.exception.Timeout:
            logger.error(f"DNS query timeout for {dkim_domain}")
            return False
        except Exception as e:
            logger.error(f"Error verifying DKIM record for {domain}: {e}")
            return False

    def _extract_dkim_public_key(self, dkim_record: str) -> Optional[str]:
        """Extract the public key from a DKIM DNS record.

        Args:
            dkim_record: The DKIM DNS TXT record value (e.g., "v=DKIM1; k=rsa; p=MIIBIj...")

        Returns:
            The base64-encoded public key, or None if not found
        """
        try:
            # DKIM records are semicolon-separated key=value pairs
            # We need to extract the value of the 'p=' tag
            parts = dkim_record.split(';')

            for part in parts:
                part = part.strip()
                if part.startswith('p='):
                    # Extract everything after 'p='
                    public_key = part[2:].strip()
                    return public_key

            return None
        except Exception as e:
            logger.error(f"Error extracting public key from DKIM record: {e}")
            return None

    def verify_dmarc_record(self, domain: str) -> bool:
        """Verify DMARC record exists.

        Args:
            domain: Domain name to check

        Returns:
            True if DMARC record exists, False otherwise
        """
        try:
            # DMARC record is at _dmarc.domain
            dmarc_domain = f"_dmarc.{domain}"

            # Query TXT records
            txt_records = self.resolver.resolve(dmarc_domain, 'TXT')

            # Find DMARC record
            for record in txt_records:
                txt_value = ''.join([s.decode('utf-8') if isinstance(s, bytes) else s for s in record.strings])

                if txt_value.startswith('v=DMARC1'):
                    logger.info(f"Found DMARC record for {domain}: {txt_value}")
                    return True

            logger.warning(f"No DMARC record found for {domain}")
            return False

        except dns.resolver.NoAnswer:
            logger.warning(f"No DMARC record found for {dmarc_domain}")
            return False
        except dns.resolver.NXDOMAIN:
            logger.warning(f"DMARC domain {dmarc_domain} does not exist")
            return False
        except dns.exception.Timeout:
            logger.error(f"DNS query timeout for {dmarc_domain}")
            return False
        except Exception as e:
            logger.error(f"Error verifying DMARC record for {domain}: {e}")
            return False

    def verify_all(
        self,
        domain: str,
        expected_mx: str = "mail.smtpy.fr",
        expected_spf_include: str = "smtpy.fr",
        dkim_selector: str = "default",
        expected_dkim_public_key: Optional[str] = None
    ) -> dict[str, bool]:
        """Verify all DNS records for a domain.

        Args:
            domain: Domain name to check
            expected_mx: Expected MX hostname
            expected_spf_include: Expected SPF include domain
            dkim_selector: DKIM selector
            expected_dkim_public_key: Expected DKIM public key (base64) to validate against

        Returns:
            Dictionary with verification results for each record type
        """
        return {
            "mx_verified": self.verify_mx_record(domain, expected_mx),
            "spf_verified": self.verify_spf_record(domain, expected_spf_include),
            "dkim_verified": self.verify_dkim_record(domain, dkim_selector, expected_dkim_public_key),
            "dmarc_verified": self.verify_dmarc_record(domain),
        }
