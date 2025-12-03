#!/bin/bash
# SMTPy Database Backup Script
#
# This script creates automated backups of the PostgreSQL database
# with rotation, compression, and optional remote storage.
#
# Usage:
#   ./scripts/backup-db.sh [OPTIONS]
#
# Options:
#   --retention DAYS    Number of days to keep backups (default: 30)
#   --remote            Upload to remote storage (S3, if configured)
#   --compress          Compress backup with gzip (default: true)
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
BACKUP_DIR="/srv/smtpy/backups"
RETENTION_DAYS=30
COMPRESS=true
REMOTE=false
VERBOSE=false
DRY_RUN=false
COMPOSE_FILE="docker-compose.prod.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="smtpy-db"

# Remote storage configuration (set these via environment variables)
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
S3_PREFIX="${BACKUP_S3_PREFIX:-smtpy/backups}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --remote)
            REMOTE=true
            shift
            ;;
        --no-compress)
            COMPRESS=false
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
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --retention DAYS    Number of days to keep backups (default: 30)"
            echo "  --remote            Upload to remote storage (S3)"
            echo "  --no-compress       Don't compress backup"
            echo "  --verbose           Show detailed output"
            echo "  --dry-run           Show what would be done"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  BACKUP_S3_BUCKET    S3 bucket for remote backups"
            echo "  BACKUP_S3_PREFIX    S3 prefix/path (default: smtpy/backups)"
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
echo "  SMTPy Database Backup"
echo "=========================================="
echo ""
log_info "Backup started at $(date)"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN MODE - No changes will be made"
fi

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

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$BACKUP_DIR"
        log_success "Created backup directory: $BACKUP_DIR"
    else
        log_info "Would create backup directory: $BACKUP_DIR"
    fi
else
    verbose "Backup directory exists: $BACKUP_DIR"
fi

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

# Calculate backup size estimate
log_info "Estimating backup size..."
DB_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
verbose "Database size: $DB_SIZE"

# Generate backup filename
if [ "$COMPRESS" = true ]; then
    BACKUP_FILE="${BACKUP_DIR}/smtpy_${TIMESTAMP}.sql.gz"
    BACKUP_TYPE="compressed"
else
    BACKUP_FILE="${BACKUP_DIR}/smtpy_${TIMESTAMP}.sql"
    BACKUP_TYPE="uncompressed"
fi

log_info "Creating $BACKUP_TYPE backup..."
verbose "Backup file: $BACKUP_FILE"

# Perform backup
if [ "$DRY_RUN" = false ]; then
    START_TIME=$(date +%s)

    if [ "$COMPRESS" = true ]; then
        docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
    else
        docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
    fi

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Check if backup was created successfully
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file was not created"
        exit 1
    fi

    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_success "Backup created successfully (${BACKUP_SIZE}, ${DURATION}s)"
    verbose "File: $BACKUP_FILE"
else
    log_info "Would create backup: $BACKUP_FILE"
fi

# Verify backup integrity
if [ "$DRY_RUN" = false ] && [ -f "$BACKUP_FILE" ]; then
    log_info "Verifying backup integrity..."

    if [ "$COMPRESS" = true ]; then
        if gzip -t "$BACKUP_FILE" 2>/dev/null; then
            log_success "Backup integrity verified"
        else
            log_error "Backup file is corrupted"
            exit 1
        fi
    else
        if [ -s "$BACKUP_FILE" ]; then
            log_success "Backup file is not empty"
        else
            log_error "Backup file is empty"
            exit 1
        fi
    fi
fi

# Upload to remote storage
if [ "$REMOTE" = true ]; then
    log_info "Uploading to remote storage..."

    if [ -z "$S3_BUCKET" ]; then
        log_error "S3_BUCKET not configured. Set BACKUP_S3_BUCKET environment variable."
        exit 1
    fi

    if [ "$DRY_RUN" = false ]; then
        if command -v aws &> /dev/null; then
            S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/$(basename "$BACKUP_FILE")"

            if aws s3 cp "$BACKUP_FILE" "$S3_PATH"; then
                log_success "Uploaded to S3: $S3_PATH"
            else
                log_error "Failed to upload to S3"
                exit 1
            fi
        else
            log_error "AWS CLI not installed. Cannot upload to S3."
            exit 1
        fi
    else
        log_info "Would upload to S3: s3://${S3_BUCKET}/${S3_PREFIX}/$(basename "$BACKUP_FILE")"
    fi
fi

# Cleanup old backups
log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."

if [ "$DRY_RUN" = false ]; then
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "smtpy_*.sql*" -mtime +${RETENTION_DAYS} 2>/dev/null || true)

    if [ -n "$OLD_BACKUPS" ]; then
        OLD_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
        echo "$OLD_BACKUPS" | while read -r old_backup; do
            if [ -f "$old_backup" ]; then
                rm "$old_backup"
                verbose "Deleted: $(basename "$old_backup")"
            fi
        done
        log_success "Deleted $OLD_COUNT old backup(s)"
    else
        verbose "No old backups to delete"
    fi
else
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "smtpy_*.sql*" -mtime +${RETENTION_DAYS} 2>/dev/null || true)
    if [ -n "$OLD_BACKUPS" ]; then
        OLD_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
        log_info "Would delete $OLD_COUNT old backup(s)"
    fi
fi

# Display backup summary
echo ""
log_info "Backup Summary:"
echo ""

if [ "$DRY_RUN" = false ]; then
    CURRENT_BACKUPS=$(find "$BACKUP_DIR" -name "smtpy_*.sql*" 2>/dev/null | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

    echo "  Backup file:     $(basename "$BACKUP_FILE")"
    echo "  Size:            $BACKUP_SIZE"
    echo "  Location:        $BACKUP_DIR"
    echo "  Total backups:   $CURRENT_BACKUPS"
    echo "  Total size:      $TOTAL_SIZE"
    echo "  Retention:       ${RETENTION_DAYS} days"

    if [ "$REMOTE" = true ] && [ -n "$S3_BUCKET" ]; then
        echo "  Remote storage:  s3://${S3_BUCKET}/${S3_PREFIX}/"
    fi
else
    echo "  DRY RUN - No backups created"
fi

echo ""
log_success "Backup completed successfully at $(date)"
echo ""

# Exit successfully
exit 0
