#!/bin/bash
# SMTPy Database Maintenance Script
#
# This script performs routine database maintenance including:
# - VACUUM to reclaim storage
# - ANALYZE to update statistics
# - REINDEX to rebuild indexes
# - Check for bloat
# - Check for long-running queries
#
# Usage:
#   ./scripts/db-maintenance.sh [OPTIONS]
#
# Options:
#   --vacuum            Run VACUUM on all tables
#   --analyze           Run ANALYZE on all tables
#   --reindex           Rebuild all indexes
#   --full              Run VACUUM FULL (requires downtime)
#   --check-bloat       Check for table/index bloat
#   --check-queries     Check for long-running queries
#   --all               Run all maintenance tasks (except FULL)
#   --verbose           Show detailed output
#   --dry-run           Show what would be done

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
VACUUM=false
ANALYZE=false
REINDEX=false
VACUUM_FULL=false
CHECK_BLOAT=false
CHECK_QUERIES=false
RUN_ALL=false
VERBOSE=false
DRY_RUN=false
CONTAINER_NAME="smtpy-db-prod"

# Parse arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --vacuum            Run VACUUM on all tables"
    echo "  --analyze           Run ANALYZE on all tables"
    echo "  --reindex           Rebuild all indexes"
    echo "  --full              Run VACUUM FULL (requires downtime)"
    echo "  --check-bloat       Check for table/index bloat"
    echo "  --check-queries     Check for long-running queries"
    echo "  --all               Run all maintenance tasks"
    echo "  --verbose           Show detailed output"
    echo "  --dry-run           Show what would be done"
    echo "  --help, -h          Show this help message"
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --vacuum)
            VACUUM=true
            shift
            ;;
        --analyze)
            ANALYZE=true
            shift
            ;;
        --reindex)
            REINDEX=true
            shift
            ;;
        --full)
            VACUUM_FULL=true
            shift
            ;;
        --check-bloat)
            CHECK_BLOAT=true
            shift
            ;;
        --check-queries)
            CHECK_QUERIES=true
            shift
            ;;
        --all)
            RUN_ALL=true
            VACUUM=true
            ANALYZE=true
            CHECK_BLOAT=true
            CHECK_QUERIES=true
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
            echo "Maintenance tasks:"
            echo "  --vacuum            Reclaim storage and update free space map"
            echo "  --analyze           Update query planner statistics"
            echo "  --reindex           Rebuild indexes to remove bloat"
            echo "  --full              VACUUM FULL (locks tables, use with caution)"
            echo ""
            echo "Health checks:"
            echo "  --check-bloat       Identify bloated tables and indexes"
            echo "  --check-queries     Find long-running queries"
            echo ""
            echo "Other options:"
            echo "  --all               Run all standard maintenance (no FULL)"
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

run_sql() {
    local query="$1"
    local description="$2"

    if [ "$DRY_RUN" = true ]; then
        log_info "Would run: $description"
        verbose "SQL: $query"
    else
        verbose "Running: $description"
        docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "$query"
    fi
}

# Header
echo ""
echo "=========================================="
echo "  SMTPy Database Maintenance"
echo "=========================================="
echo ""

if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN MODE - No changes will be made"
    echo ""
fi

# Check prerequisites
log_info "Checking prerequisites..."

if ! docker info &> /dev/null; then
    log_error "Docker is not running"
    exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_error "Database container '${CONTAINER_NAME}' is not running"
    exit 1
fi

# Get database information
DB_NAME=$(docker exec "$CONTAINER_NAME" printenv POSTGRES_DB 2>/dev/null || echo "smtpy")
DB_USER=$(docker exec "$CONTAINER_NAME" printenv POSTGRES_USER 2>/dev/null || echo "postgres")
verbose "Database: $DB_NAME"
verbose "User: $DB_USER"

if ! docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" &> /dev/null; then
    log_error "Database is not ready"
    exit 1
fi

log_success "Database is ready"
echo ""

# Get database size before maintenance
BEFORE_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
log_info "Current database size: $BEFORE_SIZE"
echo ""

# Check for long-running queries
if [ "$CHECK_QUERIES" = true ]; then
    log_info "Checking for long-running queries..."

    LONG_QUERIES=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*)
        FROM pg_stat_activity
        WHERE state != 'idle'
        AND query_start < NOW() - INTERVAL '5 minutes'
        AND pid != pg_backend_pid();
    " 2>/dev/null | xargs)

    if [ "$LONG_QUERIES" -gt 0 ]; then
        log_warning "Found $LONG_QUERIES long-running query(ies)"

        if [ "$VERBOSE" = true ]; then
            docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
                SELECT
                    pid,
                    usename,
                    application_name,
                    state,
                    NOW() - query_start AS duration,
                    LEFT(query, 50) AS query
                FROM pg_stat_activity
                WHERE state != 'idle'
                AND query_start < NOW() - INTERVAL '5 minutes'
                AND pid != pg_backend_pid()
                ORDER BY query_start;
            "
        fi
    else
        log_success "No long-running queries found"
    fi

    echo ""
fi

# Check for table/index bloat
if [ "$CHECK_BLOAT" = true ]; then
    log_info "Checking for table and index bloat..."

    # Check table bloat
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT
            schemaname || '.' || tablename AS table_name,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            n_dead_tup AS dead_tuples,
            ROUND(100 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2) AS bloat_pct
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000
        ORDER BY n_dead_tup DESC
        LIMIT 10;
    " 2>&1 | head -n 20

    echo ""
fi

# Run VACUUM
if [ "$VACUUM" = true ]; then
    if [ "$VACUUM_FULL" = true ]; then
        log_warning "Running VACUUM FULL (this will lock tables)..."
        log_warning "API services should be stopped first!"

        if [ "$DRY_RUN" = false ]; then
            read -p "Continue with VACUUM FULL? (yes/no): " CONFIRM
            if [ "$CONFIRM" != "yes" ]; then
                log_info "VACUUM FULL cancelled"
                VACUUM_FULL=false
            fi
        fi

        if [ "$VACUUM_FULL" = true ]; then
            START_TIME=$(date +%s)

            if [ "$DRY_RUN" = false ]; then
                docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "VACUUM FULL;"
                END_TIME=$(date +%s)
                DURATION=$((END_TIME - START_TIME))
                log_success "VACUUM FULL completed (${DURATION}s)"
            else
                log_info "Would run: VACUUM FULL"
            fi
        fi
    else
        log_info "Running VACUUM..."
        START_TIME=$(date +%s)

        if [ "$DRY_RUN" = false ]; then
            docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "VACUUM;"
            END_TIME=$(date +%s)
            DURATION=$((END_TIME - START_TIME))
            log_success "VACUUM completed (${DURATION}s)"
        else
            log_info "Would run: VACUUM"
        fi
    fi

    echo ""
fi

# Run ANALYZE
if [ "$ANALYZE" = true ]; then
    log_info "Running ANALYZE..."
    START_TIME=$(date +%s)

    if [ "$DRY_RUN" = false ]; then
        docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;"
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        log_success "ANALYZE completed (${DURATION}s)"
    else
        log_info "Would run: ANALYZE"
    fi

    echo ""
fi

# Run REINDEX
if [ "$REINDEX" = true ]; then
    log_warning "Running REINDEX (this may take several minutes)..."
    START_TIME=$(date +%s)

    if [ "$DRY_RUN" = false ]; then
        docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "REINDEX DATABASE $DB_NAME;"
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        log_success "REINDEX completed (${DURATION}s)"
    else
        log_info "Would run: REINDEX DATABASE $DB_NAME"
    fi

    echo ""
fi

# Get database size after maintenance
if [ "$DRY_RUN" = false ] && [ "$VACUUM" = true ]; then
    AFTER_SIZE=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
    log_info "Database size after maintenance: $AFTER_SIZE"
    echo ""
fi

# Display connection statistics
log_info "Connection statistics:"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT
        state,
        COUNT(*) as count
    FROM pg_stat_activity
    WHERE datname = '$DB_NAME'
    GROUP BY state
    ORDER BY count DESC;
"

echo ""

# Display table statistics
if [ "$VERBOSE" = true ]; then
    log_info "Top 10 largest tables:"
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT
            schemaname || '.' || tablename AS table_name,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10;
    "
    echo ""
fi

# Summary
log_info "Maintenance Summary:"
echo ""

TASKS_RUN=0
if [ "$VACUUM" = true ]; then
    echo "  ✓ VACUUM completed"
    ((TASKS_RUN++))
fi
if [ "$ANALYZE" = true ]; then
    echo "  ✓ ANALYZE completed"
    ((TASKS_RUN++))
fi
if [ "$REINDEX" = true ]; then
    echo "  ✓ REINDEX completed"
    ((TASKS_RUN++))
fi
if [ "$CHECK_BLOAT" = true ]; then
    echo "  ✓ Bloat check completed"
    ((TASKS_RUN++))
fi
if [ "$CHECK_QUERIES" = true ]; then
    echo "  ✓ Query check completed"
    ((TASKS_RUN++))
fi

if [ $TASKS_RUN -eq 0 ]; then
    echo "  No maintenance tasks were run"
    echo "  Use --help to see available options"
fi

echo ""
log_success "Maintenance completed at $(date)"
echo ""

# Recommendations
if [ "$TASKS_RUN" -gt 0 ]; then
    log_info "Recommendations:"
    echo "  • Run VACUUM ANALYZE weekly"
    echo "  • Check for bloat monthly"
    echo "  • Monitor long-running queries daily"
    echo "  • Consider REINDEX if bloat is high"
    echo "  • Schedule VACUUM FULL during maintenance windows"
    echo ""
fi

exit 0
