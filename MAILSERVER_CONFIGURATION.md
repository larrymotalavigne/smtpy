# Mailserver Configuration Guide for SMTPy

This guide explains how to set up and configure a mailserver for SMTPy, including:
1. Running a complete Docker Mailserver with `docker-compose.mail.yml`
2. Configuring email forwarding to avoid "relay access denied" errors

## Running Docker Mailserver with SMTPy

SMTPy includes a complete Docker Mailserver configuration in `docker-compose.mail.yml`. This provides a production-ready mail server with SMTP, IMAP, anti-spam, and anti-virus capabilities.

### Quick Start

1. **Create required Docker networks** (if not already created):
   ```bash
   docker network create mailserver-network
   docker network create proxy-network
   docker network create npm_letsencrypt  # For Let's Encrypt certificates
   ```

2. **Configure environment variables**:
   ```bash
   # Copy the template
   cp .env.production.template .env.production

   # Edit .env.production and configure the MAILSERVER_* variables
   nano .env.production
   ```

3. **Start the mailserver**:
   ```bash
   docker compose -f docker-compose.mail.yml up -d
   ```

4. **Create email accounts**:
   ```bash
   # Add a user account
   docker exec mailserver setup email add user@atomdev.fr

   # List all accounts
   docker exec mailserver setup email list
   ```

5. **Configure DKIM** (for better deliverability):
   ```bash
   # Generate DKIM keys
   docker exec mailserver setup config dkim

   # Show DKIM public key to add to DNS
   docker exec mailserver cat /tmp/docker-mailserver/opendkim/keys/atomdev.fr/mail.txt
   ```

6. **Configure DNS records**:
   - **MX Record**: `mail.atomdev.fr` (priority 10)
   - **A Record**: `mail.atomdev.fr` → Your server IP
   - **SPF Record**: `v=spf1 mx ~all`
   - **DKIM Record**: Copy from step 5
   - **DMARC Record**: `v=DMARC1; p=quarantine; rua=mailto:postmaster@atomdev.fr`

### Configuration Files

The mailserver uses several configuration files in the `config/mailserver/` directory:

- **`postfix-main.cf`**: Custom Postfix configuration settings
- **`postfix-virtual.cf`**: Virtual domain aliases
- **`postfix-transport`**: Transport maps for routing to SMTPy

### Routing Emails to SMTPy

To route specific email addresses to SMTPy for alias processing:

1. **Edit `config/mailserver/postfix-transport`**:
   ```
   # Route an alias to SMTPy
   myalias@atomdev.fr    smtp:[smtpy-smtp-receiver]:2525
   ```

2. **Update the transport map**:
   ```bash
   docker exec mailserver postmap /tmp/docker-mailserver/postfix-transport
   docker exec mailserver postfix reload
   ```

3. **Verify the configuration**:
   ```bash
   # Check logs
   docker compose -f docker-compose.mail.yml logs -f mailserver
   ```

### Health Checks

The mailserver includes a comprehensive health check script that monitors:
- Postfix (SMTP) status
- Dovecot (IMAP) status
- Rspamd (anti-spam) status
- ClamAV (anti-virus) status
- Port availability (25, 587, 465, 143, 993)
- Mail queue status
- Disk space usage

Check the health status:
```bash
# View container status
docker compose -f docker-compose.mail.yml ps

# Run health check manually
docker exec mailserver bash /usr/local/bin/healthcheck.sh
```

### SSL/TLS Configuration

The mailserver supports Let's Encrypt SSL certificates:

1. **Set up certificates** using nginx-proxy-manager or certbot
2. **Update `.env.production`**:
   ```bash
   MAILSERVER_SSL_TYPE=letsencrypt
   ```
3. **Restart the mailserver**:
   ```bash
   docker compose -f docker-compose.mail.yml restart mailserver
   ```

### Integrating with SMTPy

To integrate the mailserver with SMTPy's main stack:

1. **Ensure both networks are connected**:
   - The mailserver uses `mailserver-network`
   - SMTPy's `smtp-receiver` should also be on `mailserver-network`

2. **Update `docker-compose.prod.yml`** (if needed):
   ```yaml
   services:
     smtp-receiver:
       networks:
         - smtpy-network
         - mailserver-network  # Add this

   networks:
     mailserver-network:
       external: true
   ```

3. **Configure environment variables** in `.env.production`:
   ```bash
   MAILSERVER_HOST=mailserver
   MAILSERVER_PORT=587
   MAILSERVER_USER=noreply@atomdev.fr
   MAILSERVER_PASSWORD=your-password
   MAILSERVER_USE_TLS=true
   ```

---

## Email Forwarding Configuration

## Understanding the Issue

The "relay access denied" error occurs when SMTPy tries to forward emails through your mailserver but the mailserver rejects the relay request. This happens because mailservers have anti-spam protections that prevent unauthorized relay.

## How SMTPy Email Forwarding Works

1. **Incoming Email**: Mailserver receives email for an alias (e.g., `user@yourdomain.com`)
2. **Forward to SMTPy**: Mailserver forwards to SMTPy SMTP receiver (port 2525)
3. **Process & Route**: SMTPy processes the email and determines forwarding targets
4. **Relay Request**: SMTPy connects back to mailserver to relay the email to the final destination
5. **Delivery**: Mailserver sends email to the final recipient

**The Problem**: Step 4 (Relay Request) requires proper authorization

## Solution Options

Choose **ONE** of these approaches based on your setup:

### Option 1: Authenticated SMTP Relay (Recommended)

Configure SMTPy to authenticate with your mailserver. This is the most reliable approach.

#### Configuration

In your `.env.production` or environment variables:

```bash
# Mailserver connection
MAILSERVER_HOST=mailserver                  # Or mail.yourdomain.com
MAILSERVER_PORT=587                         # Use submission port (587)
MAILSERVER_USER=noreply@yourdomain.com      # SMTP username
MAILSERVER_PASSWORD=your-secure-password    # SMTP password
MAILSERVER_USE_TLS=true                     # Enable STARTTLS

# Envelope sender (must be authorized for your SMTP user)
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=SMTPy
```

#### Docker Mail Server Setup

If using Docker Mail Server, create the account:

```bash
# Add the account
docker exec mailserver setup email add noreply@yourdomain.com your-secure-password

# Verify it was created
docker exec mailserver setup email list
```

#### Benefits
- ✅ Works with any mailserver (local or external)
- ✅ Most secure approach
- ✅ Supports external SMTP services (SendGrid, AWS SES, Gmail)
- ✅ Clear authentication trail in logs

---

### Option 2: IP/Network-Based Relay Permission

Configure your mailserver to allow relay from the SMTPy SMTP receiver service.

#### Docker Mail Server Configuration

Add to your `docker-compose.yml` override or mailserver config:

```yaml
services:
  mailserver:
    environment:
      # Allow relay from Docker network
      - PERMIT_DOCKER=network
      # Or allow from specific networks
      - RELAY_NETWORKS=172.28.0.0/16
```

Or in `postfix-main.cf` override:

```
mynetworks = 127.0.0.0/8 172.28.0.0/16 [::1]/128
```

#### Configuration

In your `.env.production`:

```bash
# Mailserver connection (no authentication)
MAILSERVER_HOST=mailserver
MAILSERVER_PORT=25                          # Use standard SMTP port
MAILSERVER_USER=                            # Leave empty
MAILSERVER_PASSWORD=                        # Leave empty
MAILSERVER_USE_TLS=false                    # Usually not needed for local

# Envelope sender (must be from a local domain)
EMAIL_FROM=noreply@smtpy.local             # Or any local domain
EMAIL_FROM_NAME=SMTPy
```

#### Benefits
- ✅ No authentication needed
- ✅ Good for internal/local mailserver
- ✅ Simpler configuration

#### Drawbacks
- ❌ Only works with local mailserver
- ❌ Requires mailserver configuration changes
- ❌ Less secure (no authentication)

---

### Option 3: External SMTP Relay Service

Use a third-party SMTP service instead of a local mailserver.

#### Popular Services

**SendGrid**:
```bash
MAILSERVER_HOST=smtp.sendgrid.net
MAILSERVER_PORT=587
MAILSERVER_USER=apikey
MAILSERVER_PASSWORD=SG.your-api-key-here
MAILSERVER_USE_TLS=true
EMAIL_FROM=noreply@yourdomain.com           # Must be verified in SendGrid
```

**AWS SES**:
```bash
MAILSERVER_HOST=email-smtp.us-east-1.amazonaws.com
MAILSERVER_PORT=587
MAILSERVER_USER=your-ses-username
MAILSERVER_PASSWORD=your-ses-password
MAILSERVER_USE_TLS=true
EMAIL_FROM=noreply@yourdomain.com           # Must be verified in SES
```

**Gmail** (with app password):
```bash
MAILSERVER_HOST=smtp.gmail.com
MAILSERVER_PORT=587
MAILSERVER_USER=your-email@gmail.com
MAILSERVER_PASSWORD=your-app-password
MAILSERVER_USE_TLS=true
EMAIL_FROM=your-email@gmail.com
```

#### Benefits
- ✅ Professional deliverability
- ✅ Built-in spam filtering
- ✅ Detailed analytics
- ✅ No local mailserver maintenance

#### Drawbacks
- ❌ Per-email costs
- ❌ External dependency
- ❌ May have sending limits

---

## Verification Steps

After configuration, verify the setup works:

### 1. Check Configuration

```bash
# View current environment variables
docker compose -f docker-compose.prod.yml exec smtp-receiver env | grep MAILSERVER
docker compose -f docker-compose.prod.yml exec smtp-receiver env | grep EMAIL_FROM
```

### 2. Test SMTP Connection

```bash
# Test connection to mailserver (replace values)
docker compose -f docker-compose.prod.yml exec smtp-receiver python3 -c "
import asyncio
import aiosmtplib

async def test():
    try:
        smtp = aiosmtplib.SMTP(
            hostname='mailserver',
            port=587,
            use_tls=True
        )
        await smtp.connect()
        await smtp.login('noreply@yourdomain.com', 'password')
        print('✅ Connection successful!')
        await smtp.quit()
    except Exception as e:
        print(f'❌ Connection failed: {e}')

asyncio.run(test())
"
```

### 3. Monitor Logs

Watch for successful forwarding:

```bash
# Watch SMTP receiver logs
docker compose -f docker-compose.prod.yml logs -f smtp-receiver

# Look for these log lines:
# ✅ "Forwarding email from ... to ... using envelope sender ..."
# ✅ "Successfully forwarded email to ..."

# Errors to watch for:
# ❌ "554 5.7.1 ... Relay access denied"
# ❌ "535 5.7.8 Authentication failed"
```

### 4. Send Test Email

```bash
# Send test email to an alias
echo "Test email body" | mail -s "Test Subject" alias@yourdomain.com

# Check logs to verify forwarding
docker compose -f docker-compose.prod.yml logs smtp-receiver | grep -i "forward"
```

---

## Troubleshooting

### Error: "554 5.7.1 Relay access denied"

**Cause**: Mailserver doesn't allow relay from the sender/IP

**Solutions**:
1. ✅ Configure authentication (Option 1)
2. ✅ Add SMTPy IP to allowed relay networks (Option 2)
3. ✅ Verify EMAIL_FROM is from an authorized domain

### Error: "535 5.7.8 Authentication failed"

**Cause**: Invalid MAILSERVER_USER or MAILSERVER_PASSWORD

**Solutions**:
1. ✅ Verify credentials are correct
2. ✅ Check if account exists in mailserver
3. ✅ Try resetting the password

### Error: "Connection refused"

**Cause**: Mailserver not reachable

**Solutions**:
1. ✅ Verify MAILSERVER_HOST is correct
2. ✅ Check if mailserver service is running
3. ✅ Verify port (25 for local, 587 for submission)
4. ✅ Check Docker network connectivity

### Error: "Recipient address rejected"

**Cause**: Mailserver doesn't recognize the destination domain

**Solutions**:
1. ✅ This might not be a configuration issue
2. ✅ Verify the forwarding target email is valid
3. ✅ Check if the destination mail server is reachable

---

## Best Practices

### Security

- ✅ Always use authentication when possible
- ✅ Use strong, unique passwords
- ✅ Enable TLS/STARTTLS for submission port (587)
- ✅ Don't expose SMTP credentials in logs
- ✅ Rotate passwords regularly

### Reliability

- ✅ Use authenticated SMTP for production
- ✅ Configure email sender address properly
- ✅ Monitor logs for forwarding errors
- ✅ Set up alerts for failed forwards
- ✅ Test forwarding after any configuration changes

### Performance

- ✅ Use local mailserver for lower latency
- ✅ Consider external relay for better deliverability
- ✅ Monitor mailserver resource usage
- ✅ Configure connection pooling if needed

---

## Quick Reference

| Configuration | Use When | Auth Required | Pros | Cons |
|--------------|----------|---------------|------|------|
| **Authenticated Local** | Docker Mail Server | Yes | Secure, reliable | Needs account setup |
| **IP-Based Relay** | Internal mailserver | No | Simple | Less secure |
| **External Service** | Production, high volume | Yes | Professional | Cost, external dependency |

---

## Getting Help

If you continue to experience relay access denied errors:

1. **Check Logs**: `docker compose logs smtp-receiver`
2. **Verify Config**: Ensure EMAIL_FROM and MAILSERVER_* variables are set
3. **Test Connection**: Use the verification steps above
4. **Review Setup**: Confirm your choice (Option 1, 2, or 3) is fully configured
5. **Open Issue**: Include logs and configuration (redact passwords!)

---

## Related Documentation

- [Docker Mail Server Documentation](https://docker-mailserver.github.io/docker-mailserver/latest/)
- [Postfix SMTP Authentication](http://www.postfix.org/SASL_README.html)
- [SMTP Relay Configuration](https://www.postfix.org/postconf.5.html#relayhost)
