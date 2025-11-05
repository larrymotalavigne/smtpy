# Production Setup Guide - SMTPy

This guide walks you through setting up SMTPy for production deployment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Email Setup](#email-setup)
- [Security Configuration](#security-configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Linux Server** (Ubuntu 20.04+ recommended)
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Domain Name** with DNS access
- **SSL Certificate** (Let's Encrypt recommended)
- **Minimum Resources**:
  - 2 CPU cores
  - 4GB RAM
  - 20GB disk space

### Optional but Recommended

- **SMTP Relay Service** (SendGrid, AWS SES, Mailgun)
- **Monitoring Service** (Sentry for errors)
- **Backup Storage** (AWS S3, DigitalOcean Spaces)

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/larrymotalavigne/smtpy.git
cd smtpy
```

### 2. Copy Environment Template

```bash
cp .env.production.template .env.production
```

### 3. Configure Environment

Edit `.env.production` with your production values:

```bash
nano .env.production
```

### 4. Start Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
./scripts/verify-deployment.sh
```

---

## Environment Configuration

### Core Settings

```bash
# Application
SECRET_KEY=<generate-random-32-char-string>
APP_URL=https://smtpy.yourdomain.com
DEBUG=False

# Database
DATABASE_URL=postgresql+psycopg://postgres:CHANGE_ME@postgres:5432/smtpy

# Frontend
FRONTEND_URL=https://smtpy.yourdomain.com
```

### Generate Secure Secret Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Email Setup

### Option 1: External SMTP Relay (Recommended)

#### SendGrid Configuration

```bash
# Transactional Emails (password reset, verification)
EMAIL_ENABLED=true
EMAIL_BACKEND=smtp
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=SMTPy
EMAIL_SMTP_HOST=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=apikey
EMAIL_SMTP_PASSWORD=<your-sendgrid-api-key>
EMAIL_SMTP_USE_TLS=true

# Email Forwarding
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
```

#### AWS SES Configuration

```bash
EMAIL_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=<your-ses-username>
EMAIL_SMTP_PASSWORD=<your-ses-password>
EMAIL_SMTP_USE_TLS=true
```

### Option 2: Self-Hosted SMTP

```bash
# Transactional Emails
EMAIL_SMTP_HOST=localhost
EMAIL_SMTP_PORT=25

# Email Forwarding
SMTP_HOST=localhost
SMTP_PORT=25
```

**Note**: Self-hosting requires proper MX, SPF, DKIM, and DMARC configuration.

---

## Security Configuration

### 1. Stripe Configuration

```bash
STRIPE_API_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
STRIPE_SUCCESS_URL=https://smtpy.yourdomain.com/billing/success
STRIPE_CANCEL_URL=https://smtpy.yourdomain.com/billing/cancel
STRIPE_PORTAL_RETURN_URL=https://smtpy.yourdomain.com/billing
```

### 2. SSL/TLS Setup

#### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d smtpy.yourdomain.com

# Auto-renewal (already configured)
sudo systemctl status certbot.timer
```

#### Using Cloudflare (Alternative)

1. Point domain to Cloudflare
2. Enable "Full (strict)" SSL/TLS mode
3. Use Cloudflare origin certificate in nginx

### 3. Firewall Configuration

```bash
# Allow required ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 25/tcp   # SMTP (if self-hosting)
sudo ufw allow 587/tcp  # SMTP submission (if self-hosting)
sudo ufw enable
```

### 4. Database Security

```bash
# Strong PostgreSQL password
DATABASE_URL=postgresql+psycopg://postgres:$(openssl rand -base64 32)@postgres:5432/smtpy

# Restrict database access in docker-compose.prod.yml
services:
  postgres:
    networks:
      - backend  # Not exposed to public
```

---

## DNS Configuration

### Required DNS Records

#### 1. Application Access

```dns
A     smtpy.yourdomain.com    -> <your-server-ip>
AAAA  smtpy.yourdomain.com    -> <your-server-ipv6> (optional)
```

#### 2. Email Forwarding (Per Domain)

For each domain you want to manage (e.g., example.com):

```dns
# MX Record
MX  @  10  smtpy.yourdomain.com

# SPF Record
TXT  @  "v=spf1 a:smtpy.yourdomain.com ~all"

# DMARC Record
TXT  _dmarc  "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"

# DKIM Record (get from dashboard after domain setup)
TXT  default._domainkey  "v=DKIM1; k=rsa; p=<your-public-key>"
```

---

## Monitoring

### Application Monitoring (Sentry)

```bash
# Backend (back/.env.production)
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx

# Frontend (front/src/environments/environment.prod.ts)
export const environment = {
  production: true,
  sentryDsn: 'https://xxxxx@sentry.io/xxxxx'
};
```

### Uptime Monitoring

Recommended services:
- **UptimeRobot** (free tier available)
- **Pingdom**
- **StatusCake**

Monitor:
- `https://smtpy.yourdomain.com/` (200 OK)
- `https://smtpy.yourdomain.com/api/` (200 OK with JSON)

### Log Monitoring

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# Backend logs
docker compose -f docker-compose.prod.yml logs -f api

# SMTP logs
docker compose -f docker-compose.prod.yml logs -f smtp

# Database logs
docker compose -f docker-compose.prod.yml logs -f postgres
```

---

## Backup Strategy

### Database Backups

```bash
# Manual backup
./scripts/backup-db.sh

# Automated daily backups (cron)
0 2 * * * /path/to/smtpy/scripts/backup-db.sh >> /var/log/smtpy-backup.log 2>&1
```

### Remote Backup to S3

```bash
# Install AWS CLI
sudo apt install awscli

# Configure AWS credentials
aws configure

# Backup script with S3 upload
./scripts/backup-db.sh --remote-backup s3://your-bucket/smtpy-backups/
```

---

## Performance Optimization

### 1. Enable Redis Caching (Future)

```yaml
# docker-compose.prod.yml
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - backend
```

### 2. Database Connection Pooling

Already configured in code:
- Pool size: 20 connections
- Max overflow: 40
- Connection recycling: 1 hour

### 3. Frontend Optimization

```bash
# Build optimized frontend
cd front
npm run build -- --configuration production

# Verify bundle size
ls -lh dist/*/browser/*.js
```

---

## Troubleshooting

### Common Issues

#### 1. Email Not Sending

**Check email service logs:**
```bash
docker compose -f docker-compose.prod.yml logs smtp
```

**Test SMTP connection:**
```bash
python3 -c "
import smtplib
smtp = smtplib.SMTP('smtp.sendgrid.net', 587)
smtp.starttls()
smtp.login('apikey', 'YOUR_API_KEY')
print('SMTP connection successful')
smtp.quit()
"
```

#### 2. Database Connection Failed

**Check PostgreSQL status:**
```bash
docker compose -f docker-compose.prod.yml exec postgres pg_isready
```

**Verify credentials:**
```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d smtpy -c "SELECT 1"
```

#### 3. High Memory Usage

**Check container stats:**
```bash
docker stats
```

**Increase resource limits in docker-compose.prod.yml:**
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

#### 4. SSL Certificate Issues

**Renew certificate manually:**
```bash
sudo certbot renew --force-renewal
```

**Check certificate expiry:**
```bash
echo | openssl s_client -servername smtpy.yourdomain.com -connect smtpy.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

## Health Checks

### Application Health

```bash
# API health
curl https://smtpy.yourdomain.com/api/

# Expected: {"status":"healthy","service":"SMTPy v2 API","version":"2.0.0"}
```

### Database Health

```bash
# Inside container
docker compose -f docker-compose.prod.yml exec postgres pg_isready

# Via API (requires authentication)
curl -X GET https://smtpy.yourdomain.com/api/health \
  -H "Cookie: session=your-session-cookie"
```

---

## Security Checklist

Before going live, verify:

- [ ] `SECRET_KEY` is strong and unique
- [ ] All default passwords changed
- [ ] SSL/TLS certificate installed and valid
- [ ] Firewall configured correctly
- [ ] Database not publicly accessible
- [ ] Stripe production keys configured
- [ ] Email sending tested
- [ ] Backups configured and tested
- [ ] Monitoring/alerting configured
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Dependabot enabled for updates

---

## Maintenance

### Regular Tasks

**Daily:**
- Check application logs for errors
- Verify backups completed

**Weekly:**
- Review security alerts (Dependabot)
- Check disk space usage

**Monthly:**
- Update dependencies
- Review and update SSL certificates (auto-renewed)
- Test backup restoration

### Updating SMTPy

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker compose -f docker-compose.prod.yml build --no-cache

# Apply database migrations
docker compose -f docker-compose.prod.yml exec api uv run alembic upgrade head

# Restart services (zero-downtime)
docker compose -f docker-compose.prod.yml up -d --no-deps --build api
```

---

## Support

For issues or questions:

- **Documentation**: `/docs` folder
- **GitHub Issues**: https://github.com/larrymotalavigne/smtpy/issues
- **Email**: support@smtpy.fr

---

## License

SMTPy is licensed under the MIT License. See [LICENSE](../LICENSE) for details.
