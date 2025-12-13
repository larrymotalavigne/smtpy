#!/bin/bash
# SMTPy Production Deployment Verification Script
#
# This script verifies that all services are running correctly
# and performs basic health checks on the deployment.
#
# Usage:
#   ./scripts/verify-deployment.sh
#   ./scripts/verify-deployment.sh --verbose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
VERBOSE=false
ERRORS=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v    Show detailed output"
            echo "  --help, -h       Show this help message"
            exit 0
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
    ((ERRORS++))
}

verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${NC}  $1${NC}"
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

# Header
echo ""
echo "=========================================="
echo "  SMTPy Deployment Verification"
echo "=========================================="
echo ""

# Step 1: Check prerequisites
log_info "Step 1: Checking prerequisites..."

if check_command docker; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    verbose "Docker version: $DOCKER_VERSION"
    log_success "Docker is installed"
else
    exit 1
fi

if check_command docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
    verbose "Docker Compose version: $COMPOSE_VERSION"
    log_success "Docker Compose is installed"
else
    log_error "Docker Compose V2 is not installed"
    exit 1
fi

echo ""

# Step 2: Check environment file
log_info "Step 2: Checking environment configuration..."

if [ ! -f ".env.production" ]; then
    log_error ".env.production file not found"
    log_warning "Copy .env.production.template to .env.production and configure it"
    exit 1
else
    log_success ".env.production exists"
fi

# Check for unconfigured values
UNCONFIGURED=$(grep -c "CHANGE_ME" .env.production 2>/dev/null || true)
if [ "$UNCONFIGURED" -gt 0 ]; then
    log_error "Found $UNCONFIGURED unconfigured values (CHANGE_ME) in .env.production"
    if [ "$VERBOSE" = true ]; then
        grep "CHANGE_ME" .env.production
    fi
else
    log_success "All required values configured"
fi

# Check for required variables
REQUIRED_VARS=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY" "STRIPE_API_KEY" "STRIPE_WEBHOOK_SECRET")
for var in "${REQUIRED_VARS[@]}"; do
    if grep -q "^${var}=" .env.production; then
        VALUE=$(grep "^${var}=" .env.production | cut -d'=' -f2)
        if [ -n "$VALUE" ] && [ "$VALUE" != "CHANGE_ME" ]; then
            log_success "$var is set"
            if [ "$VERBOSE" = true ] && [ "$var" != "SECRET_KEY" ] && [ "$var" != "STRIPE_API_KEY" ]; then
                verbose "$var=${VALUE:0:10}..."
            fi
        else
            log_error "$var is not set or is still CHANGE_ME"
        fi
    else
        log_error "$var is missing from .env.production"
    fi
done

echo ""

# Step 3: Check Docker Compose configuration
log_info "Step 3: Validating Docker Compose configuration..."

if docker compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
    log_success "Docker Compose configuration is valid"
else
    log_error "Docker Compose configuration has errors"
    if [ "$VERBOSE" = true ]; then
        docker compose -f "$COMPOSE_FILE" config
    fi
fi

echo ""

# Step 4: Check if services are running
log_info "Step 4: Checking service status..."

SERVICES=("db" "redis" "smtp-receiver" "api" "front" "mailserver")

for service in "${SERVICES[@]}"; do
    if docker compose -f "$COMPOSE_FILE" ps "$service" 2>/dev/null | grep -q "Up"; then
        log_success "$service is running"

        # Check if container is healthy (if health check is defined)
        CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null)
        if [ -n "$CONTAINER_ID" ]; then
            HEALTH_STATUS=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' "$CONTAINER_ID" 2>/dev/null || echo "unknown")
            if [ "$HEALTH_STATUS" = "healthy" ]; then
                verbose "Health: $HEALTH_STATUS"
            elif [ "$HEALTH_STATUS" = "N/A" ]; then
                verbose "Health: No health check defined"
            else
                log_warning "$service health status: $HEALTH_STATUS"
            fi
        fi
    else
        log_error "$service is not running"
    fi
done

echo ""

# Step 5: Test service endpoints
log_info "Step 5: Testing service endpoints..."

# Test API health endpoint
if curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/health > /tmp/api_status 2>/dev/null; then
    STATUS_CODE=$(cat /tmp/api_status)
    if [ "$STATUS_CODE" = "200" ]; then
        log_success "API health check passed (HTTP $STATUS_CODE)"
        if [ "$VERBOSE" = true ]; then
            API_RESPONSE=$(curl -s http://localhost:8000/health)
            verbose "Response: $API_RESPONSE"
        fi
    else
        log_error "API health check failed (HTTP $STATUS_CODE)"
    fi
else
    log_error "Cannot connect to API health endpoint"
fi

# Test Frontend
if curl -sf -o /dev/null -w "%{http_code}" http://localhost:80 > /tmp/frontend_status 2>/dev/null; then
    STATUS_CODE=$(cat /tmp/frontend_status)
    if [ "$STATUS_CODE" = "200" ]; then
        log_success "Frontend accessible (HTTP $STATUS_CODE)"
    else
        log_warning "Frontend returned HTTP $STATUS_CODE"
    fi
else
    log_error "Cannot connect to Frontend"
fi

# Test SMTP Receiver (SMTPy)
if timeout 2 bash -c "echo > /dev/tcp/localhost/2525" 2>/dev/null; then
    log_success "SMTP Receiver accepting connections on port 2525"
else
    log_error "Cannot connect to SMTP Receiver on port 2525"
fi

# Test Mailserver SMTP ports
if timeout 2 bash -c "echo > /dev/tcp/localhost/25" 2>/dev/null; then
    log_success "Mailserver SMTP port 25 accepting connections"
else
    log_warning "Cannot connect to Mailserver SMTP port 25 (may require root privileges)"
fi

if timeout 2 bash -c "echo > /dev/tcp/localhost/587" 2>/dev/null; then
    log_success "Mailserver SMTP submission port 587 accepting connections"
else
    log_error "Cannot connect to Mailserver SMTP port 587"
fi

# Test Mailserver IMAP ports
if timeout 2 bash -c "echo > /dev/tcp/localhost/143" 2>/dev/null; then
    log_success "Mailserver IMAP port 143 accepting connections"
else
    log_warning "Cannot connect to Mailserver IMAP port 143"
fi

if timeout 2 bash -c "echo > /dev/tcp/localhost/993" 2>/dev/null; then
    log_success "Mailserver IMAPS port 993 accepting connections"
else
    log_warning "Cannot connect to Mailserver IMAPS port 993"
fi

# Test PostgreSQL
if docker exec smtpy-db pg_isready -U postgres &> /dev/null; then
    log_success "PostgreSQL is ready"
else
    log_error "PostgreSQL is not ready"
fi

# Test Redis
if docker exec smtpy-redis redis-cli --raw incr ping &> /dev/null; then
    log_success "Redis is responding"
else
    log_error "Redis is not responding"
fi

# Test Mailserver health
if docker exec mailserver bash /usr/local/bin/healthcheck.sh &> /dev/null; then
    log_success "Mailserver health check passed"
    if [ "$VERBOSE" = true ]; then
        verbose "Running detailed mailserver health check..."
        docker exec mailserver bash /usr/local/bin/healthcheck.sh
    fi
else
    log_error "Mailserver health check failed"
    if [ "$VERBOSE" = true ]; then
        verbose "Mailserver health check output:"
        docker exec mailserver bash /usr/local/bin/healthcheck.sh || true
    fi
fi

# Cleanup
rm -f /tmp/api_status /tmp/frontend_status

echo ""

# Step 6: Check resource usage
log_info "Step 6: Checking resource usage..."

TOTAL_CPU=0
TOTAL_MEM=0

for service in "${SERVICES[@]}"; do
    CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null)
    if [ -n "$CONTAINER_ID" ]; then
        STATS=$(docker stats "$CONTAINER_ID" --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" 2>/dev/null)
        if [ -n "$STATS" ]; then
            CPU=$(echo "$STATS" | cut -d',' -f1 | sed 's/%//')
            MEM=$(echo "$STATS" | cut -d',' -f2 | awk '{print $1}')

            if [ "$VERBOSE" = true ]; then
                verbose "$service: CPU=$CPU%, Memory=$MEM"
            fi

            # Add to totals (simple approximation)
            TOTAL_CPU=$(echo "$TOTAL_CPU + $CPU" | bc 2>/dev/null || echo "$TOTAL_CPU")
        fi
    fi
done

if [ "$VERBOSE" = true ]; then
    verbose "Total CPU usage (approximate): ${TOTAL_CPU}%"
fi

log_success "Resource usage check complete"

echo ""

# Step 7: Check logs for errors
log_info "Step 7: Checking recent logs for errors..."

ERROR_COUNT=0
for service in "${SERVICES[@]}"; do
    CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null)
    if [ -n "$CONTAINER_ID" ]; then
        RECENT_ERRORS=$(docker logs "$CONTAINER_ID" --tail 100 2>&1 | grep -i "error" | grep -v "0 error" | wc -l)
        if [ "$RECENT_ERRORS" -gt 0 ]; then
            log_warning "$service has $RECENT_ERRORS error messages in recent logs"
            if [ "$VERBOSE" = true ]; then
                verbose "Recent errors:"
                docker logs "$CONTAINER_ID" --tail 100 2>&1 | grep -i "error" | grep -v "0 error" | head -5
            fi
            ((ERROR_COUNT += RECENT_ERRORS))
        fi
    fi
done

if [ "$ERROR_COUNT" -eq 0 ]; then
    log_success "No recent errors found in logs"
fi

echo ""

# Step 8: Check database connectivity
log_info "Step 8: Testing database operations..."

if docker exec smtpy-db psql -U postgres -d smtpy -c "SELECT 1;" &> /dev/null; then
    log_success "Database query successful"

    # Check for migrations
    if docker exec smtpy-api-prod alembic current &> /dev/null; then
        CURRENT_REV=$(docker exec smtpy-api-prod alembic current 2>/dev/null | grep -o '[a-f0-9]\{12\}' | head -1)
        if [ -n "$CURRENT_REV" ]; then
            log_success "Database migrations applied (current: $CURRENT_REV)"
        else
            log_warning "Could not determine migration status"
        fi
    else
        log_warning "Could not check migration status"
    fi
else
    log_error "Database query failed"
fi

echo ""

# Step 9: Security checks
log_info "Step 9: Running security checks..."

# Check if DEBUG is disabled
if grep -q "^DEBUG=false" .env.production; then
    log_success "DEBUG mode is disabled"
else
    log_error "DEBUG mode should be set to 'false' in production"
fi

# Check if using production Stripe keys
if grep -q "^STRIPE_API_KEY=sk_live" .env.production; then
    log_success "Using production Stripe API key"
elif grep -q "^STRIPE_API_KEY=sk_test" .env.production; then
    log_error "Using test Stripe API key in production environment"
else
    log_warning "Could not determine Stripe API key type"
fi

# Check CORS configuration
CORS_ORIGINS=$(grep "^CORS_ORIGINS=" .env.production | cut -d'=' -f2)
if [[ "$CORS_ORIGINS" == *"localhost"* ]] || [[ "$CORS_ORIGINS" == *"127.0.0.1"* ]]; then
    log_warning "CORS_ORIGINS includes localhost - this should be removed in production"
else
    log_success "CORS_ORIGINS properly configured"
    if [ "$VERBOSE" = true ]; then
        verbose "CORS_ORIGINS=$CORS_ORIGINS"
    fi
fi

# Check if containers are running as non-root
API_USER=$(docker exec smtpy-api-prod whoami 2>/dev/null || echo "unknown")
if [ "$API_USER" != "root" ]; then
    log_success "API container running as non-root user ($API_USER)"
else
    log_warning "API container running as root user"
fi

echo ""

# Summary
echo "=========================================="
echo "  Verification Summary"
echo "=========================================="
echo ""

if [ "$ERRORS" -eq 0 ]; then
    log_success "All checks passed! Deployment is healthy."
    echo ""
    echo "Next steps:"
    echo "  1. Monitor logs: docker compose -f $COMPOSE_FILE logs -f"
    echo "  2. Test application functionality"
    echo "  3. Set up monitoring and alerting"
    echo "  4. Configure automated backups"
    echo ""
    exit 0
else
    log_error "$ERRORS error(s) found during verification"
    echo ""
    echo "Please review the errors above and fix them before proceeding."
    echo ""
    echo "For detailed output, run with --verbose flag:"
    echo "  ./scripts/verify-deployment.sh --verbose"
    echo ""
    echo "For help, see docs/DEPLOYMENT_GUIDE.md"
    echo ""
    exit 1
fi
