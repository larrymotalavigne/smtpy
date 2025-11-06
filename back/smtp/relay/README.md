# SMTP Relay Service

Self-hosted SMTP delivery system with optional external relay fallback for SMTPy.

## Overview

This module provides multiple email delivery strategies:

1. **Direct SMTP** - Self-hosted delivery directly to recipient mail servers (no external dependencies)
2. **External Relay** - Delivery via Gmail, SendGrid, or other SMTP services
3. **Hybrid** - Direct delivery with automatic fallback to external relay on failure
4. **Smart** - Intelligent routing based on domain reputation (future)

## Architecture

```
Email Received (mail.smtpy.fr:25)
    ↓
SMTP Handler (resolves aliases)
    ↓
Hybrid Relay Service
    ├─ DKIM Signer (signs all emails)
    ↓
    ├─ Direct SMTP (primary)
    │  ├─ MX Lookup (with caching)
    │  ├─ Connect to recipient MX
    │  ├─ STARTTLS negotiation
    │  └─ Deliver directly
    │
    └─ External Relay (fallback, optional)
       └─ Gmail/SendGrid/etc
```

## Configuration

### Environment Variables

Add to your `.env` or `.env.production`:

```bash
# Self-hosted SMTP Settings
SMTP_HOSTNAME=mail.smtpy.fr              # Your sending hostname (FQDN)
SMTP_DELIVERY_MODE=direct                # 'direct', 'relay', 'hybrid', or 'smart'
SMTP_ENABLE_DKIM=true                    # Enable DKIM signing

# External Relay Settings (optional, only for 'relay' or 'hybrid' modes)
SMTP_USER=your-email@gmail.com           # SMTP username
SMTP_PASSWORD=your-app-password          # SMTP password
SMTP_HOST=smtp.gmail.com                 # SMTP host
SMTP_PORT=587                            # SMTP port
SMTP_USE_TLS=true                        # Use STARTTLS
SMTP_USE_SSL=false                       # Use SSL/TLS (port 465)
```

### Delivery Modes

#### 1. Direct Only (Default, Recommended)
**Use case:** Full self-hosted solution, no external dependencies

```bash
SMTP_DELIVERY_MODE=direct
```

**Pros:**
- No external dependencies
- No relay credentials needed
- Complete control over delivery
- Lower latency
- No per-email costs

**Cons:**
- Requires proper DNS setup (MX, SPF, DKIM, reverse DNS)
- IP reputation management required
- Some domains may have stricter filtering

#### 2. Relay Only
**Use case:** Use external service exclusively (Gmail, SendGrid)

```bash
SMTP_DELIVERY_MODE=relay
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Pros:**
- Leverages established sender reputation
- Easier initial setup
- Higher deliverability for cold IPs

**Cons:**
- Requires external credentials
- May have sending limits
- Per-email costs (for paid services)
- External dependency

#### 3. Hybrid (Best of Both)
**Use case:** Try direct first, fall back to relay on failure

```bash
SMTP_DELIVERY_MODE=hybrid
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Pros:**
- Best of both worlds
- Automatic failover
- Gradual IP warm-up possible
- Resilient to delivery issues

**Cons:**
- Requires both setups
- More complex configuration

#### 4. Smart (Future)
**Use case:** AI-driven routing based on domain reputation

```bash
SMTP_DELIVERY_MODE=smart
```

Currently behaves like hybrid mode. Future enhancements:
- Track per-domain success rates
- Learn which domains prefer direct vs relay
- Automatic routing optimization

## DNS Setup for Self-Hosted SMTP

### Required DNS Records

#### 1. MX Record (for receiving)
```
example.com.  IN  MX  10 mail.smtpy.fr.
```

#### 2. A Record (for mail server)
```
mail.smtpy.fr.  IN  A  45.80.25.57
```

#### 3. Reverse DNS (PTR Record)
**Critical for deliverability!**

Contact your hosting provider to set:
```
45.80.25.57  →  mail.smtpy.fr
```

Verify with:
```bash
dig -x 45.80.25.57
```

#### 4. SPF Record
```
example.com.  IN  TXT  "v=spf1 include:smtpy.fr ~all"
```

Or for direct sending:
```
example.com.  IN  TXT  "v=spf1 ip4:45.80.25.57 ~all"
```

#### 5. DKIM Record
Generate DKIM keys (done automatically in SMTPy), then add:
```
default._domainkey.example.com.  IN  TXT  "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3..."
```

#### 6. DMARC Record
```
_dmarc.example.com.  IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
```

### DNS Verification

Test your DNS setup:
```bash
# Check MX records
dig example.com MX

# Check SPF
dig example.com TXT

# Check DKIM
dig default._domainkey.example.com TXT

# Check DMARC
dig _dmarc.example.com TXT

# Check reverse DNS
dig -x 45.80.25.57
```

## Components

### 1. Direct SMTP Service (`direct_smtp.py`)

Self-hosted SMTP delivery engine.

**Features:**
- MX record lookup with DNS resolver
- MX record caching (1 hour TTL)
- Direct connection to recipient mail servers
- STARTTLS negotiation
- Retry logic with exponential backoff (2s, 4s, 8s)
- Per-domain rate limiting (10 connections/min)
- Bounce handling (permanent vs temporary)
- Connection pooling and statistics

**Usage:**
```python
from smtp.relay import get_direct_smtp_service

service = get_direct_smtp_service()

# Send to single recipient
success = await service.send_email(
    message=email_message,
    recipient="user@example.com",
    mail_from="noreply@smtpy.fr"
)

# Send to multiple recipients
results = await service.send_email_bulk(
    message=email_message,
    recipients=["user1@example.com", "user2@example.com"],
    mail_from="noreply@smtpy.fr"
)
# Returns: {"user1@example.com": True, "user2@example.com": False}
```

### 2. DKIM Signer (`dkim_signer.py`)

Email authentication using DomainKeys Identified Mail.

**Features:**
- Automatic domain key lookup from database
- Signs with domain-specific DKIM private keys
- Configurable selector (default: "smtpy")
- Graceful fallback to unsigned on error

**Usage:**
```python
from smtp.relay import sign_email_dkim

# Automatic signing (looks up key by domain)
signed_message = await sign_email_dkim(
    message=email_message,
    mail_from="sender@example.com"
)
```

### 3. Hybrid Relay Service (`hybrid_relay.py`)

Intelligent routing layer combining direct and relay delivery.

**Features:**
- Four delivery modes (direct/relay/hybrid/smart)
- Automatic DKIM signing
- Per-recipient result tracking
- Automatic fallback on failure
- Comprehensive statistics

**Usage:**
```python
from smtp.relay import send_email_hybrid, EmailPriority

# Send with hybrid strategy
results = await send_email_hybrid(
    message=email_message,
    recipients=["user@example.com"],
    mail_from="noreply@smtpy.fr",
    priority=EmailPriority.NORMAL
)
# Returns: {"user@example.com": True}
```

### 4. External Relay Service (`relay_service.py`)

Connection to external SMTP services (Gmail, SendGrid, etc).

**Features:**
- Async connection pooling
- Priority queue (HIGH/NORMAL/LOW)
- Retry logic with exponential backoff
- Rate limiting
- Connection reuse

## Monitoring and Statistics

### Get Service Statistics

```python
from smtp.relay import get_hybrid_relay

relay = get_hybrid_relay()
stats = relay.get_stats()

print(stats)
# {
#     "mode": "hybrid",
#     "direct_sent": 150,
#     "direct_failed": 5,
#     "relay_sent": 3,
#     "relay_failed": 0,
#     "dkim_signed": 153,
#     "dkim_unsigned": 5,
#     "direct_service": {
#         "sent": 150,
#         "failed": 5,
#         "deferred": 8,
#         "bounced": 2,
#         "mx_lookups": 45,
#         "mx_cache_hits": 110,
#         "mx_cache_size": 23
#     }
# }
```

### Logs

All SMTP operations are logged with structured data:

```python
logging.info(
    "Successfully delivered email",
    extra={
        "sender": "sender@example.com",
        "recipient": "user@example.com",
        "subject": "Test Email",
        "action": "forward",
        "mx_host": "mx.example.com"
    }
)
```

## Deployment

### Development

The system works out of the box in development with direct mode:

```bash
# Start SMTP server (already configured in docker-compose.yml)
docker-compose up smtp
```

### Production

#### 1. Firewall Configuration

Open port 25 for outbound SMTP:
```bash
# Allow outbound SMTP
sudo ufw allow out 25/tcp

# Allow inbound SMTP (receiving)
sudo ufw allow 25/tcp
```

#### 2. Server Configuration

Ensure your server can send on port 25:
```bash
# Test connectivity
telnet mx.example.com 25
```

Some cloud providers (AWS, GCP, Azure) block port 25 by default. You may need to:
- Request port 25 unblocking from support
- Use elastic/static IP with reverse DNS
- Set up SMTP relay as fallback

#### 3. Environment Variables

Update `.env.production`:
```bash
SMTP_HOSTNAME=mail.smtpy.fr
SMTP_DELIVERY_MODE=direct
SMTP_ENABLE_DKIM=true
```

#### 4. DNS Records

Set up all required DNS records (see DNS Setup section above).

**Critical:** Configure reverse DNS (PTR record) with your hosting provider!

#### 5. IP Warm-up

For new IPs, gradually increase sending volume:
- Day 1-3: 50 emails/day
- Day 4-7: 200 emails/day
- Day 8-14: 500 emails/day
- Day 15+: Full volume

Consider using hybrid mode during warm-up:
```bash
SMTP_DELIVERY_MODE=hybrid  # Falls back to relay if direct fails
```

## Troubleshooting

### Issue: Emails not being delivered

**Check:**
1. DNS records are correct
2. Reverse DNS (PTR) is set
3. Port 25 is open outbound
4. Check logs for specific errors

```bash
# View SMTP logs
docker logs smtpy-smtp-1 -f
```

### Issue: High bounce rate

**Possible causes:**
1. Missing or incorrect SPF record
2. Missing or incorrect DKIM signature
3. No reverse DNS configured
4. IP on blocklist
5. Poor sender reputation

**Solutions:**
1. Verify all DNS records
2. Check DKIM signing is enabled
3. Test email authentication: https://www.mail-tester.com/
4. Check IP reputation: https://mxtoolbox.com/blacklists.aspx
5. Use hybrid mode with relay fallback

### Issue: DKIM signatures not working

**Check:**
1. DKIM private key is set in domain settings
2. DKIM public key DNS record is published
3. `SMTP_ENABLE_DKIM=true` is set

**Test DKIM:**
```bash
# Send test email to check-auth@verifier.port25.com
# You'll receive a report with DKIM verification results
```

### Issue: Rate limiting or deferred deliveries

**Check:**
1. Per-domain rate limits (10 conn/min default)
2. Recipient server rate limits
3. IP reputation

**Solutions:**
1. Adjust rate limits in DirectSMTPService
2. Use hybrid mode to spread load
3. Implement sending queue with delays

## Testing

### Test Direct SMTP Delivery

```bash
# Send test email
cd back
python -c "
import asyncio
from email.message import EmailMessage
from smtp.relay import send_direct

async def test():
    msg = EmailMessage()
    msg['Subject'] = 'Test Email'
    msg['From'] = 'noreply@smtpy.fr'
    msg['To'] = 'test@example.com'
    msg.set_content('This is a test email.')

    results = await send_direct(msg, ['test@example.com'])
    print(f'Results: {results}')

asyncio.run(test())
"
```

### Test DKIM Signing

Send a test email to: check-auth@verifier.port25.com

You'll receive an automated report showing:
- SPF status
- DKIM signature verification
- DMARC status

### Test Email Deliverability

Use these services:
- https://www.mail-tester.com/
- https://www.email-validator.net/
- https://mxtoolbox.com/emailhealth/

## Performance

### Benchmarks

- **MX Lookup:** ~50-100ms (first lookup), ~0.1ms (cached)
- **Direct Delivery:** ~200-500ms per email
- **Concurrent Sending:** 50+ emails/second
- **MX Cache Hit Rate:** 90%+

### Optimization Tips

1. **Enable MX caching** (enabled by default, 1 hour TTL)
2. **Use bulk sending** for multiple recipients
3. **Adjust rate limits** based on your volume
4. **Monitor stats** to identify bottlenecks
5. **Use async sending** for better throughput

## Gmail Configuration (for Relay Mode)

### Step 1: Enable 2-Factor Authentication

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification

### Step 2: Generate App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "SMTPy Relay"
4. Copy the generated password

### Step 3: Configure SMTPy

```bash
# In .env.production
SMTP_DELIVERY_MODE=relay
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
```

## SendGrid Configuration (for Relay Mode)

### Step 1: Get API Key

1. Sign up at https://sendgrid.com
2. Create an API key with "Mail Send" permissions

### Step 2: Configure SMTPy

```bash
# In .env.production
SMTP_DELIVERY_MODE=relay
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
```

## Security Considerations

1. **DKIM Signing:** Always enable DKIM signing in production
2. **SPF Records:** Configure SPF to prevent spoofing
3. **DMARC Policy:** Start with p=none, gradually move to p=quarantine
4. **Rate Limiting:** Prevent abuse with per-domain limits
5. **Input Validation:** All email addresses are validated
6. **TLS:** STARTTLS is attempted for all connections
7. **Credentials:** Never commit SMTP passwords to git

## Future Enhancements

- [ ] Smart routing based on domain reputation
- [ ] Automatic IP warm-up scheduling
- [ ] Enhanced bounce classification
- [ ] Delivery queue with retry scheduling
- [ ] Real-time deliverability monitoring
- [ ] Automatic blocklist checking
- [ ] Multi-IP rotation for high volume
- [ ] Enhanced statistics and reporting
- [ ] Webhook notifications for delivery events

## Support

For issues or questions:
1. Check logs: `docker logs smtpy-smtp-1 -f`
2. Test DNS: `dig example.com MX`
3. Test connectivity: `telnet mx.example.com 25`
4. Check IP reputation: https://mxtoolbox.com/

## References

- [RFC 5321 - SMTP](https://tools.ietf.org/html/rfc5321)
- [RFC 6376 - DKIM](https://tools.ietf.org/html/rfc6376)
- [RFC 7208 - SPF](https://tools.ietf.org/html/rfc7208)
- [RFC 7489 - DMARC](https://tools.ietf.org/html/rfc7489)
