"""Unit tests for DNS verification service."""

import pytest
from unittest.mock import Mock, MagicMock
import dns.resolver
import dns.exception

from api.services.dns_service import DNSService


class TestDNSService:
    """Test DNS verification service."""

    def test_extract_dkim_public_key_valid(self):
        """Test extracting public key from valid DKIM record."""
        dns_service = DNSService()

        # Test standard DKIM record format
        dkim_record = "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"
        result = dns_service._extract_dkim_public_key(dkim_record)
        assert result == "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"

    def test_extract_dkim_public_key_with_spaces(self):
        """Test extracting public key with extra spaces."""
        dns_service = DNSService()

        dkim_record = "v=DKIM1;  k=rsa;  p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg  "
        result = dns_service._extract_dkim_public_key(dkim_record)
        assert result == "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"

    def test_extract_dkim_public_key_missing(self):
        """Test extracting public key when p= tag is missing."""
        dns_service = DNSService()

        dkim_record = "v=DKIM1; k=rsa"
        result = dns_service._extract_dkim_public_key(dkim_record)
        assert result is None

    def test_verify_dkim_record_without_expected_key(self, monkeypatch):
        """Test DKIM verification without expected key (backward compatibility)."""
        dns_service = DNSService()

        # Mock DNS resolver
        mock_record = Mock()
        mock_record.strings = [b"v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"]

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = [mock_record]
        monkeypatch.setattr(dns_service, 'resolver', mock_resolver)

        # Verify without expected key
        result = dns_service.verify_dkim_record("example.com", "default")
        assert result is True

    def test_verify_dkim_record_with_matching_key(self, monkeypatch):
        """Test DKIM verification with matching expected key."""
        dns_service = DNSService()

        expected_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"

        # Mock DNS resolver
        mock_record = Mock()
        mock_record.strings = [b"v=DKIM1; k=rsa; p=", expected_key.encode()]

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = [mock_record]
        monkeypatch.setattr(dns_service, 'resolver', mock_resolver)

        # Verify with matching key
        result = dns_service.verify_dkim_record("example.com", "default", expected_key)
        assert result is True

    def test_verify_dkim_record_with_mismatched_key(self, monkeypatch):
        """Test DKIM verification with mismatched expected key."""
        dns_service = DNSService()

        expected_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"
        dns_key = "DifferentKeyValue123456789"

        # Mock DNS resolver
        mock_record = Mock()
        mock_record.strings = [b"v=DKIM1; k=rsa; p=", dns_key.encode()]

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = [mock_record]
        monkeypatch.setattr(dns_service, 'resolver', mock_resolver)

        # Verify with mismatched key should return False
        result = dns_service.verify_dkim_record("example.com", "default", expected_key)
        assert result is False

    def test_verify_dkim_record_key_normalization(self, monkeypatch):
        """Test that DKIM verification normalizes whitespace in keys."""
        dns_service = DNSService()

        # Expected key with no whitespace
        expected_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"
        # DNS key with whitespace
        dns_key = "MIIBIjANBgkqhkiG9w0BAQEF\nAAOCAQ8A\r\nMIIBCg"

        # Mock DNS resolver
        mock_record = Mock()
        mock_record.strings = [b"v=DKIM1; k=rsa; p=", dns_key.encode()]

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = [mock_record]
        monkeypatch.setattr(dns_service, 'resolver', mock_resolver)

        # Verify - should match after normalization
        result = dns_service.verify_dkim_record("example.com", "default", expected_key)
        assert result is True

    def test_verify_dkim_record_no_answer(self, monkeypatch):
        """Test DKIM verification when DNS returns no answer."""
        dns_service = DNSService()

        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.resolver.NoAnswer()
        monkeypatch.setattr(dns_service, 'resolver', mock_resolver)

        result = dns_service.verify_dkim_record("example.com", "default")
        assert result is False

    def test_verify_dkim_record_nxdomain(self, monkeypatch):
        """Test DKIM verification when DNS domain doesn't exist."""
        dns_service = DNSService()

        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.resolver.NXDOMAIN()
        monkeypatch.setattr(dns_service, 'resolver', mock_resolver)

        result = dns_service.verify_dkim_record("nonexistent.com", "default")
        assert result is False

    def test_verify_dkim_record_timeout(self, monkeypatch):
        """Test DKIM verification when DNS query times out."""
        dns_service = DNSService()

        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.exception.Timeout()
        monkeypatch.setattr(dns_service, 'resolver', mock_resolver)

        result = dns_service.verify_dkim_record("example.com", "default")
        assert result is False

    def test_verify_all_with_expected_dkim_key(self, monkeypatch):
        """Test verify_all passes expected DKIM key to verify_dkim_record."""
        dns_service = DNSService()

        expected_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg"

        # Mock all verification methods
        monkeypatch.setattr(dns_service, 'verify_mx_record', lambda *args, **kwargs: True)
        monkeypatch.setattr(dns_service, 'verify_spf_record', lambda *args, **kwargs: True)
        monkeypatch.setattr(dns_service, 'verify_dmarc_record', lambda *args, **kwargs: True)

        # Mock verify_dkim_record to capture arguments
        dkim_args = []
        def mock_verify_dkim(*args, **kwargs):
            dkim_args.extend(args)
            return True

        monkeypatch.setattr(dns_service, 'verify_dkim_record', mock_verify_dkim)

        # Call verify_all with expected DKIM key
        dns_service.verify_all(
            domain="example.com",
            expected_dkim_public_key=expected_key
        )

        # Verify that expected key was passed to verify_dkim_record
        assert expected_key in dkim_args
