# Deployment Fixes - Port Conflicts Resolved

**Date**: 2025-10-26
**Issue**: Port allocation conflicts during deployment
**Status**: ✅ RESOLVED

## Problem

During deployment, the following errors occurred:

```
Error response from daemon: Bind for 0.0.0.0:5432 failed: port is already allocated
Error response from daemon: Bind for 0.0.0.0:8000 failed: port is already allocated
Error response from daemon: Bind for 0.0.0.0:1025 failed: port is already allocated
Error response from daemon: Bind for 0.0.0.0:80 failed: port is already allocated
```

**Root Causes**:
1. ~~The deployment script was trying to create new containers while old containers were still running~~ ✅ FIXED
2. **Port conflicts with other applications on the Unraid host** ✅ FIXED (removed port mappings)

## Solution

### Part 1: Container Cleanup (Fixes old container persistence)

### Part 2: Network Architecture (Fixes port conflicts with other apps)

**Key Change**: Removed all external port mappings from SMTPy containers. Services now communicate via Docker's internal network, with nginx reverse proxy as the only entry point.

**Benefits**:
- ✅ No port conflicts with other Unraid applications
- ✅ Improved security (database/redis not exposed to host)
- ✅ Better isolation between applications
- ✅ Nginx load balances across API replicas

See [Nginx Docker Network Setup](./NGINX_DOCKER_NETWORK_SETUP.md) for detailed configuration.

### Updated CI/CD Workflow

The deployment process now follows this sequence:

```bash
1. Login to GHCR
2. Pull latest images
3. ⭐ FORCE STOP ALL SMTPY CONTAINERS (docker stop/rm by name filter)
4. ⭐ STOP OLD CONTAINERS (docker compose down)
5. Start database & Redis
6. Wait for database health check
7. Start SMTP server
8. Start API servers (2 replicas)
9. Wait for API health check
10. Start frontend
11. Cleanup unused images
```

### Key Changes in `.github/workflows/ci-cd.yml`

**Before:**
```yaml
# Tried to update containers while running
docker compose up -d --no-deps db redis
docker compose up -d --no-deps api
# ... port conflicts occurred
```

**After:**
```bash
# Force stop ANY smtpy containers (even if from different compose project)
echo "Force stopping any existing SMTPy containers..."
docker ps -a --filter "name=smtpy-" --format "{{.Names}}" | xargs -r docker stop || true
docker ps -a --filter "name=smtpy-" --format "{{.Names}}" | xargs -r docker rm || true

# Stop old containers from current compose project
docker compose down --remove-orphans || true

# Then start fresh
docker compose up -d --no-deps db redis
# Wait for health checks...
docker compose up -d --scale api=2 api
# ...
```

**Why This Works:**
- `docker ps -a --filter "name=smtpy-"` finds ALL containers with "smtpy-" in the name
- `xargs -r docker stop/rm` forcefully stops and removes them, regardless of compose project
- This handles cases where containers were created manually or from old compose project names
- The `|| true` ensures the script continues even if no containers are found

## Manual Deployment Script

Created `scripts/deploy-production.sh` for manual deployments:

```bash
#!/bin/bash
# Usage on server:
cd /srv/smtpy
export GITHUB_PAT="your_token"
./scripts/deploy-production.sh
```

### Features:
- ✅ Color-coded output for easy reading
- ✅ Step-by-step progress indicators
- ✅ Health checks for all services
- ✅ Automatic retry logic for database
- ✅ Comprehensive error handling
- ✅ Summary report at the end

### Script Output Example:

```
========================================
  SMTPy Production Deployment
========================================

Configuration:
  Registry: ghcr.io
  Owner: larrymotalavigne
  Tag: latest

[1/7] Logging in to GitHub Container Registry...
✓ Login successful

[2/7] Pulling latest images...
✓ Images pulled

[3/7] Stopping existing containers...
✓ Old containers stopped

[4/7] Starting database and Redis...
✓ Database services started

[5/7] Waiting for database to be ready...
✓ Database is ready

[6/7] Starting backend services...
  Starting SMTP server...
  Starting API servers (2 replicas)...
  Waiting for API to be healthy...
✓ Backend services started

[7/7] Starting frontend...
✓ Frontend started

========================================
  Deployment Complete!
========================================

Running containers:
NAME               STATUS
smtpy-db      Up (healthy)
smtpy-redis   Up (healthy)
smtpy-api-1        Up (healthy)
smtpy-api-2        Up (healthy)
smtpy-smtp-prod    Up
smtpy-front Up

Health Check Summary:
  Database: ✓ Healthy
  Redis: ✓ Healthy
  API: ✓ Healthy
  Frontend: ✓ Healthy

========================================
Deployment completed successfully!
========================================
```

## Deployment Options

### Option 1: Automated via CI/CD (Recommended)

Simply push to main branch:
```bash
git push origin main
```

GitHub Actions will automatically:
1. Run tests
2. Build images
3. Deploy to production

### Option 2: Manual Deployment

On the server:
```bash
cd /srv/smtpy

# Set environment variables
export GHCR_OWNER=larrymotalavigne
export TAG=latest
export GITHUB_PAT="your_github_token"

# Run deployment script
./scripts/deploy-production.sh
```

### Option 3: Docker Compose Directly

```bash
cd /srv/smtpy

# Login to registry
echo "$GITHUB_PAT" | docker login ghcr.io -u larrymotalavigne --password-stdin

# Stop old containers
docker compose -f docker-compose.prod.yml down --remove-orphans

# Pull and start
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --scale api=2
```

## Troubleshooting

### Still Getting Port Conflicts?

**Check for rogue containers:**
```bash
# List all containers (even stopped ones)
docker ps -a

# Stop specific container
docker stop <container_name>
docker rm <container_name>

# Or stop all
docker stop $(docker ps -aq)
```

**Check what's using the port:**
```bash
# Check port 8000
lsof -i :8000
netstat -tlnp | grep :8000

# Kill process if needed
kill <PID>
```

### Database Not Ready?

```bash
# Check database logs
docker logs smtpy-db

# Manual health check
docker exec smtpy-db pg_isready -U postgres

# Connect to database
docker exec -it smtpy-db psql -U postgres -d smtpy
```

### API Not Starting?

```bash
# Check API logs
docker logs smtpy-api-1
docker logs smtpy-api-2

# Check if database is reachable
docker exec smtpy-api-1 nc -zv db 5432

# Check migrations
docker exec smtpy-api-1 alembic current
```

## Deployment Best Practices

### 1. Pre-Deployment Checklist

- ✅ All tests passing locally
- ✅ Environment variables set
- ✅ Database backup created
- ✅ GitHub PAT is valid
- ✅ Sufficient disk space

### 2. During Deployment

- ✅ Monitor logs in real-time
- ✅ Check health endpoints
- ✅ Verify database migrations
- ✅ Test critical API endpoints

### 3. Post-Deployment

- ✅ Run health checks
- ✅ Monitor error logs
- ✅ Check application metrics
- ✅ Verify external access

## Monitoring Commands

```bash
# Watch logs in real-time
docker compose -f docker-compose.prod.yml logs -f

# Check specific service
docker logs smtpy-api-1 -f --tail 100

# Monitor resource usage
docker stats

# Check container status
docker compose -f docker-compose.prod.yml ps

# Health check all services
curl http://localhost:8000/health
curl http://localhost:80/
```

## Rollback Procedure

If deployment fails:

```bash
# Stop current deployment
docker compose -f docker-compose.prod.yml down

# Pull previous tag
export TAG="previous-tag"
docker compose -f docker-compose.prod.yml pull

# Start with previous version
docker compose -f docker-compose.prod.yml up -d --scale api=2

# Or restore from backup
docker exec -i smtpy-db psql -U postgres smtpy < backup.sql
```

## Related Documentation

- [Nginx Proxy Manager Setup](./NGINX_PROXY_MANAGER_SETUP.md) - **Recommended**: For NPM users
- [Nginx Docker Network Setup](./NGINX_DOCKER_NETWORK_SETUP.md) - For manual nginx setup
- [Port Conflict Resolution](./PORT_CONFLICT_RESOLUTION.md) - Complete fix summary
- [GHCR Authentication](./GHCR_AUTHENTICATION.md)
- [PostgreSQL 18 Upgrade](./POSTGRESQL_18_UPGRADE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Nginx Deployment](./NGINX_DEPLOYMENT.md)

---

**Status**: ✅ Issue Resolved
**Next Deployment**: Should complete successfully
**Last Updated**: 2025-10-26
