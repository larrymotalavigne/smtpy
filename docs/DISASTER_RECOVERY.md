# SMTPy Disaster Recovery Plan

**Last Updated**: October 26, 2025
**Document Version**: 1.0
**Review Frequency**: Quarterly

## Table of Contents

- [Overview](#overview)
- [Recovery Objectives](#recovery-objectives)
- [Backup Strategy](#backup-strategy)
- [Disaster Scenarios](#disaster-scenarios)
- [Recovery Procedures](#recovery-procedures)
- [Testing and Validation](#testing-and-validation)
- [Contacts and Escalation](#contacts-and-escalation)

## Overview

This document outlines the disaster recovery (DR) procedures for the SMTPy email forwarding service. It defines the processes, responsibilities, and procedures required to recover from various disaster scenarios.

### Purpose

- Minimize downtime and data loss
- Ensure business continuity
- Provide clear recovery procedures
- Define roles and responsibilities

### Scope

This plan covers:
- Database recovery
- Application recovery
- Infrastructure recovery
- Service restoration

## Recovery Objectives

### RTO (Recovery Time Objective)

Maximum acceptable downtime for each component:

| Component | RTO | Priority |
|-----------|-----|----------|
| Database | 1 hour | Critical |
| API Server | 30 minutes | Critical |
| SMTP Server | 30 minutes | Critical |
| Frontend | 15 minutes | High |
| Redis Cache | 15 minutes | Medium |

### RPO (Recovery Point Objective)

Maximum acceptable data loss:

| Data Type | RPO | Backup Frequency |
|-----------|-----|------------------|
| Database | 24 hours | Daily |
| Configuration | 0 hours | Version controlled |
| User uploads | N/A | None currently |
| Logs | 7 days | Retained 30 days |

### SLA Targets

- **Uptime**: 99.9% (8.76 hours downtime/year)
- **Data durability**: 99.999% (five nines)
- **Backup retention**: 30 days minimum

## Backup Strategy

### Database Backups

#### Automated Daily Backups

**Schedule**: Daily at 3:00 AM UTC

**Script**: `/srv/smtpy/scripts/backup-db.sh`

**Cron Configuration**:
```bash
0 3 * * * /srv/smtpy/scripts/backup-db.sh >> /var/log/smtpy-backup.log 2>&1
```

**Backup Details**:
- Format: PostgreSQL SQL dump (gzip compressed)
- Location: `/srv/smtpy/backups/`
- Naming: `smtpy_YYYYMMDD_HHMMSS.sql.gz`
- Retention: 30 days (automatic rotation)
- Compression: Yes (gzip)

#### Backup Verification

**Automated Integrity Checks**:
- Gzip integrity test after each backup
- File size validation
- Automatic failure alerts (if configured)

**Manual Monthly Testing**:
- Test restore to staging environment
- Verify data completeness
- Document test results

#### Remote Backups

**Optional S3 Configuration**:
```bash
export BACKUP_S3_BUCKET=your-bucket-name
export BACKUP_S3_PREFIX=smtpy/backups

./scripts/backup-db.sh --remote
```

**Recommended Remote Storage**:
- AWS S3 (Standard or Glacier)
- Backblaze B2
- Wasabi
- Self-hosted MinIO

### Volume Backups

#### Docker Volumes

**PostgreSQL Data Volume**:
```bash
docker run --rm \
  -v smtpy_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz -C /data .
```

**Redis Data Volume**:
```bash
docker run --rm \
  -v smtpy_redis_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis_volume_$(date +%Y%m%d).tar.gz -C /data .
```

**Frequency**: Weekly
**Retention**: 4 weeks

### Configuration Backups

**Version Controlled Files** (Git):
- docker-compose.prod.yml
- .env.production (encrypted)
- nginx.conf
- All application code

**Manual Backups Required**:
- SSL/TLS certificates (monthly)
- Secrets and credentials (encrypted, secure storage)

## Disaster Scenarios

### Scenario 1: Database Corruption

**Indicators**:
- Database connection errors
- Data integrity errors
- PostgreSQL crashes

**Impact**: Critical - Application unavailable

**Recovery Time**: 30-60 minutes

**Recovery Steps**: See [Database Corruption Recovery](#database-corruption-recovery)

### Scenario 2: Server Failure

**Indicators**:
- Server unresponsive
- Hardware failure
- Network connectivity loss

**Impact**: Critical - Complete service outage

**Recovery Time**: 2-4 hours

**Recovery Steps**: See [Server Failure Recovery](#server-failure-recovery)

### Scenario 3: Data Center Outage

**Indicators**:
- Complete loss of connectivity
- Multi-server failure
- Network infrastructure failure

**Impact**: Critical - Complete service outage

**Recovery Time**: 4-8 hours

**Recovery Steps**: See [Data Center Outage Recovery](#data-center-outage-recovery)

### Scenario 4: Accidental Data Deletion

**Indicators**:
- User reports missing data
- Admin error acknowledgment
- Audit log anomalies

**Impact**: High - Partial data loss

**Recovery Time**: 30 minutes - 2 hours

**Recovery Steps**: See [Data Deletion Recovery](#data-deletion-recovery)

### Scenario 5: Security Breach

**Indicators**:
- Unauthorized access detected
- Data exfiltration suspected
- Malware/ransomware detected

**Impact**: Critical - Service compromise

**Recovery Time**: 4-24 hours

**Recovery Steps**: See [Security Breach Recovery](#security-breach-recovery)

### Scenario 6: Application Failure

**Indicators**:
- 500 errors
- Services not starting
- Container crashes

**Impact**: High - Service degradation/outage

**Recovery Time**: 15-30 minutes

**Recovery Steps**: See [Application Failure Recovery](#application-failure-recovery)

## Recovery Procedures

### Database Corruption Recovery

**Prerequisites**:
- SSH access to server
- Database backup available
- Access to `/srv/smtpy/scripts/`

**Steps**:

1. **Assess the Damage** (5 minutes):
```bash
# Check database logs
docker compose -f docker-compose.prod.yml logs db | tail -100

# Try to connect
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "SELECT 1;"

# Check table integrity
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "
  SELECT tablename, pg_relation_size(schemaname||'.'||tablename)
  FROM pg_tables WHERE schemaname='public';"
```

2. **Stop Services** (2 minutes):
```bash
cd /srv/smtpy/
docker compose -f docker-compose.prod.yml stop api smtp
```

3. **Identify Latest Valid Backup** (3 minutes):
```bash
ls -lh backups/smtpy_*.sql.gz | tail -5
```

4. **Restore Database** (15-30 minutes):
```bash
# Automatic restore with pre-restore backup
./scripts/restore-db.sh backups/smtpy_YYYYMMDD_HHMMSS.sql.gz

# Or manual restore
./scripts/restore-db.sh backups/smtpy_YYYYMMDD_HHMMSS.sql.gz --no-backup --force
```

5. **Verify Restoration** (5 minutes):
```bash
# Run verification
./scripts/verify-deployment.sh

# Check critical tables
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "
  SELECT
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM domains) as domains,
    (SELECT COUNT(*) FROM messages) as messages;"
```

6. **Restart Services** (5 minutes):
```bash
docker compose -f docker-compose.prod.yml start api smtp

# Monitor startup
docker compose -f docker-compose.prod.yml logs -f api
```

7. **Verify Application** (5 minutes):
```bash
# Health check
curl https://smtpy.fr/health

# Test functionality
# (manual testing checklist in appendix)
```

**Total Expected Time**: 40-60 minutes

### Server Failure Recovery

**Prerequisites**:
- New/replacement server provisioned
- SSH access configured
- Backups accessible (local or remote)

**Steps**:

1. **Provision New Server** (30-60 minutes):
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install required tools
sudo apt-get update
sudo apt-get install -y git curl wget
```

2. **Clone Repository** (5 minutes):
```bash
cd /srv/
git clone https://github.com/yourusername/smtpy.git
cd smtpy
```

3. **Restore Configuration** (10 minutes):
```bash
# Copy .env.production from backup or recreate
cp backups/.env.production.backup .env.production

# Verify environment
grep -v "^#" .env.production | grep "="
```

4. **Restore SSL Certificates** (10 minutes):
```bash
# Copy from backup or regenerate
mkdir -p ssl/
cp backups/ssl/* ssl/

# Or regenerate with certbot
sudo certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/*.pem ssl/
```

5. **Pull Docker Images** (10 minutes):
```bash
# Login to GHCR
docker login ghcr.io -u username -p token

# Pull images
docker compose -f docker-compose.prod.yml pull
```

6. **Restore Database** (30 minutes):
```bash
# Start database only
docker compose -f docker-compose.prod.yml up -d db redis

# Wait for database
sleep 10

# Restore from latest backup
./scripts/restore-db.sh backups/smtpy_YYYYMMDD_HHMMSS.sql.gz --no-backup
```

7. **Start All Services** (10 minutes):
```bash
# Start remaining services
docker compose -f docker-compose.prod.yml up -d

# Monitor logs
docker compose -f docker-compose.prod.yml logs -f
```

8. **Verify Deployment** (10 minutes):
```bash
./scripts/verify-deployment.sh --verbose
```

9. **Update DNS** (if IP changed) (30-60 minutes):
```bash
# Update A records to new server IP
# Wait for DNS propagation
```

**Total Expected Time**: 2.5-4 hours

### Data Center Outage Recovery

**Prerequisites**:
- Backup data center or cloud provider available
- Recent backups accessible remotely
- DNS management access

**Steps**:

1. **Activate DR Site** (Immediate):
   - Access backup infrastructure
   - Verify connectivity and resources

2. **Deploy to New Location** (Follow [Server Failure Recovery](#server-failure-recovery)):
   - Use automated deployment if available
   - Restore from remote backups (S3, etc.)

3. **Update DNS Records** (15 minutes):
```bash
# Update to new IP addresses
# Consider using low TTL during transition
```

4. **Verify Services** (30 minutes):
   - Run full test suite
   - Monitor for issues
   - Check data integrity

5. **Communicate Status** (Ongoing):
   - Update status page
   - Notify users
   - Document incident

**Total Expected Time**: 4-8 hours

### Data Deletion Recovery

**Prerequisites**:
- Backup containing deleted data
- Knowledge of what was deleted and when

**Steps**:

1. **Identify Deletion Scope** (10 minutes):
```bash
# Check recent database activity
docker exec smtpy-db-prod psql -U postgres -d smtpy -c "
  SELECT * FROM pg_stat_activity
  WHERE state != 'idle'
  ORDER BY query_start DESC
  LIMIT 10;"
```

2. **Find Appropriate Backup** (5 minutes):
```bash
# List backups with dates
ls -lh backups/smtpy_*.sql.gz

# Identify backup before deletion
```

3. **Extract Specific Data** (15-30 minutes):
```bash
# Restore to temporary database
gunzip -c backups/smtpy_YYYYMMDD.sql.gz | \
  docker exec -i smtpy-db-prod psql -U postgres -d temp_restore

# Export specific data
docker exec smtpy-db-prod psql -U postgres -d temp_restore -c "
  COPY (SELECT * FROM table_name WHERE ...)
  TO STDOUT CSV HEADER" > recovered_data.csv
```

4. **Import Recovered Data** (10 minutes):
```bash
# Import to production
cat recovered_data.csv | docker exec -i smtpy-db-prod psql -U postgres -d smtpy -c "
  COPY table_name FROM STDIN CSV HEADER"
```

5. **Verify Recovery** (10 minutes):
```bash
# Verify data is present
# Check for conflicts or duplicates
# Validate data integrity
```

**Total Expected Time**: 50-65 minutes

### Security Breach Recovery

**Prerequisites**:
- Incident response team activated
- Forensic tools available
- Clean backups identified

**Steps**:

1. **Contain the Breach** (Immediate):
```bash
# Isolate affected systems
docker compose -f docker-compose.prod.yml down

# Block suspicious IPs at firewall
sudo ufw deny from <ATTACKER_IP>

# Disable compromised accounts
```

2. **Preserve Evidence** (30 minutes):
```bash
# Capture logs
docker compose -f docker-compose.prod.yml logs > incident_logs.txt

# Save container state
docker commit smtpy-api-prod api-forensics
docker commit smtpy-db-prod db-forensics

# Copy critical files
cp -r /srv/smtpy/ /backup/forensics/$(date +%Y%m%d)/
```

3. **Assess Damage** (1-2 hours):
   - Review logs for unauthorized access
   - Check for data exfiltration
   - Identify compromised credentials
   - Determine breach timeline

4. **Rebuild from Clean State** (2-4 hours):
```bash
# Rebuild all containers from scratch
docker compose -f docker-compose.prod.yml down -v
docker system prune -af

# Pull fresh images
docker compose -f docker-compose.prod.yml pull

# Restore from clean backup (before breach)
./scripts/restore-db.sh backups/pre_breach_backup.sql.gz
```

5. **Rotate All Credentials** (1 hour):
```bash
# Generate new passwords
export NEW_DB_PASSWORD=$(openssl rand -base64 32)
export NEW_REDIS_PASSWORD=$(openssl rand -base64 32)
export NEW_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# Update .env.production
# Restart services with new credentials
```

6. **Implement Additional Security** (2-4 hours):
   - Enable audit logging
   - Add intrusion detection
   - Update firewall rules
   - Enable 2FA for all accounts
   - Review access controls

7. **Monitor and Document** (Ongoing):
   - Enhanced monitoring for 30 days
   - Document lessons learned
   - Update security procedures
   - Notify affected parties if required

**Total Expected Time**: 8-24 hours

### Application Failure Recovery

**Prerequisites**:
- Access to logs
- Previous working version identified

**Steps**:

1. **Check Service Status** (2 minutes):
```bash
docker compose -f docker-compose.prod.yml ps
```

2. **Review Logs** (5 minutes):
```bash
docker compose -f docker-compose.prod.yml logs --tail=100 api
docker compose -f docker-compose.prod.yml logs --tail=100 smtp
```

3. **Restart Affected Services** (5 minutes):
```bash
# Restart specific service
docker compose -f docker-compose.prod.yml restart api

# Or restart all
docker compose -f docker-compose.prod.yml restart
```

4. **If Restart Fails - Rollback** (10 minutes):
```bash
# Identify previous working version
# Check GHCR for tags

# Deploy previous version
export TAG=v1.0.0  # last known good version
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

5. **Verify Recovery** (5 minutes):
```bash
./scripts/verify-deployment.sh
```

**Total Expected Time**: 15-30 minutes

## Testing and Validation

### Monthly DR Testing

**Schedule**: First Sunday of each month

**Test Checklist**:
- [ ] Verify all backups completed successfully
- [ ] Test restore to staging environment
- [ ] Validate restored data
- [ ] Check backup file integrity
- [ ] Review and update contact list
- [ ] Test notification system

### Quarterly Full DR Drill

**Schedule**: End of each quarter

**Drill Scope**:
1. Simulate complete server failure
2. Rebuild from backups on fresh server
3. Time all recovery procedures
4. Document issues encountered
5. Update procedures based on findings
6. Review and update RTO/RPO

### Documentation Updates

**After Each Test**:
- Document actual vs. expected recovery times
- Note any issues or improvements
- Update procedures if needed
- Share findings with team

## Contacts and Escalation

### Primary Contacts

**On-Call Engineer** (24/7):
- Name: [Primary Contact]
- Phone: [Phone Number]
- Email: [Email]

**Backup Engineer**:
- Name: [Backup Contact]
- Phone: [Phone Number]
- Email: [Email]

**Infrastructure Manager**:
- Name: [Manager Name]
- Phone: [Phone Number]
- Email: [Email]

### Escalation Path

**Level 1** (0-30 minutes):
- On-call engineer attempts recovery
- Follows documented procedures

**Level 2** (30-60 minutes):
- Escalate to backup engineer
- Manager notified

**Level 3** (60+ minutes):
- Executive team notified
- Consider external assistance
- Prepare public communication

### External Contacts

**Hosting Provider**:
- Provider: [Provider Name]
- Support: [Support Number]
- Account ID: [Account ID]

**DNS Provider**:
- Provider: [Provider Name]
- Support: [Support Number]
- Account ID: [Account ID]

## Appendices

### Appendix A: Pre-Disaster Checklist

- [ ] Automated backups running daily
- [ ] Backups tested monthly
- [ ] Remote backups configured
- [ ] Documentation up to date
- [ ] Contact list current
- [ ] Monitoring and alerting active
- [ ] SSL certificates have >30 days validity
- [ ] Credentials stored securely
- [ ] DR plan reviewed quarterly

### Appendix B: Post-Recovery Checklist

- [ ] All services operational
- [ ] Data integrity verified
- [ ] Monitoring restored
- [ ] Backups resumed
- [ ] Incident documented
- [ ] Root cause identified
- [ ] Preventive measures implemented
- [ ] Team debriefed
- [ ] Stakeholders notified

### Appendix C: Critical Commands Reference

```bash
# Quick backup
./scripts/backup-db.sh --verbose

# Quick restore
./scripts/restore-db.sh backups/latest.sql.gz

# Health check
./scripts/verify-deployment.sh

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Full rebuild
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Appendix D: Backup Location Map

| Backup Type | Location | Retention |
|-------------|----------|-----------|
| Daily DB | `/srv/smtpy/backups/` | 30 days |
| Weekly Volumes | `/srv/smtpy/backups/volumes/` | 4 weeks |
| Remote (S3) | `s3://bucket/smtpy/backups/` | 90 days |
| Configuration | Git repository | Indefinite |
| SSL Certs | `/srv/smtpy/ssl/` + backup | 1 year |

---

**Document Control**:
- **Version**: 1.0
- **Last Updated**: October 26, 2025
- **Next Review**: January 26, 2026
- **Owner**: Infrastructure Team
- **Approved By**: [Name], [Date]
