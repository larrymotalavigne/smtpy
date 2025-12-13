# Postfix Relay Access Denied - Troubleshooting Guide

## Understanding the Error

When you see this error in your Postfix logs:

```
NOQUEUE: reject: RCPT from mail-ed1-f47.google.com[209.85.208.47]:
554 5.7.1 <test@motalavigne.fr>: Relay access denied;
from=<larry.motalavigne@gmail.com> to=<test@motalavigne.fr>
```

This means:
- **External server** (Google) is trying to deliver mail to your server
- **Recipient** is `test@motalavigne.fr`
- **Your Postfix** rejects it because `motalavigne.fr` is not configured as a local/virtual domain

## Two Different Email Flows in SMTPy

### Flow 1: Receiving Email (Where the error occurs)
```
Internet → Postfix (port 25) → SMTPy Receiver (port 2525) → Database → Forward to target
```

**Problem**: Postfix rejects email because `motalavigne.fr` is not configured

### Flow 2: Sending Email (Your MAILSERVER config)
```
SMTPy → Postfix (port 587) → Internet
```

**Status**: Your `noreply@smtpy.fr` configuration is correct for this

## Solution: Configure Postfix to Accept motalavigne.fr

You need to tell Postfix that `motalavigne.fr` is a domain it should accept mail for.

### Step 1: Check Current Configuration

```bash
# Check what domains Postfix currently accepts
docker exec mailserver postconf virtual_mailbox_domains
docker exec mailserver postconf mydestination

# Check virtual mailbox maps
docker exec mailserver postconf virtual_mailbox_maps
```

### Step 2: Add motalavigne.fr as a Virtual Domain

#### Option A: Using Docker Mail Server Commands

```bash
# Add domain to virtual domains
docker exec mailserver setup config dkim domain motalavigne.fr

# Create a mailbox for the domain (if needed)
docker exec mailserver setup email add test@motalavigne.fr somepassword

# Or set up catch-all forwarding
docker exec mailserver setup alias add @motalavigne.fr forward@yourdomain.com
```

#### Option B: Manual Configuration

Create/edit `docker-compose.override.yml` in your mailserver directory:

```yaml
services:
  mailserver:
    volumes:
      - ./docker-data/dms/mail-state:/var/mail-state
      - ./docker-data/dms/config:/tmp/docker-mailserver
```

Then create `docker-data/dms/config/postfix-virtual.cf`:

```
@motalavigne.fr    forward-to-smtpy@localhost
```

And restart:

```bash
docker compose restart mailserver
```

### Step 3: Forward to SMTPy

You want emails to `motalavigne.fr` to go to SMTPy for processing.

#### Configure Virtual Alias to Forward to SMTPy

Create `docker-data/dms/config/postfix-main.cf`:

```
# Add motalavigne.fr as virtual domain
virtual_mailbox_domains = motalavigne.fr, smtpy.fr

# Transport map to route to SMTPy
transport_maps = hash:/etc/postfix/transport
```

Create `docker-data/dms/config/postfix-transport`:

```
motalavigne.fr    smtp:[smtpy-smtp-receiver]:2525
```

Then apply:

```bash
docker exec mailserver postmap /etc/postfix/transport
docker exec mailserver postfix reload
```

## Complete Setup Example

Here's a complete setup for receiving email at SMTPy domains:

### 1. Docker Mail Server Configuration

Create `docker-data/dms/config/postfix-main.cf`:

```
# Virtual domains handled by SMTPy
virtual_mailbox_domains = motalavigne.fr, smtpy.fr

# Local domains (for accounts on this server)
mydestination = mail.yourdomain.com, localhost

# Transport to SMTPy for virtual domains
transport_maps = hash:/etc/postfix/transport

# Relay settings
mynetworks = 127.0.0.0/8 [::1]/128 172.16.0.0/12 192.168.0.0/16
```

### 2. Transport Map

Create `docker-data/dms/config/postfix-transport`:

```
# Route SMTPy domains to SMTP receiver
motalavigne.fr         smtp:[smtpy-smtp-receiver]:2525
smtpy.fr              smtp:[smtpy-smtp-receiver]:2525
```

### 3. Apply Configuration

```bash
# Rebuild transport map
docker exec mailserver postmap /etc/postfix/transport

# Reload Postfix
docker exec mailserver postfix reload

# Verify configuration
docker exec mailserver postconf virtual_mailbox_domains
docker exec mailserver postconf transport_maps
```

### 4. Test Email Flow

```bash
# Send test email
echo "Test message" | mail -s "Test" test@motalavigne.fr

# Watch SMTPy receiver logs
docker logs -f smtpy-smtp-receiver

# Watch Postfix logs
docker exec mailserver tail -f /var/log/mail.log
```

## Verify SMTPy MAILSERVER Configuration

While fixing the inbound issue, also verify your SMTPy outbound configuration:

### Check Environment Variables

```bash
# Check SMTP receiver has correct mailserver config
docker compose -f docker-compose.prod.yml exec smtp-receiver env | grep MAILSERVER
docker compose -f docker-compose.prod.yml exec smtp-receiver env | grep EMAIL_FROM
```

Should show:
```
MAILSERVER_HOST=mailserver
MAILSERVER_PORT=587
MAILSERVER_USER=noreply@smtpy.fr
MAILSERVER_PASSWORD=***
MAILSERVER_USE_TLS=true
EMAIL_FROM=noreply@smtpy.fr
EMAIL_FROM_NAME=SMTPy
```

### Verify Account Exists

```bash
# Check if noreply@smtpy.fr account exists in mailserver
docker exec mailserver setup email list

# If not, create it
docker exec mailserver setup email add noreply@smtpy.fr yourpassword
```

### Test SMTP Authentication

```bash
# Test connection and auth
docker compose -f docker-compose.prod.yml exec smtp-receiver python3 -c "
import asyncio
import aiosmtplib
import os

async def test():
    try:
        smtp = aiosmtplib.SMTP(
            hostname=os.getenv('MAILSERVER_HOST', 'mailserver'),
            port=int(os.getenv('MAILSERVER_PORT', '587')),
            use_tls=os.getenv('MAILSERVER_USE_TLS', 'true').lower() == 'true'
        )
        await smtp.connect()

        user = os.getenv('MAILSERVER_USER', '')
        password = os.getenv('MAILSERVER_PASSWORD', '')

        if user and password:
            await smtp.login(user, password)
            print('✅ Connection and authentication successful!')
        else:
            print('✅ Connection successful (no auth configured)')

        await smtp.quit()
    except Exception as e:
        print(f'❌ Connection failed: {e}')

asyncio.run(test())
"
```

## Common Issues and Solutions

### Issue 1: Still Getting "Relay Access Denied"

**Symptoms**: After configuration, still seeing 554 5.7.1 errors

**Solutions**:
1. Verify domain is in `virtual_mailbox_domains`:
   ```bash
   docker exec mailserver postconf virtual_mailbox_domains
   ```

2. Check transport map exists:
   ```bash
   docker exec mailserver ls -la /etc/postfix/transport*
   ```

3. Verify SMTPy receiver is reachable:
   ```bash
   docker exec mailserver telnet smtpy-smtp-receiver 2525
   ```

4. Check Postfix can resolve SMTPy container:
   ```bash
   docker exec mailserver ping smtpy-smtp-receiver
   ```

### Issue 2: "Authentication Failed" When Forwarding

**Symptoms**: SMTPy can't authenticate to send forwarded emails

**Solutions**:
1. Verify credentials are correct in `.env.production`
2. Check account exists: `docker exec mailserver setup email list`
3. Reset password: `docker exec mailserver setup email update noreply@smtpy.fr newpassword`
4. Check logs: `docker logs smtpy-smtp-receiver`

### Issue 3: "Connection Refused" to Mailserver

**Symptoms**: SMTPy can't connect to mailserver

**Solutions**:
1. Verify mailserver is running: `docker ps | grep mailserver`
2. Check port is correct (587 for submission, 25 for relay)
3. Verify Docker network: `docker network inspect smtpy_default`
4. Test connectivity: `docker exec smtpy-smtp-receiver telnet mailserver 587`

## Network Configuration

Make sure SMTPy and mailserver are on the same Docker network:

### Option 1: Same docker-compose.yml

```yaml
services:
  mailserver:
    # ... mailserver config
    networks:
      - smtpy-network

  smtp-receiver:
    # ... smtp-receiver config
    networks:
      - smtpy-network

networks:
  smtpy-network:
    driver: bridge
```

### Option 2: External Network

If mailserver is in a separate compose file:

```bash
# Create shared network
docker network create smtpy-network

# In mailserver docker-compose.yml
networks:
  default:
    external: true
    name: smtpy-network

# In SMTPy docker-compose.prod.yml
networks:
  smtpy-network:
    external: true
```

## Testing the Complete Flow

### 1. Test Inbound Email

```bash
# Send email to your domain
echo "Test inbound" | mail -s "Inbound Test" alias@motalavigne.fr

# Watch SMTPy receiver process it
docker logs -f smtpy-smtp-receiver

# Should see:
# - "Received email from ..."
# - "Found alias: ..."
# - "Forwarding email..."
# - "Successfully forwarded..."
```

### 2. Test Outbound Email

```bash
# Trigger a notification (e.g., password reset)
# Or send test via API

# Watch for successful authentication
docker logs -f smtpy-smtp-receiver | grep -i "forward"

# Check mailserver logs
docker exec mailserver tail -f /var/log/mail.log
```

## Reference: Email Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ INBOUND EMAIL (Receiving)                                    │
└─────────────────────────────────────────────────────────────┘

Internet (Gmail, etc.)
  │
  │ SMTP (port 25)
  ↓
Postfix Mailserver
  │
  │ Check: Is this for virtual_mailbox_domains?
  │ - motalavigne.fr? ✅
  │ - Use transport_maps to find destination
  ↓
SMTPy SMTP Receiver (port 2525)
  │
  │ 1. Parse email
  │ 2. Check database for alias
  │ 3. Apply forwarding rules
  ↓
Database (lookup alias targets)
  │
  ↓
Forward to target(s)


┌─────────────────────────────────────────────────────────────┐
│ OUTBOUND EMAIL (Forwarding & Notifications)                  │
└─────────────────────────────────────────────────────────────┘

SMTPy (forwarding or notification)
  │
  │ SMTP (port 587) with auth
  │ USER: noreply@smtpy.fr
  │ PASS: *** (from MAILSERVER_PASSWORD)
  │ FROM: noreply@smtpy.fr (EMAIL_FROM)
  ↓
Postfix Mailserver
  │
  │ 1. Authenticate user
  │ 2. Verify sender is authorized
  │ 3. Accept for relay
  ↓
Internet (final recipient)
```

## Summary Checklist

- [ ] Postfix configured with `virtual_mailbox_domains` for your domains
- [ ] Transport map routes your domains to SMTPy receiver
- [ ] SMTPy receiver accessible from mailserver (port 2525)
- [ ] Mailserver account created for `noreply@smtpy.fr`
- [ ] SMTPy environment variables configured correctly
- [ ] Both services on same Docker network
- [ ] Test inbound email flow works
- [ ] Test outbound email flow works
- [ ] Check logs for both flows

## Getting Help

If issues persist:

1. **Collect logs**:
   ```bash
   docker logs smtpy-smtp-receiver > smtpy-receiver.log
   docker exec mailserver tail -200 /var/log/mail.log > mailserver.log
   ```

2. **Check configuration**:
   ```bash
   docker exec mailserver postconf -n > postfix-config.txt
   ```

3. **Test connectivity**:
   ```bash
   docker exec smtpy-smtp-receiver ping mailserver
   docker exec smtpy-smtp-receiver telnet mailserver 587
   ```

4. **Open GitHub issue** with logs and configuration (redact passwords!)
