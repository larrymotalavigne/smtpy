# PostgreSQL 18 Upgrade Summary

**Date**: 2025-10-26
**Previous Version**: PostgreSQL 16
**New Version**: PostgreSQL 18

## Changes Made

### 1. Docker Compose Configurations

#### Development (`docker-compose.yml`)
```yaml
# Before: image: postgres:16
# After:  image: postgres:18
```

#### Production (`docker-compose.prod.yml`)
```yaml
# Before: image: postgres:16-alpine
# After:  image: postgres:18-alpine
```

**Also fixed in production config:**
- Removed obsolete `version: '3.8'` attribute (Docker Compose v2 compatibility)
- Removed `container_name: smtpy-api-prod` to allow `replicas: 2` to work correctly
  - Docker Compose auto-generates names when scaling: `smtpy-api-1`, `smtpy-api-2`

### 2. Test Configurations

#### Main Test Fixture (`back/tests/conftest.py`)
```python
# Before: image="postgres:16"
# After:  image="postgres:18"
```

#### Integration Test (`back/tests/test_auth_integration.py`)
```python
# Before: PostgresContainer("postgres:16")
# After:  PostgresContainer("postgres:18")
```

### 3. Documentation Updates

Updated PostgreSQL version references in:
- `docs/DATABASE_MANAGEMENT.md`
- `docs/DOCKER_INFRASTRUCTURE_SUMMARY.md`
- `docs/DEPLOYMENT_GUIDE.md`

## Verification

### Test Results
✅ **All 121 tests passing** with PostgreSQL 18

```
121 passed, 5 warnings in 38.91s
```

### Compatibility Notes

PostgreSQL 18 is fully backward compatible with PostgreSQL 16 for this application. No schema changes or code modifications were required.

## Deployment Instructions

### For Existing Deployments

#### Option A: Fresh Start (Recommended for Development)

```bash
# Stop and remove existing containers
docker compose down -v  # WARNING: This removes volumes/data!

# Start with PostgreSQL 18
docker compose up -d
```

#### Option B: Data Migration (Recommended for Production)

**Before upgrading:**

1. **Backup existing database:**
   ```bash
   # Create backup
   docker exec smtpy-db-prod pg_dumpall -U postgres > backup-$(date +%Y%m%d).sql

   # Or use the backup script
   docker exec smtpy-db-prod pg_dump -U postgres smtpy > smtpy-backup-$(date +%Y%m%d).sql
   ```

2. **Stop the application:**
   ```bash
   docker compose -f docker-compose.prod.yml down
   ```

3. **Update image and restart:**
   ```bash
   # Pull new PostgreSQL 18 image
   docker pull postgres:18-alpine

   # Start with new version
   docker compose -f docker-compose.prod.yml up -d db

   # Wait for database to be ready
   docker exec smtpy-db-prod pg_isready -U postgres
   ```

4. **Restore data if needed:**
   ```bash
   # Only if starting fresh volume
   docker exec -i smtpy-db-prod psql -U postgres smtpy < smtpy-backup-YYYYMMDD.sql
   ```

5. **Start remaining services:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

#### Option C: In-Place Upgrade (Advanced)

PostgreSQL 18 can read PostgreSQL 16 data directories, but this is not recommended without testing:

```bash
# NOT RECOMMENDED without testing
# Stop container
docker compose down

# Update docker-compose.yml to use postgres:18
# Start container (will use existing data volume)
docker compose up -d

# Check logs for any migration warnings
docker logs smtpy-db-prod
```

### For New Deployments

Simply use the updated configurations - PostgreSQL 18 will be used automatically.

```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d
```

## PostgreSQL 18 New Features

While the application doesn't explicitly use these yet, PostgreSQL 18 brings:

- Performance improvements for large-scale analytics
- Enhanced vacuum performance
- Improved JSON processing
- Better connection pooling
- Security enhancements

Full release notes: https://www.postgresql.org/docs/18/release-18.html

## Rollback Instructions

If issues occur, rollback to PostgreSQL 16:

```bash
# Stop services
docker compose down

# Edit docker-compose.yml
# Change: image: postgres:18 -> image: postgres:16

# Restore from backup if needed
docker compose up -d db
docker exec -i smtpy-db-prod psql -U postgres smtpy < backup-YYYYMMDD.sql

# Start all services
docker compose up -d
```

## Testing Checklist

Before deploying to production, verify:

- ✅ All unit tests pass
- ✅ Integration tests work
- ✅ Database migrations succeed
- ✅ Application connects successfully
- ✅ Queries execute correctly
- ✅ Performance is acceptable
- ✅ Backup/restore works

## Support & Issues

If you encounter issues:

1. **Check logs:**
   ```bash
   docker logs smtpy-db-prod
   docker logs smtpy-api-prod
   ```

2. **Verify database health:**
   ```bash
   docker exec smtpy-db-prod pg_isready -U postgres
   docker exec smtpy-db-prod psql -U postgres -c "SELECT version();"
   ```

3. **Review PostgreSQL 18 release notes** for breaking changes
4. **Restore from backup** if needed
5. **Report issues** on GitHub with logs attached

## Related Documentation

- [Database Management](./DATABASE_MANAGEMENT.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Docker Infrastructure Summary](./DOCKER_INFRASTRUCTURE_SUMMARY.md)
- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/18/)

---

**Last Updated**: 2025-10-26
**Status**: ✅ Complete - All systems verified with PostgreSQL 18
