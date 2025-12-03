# SMTPy Production Quick Start Guide

This is a condensed guide for deploying SMTPy to production. For comprehensive documentation, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md).

## Prerequisites

- Docker Engine 24.0+ with Docker Compose V2
- Domain name with DNS access
- Stripe account for billing

## 5-Minute Production Deployment

### 1. Configure Environment (2 minutes)

```bash
# Copy environment template
cp .env.production.template .env.production

# Generate passwords and secrets
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env.production
echo "REDIS_PASSWORD=$(openssl rand -base64 32)" >> .env.production
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env.production

# Edit and add Stripe credentials
nano .env.production
```

**Required manual edits in `.env.production`**:
- `STRIPE_API_KEY=sk_live_...` (from Stripe Dashboard)
- `STRIPE_WEBHOOK_SECRET=whsec_...` (from Stripe Webhooks)
- `CORS_ORIGINS=https://yourdomain.com`

### 2. Build Images (2 minutes)

```bash
# Build all production images
docker compose -f docker-compose.prod.yml build

# Expected output: 3 images built (api, smtp, frontend)
```

### 3. Deploy Services (1 minute)

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy (30-60 seconds)
sleep 60
```

### 4. Verify Deployment

```bash
# Run verification script
./scripts/verify-deployment.sh

# Expected output: All checks passed
```

## Build Commands Reference

### Full Production Build

```bash
# Build all services
docker compose -f docker-compose.prod.yml build

# Build specific service
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml build smtp
docker compose -f docker-compose.prod.yml build frontend
```

### Build with Custom Tags

```bash
# Build API with version tag
docker build -f back/api/Dockerfile.prod -t smtpy-api:v1.0.0 .

# Build SMTP with version tag
docker build -f back/smtp/Dockerfile.prod -t smtpy-smtp:v1.0.0 .

# Build Frontend with version tag
docker build -f front/Dockerfile.prod -t smtpy-front:v1.0.0 .
```

### Build for GHCR (GitHub Container Registry)

```bash
# Set variables
export GHCR_OWNER=yourusername
export TAG=v1.0.0

# Build and tag for GHCR
docker build -f back/api/Dockerfile.prod -t ghcr.io/$GHCR_OWNER/smtpy-api:$TAG .
docker build -f back/smtp/Dockerfile.prod -t ghcr.io/$GHCR_OWNER/smtpy-smtp:$TAG .
docker build -f front/Dockerfile.prod -t ghcr.io/$GHCR_OWNER/smtpy-front:$TAG .

# Push to GHCR
docker push ghcr.io/$GHCR_OWNER/smtpy-api:$TAG
docker push ghcr.io/$GHCR_OWNER/smtpy-smtp:$TAG
docker push ghcr.io/$GHCR_OWNER/smtpy-front:$TAG
```

### Multi-Architecture Builds

```bash
# Create buildx builder
docker buildx create --name smtpy-builder --use

# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f back/api/Dockerfile.prod \
  -t ghcr.io/$GHCR_OWNER/smtpy-api:$TAG \
  --push \
  .

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f back/smtp/Dockerfile.prod \
  -t ghcr.io/$GHCR_OWNER/smtpy-smtp:$TAG \
  --push \
  .

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f front/Dockerfile.prod \
  -t ghcr.io/$GHCR_OWNER/smtpy-front:$TAG \
  --push \
  .
```

## Deployment Commands Reference

### Initial Deployment

```bash
# Step-by-step deployment
docker compose -f docker-compose.prod.yml up -d db redis  # Start databases
docker compose -f docker-compose.prod.yml up -d smtp api  # Start backend
docker compose -f docker-compose.prod.yml up -d frontend  # Start frontend

# Or deploy all at once
docker compose -f docker-compose.prod.yml up -d
```

### Update Deployment

```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Recreate containers with new images
docker compose -f docker-compose.prod.yml up -d

# View update logs
docker compose -f docker-compose.prod.yml logs -f
```

### Rolling Update (Zero Downtime)

```bash
# Update API with rolling restart
docker compose -f docker-compose.prod.yml up -d --no-deps --scale api=1 api
sleep 10
docker compose -f docker-compose.prod.yml up -d --no-deps --scale api=2 api

# Update other services
docker compose -f docker-compose.prod.yml up -d --no-deps smtp
docker compose -f docker-compose.prod.yml up -d --no-deps frontend
```

### Rollback

```bash
# Rollback to previous version
export TAG=v1.0.0  # Previous working version
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Common Operations

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f api

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 api

# Errors only
docker compose -f docker-compose.prod.yml logs -f | grep -i error
```

### Check Status

```bash
# All services
docker compose -f docker-compose.prod.yml ps

# Health status
./scripts/verify-deployment.sh

# Resource usage
docker stats
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart api
```

### Database Operations

```bash
# Run migrations
docker exec smtpy-api-prod alembic upgrade head

# Check migration status
docker exec smtpy-api-prod alembic current

# Backup database
docker exec smtpy-db pg_dump -U postgres smtpy > backups/smtpy_$(date +%Y%m%d).sql

# Restore database
cat backups/smtpy_20250126.sql | docker exec -i smtpy-db psql -U postgres smtpy
```

### Stop and Remove

```bash
# Stop all services
docker compose -f docker-compose.prod.yml stop

# Stop and remove containers (keeps volumes)
docker compose -f docker-compose.prod.yml down

# Remove everything including volumes (DANGEROUS!)
docker compose -f docker-compose.prod.yml down -v
```

## Health Check Endpoints

- **API**: `http://localhost:8000/health`
- **Frontend**: `http://localhost:80/`
- **Database**: `docker exec smtpy-db pg_isready`
- **Redis**: `docker exec smtpy-redis redis-cli ping`
- **SMTP**: `telnet localhost 1025`

## Troubleshooting Quick Reference

### API Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs api

# Verify database connection
docker exec smtpy-api-prod env | grep DATABASE_URL

# Run migrations manually
docker exec smtpy-api-prod alembic upgrade head

# Restart
docker compose -f docker-compose.prod.yml restart api
```

### Database Connection Issues

```bash
# Check database is running
docker compose -f docker-compose.prod.yml ps db

# Test connection
docker exec smtpy-db psql -U postgres -d smtpy -c "SELECT 1;"

# Check password in env
docker exec smtpy-api-prod env | grep POSTGRES_PASSWORD
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Reduce API workers
# Edit .env.production: API_WORKERS=2
docker compose -f docker-compose.prod.yml restart api

# Scale down API replicas
docker compose -f docker-compose.prod.yml up -d --scale api=1
```

### SSL/TLS Issues

```bash
# Verify certificates exist
ls -la ssl/

# Check nginx config
docker exec smtpy-front nginx -t

# Reload nginx
docker exec smtpy-front nginx -s reload
```

## Security Checklist

Before deploying to production:

- [ ] Generated strong passwords (32+ characters)
- [ ] Using production Stripe keys (sk_live_...)
- [ ] DEBUG=false in .env.production
- [ ] CORS_ORIGINS set to your domain only
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured (only ports 80, 443, 1025 open)
- [ ] .env.production NOT in git
- [ ] Database backups configured
- [ ] Monitoring/alerting set up

## Performance Tuning

### Optimize for Traffic

```bash
# High traffic (8 CPU cores)
API_WORKERS=17  # (2 x 8) + 1

# Medium traffic (4 CPU cores)
API_WORKERS=9   # (2 x 4) + 1

# Low traffic (2 CPU cores)
API_WORKERS=5   # (2 x 2) + 1
```

### Resource Limits

Edit `docker-compose.prod.yml` to adjust limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Increase for more CPU
      memory: 4G     # Increase for more memory
```

## Backup and Recovery

### Quick Backup

```bash
# Backup database
./scripts/backup-db.sh

# Backup volumes
docker run --rm \
  -v smtpy_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_$(date +%Y%m%d).tar.gz -C /data .
```

### Quick Restore

```bash
# Restore database
cat backups/smtpy_20250126.sql | docker exec -i smtpy-db psql -U postgres smtpy

# Restart services
docker compose -f docker-compose.prod.yml restart
```

## Monitoring

### Quick Health Check

```bash
# Run verification
./scripts/verify-deployment.sh

# Check all endpoints
curl http://localhost:8000/health  # API
curl http://localhost:80           # Frontend
telnet localhost 1025              # SMTP
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Network usage
docker compose -f docker-compose.prod.yml top
```

## Next Steps

After deployment:

1. **Test thoroughly**: Verify all functionality works
2. **Set up monitoring**: Configure alerts for downtime
3. **Configure backups**: Automate daily backups
4. **Document custom changes**: Keep track of modifications
5. **Plan scaling**: Monitor traffic and scale accordingly

## Getting Help

- **Full documentation**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Verification script**: `./scripts/verify-deployment.sh --verbose`
- **GitHub Issues**: https://github.com/yourusername/smtpy/issues

## Quick Command Reference

```bash
# Deploy
docker compose -f docker-compose.prod.yml up -d

# Verify
./scripts/verify-deployment.sh

# Logs
docker compose -f docker-compose.prod.yml logs -f api

# Status
docker compose -f docker-compose.prod.yml ps

# Restart
docker compose -f docker-compose.prod.yml restart api

# Update
docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d

# Backup
docker exec smtpy-db pg_dump -U postgres smtpy > backups/backup_$(date +%Y%m%d).sql

# Stop
docker compose -f docker-compose.prod.yml down
```
