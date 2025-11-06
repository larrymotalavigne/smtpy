# SMTPy Production Deployment Guide

This guide covers deploying SMTPy to production using Docker Compose with optimized production configurations.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Building Production Images](#building-production-images)
- [Deployment](#deployment)
- [Health Checks](#health-checks)
- [Monitoring](#monitoring)
- [Backup and Recovery](#backup-and-recovery)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- Docker Engine 24.0+ with Docker Compose V2
- Git
- Minimum 4GB RAM, 20GB disk space
- Domain name with DNS access (for production)

### Required Accounts

- Stripe account (for billing)
- SSL certificate provider (Let's Encrypt recommended)

### System Requirements

**Minimum Production Environment**:
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB SSD
- Network: 100Mbps

**Recommended Production Environment**:
- CPU: 8 cores
- RAM: 16GB
- Disk: 100GB NVMe SSD
- Network: 1Gbps

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/smtpy.git
cd smtpy

# Create production environment file
cp .env.production.template .env.production

# Edit environment variables (IMPORTANT!)
nano .env.production
```

### 2. Configure Environment

Edit `.env.production` with your production values:

```bash
# Required: Set these first
POSTGRES_PASSWORD=<generate-strong-password>
REDIS_PASSWORD=<generate-strong-password>
SECRET_KEY=<generate-secret-key>
STRIPE_API_KEY=<your-stripe-key>
STRIPE_WEBHOOK_SECRET=<your-webhook-secret>

# Optional: Customize these
POSTGRES_DB=smtpy
POSTGRES_USER=postgres
CORS_ORIGINS=https://yourdomain.com
```

### 3. Build and Deploy

```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# Verify all services are healthy
docker compose -f docker-compose.prod.yml ps
```

### 4. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/health

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Test SMTP connection
telnet localhost 1025
```

## Environment Configuration

### Required Environment Variables

Create `.env.production` with the following variables:

#### Database Configuration

```bash
# PostgreSQL settings
POSTGRES_DB=smtpy
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<strong-password>  # REQUIRED: Generate strong password
POSTGRES_PORT=5432
```

**Password Generation**:
```bash
# Generate secure password
openssl rand -base64 32
```

#### Redis Configuration

```bash
# Redis cache settings
REDIS_PASSWORD=<strong-password>  # REQUIRED: Generate strong password
REDIS_PORT=6379
```

#### Application Security

```bash
# Application security
SECRET_KEY=<secret-key>  # REQUIRED: Generate secret key
DEBUG=false
IS_PRODUCTION=true
LOG_LEVEL=INFO
```

**Secret Key Generation**:
```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Stripe Configuration

```bash
# Stripe billing
STRIPE_API_KEY=sk_live_xxxxx  # REQUIRED: From Stripe dashboard
STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # REQUIRED: From Stripe webhooks
STRIPE_SUCCESS_URL=https://yourdomain.com/billing/success
STRIPE_CANCEL_URL=https://yourdomain.com/billing/cancel
STRIPE_PORTAL_RETURN_URL=https://yourdomain.com/billing
```

**Getting Stripe Credentials**:
1. Log in to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to Developers > API keys
3. Copy your live secret key (`sk_live_...`)
4. Create webhook endpoint at Developers > Webhooks
5. Copy webhook signing secret (`whsec_...`)

#### Self-Hosted SMTP Configuration

SMTPy includes a complete self-hosted SMTP delivery system that sends emails directly to recipient mail servers without requiring external services like Gmail or SendGrid.

```bash
# Self-hosted SMTP settings
SMTP_HOSTNAME=mail.smtpy.fr              # Your sending hostname (FQDN)
SMTP_DELIVERY_MODE=direct                # Delivery mode: direct/relay/hybrid/smart
SMTP_ENABLE_DKIM=true                    # Enable DKIM signing for authentication
```

**Delivery Modes**:
- **`direct`** (default): Self-hosted delivery, no external dependencies
- **`relay`**: Use external SMTP service (Gmail, SendGrid)
- **`hybrid`**: Try direct first, fall back to relay on failure
- **`smart`**: AI-driven routing (future)

**For External Relay (optional, only if using relay/hybrid mode)**:
```bash
# External relay credentials (optional)
SMTP_USER=your-email@gmail.com           # SMTP username
SMTP_PASSWORD=your-app-password          # SMTP password
SMTP_HOST=smtp.gmail.com                 # SMTP host
SMTP_PORT=587                            # SMTP port
SMTP_USE_TLS=true                        # Use STARTTLS
```

**DNS Requirements for Self-Hosted SMTP** (CRITICAL):

1. **Reverse DNS (PTR) Record** - Contact your hosting provider:
   ```
   45.80.25.57  →  mail.smtpy.fr
   ```
   Verify: `dig -x 45.80.25.57`

2. **SPF Record** - Add to your domain's DNS:
   ```
   example.com.  IN  TXT  "v=spf1 include:smtpy.fr ~all"
   ```
   Or: `"v=spf1 ip4:45.80.25.57 ~all"`

3. **DKIM Record** - Generated automatically, add to DNS:
   ```
   default._domainkey.example.com.  IN  TXT  "v=DKIM1; k=rsa; p=<public-key>"
   ```

4. **DMARC Record** - Add to your domain's DNS:
   ```
   _dmarc.example.com.  IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
   ```

**Firewall Configuration**:
```bash
# Allow outbound SMTP
sudo ufw allow out 25/tcp

# Allow inbound SMTP (for receiving)
sudo ufw allow 25/tcp
```

**Benefits of Self-Hosted SMTP**:
- ✅ No external dependencies or per-email costs
- ✅ Complete control over email delivery
- ✅ Better privacy (emails don't pass through third parties)
- ✅ Lower latency for direct delivery
- ✅ Automatic DKIM signing for better deliverability

**Important**: For new IPs, gradually increase sending volume (IP warm-up):
- Day 1-3: 50 emails/day
- Day 4-7: 200 emails/day
- Day 8-14: 500 emails/day
- Day 15+: Full volume

See `back/smtp/relay/README.md` for complete documentation.

#### CORS and Networking

```bash
# CORS configuration
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Port configuration (if using non-standard ports)
HTTP_PORT=80
HTTPS_PORT=443
API_PORT=8000
SMTP_PORT=1025
```

#### Worker Configuration

```bash
# API workers (adjust based on CPU cores)
API_WORKERS=4  # Recommended: (2 x CPU cores) + 1
```

### Optional Environment Variables

```bash
# Docker registry (if using custom registry)
DOCKER_REGISTRY=ghcr.io
GHCR_OWNER=yourusername
TAG=latest

# Resource limits (defined in docker-compose.prod.yml)
# Adjust in compose file if needed
```

## Building Production Images

### Option 1: Build Locally

Build all production images from source:

```bash
# Build all services
docker compose -f docker-compose.prod.yml build

# Build specific service
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml build smtp
docker compose -f docker-compose.prod.yml build frontend
```

### Option 2: Use Pre-built Images from GHCR

Configure `.env.production`:

```bash
DOCKER_REGISTRY=ghcr.io
GHCR_OWNER=yourusername
TAG=v1.0.0
```

Pull images:

```bash
docker compose -f docker-compose.prod.yml pull
```

### Building Custom Images

If you need to customize the build:

```bash
# Build API with custom tag
docker build -f back/api/Dockerfile.prod -t smtpy-api:custom .

# Build SMTP server with custom tag
docker build -f back/smtp/Dockerfile.prod -t smtpy-smtp:custom .

# Build frontend with custom tag
docker build -f front/Dockerfile.prod -t smtpy-frontend:custom .
```

### Image Size Optimization

Our multi-stage builds produce optimized images:

- **API**: ~200MB (Python 3.13-slim based)
- **SMTP**: ~180MB (Python 3.13-slim based)
- **Frontend**: ~50MB (Nginx-alpine based)
- **PostgreSQL**: ~240MB (postgres:18-alpine)
- **Redis**: ~40MB (redis:7-alpine)

**Total**: ~710MB for all images

## Deployment

### Initial Deployment

```bash
# 1. Start database first
docker compose -f docker-compose.prod.yml up -d db redis

# 2. Wait for database to be healthy
docker compose -f docker-compose.prod.yml ps db

# 3. Start backend services
docker compose -f docker-compose.prod.yml up -d smtp api

# 4. Wait for API to be healthy
docker compose -f docker-compose.prod.yml ps api

# 5. Start frontend
docker compose -f docker-compose.prod.yml up -d frontend

# 6. Verify all services
docker compose -f docker-compose.prod.yml ps
```

### Updating Deployment

```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Recreate containers with new images
docker compose -f docker-compose.prod.yml up -d

# Verify update
docker compose -f docker-compose.prod.yml ps
```

### Rolling Restart

To minimize downtime:

```bash
# Restart services one at a time
docker compose -f docker-compose.prod.yml up -d --no-deps --scale api=1 api
sleep 10
docker compose -f docker-compose.prod.yml up -d --no-deps --scale api=2 api
```

### SSL/TLS Configuration

#### Using Let's Encrypt

1. Install certbot:
```bash
sudo apt-get install certbot
```

2. Generate certificates:
```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

3. Copy certificates:
```bash
mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chmod 644 ssl/*.pem
```

4. Configure nginx (mount in docker-compose.prod.yml already configured):
```yaml
volumes:
  - ./ssl:/etc/nginx/ssl:ro
```

5. Update nginx.conf for HTTPS:
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # ... rest of config
}
```

#### Certificate Auto-Renewal

Set up cron job for auto-renewal:

```bash
# Edit crontab
crontab -e

# Add renewal job (runs daily at 2am)
0 2 * * * certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/*.pem /path/to/smtpy/ssl/
```

## Health Checks

### Service Health Status

Check all services:

```bash
# Using docker compose
docker compose -f docker-compose.prod.yml ps

# Individual health checks
curl -f http://localhost:8000/health  # API
curl -f http://localhost:80  # Frontend
docker exec smtpy-db-prod pg_isready -U postgres  # Database
docker exec smtpy-redis-prod redis-cli --raw incr ping  # Redis
```

### Health Check Endpoints

- **API**: `http://localhost:8000/health`
  - Returns: `{"status": "healthy"}`
  - Checks: Database connectivity

- **Frontend**: `http://localhost:80/`
  - Returns: Angular application
  - Checks: Nginx serving files

- **Database**: Internal PostgreSQL health check
  - Command: `pg_isready -U postgres -d smtpy`

- **Redis**: Internal Redis health check
  - Command: `redis-cli --raw incr ping`

- **SMTP**: Socket connection check
  - Port: 1025
  - Check: `telnet localhost 1025`

### Automated Monitoring

Create monitoring script (`scripts/health-check.sh`):

```bash
#!/bin/bash
# Health check script for all services

services=("db" "redis" "smtp" "api" "frontend")
all_healthy=true

for service in "${services[@]}"; do
    status=$(docker compose -f docker-compose.prod.yml ps -q $service | xargs docker inspect -f '{{.State.Health.Status}}')
    if [ "$status" != "healthy" ]; then
        echo "❌ $service is $status"
        all_healthy=false
    else
        echo "✅ $service is healthy"
    fi
done

if [ "$all_healthy" = true ]; then
    echo "✅ All services healthy"
    exit 0
else
    echo "❌ Some services unhealthy"
    exit 1
fi
```

Run periodically with cron:

```bash
# Check every 5 minutes
*/5 * * * * /path/to/smtpy/scripts/health-check.sh >> /var/log/smtpy-health.log 2>&1
```

## Monitoring

### Log Management

#### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f api

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 api

# Filter by time
docker compose -f docker-compose.prod.yml logs --since 1h api
```

#### Log Rotation

Logs are automatically rotated (configured in docker-compose.prod.yml):

- **Max size**: 10MB per file
- **Max files**: 3 files kept
- **Total per service**: ~30MB

#### Centralized Logging

For production, consider centralized logging:

**Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)**

```yaml
# Add to docker-compose.prod.yml
logging:
  driver: "fluentd"
  options:
    fluentd-address: "localhost:24224"
    tag: "smtpy.{{.Name}}"
```

**Option 2: Grafana Loki**

```yaml
logging:
  driver: "loki"
  options:
    loki-url: "http://localhost:3100/loki/api/v1/push"
```

### Resource Monitoring

#### View Resource Usage

```bash
# All containers
docker stats

# Specific container
docker stats smtpy-api-prod

# One-time snapshot
docker compose -f docker-compose.prod.yml ps --format json | jq
```

#### Resource Limits

Configured in `docker-compose.prod.yml`:

| Service  | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|----------|-----------|--------------|--------------|-----------------|
| DB       | 2 cores   | 2GB          | 1 core       | 1GB             |
| Redis    | 1 core    | 512MB        | 0.5 cores    | 256MB           |
| SMTP     | 1 core    | 1GB          | 0.5 cores    | 512MB           |
| API      | 2 cores   | 2GB          | 1 core       | 1GB             |
| Frontend | 1 core    | 512MB        | 0.25 cores   | 128MB           |

**Total Requirements**:
- **CPU**: 7 cores (limit), 3.25 cores (reserved)
- **Memory**: 6GB (limit), 2.9GB (reserved)

### Performance Metrics

Monitor key metrics:

```bash
# Database connections
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory usage
docker exec smtpy-redis-prod redis-cli INFO memory

# API request count
docker exec smtpy-api-prod curl localhost:8000/metrics  # If Prometheus enabled
```

## Backup and Recovery

### Database Backup

#### Manual Backup

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker exec smtpy-db-prod pg_dump -U postgres smtpy > backups/smtpy_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec smtpy-db-prod pg_dump -U postgres smtpy | gzip > backups/smtpy_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Automated Backup Script

Create `scripts/backup-db.sh`:

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/path/to/smtpy/backups"
RETENTION_DAYS=30

# Create backup
BACKUP_FILE="$BACKUP_DIR/smtpy_$(date +%Y%m%d_%H%M%S).sql.gz"
docker exec smtpy-db-prod pg_dump -U postgres smtpy | gzip > "$BACKUP_FILE"

# Remove old backups
find "$BACKUP_DIR" -name "smtpy_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup created: $BACKUP_FILE"
```

Set up daily backup cron:

```bash
# Daily backup at 3am
0 3 * * * /path/to/smtpy/scripts/backup-db.sh >> /var/log/smtpy-backup.log 2>&1
```

#### Backup to Remote Storage

```bash
# Backup to S3
docker exec smtpy-db-prod pg_dump -U postgres smtpy | gzip | aws s3 cp - s3://your-bucket/backups/smtpy_$(date +%Y%m%d).sql.gz

# Backup to remote server
docker exec smtpy-db-prod pg_dump -U postgres smtpy | gzip | ssh user@backup-server "cat > /backups/smtpy_$(date +%Y%m%d).sql.gz"
```

### Database Restore

#### From Local Backup

```bash
# Restore from uncompressed backup
docker exec -i smtpy-db-prod psql -U postgres smtpy < backups/smtpy_20250126.sql

# Restore from compressed backup
gunzip -c backups/smtpy_20250126.sql.gz | docker exec -i smtpy-db-prod psql -U postgres smtpy
```

#### Full Recovery Procedure

```bash
# 1. Stop API to prevent new connections
docker compose -f docker-compose.prod.yml stop api smtp

# 2. Drop and recreate database
docker exec smtpy-db-prod psql -U postgres -c "DROP DATABASE smtpy;"
docker exec smtpy-db-prod psql -U postgres -c "CREATE DATABASE smtpy;"

# 3. Restore backup
gunzip -c backups/smtpy_20250126.sql.gz | docker exec -i smtpy-db-prod psql -U postgres smtpy

# 4. Restart services
docker compose -f docker-compose.prod.yml start smtp api

# 5. Verify
curl http://localhost:8000/health
```

### Volume Backup

Backup Docker volumes for complete recovery:

```bash
# Backup PostgreSQL volume
docker run --rm \
  -v smtpy_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz -C /data .

# Backup Redis volume
docker run --rm \
  -v smtpy_redis_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis_volume_$(date +%Y%m%d).tar.gz -C /data .
```

### Disaster Recovery Plan

1. **Daily automated backups** (database + volumes)
2. **Off-site backup** to S3 or remote server
3. **Test restore monthly** to verify backup integrity
4. **Document recovery time objective (RTO)**: < 1 hour
5. **Document recovery point objective (RPO)**: < 24 hours

## Security Considerations

### Secret Management

**DO NOT**:
- Commit `.env.production` to git
- Use default passwords
- Share secrets in plain text

**DO**:
- Use strong, unique passwords for all services
- Use environment variables for secrets
- Consider external secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets regularly

### Network Security

1. **Firewall Configuration**:
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 1025/tcp # SMTP (if external access needed)
sudo ufw enable
```

2. **Internal Network**: Services communicate on isolated bridge network (172.28.0.0/16)

3. **Database Access**: PostgreSQL only accessible within Docker network (not exposed externally in production)

### Container Security

Implemented in Dockerfile.prod:

- **Non-root user**: All services run as `smtpy` user
- **Minimal base images**: Using slim/alpine variants
- **No unnecessary packages**: Only runtime dependencies
- **Read-only mounts**: SSL certificates mounted read-only

### Application Security

- **CORS**: Configured in `.env.production` (CORS_ORIGINS)
- **DEBUG=false**: Debug mode disabled in production
- **Secret key**: Cryptographically secure random key
- **HTTPS**: SSL/TLS encryption for all traffic

### Security Monitoring

```bash
# Check for security updates
docker compose -f docker-compose.prod.yml pull  # Updates images

# Scan images for vulnerabilities
docker scan smtpy-api-prod
docker scan smtpy-smtp-prod
docker scan smtpy-frontend-prod

# Check container security
docker inspect smtpy-api-prod | jq '.[0].HostConfig.SecurityOpt'
```

## Troubleshooting

### Common Issues

#### Issue 1: Database Connection Failed

**Symptom**: API logs show "could not connect to database"

**Solutions**:
```bash
# Check database is running
docker compose -f docker-compose.prod.yml ps db

# Check database health
docker compose -f docker-compose.prod.yml ps db | grep healthy

# Check database logs
docker compose -f docker-compose.prod.yml logs db

# Verify DATABASE_URL
docker exec smtpy-api-prod env | grep DATABASE_URL

# Test connection manually
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "SELECT 1;"
```

#### Issue 2: API Returns 500 Errors

**Symptom**: API health check fails or returns 500

**Solutions**:
```bash
# Check API logs
docker compose -f docker-compose.prod.yml logs api

# Check environment variables
docker exec smtpy-api-prod env | grep -E "SECRET_KEY|DATABASE_URL|STRIPE"

# Verify migrations ran
docker exec smtpy-api-prod alembic current

# Run migrations manually
docker exec smtpy-api-prod alembic upgrade head

# Restart API
docker compose -f docker-compose.prod.yml restart api
```

#### Issue 3: SMTP Server Not Accepting Connections

**Symptom**: Cannot connect to port 1025

**Solutions**:
```bash
# Check SMTP server is running
docker compose -f docker-compose.prod.yml ps smtp

# Check port binding
netstat -tulpn | grep 1025

# Test connection
telnet localhost 1025

# Check firewall
sudo ufw status | grep 1025

# Check SMTP logs
docker compose -f docker-compose.prod.yml logs smtp
```

#### Issue 4: Frontend Returns 404

**Symptom**: Accessing domain returns 404 or nginx error

**Solutions**:
```bash
# Check frontend is running
docker compose -f docker-compose.prod.yml ps frontend

# Check nginx logs
docker compose -f docker-compose.prod.yml logs frontend

# Verify nginx config
docker exec smtpy-frontend-prod nginx -t

# Check file permissions
docker exec smtpy-frontend-prod ls -la /usr/share/nginx/html

# Restart frontend
docker compose -f docker-compose.prod.yml restart frontend
```

#### Issue 5: Out of Memory

**Symptom**: Containers being killed, OOMKilled status

**Solutions**:
```bash
# Check memory usage
docker stats

# Check system memory
free -h

# Adjust resource limits in docker-compose.prod.yml
# Reduce API workers
docker compose -f docker-compose.prod.yml up -d --scale api=1
```

### Debug Mode

To enable detailed logging temporarily:

```bash
# Edit .env.production
LOG_LEVEL=DEBUG

# Restart services
docker compose -f docker-compose.prod.yml restart api smtp

# View detailed logs
docker compose -f docker-compose.prod.yml logs -f api
```

**Remember to disable debug mode after troubleshooting**:

```bash
LOG_LEVEL=INFO
docker compose -f docker-compose.prod.yml restart api smtp
```

### Getting Help

If you encounter issues not covered here:

1. Check logs for all services
2. Verify all environment variables are set correctly
3. Ensure system requirements are met
4. Review recent changes to configuration
5. Check GitHub issues: https://github.com/yourusername/smtpy/issues
6. Create new issue with:
   - Error messages from logs
   - Output of `docker compose -f docker-compose.prod.yml ps`
   - System information (OS, Docker version, resources)

## Production Checklist

Before going live:

- [ ] All required environment variables configured
- [ ] Strong, unique passwords generated for all services
- [ ] SSL/TLS certificates installed and configured
- [ ] CORS origins configured for your domain
- [ ] Stripe API keys configured (live, not test)
- [ ] Database backups automated and tested
- [ ] Health check monitoring configured
- [ ] Firewall rules configured
- [ ] Log rotation configured
- [ ] Resource limits appropriate for your traffic
- [ ] Domain DNS configured correctly
- [ ] All services passing health checks
- [ ] Test email flow end-to-end
- [ ] Test billing flow with Stripe test mode
- [ ] Load testing completed
- [ ] Security scan completed
- [ ] Disaster recovery plan documented
- [ ] Team trained on deployment procedures

## Next Steps

After successful deployment:

1. **Monitor** for the first 24 hours closely
2. **Test** all functionality in production
3. **Set up alerts** for downtime/errors
4. **Document** any custom configurations
5. **Plan** for scaling based on traffic

## Support

For production support:

- Documentation: `/docs`
- GitHub Issues: https://github.com/yourusername/smtpy/issues
- Email: support@yourdomain.com
