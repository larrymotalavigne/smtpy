# Mailserver Deployment Guide

## Issue: Mailserver Not Deployed

The mailserver service was configured in `docker-compose.prod.yml` but was not running on the production server. This was due to missing Docker volumes that the mailserver configuration referenced as external volumes.

### Root Cause

The `docker-compose.prod.yml` file references external volumes from an "infra" project:
- `infra_mailserver_data`
- `infra_mailserver_state`
- `infra_mailserver_logs`
- `infra_mailserver_config`
- `infra_npm_letsencrypt`

These volumes did not exist on the server, preventing the mailserver container from starting.

## Solution: Automated Deployment Script

We've created a deployment script that automatically sets up all required resources and deploys the mailserver.

### Quick Start (On Production Server)

```bash
# Navigate to the SMTPy directory
cd /srv/smtpy

# Pull latest changes
git pull origin claude/deploy-mailserver-H2str

# Run the deployment script
sudo ./scripts/deploy-mailserver.sh
```

### What the Script Does

1. **Creates Required Networks**:
   - `smtpy-network` - Main application network
   - `mailserver-network` - Mail-specific network
   - `proxy-network` - For nginx integration

2. **Creates Required Volumes**:
   - `infra_mailserver_data` - Mail data storage
   - `infra_mailserver_state` - Mail server state
   - `infra_mailserver_logs` - Mail server logs
   - `infra_mailserver_config` - Mail server configuration
   - `infra_npm_letsencrypt` - SSL certificates

3. **Deploys Mailserver**:
   - Pulls the latest Docker Mailserver image
   - Starts the mailserver container
   - Waits for health checks
   - Shows deployment status and logs

## Post-Deployment Configuration

After the mailserver is deployed, follow these steps:

### 1. Create Email Accounts

```bash
# Create a service account for SMTPy
docker exec mailserver setup email add noreply@atomdev.fr

# Create a postmaster account
docker exec mailserver setup email add postmaster@atomdev.fr

# List all accounts
docker exec mailserver setup email list
```

### 2. Configure DKIM (Email Authentication)

```bash
# Generate DKIM keys
docker exec mailserver setup config dkim

# View the public key to add to DNS
docker exec mailserver cat /tmp/docker-mailserver/opendkim/keys/atomdev.fr/mail.txt
```

### 3. Set Up DNS Records

Add these DNS records to your domain:

**MX Record**:
```
atomdev.fr.  IN  MX  10  mail.atomdev.fr.
```

**A Record**:
```
mail.atomdev.fr.  IN  A  <YOUR_SERVER_IP>
```

**SPF Record**:
```
atomdev.fr.  IN  TXT  "v=spf1 mx ~all"
```

**DKIM Record**:
```
mail._domainkey.atomdev.fr.  IN  TXT  "<DKIM_PUBLIC_KEY_FROM_STEP_2>"
```

**DMARC Record**:
```
_dmarc.atomdev.fr.  IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:postmaster@atomdev.fr"
```

### 4. Configure SMTPy to Use Mailserver

Update `.env.production` with mailserver credentials:

```bash
# Mailserver connection settings
MAILSERVER_HOST=mailserver
MAILSERVER_PORT=587
MAILSERVER_USER=noreply@atomdev.fr
MAILSERVER_PASSWORD=<password_from_step_1>
MAILSERVER_USE_TLS=true

# Email sender settings
EMAIL_ENABLED=true
EMAIL_FROM=noreply@atomdev.fr
EMAIL_FROM_NAME=SMTPy
```

Then restart the SMTPy services:

```bash
docker compose -f docker-compose.prod.yml restart api smtp-receiver
```

### 5. Configure SSL/TLS (Optional but Recommended)

If you have Let's Encrypt certificates set up:

```bash
# Update .env.production
echo "MAILSERVER_SSL_TYPE=letsencrypt" >> .env.production

# Restart mailserver
docker compose -f docker-compose.prod.yml restart mailserver
```

## Verification

### Check Mailserver Status

```bash
# View running containers
docker ps | grep mailserver

# Check health status
docker inspect --format='{{.State.Health.Status}}' mailserver

# View logs
docker logs mailserver --tail 50
```

### Test Email Sending

```bash
# Send a test email
echo "Test email body" | docker exec -i mailserver mail -s "Test Subject" your-email@example.com
```

### Monitor Mail Queue

```bash
# Check mail queue
docker exec mailserver postqueue -p

# View mail logs
docker exec mailserver tail -f /var/log/mail/mail.log
```

## Troubleshooting

### Mailserver Won't Start

```bash
# Check logs for errors
docker logs mailserver

# Check docker compose status
docker compose -f docker-compose.prod.yml ps mailserver

# Restart mailserver
docker compose -f docker-compose.prod.yml restart mailserver
```

### Port Conflicts

If ports 25, 587, 465, 143, or 993 are already in use:

```bash
# Check what's using the ports
sudo lsof -i :25
sudo lsof -i :587

# Stop conflicting services if needed
sudo systemctl stop postfix
sudo systemctl disable postfix
```

### Health Check Failing

The mailserver health check monitors:
- Postfix (SMTP)
- Dovecot (IMAP)
- Rspamd (anti-spam)
- ClamAV (anti-virus)

If health checks fail, check individual services:

```bash
# Check Postfix status
docker exec mailserver postfix status

# Check Dovecot status
docker exec mailserver doveadm who

# View Rspamd status
docker exec mailserver rspamadm configtest
```

### Can't Send Email

```bash
# Check SMTP authentication
docker exec mailserver doveadm auth test noreply@atomdev.fr <password>

# Test SMTP connection
telnet localhost 587

# Check mail queue for stuck messages
docker exec mailserver postqueue -p
```

## Manual Deployment (Alternative)

If you prefer to deploy manually without the script:

```bash
# Create networks
docker network create smtpy-network
docker network create mailserver-network
docker network create proxy-network

# Create volumes
docker volume create infra_mailserver_data
docker volume create infra_mailserver_state
docker volume create infra_mailserver_logs
docker volume create infra_mailserver_config
docker volume create infra_npm_letsencrypt

# Deploy mailserver
docker compose -f docker-compose.prod.yml up -d mailserver
```

## Additional Resources

- [Full Mailserver Configuration Guide](MAILSERVER_CONFIGURATION.md)
- [Docker Mailserver Documentation](https://docker-mailserver.github.io/docker-mailserver/latest/)
- [Postfix Configuration](http://www.postfix.org/documentation.html)

## Support

If you encounter issues:

1. Check the logs: `docker logs mailserver`
2. Review the configuration: `docker exec mailserver postconf -n`
3. Run the health check: `docker exec mailserver bash /usr/local/bin/healthcheck.sh`
4. Consult MAILSERVER_CONFIGURATION.md for detailed troubleshooting steps
