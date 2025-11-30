# Docker Mailserver Integration Guide

This guide explains how to configure SMTPy to use your docker-mailserver (mail.atomdev.fr) for sending emails.

## Overview

SMTPy is now configured to use your existing docker-mailserver running at `mail.atomdev.fr` for all outbound email delivery. This integration uses the SMTP relay functionality built into SMTPy.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   SMTPy API     │────────▶│  mail.atomdev.fr │────────▶│  Internet       │
│   (Relay Mode)  │  SMTP   │  (docker-mail-   │  SMTP   │  (Recipients)   │
│                 │  Port   │   server)        │         │                 │
└─────────────────┘   25    └──────────────────┘         └─────────────────┘
```

## Configuration

### 1. Environment Variables

The following environment variables are configured in `.env.production`:

```bash
# SMTP Relay Configuration
SMTP_HOST=mail.atomdev.fr           # Your mailserver hostname
SMTP_PORT=25                         # Internal SMTP port (no TLS needed)
SMTP_USER=                           # Empty (no auth on internal network)
SMTP_PASSWORD=                       # Empty (no auth on internal network)
SMTP_USE_TLS=false                  # No TLS for internal Docker communication
SMTP_USE_SSL=false                  # No SSL for internal Docker communication
SMTP_HOSTNAME=mail.atomdev.fr       # Sending hostname
SMTP_DELIVERY_MODE=relay            # Use relay mode (not direct delivery)
SMTP_ENABLE_DKIM=true               # Enable DKIM signing
```

### 2. Docker Network Configuration

Since both SMTPy and docker-mailserver run on the same Docker host, they need to communicate via Docker networking.

#### Option A: Same Docker Network (Recommended)

If your mailserver is accessible via `mail.atomdev.fr` hostname within Docker:

1. Ensure the hostname resolves to your mailserver container
2. No additional network configuration needed
3. Use port 25 for internal communication

#### Option B: Shared External Network

If your mailserver uses a separate Docker network:

1. Find your mailserver's network name:
   ```bash
   docker inspect <mailserver-container> | grep NetworkMode
   ```

2. Update `docker-compose.prod.yml`:
   ```yaml
   networks:
     smtpy-network:
       driver: bridge

     mailserver-network:
       external: true
       name: <your-mailserver-network-name>
   ```

3. Connect the API service to both networks:
   ```yaml
   api:
     networks:
       - smtpy-network
       - mailserver-network
   ```

### 3. Port Options

Your mailserver supports multiple ports:

| Port | Protocol | Use Case | Configuration |
|------|----------|----------|---------------|
| 25   | SMTP     | Internal Docker communication (recommended) | `SMTP_PORT=25`, `SMTP_USE_TLS=false` |
| 587  | Submission | Secure external communication | `SMTP_PORT=587`, `SMTP_USE_TLS=true` |
| 465  | SMTPS    | Legacy secure communication | `SMTP_PORT=465`, `SMTP_USE_SSL=true` |

**Recommendation**: Use port 25 for internal Docker communication (no TLS/auth needed).

## Deployment Steps

### 1. Verify Mailserver Configuration

On your server, check your mailserver container:

```bash
# Find mailserver container
docker ps | grep mail

# Check mailserver networks
docker inspect <mailserver-container> | grep -A 10 Networks

# Verify mailserver is listening on ports
docker exec <mailserver-container> netstat -tlnp | grep -E ':(25|587|465)'
```

### 2. Update Environment Variables

Create or update your `.env.production` file:

```bash
# Copy template
cp .env.production.template .env.production

# Edit with your values
nano .env.production
```

Ensure these values are set:
```bash
SMTP_HOST=mail.atomdev.fr
SMTP_PORT=25
SMTP_DELIVERY_MODE=relay
SMTP_USE_TLS=false
SMTP_USE_SSL=false
SMTP_USER=
SMTP_PASSWORD=
```

### 3. Deploy SMTPy

Deploy with the updated configuration:

```bash
# Stop existing containers
docker compose -f docker-compose.prod.yml down

# Pull latest images (if using GHCR)
docker compose -f docker-compose.prod.yml pull

# Start with new configuration
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Check logs
docker logs smtpy-api-prod-1 -f
```

### 4. Test Email Delivery

Test that emails are being sent through your mailserver:

```bash
# Watch SMTPy API logs for SMTP connections
docker logs smtpy-api-prod-1 -f | grep -i smtp

# Watch mailserver logs for incoming connections from SMTPy
docker logs <mailserver-container> -f | grep -i "connect from"
```

From SMTPy dashboard:
1. Create a test alias
2. Send an email to the alias
3. Check that it forwards to your destination email
4. Verify in logs that it used mail.atomdev.fr

## Troubleshooting

### Issue: Cannot Connect to mail.atomdev.fr

**Symptoms**:
- Connection refused errors
- Timeout errors

**Solutions**:

1. **Check hostname resolution**:
   ```bash
   docker exec smtpy-api-prod-1 ping mail.atomdev.fr
   docker exec smtpy-api-prod-1 nslookup mail.atomdev.fr
   ```

2. **Use container name instead**:
   If `mail.atomdev.fr` doesn't resolve, use the actual container name:
   ```bash
   # Find container name
   docker ps | grep mail

   # Update .env.production
   SMTP_HOST=<actual-container-name>
   ```

3. **Check network connectivity**:
   ```bash
   docker exec smtpy-api-prod-1 telnet mail.atomdev.fr 25
   ```

### Issue: Authentication Required

**Symptoms**:
- "Authentication required" errors
- "Relay access denied" errors

**Solutions**:

1. **Check if auth is required**:
   ```bash
   docker exec <mailserver-container> cat /etc/postfix/main.cf | grep smtpd_relay_restrictions
   ```

2. **Create SMTP credentials** in your mailserver if needed

3. **Update .env.production**:
   ```bash
   SMTP_USER=your-username
   SMTP_PASSWORD=your-password
   ```

### Issue: TLS Certificate Errors

**Symptoms**:
- Certificate verification failed
- SSL handshake errors

**Solutions**:

1. **For internal communication, disable TLS**:
   ```bash
   SMTP_PORT=25
   SMTP_USE_TLS=false
   SMTP_USE_SSL=false
   ```

2. **For secure communication, use port 587**:
   ```bash
   SMTP_PORT=587
   SMTP_USE_TLS=true
   SMTP_USE_SSL=false
   ```

### Issue: Emails Not Being Sent

**Debugging steps**:

1. **Check SMTPy logs**:
   ```bash
   docker logs smtpy-api-prod-1 | grep -i "forward\|smtp\|error"
   ```

2. **Check mailserver logs**:
   ```bash
   docker logs <mailserver-container> | tail -100
   ```

3. **Verify SMTP configuration**:
   ```bash
   docker exec smtpy-api-prod-1 env | grep SMTP
   ```

4. **Test SMTP connection manually**:
   ```bash
   docker exec -it smtpy-api-prod-1 sh
   telnet mail.atomdev.fr 25
   EHLO smtpy.fr
   QUIT
   ```

## Network Connectivity Test

To verify everything is configured correctly, run this test from within the SMTPy container:

```bash
# Enter SMTPy container
docker exec -it smtpy-api-prod-1 sh

# Test DNS resolution
nslookup mail.atomdev.fr

# Test port connectivity
telnet mail.atomdev.fr 25

# Test SMTP manually
cat << EOF | telnet mail.atomdev.fr 25
EHLO smtpy.fr
MAIL FROM:<test@smtpy.fr>
RCPT TO:<your-test-email@example.com>
DATA
Subject: Test from SMTPy

This is a test email.
.
QUIT
EOF
```

## Advanced Configuration

### Hybrid Mode (Fallback)

If you want SMTPy to try direct delivery first and fall back to your mailserver:

```bash
SMTP_DELIVERY_MODE=hybrid
```

This will:
1. First attempt direct delivery to recipient MX servers
2. If that fails, use mail.atomdev.fr as relay
3. Useful for ensuring delivery even if direct delivery is blocked

### Custom Relay per Domain

For advanced setups, you can configure different relays per domain by modifying the relay service code in `back/smtp/relay/`.

## Security Considerations

1. **Internal Network**: Since both services are on the same host, no TLS/auth is needed for internal communication
2. **Firewall**: Ensure your mailserver's port 25 is accessible within the Docker network
3. **DKIM**: Keep `SMTP_ENABLE_DKIM=true` for better deliverability
4. **SPF/DMARC**: Configure these on your domains to point to mail.atomdev.fr

## Monitoring

Monitor email delivery:

```bash
# SMTPy logs (SMTP relay activity)
docker logs smtpy-api-prod-1 -f | grep "SMTPRelayService\|forward_email"

# Mailserver logs (incoming from SMTPy)
docker logs <mailserver-container> -f | grep "smtpy\|relay"
```

## References

- [SMTPy SMTP Configuration](../back/shared/core/config.py)
- [SMTP Relay Service](../back/smtp/relay/relay_service.py)
- [Email Forwarder](../back/smtp/forwarding/forwarder.py)
- [Docker Mailserver Documentation](https://docker-mailserver.github.io/docker-mailserver/latest/)

## Support

If you encounter issues:

1. Check SMTPy logs: `docker logs smtpy-api-prod-1 -f`
2. Check mailserver logs: `docker logs <mailserver-container> -f`
3. Verify environment variables: `docker exec smtpy-api-prod-1 env | grep SMTP`
4. Test connectivity manually (see Network Connectivity Test section)

## Summary

Your SMTPy installation is now configured to:
- Use mail.atomdev.fr as SMTP relay
- Connect via port 25 (internal, no TLS)
- No authentication required (internal Docker network)
- Send all outbound emails through your docker-mailserver
- Use DKIM signing for better deliverability

This configuration provides a robust, self-hosted email solution without depending on external email services.
