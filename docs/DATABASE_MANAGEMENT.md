# SMTPy Database Management Guide

**Last Updated**: October 26, 2025
**Database**: PostgreSQL 16
**Version**: 1.0

## Table of Contents

- [Overview](#overview)
- [Backup Procedures](#backup-procedures)
- [Restore Procedures](#restore-procedures)
- [Maintenance Tasks](#maintenance-tasks)
- [Monitoring and Health](#monitoring-and-health)
- [Performance Optimization](#performance-optimization)
- [Disaster Recovery](#disaster-recovery)
- [Security](#security)

## Overview

### Database Architecture

**Database Management System**: PostgreSQL 16
**Deployment**: Docker container (`smtpy-db`)
**Image**: `postgres:18-alpine`
**Data Volume**: `smtpy_postgres_data`
**Backup Location**: `/srv/smtpy/backups/`

### Key Characteristics

- **Size**: ~50-100MB (varies with usage)
- **Tables**: ~15 tables (users, domains, messages, etc.)
- **Connections**: Up to 100 concurrent
- **Encoding**: UTF-8
- **Locale**: en_US.UTF-8

## Backup Procedures

### Automated Daily Backups

**Script**: `/srv/smtpy/scripts/backup-db.sh`

#### Basic Usage

```bash
# Standard backup
./scripts/backup-db.sh

# Verbose output
./scripts/backup-db.sh --verbose

# Custom retention (keep 60 days)
./scripts/backup-db.sh --retention 60

# Dry run (test without executing)
./scripts/backup-db.sh --dry-run
```

#### Remote Backup to S3

```bash
# Configure S3 (one-time setup)
export BACKUP_S3_BUCKET=your-backup-bucket
export BACKUP_S3_PREFIX=smtpy/backups

# Backup with remote upload
./scripts/backup-db.sh --remote --verbose
```

#### Schedule Automated Backups

**Add to crontab**:
```bash
# Edit crontab
crontab -e

# Add daily backup at 3 AM
0 3 * * * /srv/smtpy/scripts/backup-db.sh >> /var/log/smtpy-backup.log 2>&1

# Add weekly backup with remote upload (Sunday 4 AM)
0 4 * * 0 /srv/smtpy/scripts/backup-db.sh --remote >> /var/log/smtpy-backup.log 2>&1
```

#### Backup Output

Backups are saved as:
- **Format**: Gzip-compressed SQL dump
- **Naming**: `smtpy_YYYYMMDD_HHMMSS.sql.gz`
- **Location**: `/srv/smtpy/backups/`
- **Retention**: 30 days (default, configurable)

#### Backup Verification

The script automatically:
- ✅ Tests gzip integrity
- ✅ Verifies file size
- ✅ Confirms database connectivity
- ✅ Logs all operations

### Manual Backups

#### Quick Manual Backup

```bash
# Compressed backup
docker exec smtpy-db pg_dump -U postgres smtpy | gzip > backups/manual_$(date +%Y%m%d).sql.gz

# Uncompressed backup
docker exec smtpy-db pg_dump -U postgres smtpy > backups/manual_$(date +%Y%m%d).sql
```

#### Specific Table Backup

```bash
# Backup single table
docker exec smtpy-db pg_dump -U postgres -d smtpy -t messages | gzip > backups/messages_only.sql.gz
```

#### Schema-Only Backup

```bash
# Backup structure without data
docker exec smtpy-db pg_dump -U postgres -d smtpy --schema-only > backups/schema_only.sql
```

### Volume Backups

```bash
# Backup entire PostgreSQL data volume
docker run --rm \
  -v smtpy_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz -C /data .
```

## Restore Procedures

### Automated Restore

**Script**: `/srv/smtpy/scripts/restore-db.sh`

#### Basic Usage

```bash
# Interactive restore (with confirmation)
./scripts/restore-db.sh backups/smtpy_20250126_120000.sql.gz

# Force restore (skip confirmation)
./scripts/restore-db.sh backups/smtpy_20250126_120000.sql.gz --force

# Skip pre-restore backup
./scripts/restore-db.sh backups/smtpy_20250126_120000.sql.gz --no-backup

# Verbose output
./scripts/restore-db.sh backups/smtpy_20250126_120000.sql.gz --verbose

# Dry run (test without executing)
./scripts/restore-db.sh backups/smtpy_20250126_120000.sql.gz --dry-run
```

#### What the Script Does

1. ✅ Verifies backup file integrity
2. ✅ Creates pre-restore backup (optional)
3. ✅ Stops API and SMTP services
4. ✅ Drops and recreates database
5. ✅ Restores from backup
6. ✅ Verifies restoration
7. ✅ Restarts services
8. ✅ Waits for health checks

### Manual Restore

#### Full Database Restore

```bash
# Stop services
docker compose -f docker-compose.prod.yml stop api smtp

# Restore from compressed backup
gunzip -c backups/smtpy_20250126.sql.gz | \
  docker exec -i smtpy-db psql -U postgres -d smtpy

# Restart services
docker compose -f docker-compose.prod.yml start api smtp
```

#### Restore Specific Tables

```bash
# Create temporary database
docker exec smtpy-db psql -U postgres -c "CREATE DATABASE temp_restore;"

# Restore full backup to temp
gunzip -c backups/smtpy_20250126.sql.gz | \
  docker exec -i smtpy-db psql -U postgres -d temp_restore

# Export specific table
docker exec smtpy-db psql -U postgres -d temp_restore -c \
  "COPY messages TO STDOUT CSV HEADER" > messages_export.csv

# Import to production
cat messages_export.csv | docker exec -i smtpy-db psql -U postgres -d smtpy -c \
  "COPY messages FROM STDIN CSV HEADER"

# Drop temp database
docker exec smtpy-db psql -U postgres -c "DROP DATABASE temp_restore;"
```

### Point-in-Time Recovery

**Prerequisites**: WAL archiving enabled (not configured by default)

For future implementation:
```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
```

## Maintenance Tasks

### Automated Maintenance

**Script**: `/srv/smtpy/scripts/db-maintenance.sh`

#### Common Operations

**Check Database Health**:
```bash
./scripts/db-maintenance.sh --check-bloat --check-queries --verbose
```

**Weekly Maintenance** (VACUUM and ANALYZE):
```bash
./scripts/db-maintenance.sh --vacuum --analyze --verbose
```

**Monthly Deep Maintenance**:
```bash
./scripts/db-maintenance.sh --all --verbose
```

**Full Maintenance** (requires downtime):
```bash
# Stop services first
docker compose -f docker-compose.prod.yml stop api smtp

# Run VACUUM FULL
./scripts/db-maintenance.sh --full --verbose

# Restart services
docker compose -f docker-compose.prod.yml start api smtp
```

#### Maintenance Schedule

**Recommended Schedule**:
```bash
# Edit crontab
crontab -e

# Weekly VACUUM ANALYZE (Sunday 2 AM)
0 2 * * 0 /srv/smtpy/scripts/db-maintenance.sh --vacuum --analyze >> /var/log/smtpy-maintenance.log 2>&1

# Monthly health check (1st of month, 1 AM)
0 1 1 * * /srv/smtpy/scripts/db-maintenance.sh --check-bloat --check-queries >> /var/log/smtpy-maintenance.log 2>&1
```

### Manual Maintenance

#### VACUUM

```bash
# Standard VACUUM (no locks)
docker exec smtpy-db psql -U postgres -d smtpy -c "VACUUM;"

# VACUUM specific table
docker exec smtpy-db psql -U postgres -d smtpy -c "VACUUM messages;"

# VACUUM VERBOSE for details
docker exec smtpy-db psql -U postgres -d smtpy -c "VACUUM VERBOSE;"

# VACUUM ANALYZE (reclaim + update stats)
docker exec smtpy-db psql -U postgres -d smtpy -c "VACUUM ANALYZE;"
```

#### ANALYZE

```bash
# Update query planner statistics
docker exec smtpy-db psql -U postgres -d smtpy -c "ANALYZE;"

# Analyze specific table
docker exec smtpy-db psql -U postgres -d smtpy -c "ANALYZE messages;"
```

#### REINDEX

```bash
# Rebuild all indexes
docker exec smtpy-db psql -U postgres -d smtpy -c "REINDEX DATABASE smtpy;"

# Reindex specific table
docker exec smtpy-db psql -U postgres -d smtpy -c "REINDEX TABLE messages;"

# Reindex specific index
docker exec smtpy-db psql -U postgres -d smtpy -c "REINDEX INDEX messages_pkey;"
```

## Monitoring and Health

### Database Health Checks

**Quick Health Check**:
```bash
# Is database accepting connections?
docker exec smtpy-db pg_isready -U postgres

# Can we query?
docker exec smtpy-db psql -U postgres -d smtpy -c "SELECT 1;"
```

### Database Size Monitoring

```bash
# Total database size
docker exec smtpy-db psql -U postgres -d smtpy -c \
  "SELECT pg_size_pretty(pg_database_size('smtpy'));"

# Table sizes
docker exec smtpy-db psql -U postgres -d smtpy -c "
  SELECT
    schemaname || '.' || tablename AS table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Connection Monitoring

```bash
# Active connections
docker exec smtpy-db psql -U postgres -d smtpy -c "
  SELECT COUNT(*) as connections
  FROM pg_stat_activity
  WHERE datname = 'smtpy';"

# Connection details
docker exec smtpy-db psql -U postgres -d smtpy -c "
  SELECT
    usename,
    application_name,
    client_addr,
    state,
    query_start
  FROM pg_stat_activity
  WHERE datname = 'smtpy'
  ORDER BY query_start DESC;"
```

### Long-Running Queries

```bash
# Queries running >5 minutes
docker exec smtpy-db psql -U postgres -d smtpy -c "
  SELECT
    pid,
    usename,
    state,
    NOW() - query_start AS duration,
    LEFT(query, 100) AS query
  FROM pg_stat_activity
  WHERE state != 'idle'
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND pid != pg_backend_pid()
  ORDER BY query_start;"
```

### Table Statistics

```bash
# Dead tuples and bloat
docker exec smtpy-db psql -U postgres -d smtpy -c "
  SELECT
    schemaname || '.' || tablename AS table_name,
    n_live_tup AS live_rows,
    n_dead_tup AS dead_rows,
    ROUND(100 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2) AS bloat_pct,
    last_vacuum,
    last_autovacuum
  FROM pg_stat_user_tables
  ORDER BY n_dead_tup DESC;"
```

## Performance Optimization

### Query Performance

**Enable Query Logging** (temporary):
```bash
docker exec smtpy-db psql -U postgres -c \
  "ALTER SYSTEM SET log_min_duration_statement = 1000;"  # Log queries >1s

docker exec smtpy-db psql -U postgres -c "SELECT pg_reload_conf();"
```

**View Slow Queries**:
```bash
docker compose -f docker-compose.prod.yml logs db | grep "duration:"
```

### Index Management

**Find Missing Indexes**:
```bash
docker exec smtpy-db psql -U postgres -d smtpy -c "
  SELECT
    schemaname || '.' || tablename AS table_name,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / GREATEST(seq_scan, 1) AS avg_rows_per_scan
  FROM pg_stat_user_tables
  WHERE seq_scan > 0
  ORDER BY seq_tup_read DESC
  LIMIT 10;"
```

**Find Unused Indexes**:
```bash
docker exec smtpy-db psql -U postgres -d smtpy -c "
  SELECT
    schemaname || '.' || tablename AS table_name,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0
  AND schemaname = 'public'
  ORDER BY pg_relation_size(indexrelid) DESC;"
```

### Connection Pooling

Consider implementing PgBouncer for connection pooling in high-traffic scenarios.

## Disaster Recovery

See [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md) for comprehensive disaster recovery procedures.

**Quick Recovery Summary**:

1. **Database Corruption**: Use `restore-db.sh` with latest backup (30-60 min)
2. **Accidental Deletion**: Restore specific tables from backup (30-60 min)
3. **Server Failure**: Rebuild on new server with backups (2-4 hours)

## Security

### Access Control

**Default Configuration**:
- User: `postgres`
- Password: From `.env.production` (`POSTGRES_PASSWORD`)
- Network: Internal Docker network only
- Port: Not exposed externally

### Password Rotation

**Change Database Password**:
```bash
# Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# Update in database
docker exec smtpy-db psql -U postgres -c \
  "ALTER USER postgres WITH PASSWORD '$NEW_PASSWORD';"

# Update .env.production
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASSWORD/" .env.production

# Restart services
docker compose -f docker-compose.prod.yml restart api smtp
```

### Encryption

**Data at Rest**:
- Docker volume encryption (if enabled at host level)
- Consider encrypted filesystems for sensitive data

**Data in Transit**:
- SSL/TLS between application and database (configurable)
- All external connections use HTTPS

### Backup Security

**Encrypt Backups** (recommended):
```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 backups/smtpy_20250126.sql.gz

# Decrypt for restore
gpg --decrypt backups/smtpy_20250126.sql.gz.gpg | \
  gunzip | docker exec -i smtpy-db psql -U postgres -d smtpy
```

## Best Practices

### Daily Operations

- [ ] Monitor backup success logs
- [ ] Check database size trends
- [ ] Review slow query logs
- [ ] Monitor connection counts

### Weekly Tasks

- [ ] Run VACUUM ANALYZE
- [ ] Review table statistics
- [ ] Check for bloat
- [ ] Test backup restoration (monthly)

### Monthly Tasks

- [ ] Full database maintenance
- [ ] Review and optimize indexes
- [ ] Test disaster recovery procedures
- [ ] Update documentation if needed

### Quarterly Tasks

- [ ] Full DR drill
- [ ] Review backup retention policy
- [ ] Audit database security
- [ ] Performance tuning review

## Troubleshooting

### Common Issues

**Issue**: Backup fails with "Permission denied"
**Solution**:
```bash
# Fix permissions
sudo chown -R $(whoami):$(whoami) /srv/smtpy/backups/
chmod +x /srv/smtpy/scripts/backup-db.sh
```

**Issue**: Database out of disk space
**Solution**:
```bash
# Check disk usage
df -h

# Run VACUUM FULL to reclaim space
./scripts/db-maintenance.sh --full

# Clean old backups
find /srv/smtpy/backups/ -name "smtpy_*.sql.gz" -mtime +30 -delete
```

**Issue**: Restore fails with "database is being accessed"
**Solution**:
```bash
# Kill all connections
docker exec smtpy-db psql -U postgres -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE datname = 'smtpy' AND pid <> pg_backend_pid();"

# Then retry restore
./scripts/restore-db.sh backups/latest.sql.gz
```

**Issue**: Slow queries
**Solution**:
```bash
# Run ANALYZE to update statistics
docker exec smtpy-db psql -U postgres -d smtpy -c "ANALYZE;"

# Check for missing indexes
./scripts/db-maintenance.sh --check-bloat

# Consider REINDEX
./scripts/db-maintenance.sh --reindex
```

## Quick Reference

### Essential Commands

```bash
# Backup
./scripts/backup-db.sh --verbose

# Restore
./scripts/restore-db.sh backups/latest.sql.gz

# Maintenance
./scripts/db-maintenance.sh --all

# Health check
docker exec smtpy-db pg_isready

# Database size
docker exec smtpy-db psql -U postgres -d smtpy -c \
  "SELECT pg_size_pretty(pg_database_size('smtpy'));"

# Connection count
docker exec smtpy-db psql -U postgres -d smtpy -c \
  "SELECT COUNT(*) FROM pg_stat_activity WHERE datname='smtpy';"
```

---

**For detailed disaster recovery procedures**, see [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md)
**For deployment procedures**, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
