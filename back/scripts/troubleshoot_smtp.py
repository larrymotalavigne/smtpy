#!/usr/bin/env python3
"""
Comprehensive SMTP Troubleshooting Script for SMTPy

This script performs extensive diagnostics to help troubleshoot SMTP configuration issues:
- Connection testing (TCP connectivity on multiple ports)
- Authentication testing (verify credentials)
- TLS/SSL testing (check encryption support)
- DNS checks (MX, SPF, DKIM, DMARC records)
- Port scanning (identify accessible ports)
- Message sending tests (end-to-end delivery)
- Configuration validation (detect common misconfigurations)
- Network diagnostics (firewall and connectivity issues)

Usage:
    # Run full diagnostic suite
    python scripts/troubleshoot_smtp.py --full

    # Quick connection test
    python scripts/troubleshoot_smtp.py --quick

    # Test specific SMTP server
    python scripts/troubleshoot_smtp.py --host smtp.gmail.com --port 587

    # Test with authentication
    python scripts/troubleshoot_smtp.py --host smtp.gmail.com --port 587 \\
        --username user@example.com --password "app-password"

    # Test DNS records for a domain
    python scripts/troubleshoot_smtp.py --check-dns example.com

    # Test email delivery
    python scripts/troubleshoot_smtp.py --send-test sender@domain.com recipient@example.com
"""

import asyncio
import argparse
import socket
import ssl
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import optional dependencies
try:
    import dns.resolver
    import dns.rdatatype
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("⚠️  Warning: dnspython not installed. DNS checks will be limited.")
    print("   Install with: pip install dnspython")

try:
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False
    print("⚠️  Warning: aiosmtplib not installed. Async SMTP features will be limited.")
    print("   Install with: pip install aiosmtplib")

import smtplib
from email.message import EmailMessage

# Try to import settings
try:
    from shared.core.config import SETTINGS
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️  Warning: Could not load SMTPy settings")


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def test_tcp_connection(host: str, port: int, timeout: int = 10) -> Tuple[bool, str]:
    """
    Test basic TCP connectivity to a host and port.

    Returns:
        (success, message)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        result = sock.connect_ex((host, port))
        elapsed = time.time() - start_time
        sock.close()

        if result == 0:
            return True, f"Connected successfully in {elapsed:.2f}s"
        else:
            return False, f"Connection refused (error code: {result})"
    except socket.gaierror as e:
        return False, f"DNS resolution failed: {e}"
    except socket.timeout:
        return False, f"Connection timeout after {timeout}s"
    except Exception as e:
        return False, f"Connection error: {e}"


def test_smtp_banner(host: str, port: int, timeout: int = 10) -> Tuple[bool, str, Optional[str]]:
    """
    Test SMTP connection and retrieve server banner.

    Returns:
        (success, message, banner)
    """
    try:
        smtp = smtplib.SMTP(timeout=timeout)
        smtp.connect(host, port)
        code, banner = smtp.ehlo_or_helo_if_needed()
        capabilities = smtp.esmtp_features
        smtp.quit()

        return True, "SMTP banner received", banner.decode() if isinstance(banner, bytes) else str(banner)
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}", None
    except Exception as e:
        return False, f"Error: {e}", None


def test_smtp_tls(host: str, port: int, timeout: int = 10) -> Tuple[bool, str, Dict]:
    """
    Test SMTP TLS/STARTTLS support.

    Returns:
        (success, message, tls_info)
    """
    tls_info = {
        "starttls_supported": False,
        "tls_version": None,
        "cipher": None,
        "certificate": None
    }

    try:
        # Test STARTTLS
        smtp = smtplib.SMTP(host, port, timeout=timeout)
        smtp.ehlo()

        if smtp.has_extn('STARTTLS'):
            tls_info["starttls_supported"] = True
            smtp.starttls()

            # Get TLS info
            if hasattr(smtp, 'sock') and hasattr(smtp.sock, 'version'):
                tls_info["tls_version"] = smtp.sock.version()
                tls_info["cipher"] = smtp.sock.cipher()

        smtp.quit()

        if tls_info["starttls_supported"]:
            return True, "STARTTLS supported and working", tls_info
        else:
            return False, "STARTTLS not supported", tls_info

    except smtplib.SMTPException as e:
        return False, f"SMTP TLS error: {e}", tls_info
    except Exception as e:
        return False, f"TLS test error: {e}", tls_info


def test_smtp_ssl(host: str, port: int, timeout: int = 10) -> Tuple[bool, str]:
    """
    Test SMTP over SSL (SMTPS).

    Returns:
        (success, message)
    """
    try:
        smtp = smtplib.SMTP_SSL(host, port, timeout=timeout)
        smtp.ehlo()
        smtp.quit()
        return True, "SMTP SSL connection successful"
    except smtplib.SMTPException as e:
        return False, f"SMTP SSL error: {e}"
    except ssl.SSLError as e:
        return False, f"SSL error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def test_smtp_auth(host: str, port: int, username: str, password: str,
                   use_tls: bool = True, use_ssl: bool = False,
                   timeout: int = 10) -> Tuple[bool, str]:
    """
    Test SMTP authentication.

    Returns:
        (success, message)
    """
    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            smtp = smtplib.SMTP(host, port, timeout=timeout)
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()

        # Test authentication
        smtp.login(username, password)
        smtp.quit()

        return True, "Authentication successful"
    except smtplib.SMTPAuthenticationError as e:
        return False, f"Authentication failed: {e}"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def check_dns_mx_records(domain: str) -> Tuple[bool, List[str], str]:
    """
    Check MX records for a domain.

    Returns:
        (success, mx_records, message)
    """
    if not DNS_AVAILABLE:
        return False, [], "dnspython not available"

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10
        resolver.lifetime = 10

        mx_records = resolver.resolve(domain, 'MX')
        mx_hosts = [
            f"{mx.preference} {str(mx.exchange).rstrip('.')}"
            for mx in sorted(mx_records, key=lambda x: x.preference)
        ]

        return True, mx_hosts, f"Found {len(mx_hosts)} MX record(s)"
    except dns.resolver.NoAnswer:
        return False, [], "No MX records found"
    except dns.resolver.NXDOMAIN:
        return False, [], "Domain does not exist"
    except dns.exception.Timeout:
        return False, [], "DNS query timeout"
    except Exception as e:
        return False, [], f"DNS error: {e}"


def check_dns_spf_record(domain: str) -> Tuple[bool, Optional[str], str]:
    """
    Check SPF record for a domain.

    Returns:
        (success, spf_record, message)
    """
    if not DNS_AVAILABLE:
        return False, None, "dnspython not available"

    try:
        resolver = dns.resolver.Resolver()
        txt_records = resolver.resolve(domain, 'TXT')

        for record in txt_records:
            txt = record.to_text().strip('"')
            if txt.startswith('v=spf1'):
                return True, txt, "SPF record found"

        return False, None, "No SPF record found"
    except Exception as e:
        return False, None, f"Error checking SPF: {e}"


def check_dns_dkim_record(domain: str, selector: str = "default") -> Tuple[bool, Optional[str], str]:
    """
    Check DKIM record for a domain.

    Returns:
        (success, dkim_record, message)
    """
    if not DNS_AVAILABLE:
        return False, None, "dnspython not available"

    try:
        resolver = dns.resolver.Resolver()
        dkim_domain = f"{selector}._domainkey.{domain}"
        txt_records = resolver.resolve(dkim_domain, 'TXT')

        for record in txt_records:
            txt = record.to_text().strip('"')
            if 'v=DKIM1' in txt or 'p=' in txt:
                return True, txt, "DKIM record found"

        return False, None, "No DKIM record found"
    except dns.resolver.NXDOMAIN:
        return False, None, f"DKIM record not found at {dkim_domain}"
    except Exception as e:
        return False, None, f"Error checking DKIM: {e}"


def check_dns_dmarc_record(domain: str) -> Tuple[bool, Optional[str], str]:
    """
    Check DMARC record for a domain.

    Returns:
        (success, dmarc_record, message)
    """
    if not DNS_AVAILABLE:
        return False, None, "dnspython not available"

    try:
        resolver = dns.resolver.Resolver()
        dmarc_domain = f"_dmarc.{domain}"
        txt_records = resolver.resolve(dmarc_domain, 'TXT')

        for record in txt_records:
            txt = record.to_text().strip('"')
            if txt.startswith('v=DMARC1'):
                return True, txt, "DMARC record found"

        return False, None, "No DMARC record found"
    except Exception as e:
        return False, None, f"Error checking DMARC: {e}"


def send_test_email(host: str, port: int, sender: str, recipient: str,
                   username: Optional[str] = None, password: Optional[str] = None,
                   use_tls: bool = True, use_ssl: bool = False,
                   timeout: int = 30) -> Tuple[bool, str]:
    """
    Send a test email.

    Returns:
        (success, message)
    """
    try:
        # Create message
        msg = EmailMessage()
        msg['Subject'] = f'SMTPy SMTP Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        msg['From'] = sender
        msg['To'] = recipient
        msg.set_content(f"""
This is a test email from SMTPy SMTP troubleshooting script.

Configuration:
- SMTP Host: {host}:{port}
- Sender: {sender}
- Recipient: {recipient}
- TLS: {use_tls}
- SSL: {use_ssl}
- Authenticated: {username is not None}
- Timestamp: {datetime.now().isoformat()}

If you receive this email, your SMTP configuration is working correctly!
""")

        # Connect and send
        if use_ssl:
            smtp = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            smtp = smtplib.SMTP(host, port, timeout=timeout)
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()

        # Authenticate if credentials provided
        if username and password:
            smtp.login(username, password)

        # Send email
        smtp.send_message(msg)
        smtp.quit()

        return True, "Test email sent successfully"
    except Exception as e:
        return False, f"Failed to send test email: {e}"


def run_quick_test(host: str = None, port: int = None):
    """Run a quick connectivity test"""
    print_header("QUICK SMTP CONNECTION TEST")

    # Use settings if available and no host specified
    if host is None and SETTINGS_AVAILABLE:
        host = SETTINGS.EMAIL_SMTP_HOST
        port = SETTINGS.EMAIL_SMTP_PORT
    elif host is None:
        host = "localhost"
        port = port or 25

    print_info(f"Testing connection to {host}:{port}")

    # Test TCP connection
    success, message = test_tcp_connection(host, port)
    if success:
        print_success(f"TCP connection: {message}")
    else:
        print_error(f"TCP connection: {message}")
        return

    # Test SMTP banner
    success, message, banner = test_smtp_banner(host, port)
    if success:
        print_success(f"SMTP banner: {message}")
        if banner:
            print_info(f"  Banner: {banner[:100]}...")
    else:
        print_error(f"SMTP banner: {message}")


def run_full_diagnostics(host: str = None, port: int = None,
                         username: str = None, password: str = None,
                         use_tls: bool = True, use_ssl: bool = False):
    """Run comprehensive SMTP diagnostics"""
    print_header("COMPREHENSIVE SMTP DIAGNOSTICS")

    # Use settings if available and no host specified
    if host is None and SETTINGS_AVAILABLE:
        host = SETTINGS.EMAIL_SMTP_HOST
        port = SETTINGS.EMAIL_SMTP_PORT
        username = username or SETTINGS.EMAIL_SMTP_USERNAME
        password = password or SETTINGS.EMAIL_SMTP_PASSWORD
        use_tls = SETTINGS.EMAIL_SMTP_USE_TLS
        use_ssl = SETTINGS.EMAIL_SMTP_USE_SSL
    elif host is None:
        host = "localhost"
        port = port or 25

    print_info(f"Testing SMTP server: {host}:{port}")
    print_info(f"Configuration: TLS={use_tls}, SSL={use_ssl}, Auth={'Yes' if username else 'No'}\n")

    # 1. TCP Connection Test
    print(f"{Colors.BOLD}1. TCP Connection Test{Colors.ENDC}")
    success, message = test_tcp_connection(host, port)
    if success:
        print_success(message)
    else:
        print_error(message)
        print_warning("Cannot proceed with further tests - connection failed")
        return

    # 2. SMTP Banner Test
    print(f"\n{Colors.BOLD}2. SMTP Banner Test{Colors.ENDC}")
    success, message, banner = test_smtp_banner(host, port)
    if success:
        print_success(message)
        if banner:
            print_info(f"  Banner: {banner[:200]}")
    else:
        print_error(message)

    # 3. Common Ports Scan
    print(f"\n{Colors.BOLD}3. Common SMTP Ports Scan{Colors.ENDC}")
    common_ports = [25, 465, 587, 1025, 2525]
    for test_port in common_ports:
        success, message = test_tcp_connection(host, test_port, timeout=5)
        status = "✓ Open" if success else "✗ Closed/Filtered"
        color = Colors.GREEN if success else Colors.RED
        print(f"  Port {test_port:5d}: {color}{status}{Colors.ENDC}")

    # 4. TLS/SSL Tests
    print(f"\n{Colors.BOLD}4. TLS/SSL Tests{Colors.ENDC}")

    # Test STARTTLS
    if not use_ssl:
        success, message, tls_info = test_smtp_tls(host, port)
        if success:
            print_success(f"STARTTLS: {message}")
            if tls_info.get("tls_version"):
                print_info(f"  TLS Version: {tls_info['tls_version']}")
            if tls_info.get("cipher"):
                print_info(f"  Cipher: {tls_info['cipher']}")
        else:
            print_warning(f"STARTTLS: {message}")

    # Test SSL
    if use_ssl or port == 465:
        success, message = test_smtp_ssl(host, port)
        if success:
            print_success(f"SMTP SSL: {message}")
        else:
            print_error(f"SMTP SSL: {message}")

    # 5. Authentication Test
    if username and password:
        print(f"\n{Colors.BOLD}5. Authentication Test{Colors.ENDC}")
        success, message = test_smtp_auth(host, port, username, password, use_tls, use_ssl)
        if success:
            print_success(message)
        else:
            print_error(message)
    else:
        print(f"\n{Colors.BOLD}5. Authentication Test{Colors.ENDC}")
        print_warning("Skipped (no credentials provided)")

    # 6. Configuration Summary
    print(f"\n{Colors.BOLD}6. Configuration Summary{Colors.ENDC}")
    if SETTINGS_AVAILABLE:
        print_info("Transactional Email Settings:")
        print(f"  EMAIL_ENABLED: {SETTINGS.EMAIL_ENABLED}")
        print(f"  EMAIL_SMTP_HOST: {SETTINGS.EMAIL_SMTP_HOST}")
        print(f"  EMAIL_SMTP_PORT: {SETTINGS.EMAIL_SMTP_PORT}")
        print(f"  EMAIL_SMTP_USERNAME: {SETTINGS.EMAIL_SMTP_USERNAME or '(not set)'}")
        print(f"  EMAIL_SMTP_USE_TLS: {SETTINGS.EMAIL_SMTP_USE_TLS}")
        print(f"  EMAIL_SMTP_USE_SSL: {SETTINGS.EMAIL_SMTP_USE_SSL}")
    else:
        print_warning("Settings not available")


def run_dns_checks(domain: str):
    """Run DNS checks for a domain"""
    print_header(f"DNS CHECKS FOR {domain}")

    if not DNS_AVAILABLE:
        print_error("dnspython not installed. Cannot perform DNS checks.")
        print_info("Install with: pip install dnspython")
        return

    # 1. MX Records
    print(f"{Colors.BOLD}1. MX Records{Colors.ENDC}")
    success, mx_records, message = check_dns_mx_records(domain)
    if success:
        print_success(message)
        for mx in mx_records:
            print(f"  {mx}")
    else:
        print_error(message)

    # 2. SPF Record
    print(f"\n{Colors.BOLD}2. SPF Record{Colors.ENDC}")
    success, spf_record, message = check_dns_spf_record(domain)
    if success:
        print_success(message)
        print(f"  {spf_record}")
    else:
        print_warning(message)

    # 3. DKIM Record
    print(f"\n{Colors.BOLD}3. DKIM Record (selector: default){Colors.ENDC}")
    success, dkim_record, message = check_dns_dkim_record(domain)
    if success:
        print_success(message)
        # Truncate long DKIM records
        display_record = dkim_record[:100] + "..." if len(dkim_record) > 100 else dkim_record
        print(f"  {display_record}")
    else:
        print_warning(message)

    # 4. DMARC Record
    print(f"\n{Colors.BOLD}4. DMARC Record{Colors.ENDC}")
    success, dmarc_record, message = check_dns_dmarc_record(domain)
    if success:
        print_success(message)
        print(f"  {dmarc_record}")
    else:
        print_warning(message)

    # Summary
    print(f"\n{Colors.BOLD}DNS Configuration Summary:{Colors.ENDC}")
    all_records = [
        ("MX", check_dns_mx_records(domain)[0]),
        ("SPF", check_dns_spf_record(domain)[0]),
        ("DKIM", check_dns_dkim_record(domain)[0]),
        ("DMARC", check_dns_dmarc_record(domain)[0])
    ]

    configured = sum(1 for _, success in all_records if success)
    total = len(all_records)

    if configured == total:
        print_success(f"All DNS records configured ({configured}/{total})")
    elif configured > 0:
        print_warning(f"Some DNS records missing ({configured}/{total})")
    else:
        print_error("No DNS records configured")


def run_send_test(sender: str, recipient: str, host: str = None, port: int = None,
                 username: str = None, password: str = None,
                 use_tls: bool = True, use_ssl: bool = False):
    """Send a test email"""
    print_header("SEND TEST EMAIL")

    # Use settings if available and no host specified
    if host is None and SETTINGS_AVAILABLE:
        host = SETTINGS.EMAIL_SMTP_HOST
        port = SETTINGS.EMAIL_SMTP_PORT
        username = username or SETTINGS.EMAIL_SMTP_USERNAME
        password = password or SETTINGS.EMAIL_SMTP_PASSWORD
        use_tls = SETTINGS.EMAIL_SMTP_USE_TLS
        use_ssl = SETTINGS.EMAIL_SMTP_USE_SSL
    elif host is None:
        print_error("No SMTP host specified and settings not available")
        return

    print_info(f"From: {sender}")
    print_info(f"To: {recipient}")
    print_info(f"Via: {host}:{port}")
    print()

    success, message = send_test_email(
        host, port, sender, recipient,
        username, password, use_tls, use_ssl
    )

    if success:
        print_success(message)
        print_info(f"Check inbox at: {recipient}")
    else:
        print_error(message)


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive SMTP troubleshooting script for SMTPy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full diagnostic suite with settings from .env
  python scripts/troubleshoot_smtp.py --full

  # Quick connection test
  python scripts/troubleshoot_smtp.py --quick

  # Test specific SMTP server
  python scripts/troubleshoot_smtp.py --host smtp.gmail.com --port 587 --full

  # Test with authentication
  python scripts/troubleshoot_smtp.py --host smtp.gmail.com --port 587 \\
      --username user@example.com --password "app-password" --full

  # Check DNS records
  python scripts/troubleshoot_smtp.py --check-dns example.com

  # Send test email
  python scripts/troubleshoot_smtp.py --send-test sender@domain.com recipient@example.com
        """
    )

    # Test modes
    parser.add_argument('--quick', action='store_true',
                       help='Run quick connection test')
    parser.add_argument('--full', action='store_true',
                       help='Run full diagnostic suite')
    parser.add_argument('--check-dns', metavar='DOMAIN',
                       help='Check DNS records for domain')
    parser.add_argument('--send-test', nargs=2, metavar=('SENDER', 'RECIPIENT'),
                       help='Send test email')

    # SMTP server configuration
    parser.add_argument('--host', help='SMTP host')
    parser.add_argument('--port', type=int, help='SMTP port')
    parser.add_argument('--username', help='SMTP username')
    parser.add_argument('--password', help='SMTP password')
    parser.add_argument('--use-tls', action='store_true', default=True,
                       help='Use STARTTLS (default: True)')
    parser.add_argument('--no-tls', dest='use_tls', action='store_false',
                       help='Disable STARTTLS')
    parser.add_argument('--use-ssl', action='store_true',
                       help='Use SSL/TLS (SMTPS)')

    args = parser.parse_args()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    try:
        # Run requested test
        if args.quick:
            run_quick_test(args.host, args.port)
        elif args.full:
            run_full_diagnostics(
                args.host, args.port,
                args.username, args.password,
                args.use_tls, args.use_ssl
            )
        elif args.check_dns:
            run_dns_checks(args.check_dns)
        elif args.send_test:
            sender, recipient = args.send_test
            run_send_test(
                sender, recipient,
                args.host, args.port,
                args.username, args.password,
                args.use_tls, args.use_ssl
            )
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
