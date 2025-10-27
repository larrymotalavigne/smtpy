# Nginx to Docker Network Integration

**Date**: 2025-10-27
**Purpose**: Configure host nginx to communicate with SMTPy Docker containers

## Problem

When running nginx on the host (e.g., `nginx.atomdev.fr`) and SMTPy services in Docker containers, there are two networking challenges:

1. **Port conflicts**: Multiple applications on the same host competing for ports (80, 443, 5432, 8000, etc.)
2. **Network isolation**: Docker containers are isolated from the host network by default

## Solution Overview

We've removed all external port mappings from SMTPy containers. Instead, nginx connects directly to containers via Docker's network. This approach:

✅ **Prevents port conflicts** - No ports exposed to host
✅ **Improves security** - Database/Redis not accessible from host
✅ **Enables load balancing** - Nginx can balance across API replicas
✅ **Simplifies deployment** - No port coordination needed

## Architecture

```
Internet
   │
   ├─> nginx.atomdev.fr (Host nginx on port 80/443)
   │       │
   │       └─> Docker Network: smtpy_smtpy-network
   │               │
   │               ├─> smtpy-frontend-prod:80
   │               ├─> smtpy-api-1:8000
   │               ├─> smtpy-api-2:8000
   │               ├─> smtpy-smtp-prod:1025 (internal)
   │               ├─> smtpy-db-prod:5432 (internal)
   │               └─> smtpy-redis-prod:6379 (internal)
```

## Implementation

### Option 1: Connect Existing Nginx Container to Docker Network (Recommended)

If your nginx is already running in Docker:

```bash
# Find the nginx container name
docker ps | grep nginx

# Connect nginx to SMTPy network
docker network connect smtpy_smtpy-network <nginx-container-name>

# Verify connection
docker network inspect smtpy_smtpy-network
```

**Configuration**: Use container names in `nginx/smtpy.conf`:
```nginx
upstream smtpy_frontend {
    server smtpy-frontend-prod:80;
}

upstream smtpy_api {
    server smtpy-api-1:8000;
    server smtpy-api-2:8000;
    keepalive 32;
}
```

### Option 2: Run Nginx in Docker with Shared Network

Create or update your nginx docker-compose to include SMTPy network:

```yaml
# /path/to/nginx/docker-compose.yml
version: '3.8'
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./sites-enabled:/etc/nginx/sites-enabled:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    networks:
      - default
      - smtpy_network  # Connect to SMTPy network

networks:
  smtpy_network:
    external: true
    name: smtpy_smtpy-network  # Reference existing SMTPy network
```

Then restart nginx:
```bash
docker compose down
docker compose up -d
```

### Option 3: Host-Based Nginx with Docker Network Access

If nginx is installed directly on the host (not in Docker), you need to expose containers on localhost only:

**Update `docker-compose.prod.yml`**:
```yaml
services:
  api:
    ports:
      - "127.0.0.1:8000:8000"  # Only accessible from localhost

  frontend:
    ports:
      - "127.0.0.1:8080:80"    # Only accessible from localhost
```

**Update `nginx/smtpy.conf`**:
```nginx
upstream smtpy_frontend {
    server 127.0.0.1:8080;
}

upstream smtpy_api {
    server 127.0.0.1:8000;
}
```

**Note**: This option sacrifices some security benefits but avoids Docker networking complexity.

## Deployment Steps

### Step 1: Verify Current Nginx Setup

```bash
# Check if nginx is running in Docker
docker ps | grep nginx

# OR check if nginx is on host
systemctl status nginx  # systemd
service nginx status    # init.d
```

### Step 2: Update SMTPy Configuration

The production compose file has already been updated to remove port mappings. No changes needed.

### Step 3: Connect Nginx to Docker Network

**If nginx is in Docker** (recommended):
```bash
# Deploy SMTPy first
cd /srv/smtpy
./scripts/deploy-production.sh

# Connect nginx to SMTPy network
docker network connect smtpy_smtpy-network nginx

# Verify
docker exec nginx ping -c 1 smtpy-frontend-prod
docker exec nginx ping -c 1 smtpy-api-1
```

**If nginx is on host**:
```bash
# Uncomment port mappings in docker-compose.prod.yml for localhost only:
# ports:
#   - "127.0.0.1:8000:8000"
#   - "127.0.0.1:8080:80"

# Then deploy
./scripts/deploy-production.sh
```

### Step 4: Update Nginx Configuration

Copy the updated configuration:
```bash
# For Docker nginx
docker cp nginx/smtpy.conf nginx:/etc/nginx/sites-available/smtpy.conf
docker exec nginx ln -sf /etc/nginx/sites-available/smtpy.conf /etc/nginx/sites-enabled/
docker exec nginx nginx -t
docker exec nginx nginx -s reload

# For host nginx
sudo cp nginx/smtpy.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/smtpy.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Test Connectivity

```bash
# Test from nginx container to SMTPy services
docker exec nginx curl -f http://smtpy-frontend-prod:80
docker exec nginx curl -f http://smtpy-api-1:8000/health
docker exec nginx curl -f http://smtpy-api-2:8000/health

# Test external access
curl -f https://smtpy.fr/
curl -f https://smtpy.fr/health
```

## Troubleshooting

### Issue: "could not be resolved" or "host not found"

**Symptom**:
```
nginx: [emerg] host not found in upstream "smtpy-frontend-prod"
```

**Cause**: Nginx cannot resolve Docker container names

**Fix**: Verify nginx is connected to the Docker network
```bash
# Check nginx network connections
docker inspect nginx | grep -A 20 Networks

# Should show smtpy_smtpy-network
# If not, connect it:
docker network connect smtpy_smtpy-network nginx
```

### Issue: "Connection refused"

**Symptom**:
```
connect() failed (111: Connection refused) while connecting to upstream
```

**Cause**: Container is not running or not listening on expected port

**Fix**: Check container status
```bash
# Verify containers are running
docker ps | grep smtpy

# Check container logs
docker logs smtpy-api-1
docker logs smtpy-frontend-prod

# Test connectivity from within nginx
docker exec nginx curl -v http://smtpy-api-1:8000/health
```

### Issue: "Network not found"

**Symptom**:
```
Error response from daemon: network smtpy_smtpy-network not found
```

**Cause**: SMTPy containers not deployed yet

**Fix**: Deploy SMTPy first
```bash
cd /srv/smtpy
./scripts/deploy-production.sh

# Then connect nginx
docker network connect smtpy_smtpy-network nginx
```

### Issue: Port conflicts still occurring

**Symptom**:
```
Bind for 0.0.0.0:80 failed: port is already allocated
```

**Cause**: You have port mappings uncommented in docker-compose.prod.yml

**Fix**: Ensure all external port mappings are commented out
```bash
# Check for exposed ports
grep -n "ports:" docker-compose.prod.yml

# Should only see commented lines or localhost bindings (127.0.0.1:)
```

## Verification Checklist

After setup, verify:

- [ ] SMTPy containers are running: `docker ps | grep smtpy`
- [ ] Nginx is connected to network: `docker network inspect smtpy_smtpy-network | grep nginx`
- [ ] DNS resolution works: `docker exec nginx ping -c 1 smtpy-api-1`
- [ ] HTTP connectivity works: `docker exec nginx curl http://smtpy-api-1:8000/health`
- [ ] External access works: `curl https://smtpy.fr/health`
- [ ] No port conflicts: `docker ps` shows no host port mappings for SMTPy services
- [ ] Load balancing works: Check logs from both API instances

## Monitoring

```bash
# Watch nginx access logs
docker logs -f nginx 2>&1 | grep smtpy

# Monitor SMTPy services
docker stats smtpy-frontend-prod smtpy-api-1 smtpy-api-2

# Check which backend is serving requests
docker logs smtpy-api-1 -f --tail 10
docker logs smtpy-api-2 -f --tail 10
```

## Security Benefits

By keeping services internal to Docker network:

✅ **Database not exposed** - PostgreSQL only accessible from application containers
✅ **Redis not exposed** - Cache layer protected from external access
✅ **SMTP not exposed** - Mail server only accessible via API
✅ **Reduced attack surface** - Only nginx exposed to internet
✅ **Better isolation** - Services can't be accessed directly from other host applications

## Performance Benefits

✅ **Direct container-to-container communication** - No NAT overhead
✅ **Load balancing** - Nginx distributes load across API replicas
✅ **Connection pooling** - Nginx maintains keepalive connections
✅ **No localhost bottleneck** - Docker networking is more efficient than host networking

## Related Documentation

- [Deployment Fixes](./DEPLOYMENT_FIXES.md) - Port conflict resolution
- [Nginx Deployment](./NGINX_DEPLOYMENT.md) - SSL/TLS setup
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Full deployment instructions
- [Docker Infrastructure Summary](./DOCKER_INFRASTRUCTURE_SUMMARY.md) - Architecture overview

---

**Last Updated**: 2025-10-27
**Status**: ✅ Production Ready
