#!/usr/bin/env python3
"""Test script for DNS verification service."""

import sys
import asyncio
from api.services.dns_service import DNSService


async def test_domain(domain: str):
    """Test DNS verification for a domain."""
    print(f"\n{'='*60}")
    print(f"Testing DNS verification for: {domain}")
    print(f"{'='*60}\n")

    dns_service = DNSService(timeout=10.0)

    # Test individual records
    print("Testing MX record...")
    mx_result = dns_service.verify_mx_record(domain, "smtp.smtpy.fr")
    print(f"  ✓ MX verified: {mx_result}\n")

    print("Testing SPF record...")
    spf_result = dns_service.verify_spf_record(domain, "smtpy.fr")
    print(f"  ✓ SPF verified: {spf_result}\n")

    print("Testing DKIM record...")
    dkim_result = dns_service.verify_dkim_record(domain, "default")
    print(f"  ✓ DKIM verified: {dkim_result}\n")

    print("Testing DMARC record...")
    dmarc_result = dns_service.verify_dmarc_record(domain)
    print(f"  ✓ DMARC verified: {dmarc_result}\n")

    # Test all records at once
    print("-" * 60)
    print("Running complete verification...")
    results = dns_service.verify_all(
        domain=domain,
        expected_mx="smtp.smtpy.fr",
        expected_spf_include="smtpy.fr",
        dkim_selector="default"
    )

    print("\nResults:")
    for record_type, verified in results.items():
        status = "✓" if verified else "✗"
        print(f"  {status} {record_type}: {verified}")

    all_verified = all(results.values())
    print(f"\n{'='*60}")
    print(f"Overall: {'✓ FULLY VERIFIED' if all_verified else '✗ NOT FULLY VERIFIED'}")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_dns_verification.py <domain>")
        print("Example: python test_dns_verification.py motalavigne.fr")
        sys.exit(1)

    domain = sys.argv[1]
    asyncio.run(test_domain(domain))
