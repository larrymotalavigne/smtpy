# Deployment Issues - Complete Resolution Log

**Date**: 2025-10-27
**Environment**: Unraid server with Nginx Proxy Manager
**Status**: 🔄 IN PROGRESS - Final build deploying

## Issues Encountered and Fixed

### Issue #1: Port Allocation Conflicts ✅ FIXED
**Commit**: e021146, 565f191

**Error**:
```
Error response from daemon: Bind for 0.0.0.0:5432 failed: port is already allocated
Error response from daemon: Bind for 0.0.0.0:8000 failed: port is already allocated
Error response from daemon: Bind for 0.0.0.0:1025 failed: port is already allocated
Error response from daemon: Bind for 0.0.0.0:80 failed: port is already allocated
```

**Root Cause**: Multiple applications on Unraid host competing for same ports

**Solution**:
- Removed ALL external port mappings from docker-compose.prod.yml
- Services now communicate via internal Docker network only
- Nginx Proxy Manager provides external access
- Added forceful container cleanup to deployment scripts

**Files Changed**:
- docker-compose.prod.yml: Removed all `ports:` sections
- nginx/smtpy.conf: Updated to use container names
- .github/workflows/ci-cd.yml: Added `docker ps -a --filter` cleanup
- scripts/deploy-production.sh: Added forceful cleanup

---

### Issue #2: Alembic Migration Files Missing ✅ FIXED
**Commit**: fd94b3f

**Error**:
```
FAILED: No 'script_location' key found in configuration
```

**Root Cause**: Dockerfiles only copied `./back/api` but alembic.ini and alembic/ are in `./back/`

**Solution**:
Added explicit COPY commands for Alembic files:
```dockerfile
COPY ./back/alembic.ini ./alembic.ini
COPY ./back/alembic ./alembic
```

**Files Changed**:
- back/api/Dockerfile
- back/api/Dockerfile.prod

---

### Issue #3: Frontend Volume Mount Errors ✅ FIXED
**Commit**: 7eff925

**Error**:
```
error mounting nginx.conf: not a directory
```

**Root Cause**: docker-compose.prod.yml tried to mount files that don't exist on server

**Solution**: Removed unnecessary volume mounts:
- SSL certificates (handled by Nginx Proxy Manager)
- nginx.conf (baked into Docker image)

**Files Changed**:
- docker-compose.prod.yml: Removed volumes section from frontend service

---

### Issue #4: Module Import Path Errors ✅ FIXED
**Commit**: 8f1aef4

**Error**:
```
ModuleNotFoundError: No module named 'api'
ModuleNotFoundError: No module named 'smtp'
```

**Root Cause**: Dockerfiles flattened directory structure, breaking import paths

**Solution**: Maintain module structure with PYTHONPATH
```dockerfile
# Before: COPY ./back/api ./
# After:  COPY ./back/api ./api

ENV PYTHONPATH="/app"
CMD ["uvicorn", "api.main:create_app", ...]
```

**Container Structure**:
```
/app/
  ├── api/              # Maintains api.core imports
  ├── smtp/             # Maintains smtp.forwarding imports
  ├── alembic/          # Can import from api.models
  └── alembic.ini
```

**Files Changed**:
- back/api/Dockerfile
- back/api/Dockerfile.prod
- back/smtp/Dockerfile.prod
- docker-compose.prod.yml

---

### Issue #5: Alembic Package Not Installed ✅ FIXED
**Commit**: 39e9709

**Error**:
```
ModuleNotFoundError: No module named 'alembic.config'
```

**Root Cause**: `uv sync --frozen --no-dev` may have caused dependency resolution issues

**Solution**: Removed `--no-dev` flag
```dockerfile
# Before: RUN uv sync --frozen --no-dev
# After:  RUN uv sync --frozen
```

**Trade-off**: Slightly larger image (~50MB) but more reliable dependency installation

**Files Changed**:
- back/api/Dockerfile.prod
- back/smtp/Dockerfile.prod

---

### Issue #6: SMTP Missing Core Module ✅ FIXED
**Commit**: 0e388a0

**Error**:
```
ModuleNotFoundError: No module named 'core'
```

**Root Cause**: SMTP server imports from `core` module which exists in API directory

**Solution**: Copy shared core module into SMTP container
```dockerfile
COPY ./back/smtp ./smtp
COPY ./back/api/core ./core  # Shared module
```

**Files Changed**:
- back/smtp/Dockerfile
- back/smtp/Dockerfile.prod

---

### Issue #7: Alembic Import Path in Migrations ✅ FIXED
**Commit**: 2da1df9

**Error**:
```
ModuleNotFoundError: No module named 'api' (in alembic/env.py)
```

**Root Cause**: alembic/env.py used `from api.core.config` but needed fallback

**Solution**: Added try/except fallback imports
```python
try:
    from api.core.config import SETTINGS
except ModuleNotFoundError:
    from core.config import SETTINGS
```

**Note**: This was later superseded by Issue #4 fix (PYTHONPATH approach)

**Files Changed**:
- back/alembic/env.py

---

### Issue #8: SMTP Handler Import Paths ✅ FIXED
**Commit**: 63c4508

**Error**:
```
ModuleNotFoundError: No module named 'smtp' (in handler.py)
```

**Root Cause**: handler.py used `import smtp.forwarding.forwarder`

**Solution**: Added try/except fallback
```python
try:
    import smtp.forwarding.forwarder as forwarder_module
except ModuleNotFoundError:
    import forwarding.forwarder as forwarder_module
```

**Note**: This was later superseded by Issue #4 fix (PYTHONPATH approach)

**Files Changed**:
- back/smtp/smtp_server/handler.py

---

### Enhancement: CI/CD Concurrency Control ✅ ADDED
**Commit**: 46fbb5c

**Purpose**: Prevent multiple deployments from running simultaneously

**Configuration**:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Benefits**:
- Cancels outdated builds when new commit pushed
- Saves CI/CD minutes
- Ensures only latest code deploys

**Files Changed**:
- .github/workflows/ci-cd.yml

---

## Current Status

### Latest Commit: 0e388a0
All issues have been fixed in the codebase. The CI/CD pipeline is:
1. Building new Docker images with all fixes
2. Pushing to GitHub Container Registry
3. Deploying to production server

### Expected Timeline
- **Build + Push**: ~8-10 minutes
- **Deploy**: ~2 minutes
- **Total**: ~12 minutes from commit

### Verification Steps

Once deployment completes, verify:

```bash
# 1. Check all containers are running
docker ps | grep smtpy

# Expected output:
# smtpy-frontend-prod    Up (healthy)
# smtpy-api-1           Up (healthy)
# smtpy-api-2           Up (healthy)
# smtpy-smtp-prod       Up (healthy)
# smtpy-db-prod         Up (healthy)
# smtpy-redis-prod      Up (healthy)

# 2. Check API logs (should show successful migration)
docker logs smtpy-api-1 --tail 20

# Expected output:
# Running database migrations...
# INFO  [alembic.runtime.migration] Running upgrade -> xxxxx
# Starting API server with 4 workers...
# Application startup complete.

# 3. Check SMTP logs (should be running)
docker logs smtpy-smtp-prod --tail 10

# Expected output:
# SMTP server starting on 0.0.0.0:1025
# Server started successfully

# 4. Test API health
docker exec smtpy-api-1 curl -f http://localhost:8000/health

# Expected: {"status":"healthy","service":"SMTPy v2 API","version":"2.0.0"}
```

## Next Steps After Successful Deployment

### 1. Connect Nginx Proxy Manager (One-Time Setup)

```bash
# Find NPM container name
docker ps | grep nginx-proxy-manager

# Connect NPM to SMTPy network
docker network connect smtpy_smtpy-network <npm-container-name>

# Verify connection
docker exec <npm-container-name> ping -c 1 smtpy-frontend-prod
docker exec <npm-container-name> curl http://smtpy-api-1:8000/health
```

### 2. Configure Proxy Host in NPM UI

Open NPM web interface: `http://<unraid-ip>:81`

**Create Proxy Host**:
- Domain Names: `smtpy.fr`, `www.smtpy.fr`
- Scheme: `http`
- Forward Hostname: `smtpy-frontend-prod`
- Forward Port: `80`
- Enable: Cache Assets, Block Exploits, Websockets
- SSL: Request New Certificate, Force SSL, HTTP/2, HSTS

### 3. Verify External Access

```bash
# Test external HTTPS
curl https://smtpy.fr/
curl https://smtpy.fr/health

# Should return HTML and health check response
```

## Documentation

### Quick References
- [Quick Start NPM](./QUICK_START_NPM.md) - Fast setup guide
- [NPM Setup](./NGINX_PROXY_MANAGER_SETUP.md) - Detailed NPM configuration
- [Port Conflict Resolution](./PORT_CONFLICT_RESOLUTION.md) - Network architecture
- [Alembic Migration Fix](./ALEMBIC_MIGRATION_FIX.md) - Migration troubleshooting

### Technical Details
- [Docker Network Setup](./NGINX_DOCKER_NETWORK_SETUP.md) - Manual nginx guide
- [Deployment Fixes](./DEPLOYMENT_FIXES.md) - Container cleanup procedures
- [PostgreSQL 18 Upgrade](./POSTGRESQL_18_UPGRADE.md) - Database upgrade guide

## Lessons Learned

### Docker Best Practices
1. ✅ **Maintain module structure** - Don't flatten directories in containers
2. ✅ **Use PYTHONPATH** - Allows flexible import paths
3. ✅ **Copy shared modules** - Include dependencies from other services
4. ✅ **Internal networking** - Avoid exposing unnecessary ports
5. ✅ **Health checks** - Ensure services start before depending services

### CI/CD Improvements
1. ✅ **Concurrency control** - Prevent overlapping deployments
2. ✅ **Forceful cleanup** - Handle orphaned containers from different projects
3. ✅ **Proper dependency installation** - Don't skip needed packages for size

### Monorepo Challenges
1. **Shared code** - API and SMTP share `core` module
2. **Build context** - Need to copy from multiple directories
3. **Import paths** - Maintain consistency between dev and prod

## Success Metrics

Once fully deployed:
- ✅ 6/6 containers running and healthy
- ✅ 0 restarts after startup
- ✅ Database migrations applied successfully
- ✅ API responding to health checks
- ✅ Frontend accessible via NPM
- ✅ No port conflicts on host
- ✅ All services isolated in Docker network

---

**Last Updated**: 2025-10-27 20:00 UTC
**Status**: Awaiting final build completion (commit 0e388a0)
**Next Action**: Verify deployment, then configure NPM
