#!/bin/bash
# SMTPy Database Restore Script
#
# This script restores a PostgreSQL database from a backup file
# with safety checks and optional pre-restore backup.
#
# Usage:
#   ./scripts/restore-db.sh BACKUP_FILE [OPTIONS]
#
# Options:
#   --no-backup         Skip creating backup before restore
#   --force             Skip confirmation prompts
#   --verbose           Show detailed output
#   --dry-run           Show what would be done without executing

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
PRE_RESTORE_BACKUP=true
FORCE=false
VERBOSE=false
DRY_RUN=false
CONTAINER_NAME="smtpy-db"
COMPOSE_FILE="docker-compose.prod.yml"

# Parse arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 BACKUP_FILE [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-backup         Skip creating backup before restore"
    echo "  --force             Skip confirmation prompts"
    echo "  --verbose           Show detailed output"
    echo "  --dry-run           Show what would be done"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 backups/smtpy_20250126_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-backup)
            PRE_RESTORE_BACKUP=false
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 BACKUP_FILE [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-backup         Skip creating backup before restore"
            echo "  --force             Skip confirmation prompts"
            echo "  --verbose           Show detailed output"
            echo "  --dry-run           Show what would be done"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${NC}  $1${NC}"
    fi
}

# Header
echo ""
echo "=========================================="
echo "  SMTPy Database Restore"
echo "=========================================="
echo ""
log_warning "WARNING: This will REPLACE the current database!"
echo ""

if [ "$DRY_RUN" = true ]; then
    log_info "DRY RUN MODE - No changes will be made"
    echo ""
fi

# Check if backup file exists
log_info "Checking backup file..."

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
BACKUP_DATE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$BACKUP_FILE" 2>/dev/null || stat -c "%y" "$BACKUP_FILE" 2>/dev/null | cut -d'.' -f1)
log_success "Backup file found"
verbose "File: $BACKUP_FILE"
verbose "Size: $BACKUP_SIZE"
verbose "Date: $BACKUP_DATE"

# Detect if backup is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    COMPRESSED=true
    log_info "Backup is compressed (gzip)"

    # Verify gzip integrity
    if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
        log_error "Backup file is corrupted (failed gzip test)"
        exit 1
    fi
    log_success "Backup integrity verified"
else
    COMPRESSED=false
    verbose "Backup is uncompressed"
fi

# Check prerequisites
log_info "Checking prerequisites..."

# Check if Docker is running
if ! docker info &> /dev/null; then
    log_error "Docker is not running"
    exit 1
fi
verbose "Docker is running"

# Check if database container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_error "Database container '${CONTAINER_NAME}' not found"
    exit 1
fi
verbose "Database container found"

# Check if database container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_error "Database container '${CONTAINER_NAME}' is not running"
    exit 1
fi
log_success "Database container is running"

# Get database information
log_info "Retrieving database information..."
DB_NAME=$(docker exec "$CONTAINER_NAME" printenv POSTGRES_DB 2>/dev/null || echo "smtpy")
DB_USER=$(docker exec "$CONTAINER_NAME" printenv POSTGRES_USER 2>/dev/null || echo "postgres")
verbose "Database: $DB_NAME"
verbose "User: $DB_USER"

# Check database connectivity
if ! docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" &> /dev/null; then
    log_error "Database is not ready"
    exit 1
fi
log_success "Database is ready"

# Get current database size
CURRENT_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
verbose "Current database size: $CURRENT_SIZE"

# Create pre-restore backup
if [ "$PRE_RESTORE_BACKUP" = true ]; then
    log_info "Creating pre-restore backup..."

    PRE_RESTORE_FILE="/srv/smtpy/backups/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"

    if [ "$DRY_RUN" = false ]; then
        if ./scripts/backup-db.sh --verbose 2>&1 | tail -n 5; then
            log_success "Pre-restore backup created"
        else
            log_error "Failed to create pre-restore backup"
            exit 1
        fi
    else
        log_info "Would create pre-restore backup"
    fi
else
    log_warning "Skipping pre-restore backup (--no-backup specified)"
fi

# Confirmation prompt
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    echo ""
    log_warning "You are about to:"
    echo "  1. Stop API and SMTP services"
    echo "  2. Drop the current database '$DB_NAME'"
    echo "  3. Restore from: $(basename "$BACKUP_FILE")"
    echo "  4. Restart all services"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log_info "Restore cancelled by user"
        exit 0
    fi
    echo ""
fi

# Stop dependent services
log_info "Stopping API and SMTP services..."

if [ "$DRY_RUN" = false ]; then
    docker compose -f "$COMPOSE_FILE" stop api smtp 2>&1 | grep -v "^$" || true
    sleep 2
    log_success "Services stopped"
else
    log_info "Would stop API and SMTP services"
fi

# Drop and recreate database
log_info "Dropping and recreating database..."

if [ "$DRY_RUN" = false ]; then
    # Drop all connections
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
    " &>/dev/null || true

    # Drop database
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>&1 | grep -v "^$" || true

    # Create database
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>&1 | grep -v "^$" || true

    log_success "Database recreated"
else
    log_info "Would drop and recreate database"
fi

# Restore backup
log_info "Restoring backup (this may take several minutes)..."

if [ "$DRY_RUN" = false ]; then
    START_TIME=$(date +%s)

    if [ "$COMPRESSED" = true ]; then
        gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" 2>&1 | grep -i "error" || true
    else
        cat "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" 2>&1 | grep -i "error" || true
    fi

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    log_success "Database restored (${DURATION}s)"
else
    log_info "Would restore backup from: $BACKUP_FILE"
fi

# Verify restoration
log_info "Verifying restoration..."

if [ "$DRY_RUN" = false ]; then
    # Check if database exists
    DB_EXISTS=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | xargs)

    if [ "$DB_EXISTS" != "1" ]; then
        log_error "Database was not created properly"
        exit 1
    fi

    # Check table count
    TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)

    if [ "$TABLE_COUNT" -eq 0 ]; then
        log_error "No tables found in restored database"
        exit 1
    fi

    RESTORED_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)

    log_success "Database verification passed"
    verbose "Tables: $TABLE_COUNT"
    verbose "Size: $RESTORED_SIZE"
else
    log_info "Would verify restored database"
fi

# Restart services
log_info "Restarting all services..."

if [ "$DRY_RUN" = false ]; then
    docker compose -f "$COMPOSE_FILE" start smtp api 2>&1 | grep -v "^$" || true
    sleep 5

    # Wait for API to be healthy
    log_info "Waiting for services to be ready..."
    RETRY=0
    MAX_RETRIES=30

    while [ $RETRY -lt $MAX_RETRIES ]; do
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Services are ready"
            break
        fi
        sleep 2
        ((RETRY++))
    done

    if [ $RETRY -eq $MAX_RETRIES ]; then
        log_warning "Services did not become healthy within timeout"
        log_warning "Check logs: docker compose -f $COMPOSE_FILE logs api"
    fi
else
    log_info "Would restart services and wait for health checks"
fi

# Summary
echo ""
log_info "Restore Summary:"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "  Backup file:     $(basename "$BACKUP_FILE")"
    echo "  Backup size:     $BACKUP_SIZE"
    echo "  Backup date:     $BACKUP_DATE"
    echo "  Tables restored: $TABLE_COUNT"
    echo "  Database size:   $RESTORED_SIZE"
    echo "  Duration:        ${DURATION}s"

    if [ "$PRE_RESTORE_BACKUP" = true ]; then
        echo "  Pre-restore backup created for rollback if needed"
    fi
else
    echo "  DRY RUN - No restore performed"
fi

echo ""
log_success "Restore completed successfully at $(date)"
echo ""

# Recommendations
log_info "Post-restore recommendations:"
echo "  1. Test application functionality"
echo "  2. Check API logs: docker compose -f $COMPOSE_FILE logs api"
echo "  3. Verify data integrity"
echo "  4. Monitor for errors"
echo ""

# Exit successfully
exit 0
