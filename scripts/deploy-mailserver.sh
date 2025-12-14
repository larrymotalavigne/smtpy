#!/bin/bash
# Deploy Docker Mailserver for SMTPy
# This script sets up and deploys the mailserver service

set -e  # Exit on error

echo "========================================="
echo "SMTPy Mailserver Deployment Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "ℹ $1"; }

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root or with sudo"
    exit 1
fi

# Check if .env.production exists
if [ ! -f .env.production ]; then
    print_error ".env.production file not found"
    print_info "Please create .env.production from .env.production.template"
    exit 1
fi

print_info "Checking prerequisites..."

# Create required Docker networks if they don't exist
print_info "Creating required Docker networks..."

if ! docker network inspect smtpy-network >/dev/null 2>&1; then
    docker network create smtpy-network
    print_success "Created smtpy-network"
else
    print_info "Network smtpy-network already exists"
fi

if ! docker network inspect mailserver-network >/dev/null 2>&1; then
    docker network create mailserver-network
    print_success "Created mailserver-network"
else
    print_info "Network mailserver-network already exists"
fi

if ! docker network inspect proxy-network >/dev/null 2>&1; then
    docker network create proxy-network
    print_success "Created proxy-network"
else
    print_info "Network proxy-network already exists"
fi

# Create required Docker volumes
print_info "Creating required Docker volumes..."

VOLUMES=(
    "infra_mailserver_data"
    "infra_mailserver_state"
    "infra_mailserver_logs"
    "infra_mailserver_config"
    "infra_npm_letsencrypt"
)

for volume in "${VOLUMES[@]}"; do
    if ! docker volume inspect "$volume" >/dev/null 2>&1; then
        docker volume create "$volume"
        print_success "Created volume $volume"
    else
        print_info "Volume $volume already exists"
    fi
done

print_success "All prerequisites are ready!"
echo ""

# Deploy the mailserver
print_info "Deploying mailserver service..."
echo ""

# Check if docker-compose or docker compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Pull the latest mailserver image
print_info "Pulling latest mailserver image..."
$COMPOSE_CMD -f docker-compose.prod.yml pull mailserver || print_warning "Failed to pull image, will use existing"

# Start only the mailserver service (and its dependencies)
print_info "Starting mailserver service..."
$COMPOSE_CMD -f docker-compose.prod.yml up -d mailserver

echo ""
print_success "Mailserver deployment initiated!"
echo ""

# Wait for container to start
print_info "Waiting for mailserver container to start..."
sleep 5

# Check if mailserver is running
if docker ps | grep -q mailserver; then
    print_success "Mailserver container is running"

    # Show container status
    echo ""
    print_info "Container status:"
    docker ps | grep mailserver

    echo ""
    print_info "Checking mailserver health (this may take up to 2 minutes)..."
    echo ""

    # Wait for health check to pass (up to 2 minutes)
    COUNTER=0
    MAX_WAIT=120
    while [ $COUNTER -lt $MAX_WAIT ]; do
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' mailserver 2>/dev/null || echo "unknown")

        if [ "$HEALTH_STATUS" = "healthy" ]; then
            print_success "Mailserver is healthy!"
            break
        elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
            print_error "Mailserver is unhealthy"
            print_info "Check logs with: docker logs mailserver"
            break
        else
            echo -n "."
            sleep 5
            COUNTER=$((COUNTER + 5))
        fi
    done

    echo ""
    echo ""
    print_info "Mailserver logs (last 20 lines):"
    echo "---------------------------------------"
    docker logs mailserver --tail 20
    echo "---------------------------------------"

else
    print_error "Mailserver container failed to start"
    print_info "Checking logs..."
    $COMPOSE_CMD -f docker-compose.prod.yml logs mailserver
    exit 1
fi

echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "1. Create email accounts:"
echo "   docker exec mailserver setup email add user@atomdev.fr"
echo ""
echo "2. Configure DKIM:"
echo "   docker exec mailserver setup config dkim"
echo ""
echo "3. View DKIM public key for DNS:"
echo "   docker exec mailserver cat /tmp/docker-mailserver/opendkim/keys/atomdev.fr/mail.txt"
echo ""
echo "4. Set up DNS records (MX, SPF, DKIM, DMARC)"
echo "   See MAILSERVER_CONFIGURATION.md for details"
echo ""
echo "5. Monitor logs:"
echo "   docker logs -f mailserver"
echo ""
echo "For more information, see MAILSERVER_CONFIGURATION.md"
echo ""
print_success "Deployment complete!"
