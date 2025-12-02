#!/usr/bin/env python3
"""
Test SMTP configuration for SMTPy.

This script tests both:
1. Transactional email sending (password reset, welcome emails)
2. SMTP relay configuration

Usage:
    python scripts/test_smtp_config.py --test-transactional test@example.com
    python scripts/test_smtp_config.py --test-relay sender@domain.com recipient@example.com
    python scripts/test_smtp_config.py --check-config
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.core.config import SETTINGS
from api.services.email_service import EmailService


def check_config():
    """Display current SMTP configuration."""
    print("\n" + "="*60)
    print("SMTP CONFIGURATION CHECK")
    print("="*60)

    print("\n📧 TRANSACTIONAL EMAIL SETTINGS:")
    print(f"  EMAIL_ENABLED: {SETTINGS.EMAIL_ENABLED}")
    print(f"  EMAIL_BACKEND: {SETTINGS.EMAIL_BACKEND}")
    print(f"  EMAIL_FROM: {SETTINGS.EMAIL_FROM}")
    print(f"  EMAIL_FROM_NAME: {SETTINGS.EMAIL_FROM_NAME}")
    print(f"  EMAIL_SMTP_HOST: {SETTINGS.EMAIL_SMTP_HOST}")
    print(f"  EMAIL_SMTP_PORT: {SETTINGS.EMAIL_SMTP_PORT}")
    print(f"  EMAIL_SMTP_USERNAME: {SETTINGS.EMAIL_SMTP_USERNAME}")
    print(f"  EMAIL_SMTP_PASSWORD: {'***' if SETTINGS.EMAIL_SMTP_PASSWORD else '(not set)'}")
    print(f"  EMAIL_SMTP_USE_TLS: {SETTINGS.EMAIL_SMTP_USE_TLS}")
    print(f"  EMAIL_SMTP_USE_SSL: {SETTINGS.EMAIL_SMTP_USE_SSL}")

    print("\n📨 SMTP RELAY SETTINGS (for forwarding):")
    print(f"  SMTP_HOSTNAME: {SETTINGS.SMTP_HOSTNAME}")
    print(f"  SMTP_DELIVERY_MODE: {SETTINGS.SMTP_DELIVERY_MODE}")
    print(f"  SMTP_ENABLE_DKIM: {SETTINGS.SMTP_ENABLE_DKIM}")
    print(f"  SMTP_HOST: {SETTINGS.SMTP_HOST}")
    print(f"  SMTP_PORT: {SETTINGS.SMTP_PORT}")
    print(f"  SMTP_USER: {SETTINGS.SMTP_USER}")
    print(f"  SMTP_PASSWORD: {'***' if SETTINGS.SMTP_PASSWORD else '(not set)'}")
    print(f"  SMTP_USE_TLS: {SETTINGS.SMTP_USE_TLS}")
    print(f"  SMTP_USE_SSL: {SETTINGS.SMTP_USE_SSL}")

    print("\n" + "="*60)

    # Configuration warnings
    warnings = []

    if not SETTINGS.EMAIL_ENABLED:
        warnings.append("⚠️  EMAIL_ENABLED is False - emails will not be sent")

    if SETTINGS.EMAIL_SMTP_HOST == "localhost" and SETTINGS.EMAIL_SMTP_PORT == 1025:
        warnings.append("⚠️  Using localhost:1025 - this is for development only")

    if not SETTINGS.EMAIL_SMTP_USERNAME and SETTINGS.EMAIL_SMTP_HOST != "localhost":
        warnings.append("⚠️  EMAIL_SMTP_USERNAME is not set (may be required)")

    if not SETTINGS.EMAIL_SMTP_PASSWORD and SETTINGS.EMAIL_SMTP_HOST != "localhost":
        warnings.append("⚠️  EMAIL_SMTP_PASSWORD is not set (may be required)")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
        print()


def test_transactional_email(recipient_email: str):
    """Test sending a transactional email."""
    print("\n" + "="*60)
    print("TESTING TRANSACTIONAL EMAIL")
    print("="*60)
    print(f"\n📧 Sending test email to: {recipient_email}")
    print(f"📤 From: {SETTINGS.EMAIL_FROM}")
    print(f"🖥️  SMTP Host: {SETTINGS.EMAIL_SMTP_HOST}:{SETTINGS.EMAIL_SMTP_PORT}")
    print(f"🔐 TLS: {SETTINGS.EMAIL_SMTP_USE_TLS}, SSL: {SETTINGS.EMAIL_SMTP_USE_SSL}")

    # Send test password reset email
    print("\n⏳ Sending password reset email...")
    success = EmailService.send_password_reset_email(
        to=recipient_email,
        username="TestUser",
        reset_token="test-token-12345"
    )

    if success:
        print("✅ Email sent successfully!")
        print(f"\n📬 Check inbox at: {recipient_email}")
        print("   Subject: 'Reset Your SMTPy Password'")
        return True
    else:
        print("❌ Failed to send email!")
        print("\n🔍 Troubleshooting steps:")
        print("   1. Check SMTP credentials are correct")
        print("   2. Verify SMTP host and port are accessible")
        print("   3. Check firewall/network settings")
        print("   4. Review logs for detailed error messages")
        return False


def test_smtp_relay(sender: str, recipient: str):
    """Test SMTP relay configuration."""
    print("\n" + "="*60)
    print("TESTING SMTP RELAY")
    print("="*60)
    print(f"\n📧 Testing relay from {sender} to {recipient}")
    print(f"🖥️  SMTP Host: {SETTINGS.SMTP_HOST}:{SETTINGS.SMTP_PORT}")
    print(f"🔐 TLS: {SETTINGS.SMTP_USE_TLS}, SSL: {SETTINGS.SMTP_USE_SSL}")

    try:
        import smtplib
        from email.message import EmailMessage

        # Create test message
        msg = EmailMessage()
        msg['Subject'] = 'SMTPy SMTP Relay Test'
        msg['From'] = sender
        msg['To'] = recipient
        msg.set_content(f"""
This is a test email from SMTPy SMTP relay.

Configuration:
- SMTP Host: {SETTINGS.SMTP_HOST}:{SETTINGS.SMTP_PORT}
- Sender: {sender}
- Recipient: {recipient}
- Delivery Mode: {SETTINGS.SMTP_DELIVERY_MODE}

If you receive this email, your SMTP relay is working correctly!
""")

        print("\n⏳ Connecting to SMTP server...")

        # Connect based on configuration
        if SETTINGS.SMTP_USE_SSL:
            smtp = smtplib.SMTP_SSL(
                SETTINGS.SMTP_HOST,
                SETTINGS.SMTP_PORT,
                timeout=10
            )
        else:
            smtp = smtplib.SMTP(
                SETTINGS.SMTP_HOST,
                SETTINGS.SMTP_PORT,
                timeout=10
            )

        # Use TLS if configured
        if SETTINGS.SMTP_USE_TLS and not SETTINGS.SMTP_USE_SSL:
            print("🔐 Starting TLS...")
            smtp.starttls()

        # Login if credentials provided
        if SETTINGS.SMTP_USER and SETTINGS.SMTP_PASSWORD:
            print("🔑 Authenticating...")
            smtp.login(SETTINGS.SMTP_USER, SETTINGS.SMTP_PASSWORD)

        # Send email
        print("📤 Sending test email...")
        smtp.send_message(msg)
        smtp.quit()

        print("✅ Email sent successfully via relay!")
        print(f"\n📬 Check inbox at: {recipient}")
        return True

    except Exception as e:
        print(f"❌ Failed to send via relay: {str(e)}")
        print("\n🔍 Troubleshooting steps:")
        print("   1. Verify SMTP credentials (SMTP_USER, SMTP_PASSWORD)")
        print("   2. Check SMTP host and port are correct")
        print("   3. Ensure firewall allows outbound connections")
        print("   4. Verify mail.atomdev.fr is accessible from this server")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test SMTP configuration for SMTPy",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--check-config',
        action='store_true',
        help='Display current SMTP configuration'
    )
    parser.add_argument(
        '--test-transactional',
        metavar='EMAIL',
        help='Test transactional email sending (password reset)'
    )
    parser.add_argument(
        '--test-relay',
        nargs=2,
        metavar=('SENDER', 'RECIPIENT'),
        help='Test SMTP relay with sender and recipient addresses'
    )

    args = parser.parse_args()

    # Show config by default or when requested
    if args.check_config or not any([args.test_transactional, args.test_relay]):
        check_config()

    success = True

    # Test transactional email
    if args.test_transactional:
        if not test_transactional_email(args.test_transactional):
            success = False

    # Test relay
    if args.test_relay:
        sender, recipient = args.test_relay
        if not test_smtp_relay(sender, recipient):
            success = False

    print("\n" + "="*60)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
