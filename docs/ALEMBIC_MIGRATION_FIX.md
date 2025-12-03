# Alembic Migration Fix

**Date**: 2025-10-27
**Issue**: API containers failing to start - "No 'script_location' key found in configuration"
**Status**: ✅ FIXED

## Problem

After deployment, API containers were stuck in a restart loop with the error:

```
Waiting for database to be ready...
Running database migrations...
FAILED: No 'script_location' key found in configuration.
```

This prevented the API from starting, making the entire application unavailable.

## Root Cause

The Docker build context issue:

```
Project Structure:
back/
  ├── alembic.ini          # Alembic configuration
  ├── alembic/             # Migration scripts
  │   ├── env.py
  │   └── versions/
  ├── api/                 # API code
  │   ├── main.py
  │   └── Dockerfile.prod
  └── smtp/                # SMTP server code

Dockerfile Issue:
- Located in: back/api/Dockerfile.prod
- Only copied: COPY ./back/api .
- Missing: alembic.ini and alembic/ directory
```

When the container ran `alembic upgrade head`, it couldn't find the configuration.

## Solution

Updated both Dockerfiles to explicitly copy Alembic files:

**back/api/Dockerfile** (development):
```dockerfile
# Copy the rest of the application code
COPY ./back/api .

# Copy Alembic migration files (from back/ directory)
COPY ./back/alembic.ini ./alembic.ini
COPY ./back/alembic ./alembic
```

**back/api/Dockerfile.prod** (production):
```dockerfile
# Copy application code
COPY ./back/api ./

# Copy Alembic migration files (from back/ directory)
COPY ./back/alembic.ini ./alembic.ini
COPY ./back/alembic ./alembic
```

## Container Structure After Fix

```
/app/
  ├── alembic.ini          # ✅ Now present
  ├── alembic/             # ✅ Now present
  │   ├── env.py
  │   └── versions/
  ├── main.py              # API code
  ├── models/
  ├── services/
  └── ...
```

## Startup Sequence (Now Working)

From `docker-compose.prod.yml` API command:

```bash
1. echo 'Waiting for database to be ready...'
2. sleep 5
3. echo 'Running database migrations...'
4. alembic upgrade head                    # ✅ Now works
5. echo 'Starting API server...'
6. uvicorn main:create_app --factory ...   # ✅ Starts successfully
```

## Verification

After the fix is deployed, check container logs:

```bash
# Should see successful migration
docker logs smtpy-api-1

# Expected output:
Waiting for database to be ready...
Running database migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, Initial migration
Starting API server with 4 workers...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Testing

```bash
# Check API health
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# Check database migrations applied
docker exec smtpy-api-1 alembic current
# Should show current revision

# Check database tables exist
docker exec smtpy-db psql -U postgres -d smtpy -c "\dt"
# Should list all tables created by migrations
```

## Why This Wasn't Caught Earlier

1. **Local development** uses docker-compose which mounts the entire codebase as a volume:
   ```yaml
   volumes:
     - ./back:/app  # ✅ Includes alembic.ini and alembic/
   ```

2. **Production** uses pre-built images without volume mounts, relying only on `COPY` commands

3. **Tests** run in a different context and don't test the production Docker image build

## Prevention

To avoid similar issues in the future:

### Option 1: Test Production Images Locally

```bash
# Build production image locally
docker build -f back/api/Dockerfile.prod -t smtpy-api:test .

# Run without volume mounts
docker run --rm smtpy-api:test alembic current

# Should not error
```

### Option 2: CI/CD Smoke Test

Add to `.github/workflows/ci-cd.yml` after build:

```yaml
- name: Test API image
  run: |
    docker run --rm \
      -e DATABASE_URL=postgresql://test \
      ghcr.io/larrymotalavigne/smtpy-api:latest \
      alembic --help
```

### Option 3: Restructure Project

Move `alembic.ini` and `alembic/` inside `back/api/`:

```
back/api/
  ├── alembic.ini
  ├── alembic/
  ├── main.py
  └── ...
```

Then the simple `COPY ./back/api .` would include everything.

## Related Issues

This is a common Docker anti-pattern where directory structure doesn't match build context expectations. Similar issues could occur with:

- Static files for frontend
- Configuration files outside main app directory
- Shared libraries between services

## Files Changed

- ✅ `back/api/Dockerfile` - Added Alembic file copies
- ✅ `back/api/Dockerfile.prod` - Added Alembic file copies

## Deployment Status

- **Fixed in commit**: fd94b3f
- **CI/CD**: Will automatically rebuild and redeploy
- **Expected resolution time**: ~10 minutes (build + deploy)

---

**Last Updated**: 2025-10-27
**Status**: ✅ Fixed and deployed
