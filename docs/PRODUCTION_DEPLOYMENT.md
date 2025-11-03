# SMTPy Production Deployment Guide

## Overview

This guide covers deploying SMTPy to production with the following domains:
- **Frontend**: https://smtpy.fr
- **API**: https://api.smtpy.fr
- **SMTP**: smtp.smtpy.fr (port 25)

## Prerequisites

- Docker and Docker Compose installed on production server
- Domain names configured with DNS pointing to your server:
  - `smtpy.fr` → Server IP
  - `api.smtpy.fr` → Server IP
  - `smtp.smtpy.fr` → Server IP (MX record)
- Nginx Proxy Manager or similar for SSL termination
- Stripe account with API keys
- SMTP relay server for email forwarding (Gmail, SendGrid, Mailgun, AWS SES, etc.)

## Step 1: Environment Configuration

### 1.1 Copy Environment Template

```bash
cd /srv/smtpy
cp .env.production.template .env.production
```

### 1.2 Generate Secure Passwords

```bash
# PostgreSQL password
openssl rand -base64 32

# Redis password
openssl rand -base64 32

# Secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 1.3 Configure .env.production

Edit `.env.production` and update the following:

```bash
# =============================================================================
# DATABASE
# =============================================================================
POSTGRES_DB=smtpy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<generated-password-1>

# =============================================================================
# REDIS
# =============================================================================
REDIS_PASSWORD=<generated-password-2>

# =============================================================================
# SECURITY
# =============================================================================
SECRET_KEY=<generated-secret-key>
DEBUG=false
IS_PRODUCTION=true

# =============================================================================
# STRIPE
# =============================================================================
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=https://smtpy.fr/billing/success
STRIPE_CANCEL_URL=https://smtpy.fr/billing/cancel
STRIPE_PORTAL_RETURN_URL=https://smtpy.fr/billing

# =============================================================================
# CORS
# =============================================================================
CORS_ORIGINS=https://smtpy.fr

# =============================================================================
# EMAIL FORWARDING
# =============================================================================
# Configure your SMTP relay for forwarding emails
SMTP_HOST=smtp.gmail.com  # Or smtp.sendgrid.net, smtp.mailgun.org, etc.
SMTP_PORT=587

# If your SMTP relay requires authentication, add:
# SMTP_USER=your-email@example.com
# SMTP_PASSWORD=your-app-password

# =============================================================================
# DOCKER
# =============================================================================
DOCKER_REGISTRY=ghcr.io
GHCR_OWNER=larrymotalavigne
TAG=latest  # Or specific version like v1.0.0
```

### 1.4 Verify Configuration

```bash
# Ensure no default values remain
grep "CHANGE_ME" .env.production
# Should return no results

# Ensure sensitive values are set
grep -E "POSTGRES_PASSWORD|REDIS_PASSWORD|SECRET_KEY|STRIPE_API_KEY" .env.production
```

## Step 2: Stripe Configuration

### 2.1 Get Stripe API Keys

1. Go to https://dashboard.stripe.com/apikeys
2. Copy your **Live mode** secret key (starts with `sk_live_`)
3. Add to `.env.production` as `STRIPE_API_KEY`

### 2.2 Create Stripe Products and Prices

1. Go to https://dashboard.stripe.com/products
2. Create subscription products (e.g., Free, Pro, Enterprise)
3. Note the Price IDs (start with `price_`)
4. These Price IDs will be used in the frontend billing component

### 2.3 Configure Stripe Webhook

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Set URL to: `https://api.smtpy.fr/billing/webhook`
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the webhook signing secret (starts with `whsec_`)
6. Add to `.env.production` as `STRIPE_WEBHOOK_SECRET`

## Step 3: Email Server Configuration

### 3.1 Configure Email Relay

SMTPy receives emails via its SMTP server but forwards them through an external relay. Configure one of:

#### Option A: Gmail (Recommended for testing)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app-password>  # Create at https://myaccount.google.com/apppasswords
```

#### Option B: SendGrid

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>
```

#### Option C: Mailgun

```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=<mailgun-smtp-user>
SMTP_PASSWORD=<mailgun-smtp-password>
```

#### Option D: AWS SES

```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=<ses-smtp-user>
SMTP_PASSWORD=<ses-smtp-password>
```

### 3.2 Configure DNS for Email Receiving

Users will need to configure their domains to receive emails through SMTPy. The application will provide DNS instructions, but here's what's needed:

#### MX Record
Point domain to SMTPy server:
```
Type: MX
Host: @
Value: smtp.smtpy.fr
Priority: 10
TTL: 3600
```

#### SPF Record
Allow SMTPy to send emails:
```
Type: TXT
Host: @
Value: v=spf1 include:smtp.smtpy.fr ~all
TTL: 3600
```

## Step 4: Nginx Proxy Manager Configuration

### 4.1 Frontend Proxy (smtpy.fr)

1. Add Proxy Host in Nginx Proxy Manager
2. Configure:
   - Domain: `smtpy.fr`
   - Scheme: `http`
   - Forward Hostname/IP: `smtpy-frontend-prod`
   - Forward Port: `80`
   - Enable SSL with Let's Encrypt
   - Force SSL: Yes

### 4.2 API Proxy (api.smtpy.fr)

1. Add Proxy Host
2. Configure:
   - Domain: `api.smtpy.fr`
   - Scheme: `http`
   - Forward Hostname/IP: `smtpy-api-prod`
   - Forward Port: `8000`
   - Enable SSL with Let's Encrypt
   - Force SSL: Yes
   - Advanced: Add custom location for websockets if needed

### 4.3 SMTP Server (smtp.smtpy.fr)

SMTP server needs direct access on port 25 (MX record). If using Nginx Proxy Manager:

1. Configure Stream (TCP proxy) for port 25
2. Or expose Docker port directly and configure firewall

## Step 5: Docker Deployment

### 5.1 Login to GitHub Container Registry

```bash
export GITHUB_PAT=<your-github-personal-access-token>
echo "$GITHUB_PAT" | docker login ghcr.io -u larrymotalavigne --password-stdin
```

### 5.2 Pull Latest Images

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production pull
```

### 5.3 Start Services

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### 5.4 Verify Deployment

```bash
# Check all containers are running
docker compose -f docker-compose.prod.yml ps

# Check API health
curl https://api.smtpy.fr/health

# Check frontend
curl https://smtpy.fr

# Check SMTP server (from another machine)
telnet smtp.smtpy.fr 25
```

### 5.5 View Logs

```bash
# API logs
docker logs smtpy-api-prod --tail 100 -f

# Frontend logs
docker logs smtpy-frontend-prod --tail 100 -f

# SMTP logs
docker logs smtpy-smtp-prod --tail 100 -f

# Database logs
docker logs smtpy-db-prod --tail 100 -f
```

## Step 6: Database Migrations

Database migrations run automatically on API startup, but you can run them manually if needed:

```bash
# Run migrations
docker exec smtpy-api-prod alembic upgrade head

# Check migration status
docker exec smtpy-api-prod alembic current
```

## Step 7: Create Admin User

```bash
# Connect to database
docker exec -it smtpy-db-prod psql -U postgres -d smtpy

# Create admin user (example)
INSERT INTO users (username, email, password_hash, is_admin, created_at)
VALUES ('admin', 'admin@smtpy.fr', '<bcrypt-hash>', true, NOW());
```

Or use the seed script (development only):
```bash
docker exec smtpy-api-prod python scripts/seed_dev_db.py
```

## Step 8: SSL/TLS Configuration

### 8.1 Frontend (Nginx Proxy Manager)

Nginx Proxy Manager handles SSL automatically with Let's Encrypt.

### 8.2 API (Nginx Proxy Manager)

Same as frontend - automatic SSL with Let's Encrypt.

### 8.3 SMTP Server

For SMTP, you may want to configure STARTTLS. This requires:
1. SSL certificates for smtp.smtpy.fr
2. Configuring the SMTP server to support TLS (currently not implemented)

## Step 9: Monitoring and Maintenance

### 9.1 Health Checks

```bash
# API health endpoint
curl https://api.smtpy.fr/health

# Check all services
docker compose -f docker-compose.prod.yml ps
```

### 9.2 Backup Database

```bash
# Backup database
docker exec smtpy-db-prod pg_dump -U postgres smtpy > backup-$(date +%Y%m%d).sql

# Or use the mounted backup directory
docker exec smtpy-db-prod pg_dump -U postgres smtpy > /backups/backup-$(date +%Y%m%d).sql
```

### 9.3 Restore Database

```bash
# Restore from backup
docker exec -i smtpy-db-prod psql -U postgres smtpy < backup-20250101.sql
```

### 9.4 Update Application

```bash
# Pull latest images
docker compose -f docker-compose.prod.yml --env-file .env.production pull

# Restart services (zero-downtime with multiple replicas)
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps --scale api=2 api
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps frontend
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps smtp

# Clean up old images
docker image prune -f
```

## Step 10: Security Best Practices

### 10.1 Firewall Configuration

```bash
# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow SMTP
ufw allow 25/tcp

# Allow SSH (if not already allowed)
ufw allow 22/tcp

# Enable firewall
ufw enable
```

### 10.2 Regular Security Updates

```bash
# Update system packages
apt update && apt upgrade -y

# Update Docker images regularly
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### 10.3 Secrets Rotation

Rotate the following secrets every 90 days:
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `STRIPE_API_KEY` (if compromised)

### 10.4 Monitoring Logs

```bash
# Watch for suspicious activity
docker logs smtpy-api-prod --tail 100 -f | grep -i "error\|failed\|unauthorized"

# Monitor SMTP for spam/abuse
docker logs smtpy-smtp-prod --tail 100 -f | grep -i "bounce\|reject"
```

## Troubleshooting

### API Not Starting

```bash
# Check logs
docker logs smtpy-api-prod

# Common issues:
# - Database connection failed: Check POSTGRES_PASSWORD
# - Stripe error: Check STRIPE_API_KEY
# - Migration failed: Run migrations manually
```

### SMTP Not Receiving Emails

```bash
# Check DNS MX record
dig MX example.com

# Check SMTP server is listening
telnet smtp.smtpy.fr 25

# Check SMTP logs
docker logs smtpy-smtp-prod --tail 100
```

### Payment Processing Errors

```bash
# Verify Stripe webhook is receiving events
# Check Stripe dashboard: https://dashboard.stripe.com/webhooks

# Test webhook locally
curl -X POST https://api.smtpy.fr/billing/webhook \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test" \
  -d '{"type":"test"}'
```

### Database Performance Issues

```bash
# Check database size
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "SELECT pg_size_pretty(pg_database_size('smtpy'));"

# Check active connections
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "SELECT count(*) FROM pg_stat_activity;"

# Vacuum database
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "VACUUM ANALYZE;"
```

## Performance Tuning

### API Workers

Adjust based on CPU cores:
```bash
# In .env.production
API_WORKERS=8  # For 4 CPU cores: (2 * 4) = 8
```

### Database Connection Pooling

Configure in API settings if needed (not currently exposed).

### Redis Caching

Redis is configured for session storage and caching. Monitor usage:
```bash
docker exec smtpy-redis-prod redis-cli --raw incr ping
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/larrymotalavigne/smtpy/issues
- Documentation: https://docs.smtpy.fr (if available)
- Email: support@smtpy.fr
