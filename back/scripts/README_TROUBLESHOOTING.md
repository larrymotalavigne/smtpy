# SMTP Troubleshooting Guide

This guide explains how to use the comprehensive SMTP troubleshooting script to diagnose and fix SMTP configuration issues in SMTPy.

## Overview

The `troubleshoot_smtp.py` script provides extensive diagnostics to help troubleshoot SMTP problems:

- **Connection Testing**: Test TCP connectivity on multiple ports (25, 465, 587, 1025, 2525)
- **Authentication Testing**: Verify SMTP credentials
- **TLS/SSL Testing**: Check encryption support (STARTTLS, SSL/TLS)
- **DNS Checks**: Verify MX, SPF, DKIM, and DMARC records
- **Port Scanning**: Identify which SMTP ports are accessible
- **Message Sending**: Test end-to-end email delivery
- **Configuration Validation**: Detect common misconfigurations
- **Network Diagnostics**: Check for firewall and connectivity issues

## Installation

The script works standalone but has optional dependencies for enhanced features:

```bash
# Optional: Install DNS checking support
pip install dnspython

# Optional: Install async SMTP support
pip install aiosmtplib
```

## Usage Examples

### 1. Quick Connection Test

Test basic connectivity to your SMTP server:

```bash
# Test using settings from .env
python scripts/troubleshoot_smtp.py --quick

# Test specific server
python scripts/troubleshoot_smtp.py --quick --host smtp.gmail.com --port 587
```

### 2. Full Diagnostic Suite

Run comprehensive diagnostics:

```bash
# Use settings from .env
python scripts/troubleshoot_smtp.py --full

# Test specific server with authentication
python scripts/troubleshoot_smtp.py --full \
    --host smtp.gmail.com \
    --port 587 \
    --username your-email@gmail.com \
    --password "your-app-password"

# Test SSL connection (port 465)
python scripts/troubleshoot_smtp.py --full \
    --host smtp.gmail.com \
    --port 465 \
    --use-ssl
```

### 3. DNS Checks

Check DNS records for email authentication:

```bash
# Check your domain's DNS records
python scripts/troubleshoot_smtp.py --check-dns example.com

# This checks:
# - MX records (mail server addresses)
# - SPF record (sender authentication)
# - DKIM record (email signing)
# - DMARC record (email policy)
```

### 4. Send Test Email

Send a test email to verify end-to-end delivery:

```bash
# Send test using settings from .env
python scripts/troubleshoot_smtp.py --send-test \
    sender@yourdomain.com \
    recipient@example.com

# Send test via specific server
python scripts/troubleshoot_smtp.py --send-test \
    sender@yourdomain.com \
    recipient@example.com \
    --host smtp.gmail.com \
    --port 587 \
    --username your-email@gmail.com \
    --password "your-app-password"
```

## Common Issues and Solutions

### 1. Connection Refused

**Symptoms:**
```
✗ TCP connection: Connection refused (error code: 111)
```

**Solutions:**
- Verify the SMTP server is running
- Check the host and port are correct
- Verify firewall rules allow outbound connections
- Check if the port is blocked by your hosting provider

### 2. Connection Timeout

**Symptoms:**
```
✗ TCP connection: Connection timeout after 10s
```

**Solutions:**
- Check network connectivity
- Verify firewall allows outbound SMTP (ports 25, 465, 587)
- Confirm the SMTP server is accessible from your network
- Some hosting providers block port 25 for anti-spam reasons

### 3. Authentication Failed

**Symptoms:**
```
✗ Authentication failed: (535, b'5.7.8 Username and Password not accepted')
```

**Solutions:**
- Verify username and password are correct
- For Gmail: Use an app-specific password, not your regular password
- Check if the account requires additional security settings
- Verify 2FA settings if enabled

### 4. TLS/SSL Errors

**Symptoms:**
```
✗ STARTTLS: TLS test error: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solutions:**
- Update your system's SSL certificates
- Verify the server's SSL certificate is valid
- Check if self-signed certificates are in use
- Try connecting without TLS to test basic connectivity first

### 5. DNS Issues

**Symptoms:**
```
✗ No MX records found
⚠ No SPF record found
⚠ No DKIM record found
```

**Solutions:**
- Add MX records pointing to your mail server
- Configure SPF record: `v=spf1 include:smtpy.fr ~all`
- Set up DKIM signing and add DKIM record
- Configure DMARC policy: `v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com`

## Configuration Examples

### Gmail (Port 587 with STARTTLS)

```bash
python scripts/troubleshoot_smtp.py --full \
    --host smtp.gmail.com \
    --port 587 \
    --username your-email@gmail.com \
    --password "your-app-password" \
    --use-tls
```

**Notes:**
- Use app-specific password from https://myaccount.google.com/apppasswords
- Enable "Less secure app access" if using regular password (not recommended)

### Gmail (Port 465 with SSL)

```bash
python scripts/troubleshoot_smtp.py --full \
    --host smtp.gmail.com \
    --port 465 \
    --username your-email@gmail.com \
    --password "your-app-password" \
    --use-ssl
```

### SendGrid

```bash
python scripts/troubleshoot_smtp.py --full \
    --host smtp.sendgrid.net \
    --port 587 \
    --username apikey \
    --password "your-sendgrid-api-key" \
    --use-tls
```

### Mailgun

```bash
python scripts/troubleshoot_smtp.py --full \
    --host smtp.mailgun.org \
    --port 587 \
    --username postmaster@your-domain.mailgun.org \
    --password "your-mailgun-password" \
    --use-tls
```

### AWS SES

```bash
python scripts/troubleshoot_smtp.py --full \
    --host email-smtp.us-east-1.amazonaws.com \
    --port 587 \
    --username "your-ses-smtp-username" \
    --password "your-ses-smtp-password" \
    --use-tls
```

### Local Development (MailHog/Mailpit)

```bash
python scripts/troubleshoot_smtp.py --full \
    --host localhost \
    --port 1025 \
    --no-tls
```

## Understanding the Output

### Full Diagnostic Output

```
1. TCP Connection Test
   ✓ Connected successfully in 0.12s

2. SMTP Banner Test
   ✓ SMTP banner received
   ℹ Banner: 220 smtp.gmail.com ESMTP...

3. Common SMTP Ports Scan
   Port    25: ✗ Closed/Filtered
   Port   465: ✓ Open
   Port   587: ✓ Open
   Port  1025: ✗ Closed/Filtered
   Port  2525: ✗ Closed/Filtered

4. TLS/SSL Tests
   ✓ STARTTLS: STARTTLS supported and working
   ℹ TLS Version: TLSv1.3
   ℹ Cipher: ('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)

5. Authentication Test
   ✓ Authentication successful

6. Configuration Summary
   ℹ Transactional Email Settings:
     EMAIL_ENABLED: True
     EMAIL_SMTP_HOST: smtp.gmail.com
     EMAIL_SMTP_PORT: 587
     EMAIL_SMTP_USERNAME: user@example.com
     EMAIL_SMTP_USE_TLS: True
     EMAIL_SMTP_USE_SSL: False
```

## Troubleshooting Workflow

1. **Start with Quick Test**: Run `--quick` to verify basic connectivity
2. **Run Full Diagnostics**: Use `--full` to identify specific issues
3. **Check DNS Records**: Use `--check-dns` to verify email authentication
4. **Test Authentication**: Add credentials to test login
5. **Send Test Email**: Use `--send-test` to verify end-to-end delivery
6. **Review Logs**: Check application logs for detailed error messages

## Related Scripts

- **test_smtp_config.py**: Original SMTP testing script with SMTPy integration
- **troubleshoot_smtp.py**: Comprehensive standalone troubleshooting tool (this script)

## Additional Resources

- [SMTPy Documentation](../README.md)
- [SMTP Port Guide](https://www.mailgun.com/blog/which-smtp-port-understanding-ports-25-465-587/)
- [Gmail SMTP Setup](https://support.google.com/mail/answer/7126229)
- [SPF Record Guide](https://www.cloudflare.com/learning/dns/dns-records/dns-spf-record/)
- [DKIM Guide](https://www.cloudflare.com/learning/dns/dns-records/dns-dkim-record/)
- [DMARC Guide](https://www.cloudflare.com/learning/dns/dns-records/dns-dmarc-record/)

## Getting Help

If you're still experiencing issues after using this script:

1. Review the detailed error messages
2. Check the SMTPy logs for additional context
3. Verify your environment variables in `.env`
4. Test with a known-working SMTP provider (like Gmail) to isolate the issue
5. Check your hosting provider's documentation for SMTP restrictions
6. Open an issue on the SMTPy GitHub repository with the diagnostic output
