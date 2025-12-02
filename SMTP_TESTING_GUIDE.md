# SMTP Testing Guide for SMTPy with mail.atomdev.fr

Complete guide for testing SMTP configuration with `mail.atomdev.fr`.

## Quick Start

```bash
# 1. Test connectivity to mail.atomdev.fr
./test-smtp.sh

# 2. Check SMTP configuration
cd back && python scripts/test_smtp_config.py --check-config

# 3. Send test transactional email
cd back && python scripts/test_smtp_config.py --test-transactional your@email.com

# 4. Test SMTP relay
cd back && python scripts/test_smtp_config.py --test-relay sender@domain.com recipient@email.com
```

---

## Configuration for mail.atomdev.fr

### 1. Create `.env.production`

```bash
cp .env.production.template .env.production
```

### 2. Add SMTP Configuration

Edit `.env.production` and add:

```bash
# =============================================================================
# SMTP CONFIGURATION FOR mail.atomdev.fr
# =============================================================================

# Transactional Emails (password reset, welcome emails, etc.)
EMAIL_ENABLED=true
EMAIL_BACKEND=smtp
EMAIL_FROM=noreply@atomdev.fr
EMAIL_FROM_NAME=SMTPy
EMAIL_SMTP_HOST=mail.atomdev.fr
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=your-smtp-username
EMAIL_SMTP_PASSWORD=your-smtp-password
EMAIL_SMTP_USE_TLS=true
EMAIL_SMTP_USE_SSL=false

# SMTP Relay (for email forwarding - optional)
SMTP_HOST=mail.atomdev.fr
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_HOSTNAME=mail.atomdev.fr
SMTP_DELIVERY_MODE=hybrid  # or "direct" or "relay"
SMTP_ENABLE_DKIM=true

# Application URL (for email links)
APP_URL=https://yourdomain.com
```

### Common Port Configurations

**Port 587 (STARTTLS) - Recommended:**
```bash
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USE_TLS=true
EMAIL_SMTP_USE_SSL=false
```

**Port 465 (SSL/TLS):**
```bash
EMAIL_SMTP_PORT=465
EMAIL_SMTP_USE_TLS=false
EMAIL_SMTP_USE_SSL=true
```

**Port 25 (unencrypted - not recommended):**
```bash
EMAIL_SMTP_PORT=25
EMAIL_SMTP_USE_TLS=false
EMAIL_SMTP_USE_SSL=false
```

---

## Testing Methods

### Method 1: Shell Script - Connectivity Test

Tests DNS, port accessibility, and SMTP banner.

```bash
./test-smtp.sh
```

**What it tests:**
- DNS resolution of mail.atomdev.fr
- Port 587 (STARTTLS) accessibility
- Port 465 (SSL/TLS) accessibility
- Port 25 (standard SMTP) accessibility
- SMTP banner response
- EHLO command support
- Environment variables check

### Method 2: Python Script - Configuration Check

Shows current SMTP settings from environment variables.

```bash
cd back
python scripts/test_smtp_config.py --check-config
```

**Output:**
```
SMTP CONFIGURATION CHECK
========================================

📧 TRANSACTIONAL EMAIL SETTINGS:
  EMAIL_ENABLED: True
  EMAIL_BACKEND: smtp
  EMAIL_FROM: noreply@atomdev.fr
  EMAIL_SMTP_HOST: mail.atomdev.fr
  EMAIL_SMTP_PORT: 587
  ...
```

### Method 3: Python Script - Test Transactional Email

Sends an actual test email (password reset template).

```bash
cd back
python scripts/test_smtp_config.py --test-transactional recipient@example.com
```

**What it does:**
- Connects to mail.atomdev.fr
- Authenticates with credentials
- Sends a password reset email
- Reports success or failure

### Method 4: Python Script - Test SMTP Relay

Tests the SMTP relay functionality.

```bash
cd back
python scripts/test_smtp_config.py --test-relay sender@domain.com recipient@example.com
```

### Method 5: Manual Command Line Test

#### Using `nc` (netcat):

```bash
# Test port 587
nc -zv mail.atomdev.fr 587

# Get SMTP banner
echo "QUIT" | nc mail.atomdev.fr 587

# Test EHLO command
echo -e "EHLO test.com\nQUIT" | nc mail.atomdev.fr 587
```

#### Using `telnet`:

```bash
telnet mail.atomdev.fr 587

# Then type:
EHLO test.com
QUIT
```

#### Using `openssl` for TLS test:

```bash
openssl s_client -starttls smtp -connect mail.atomdev.fr:587 -crlf

# Then type:
EHLO test.com
MAIL FROM:<test@example.com>
RCPT TO:<recipient@example.com>
QUIT
```

### Method 6: Python Interactive Test

```python
cd back
python

# In Python shell:
from shared.core.config import SETTINGS
from api.services.email_service import EmailService

# Check configuration
print(f"SMTP Host: {SETTINGS.EMAIL_SMTP_HOST}")
print(f"SMTP Port: {SETTINGS.EMAIL_SMTP_PORT}")

# Send test email
success = EmailService.send_password_reset_email(
    to="your@email.com",
    username="TestUser",
    reset_token="test-123"
)

print(f"Email sent: {success}")
```

### Method 7: Docker Container Test

Test from within the API container:

```bash
# Enter the container
docker exec -it smtpy-api-dev bash

# Or for production
docker exec -it smtpy-api-prod bash

# Run test script inside container
python scripts/test_smtp_config.py --check-config
python scripts/test_smtp_config.py --test-transactional your@email.com
```

### Method 8: cURL SMTP Test

```bash
# Test sending via curl
curl --url "smtp://mail.atomdev.fr:587" \
     --ssl-reqd \
     --mail-from "sender@domain.com" \
     --mail-rcpt "recipient@example.com" \
     --upload-file - \
     --user "your-username:your-password" \
     << EOF
From: sender@domain.com
To: recipient@example.com
Subject: Test Email

This is a test email from curl.
EOF
```

### Method 9: Use Existing Tests

Run the existing test suite:

```bash
cd back

# Run all tests
pytest tests/

# Run specific test
pytest tests/test_auth_integration.py -v

# Run with output
pytest tests/test_auth_integration.py -v -s
```

### Method 10: Integration Test via API

Test through the actual API endpoints:

```bash
# 1. Start the API server
docker-compose up -d api

# 2. Trigger password reset (which sends email)
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 3. Check API logs
docker logs smtpy-api-dev -f
```

---

## Troubleshooting

### Issue: Connection Timeout

```bash
# Check if mail.atomdev.fr is reachable
ping mail.atomdev.fr

# Check DNS
dig mail.atomdev.fr

# Check port
nc -zv mail.atomdev.fr 587
```

### Issue: Authentication Failed

```bash
# Verify credentials are correct
cd back
python scripts/test_smtp_config.py --check-config

# Check if username/password are properly set
grep EMAIL_SMTP .env.production | grep -v PASSWORD
```

### Issue: TLS/SSL Errors

```bash
# Test TLS connection
openssl s_client -starttls smtp -connect mail.atomdev.fr:587

# If using SSL (port 465), test with:
openssl s_client -connect mail.atomdev.fr:465
```

### Issue: Email Not Received

1. **Check spam folder**
2. **Verify sender email** is allowed by recipient server
3. **Test with different recipient** (Gmail, Yahoo, etc.)
4. **Check email logs:**
   ```bash
   docker logs smtpy-api-dev | grep -i email
   docker logs smtpy-api-dev | grep -i smtp
   ```

### Issue: Permission Denied

```bash
# Make scripts executable
chmod +x test-smtp.sh
chmod +x back/scripts/test_smtp_config.py
```

### Debug Mode

Enable debug logging in `.env.production`:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

Then check logs:
```bash
docker logs smtpy-api-dev -f | grep -i smtp
```

---

## Common SMTP Server Configurations

### Gmail (for comparison)

```bash
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USE_TLS=true
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password  # Not regular password!
```

### Office 365 / Outlook

```bash
EMAIL_SMTP_HOST=smtp.office365.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USE_TLS=true
EMAIL_SMTP_USERNAME=your-email@domain.com
EMAIL_SMTP_PASSWORD=your-password
```

### SendGrid

```bash
EMAIL_SMTP_HOST=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USE_TLS=true
EMAIL_SMTP_USERNAME=apikey
EMAIL_SMTP_PASSWORD=your-sendgrid-api-key
```

---

## Expected Test Results

### Successful Connection

```
✅ DNS resolved: mail.atomdev.fr -> x.x.x.x
✅ Port 587 is accessible
✅ SMTP banner received: 220 mail.atomdev.fr ESMTP
✅ SMTP server responds to EHLO
✅ STARTTLS is supported
```

### Successful Email Send

```
✅ Email sent successfully!
📬 Check inbox at: recipient@example.com
   Subject: 'Reset Your SMTPy Password'
```

### Configuration Validation

```
✅ EMAIL_ENABLED is True
✅ EMAIL_SMTP_HOST configured
✅ EMAIL_SMTP_PORT configured
✅ Credentials set
✅ TLS enabled
```

---

## Production Checklist

Before deploying to production:

- [ ] Test connectivity: `./test-smtp.sh`
- [ ] Verify config: `python scripts/test_smtp_config.py --check-config`
- [ ] Send test email: `python scripts/test_smtp_config.py --test-transactional`
- [ ] Test from container: `docker exec smtpy-api-prod python scripts/test_smtp_config.py --check-config`
- [ ] Verify email received (check spam folder)
- [ ] Test password reset flow via UI
- [ ] Check logs for errors
- [ ] Verify SPF/DKIM records (if applicable)
- [ ] Test with multiple email providers (Gmail, Yahoo, Outlook)

---

## Quick Reference Commands

```bash
# Full test suite
./test-smtp.sh && \
cd back && \
python scripts/test_smtp_config.py --check-config && \
python scripts/test_smtp_config.py --test-transactional your@email.com

# Just check config
cd back && python scripts/test_smtp_config.py --check-config

# Quick connectivity test
nc -zv mail.atomdev.fr 587

# View logs
docker logs smtpy-api-dev -f | grep -i smtp

# Test from inside container
docker exec -it smtpy-api-dev python scripts/test_smtp_config.py --test-transactional your@email.com
```

---

## Resources

- **Existing Documentation:**
  - `MAIL_TESTING_COMMANDS.md` - Manual testing commands
  - `MAIL_SERVER_TEST_RESULTS.md` - Test results and DNS setup
  - `back/smtp/relay/README.md` - SMTP relay documentation
  - `.env.production.template` - Configuration template

- **Test Scripts:**
  - `test-smtp.sh` - Shell connectivity test
  - `back/scripts/test_smtp_config.py` - Python SMTP test

- **Code References:**
  - `back/api/services/email_service.py` - Email service implementation
  - `back/shared/core/config.py` - Configuration settings

---

## Support

If you encounter issues:

1. Run diagnostics: `./test-smtp.sh`
2. Check configuration: `cd back && python scripts/test_smtp_config.py --check-config`
3. Review logs: `docker logs smtpy-api-dev | grep -i smtp`
4. Verify credentials with mail.atomdev.fr provider
5. Test with different email providers
6. Check firewall/network settings
