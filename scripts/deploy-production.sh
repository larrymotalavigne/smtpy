#!/bin/bash
# Production Deployment Script for SMTPy
# This script deploys the SMTPy application to production with proper container orchestration

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SMTPy Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running from correct directory
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: $COMPOSE_FILE not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Set required environment variables
export GHCR_OWNER="${GHCR_OWNER:-larrymotalavigne}"
export TAG="${TAG:-latest}"
export DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"

echo -e "${GREEN}Configuration:${NC}"
echo "  Registry: $DOCKER_REGISTRY"
echo "  Owner: $GHCR_OWNER"
echo "  Tag: $TAG"
echo ""

# Compose env-file option (only if file exists)
COMPOSE_ENV_FILE_OPT=""
if [ -f "$ENV_FILE" ]; then
    COMPOSE_ENV_FILE_OPT="--env-file $ENV_FILE"
    echo -e "${GREEN}✓ Using environment file: $ENV_FILE${NC}"
else
    echo -e "${YELLOW}⚠ Warning: $ENV_FILE not found. Using environment variables.${NC}"
fi
echo ""

# Mailserver Prerequisites: Create required networks and volumes
echo -e "${BLUE}Checking mailserver prerequisites...${NC}"

# Create required Docker networks if they don't exist
NETWORKS=("smtpy-network" "mailserver-network" "proxy-network")
for network in "${NETWORKS[@]}"; do
    if ! docker network inspect "$network" >/dev/null 2>&1; then
        docker network create "$network"
        echo -e "${GREEN}✓ Created network: $network${NC}"
    fi
done

# Create required Docker volumes for mailserver
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
        echo -e "${GREEN}✓ Created volume: $volume${NC}"
    fi
done

echo -e "${GREEN}✓ Prerequisites ready${NC}"
echo ""

# Step 1: Login to registry (if credentials available)
if [ -n "$GITHUB_PAT" ] || [ -n "$CR_PAT" ]; then
    echo -e "${BLUE}[1/8]${NC} Logging in to GitHub Container Registry..."
    PAT="${GITHUB_PAT:-$CR_PAT}"
    echo "$PAT" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin
    echo -e "${GREEN}✓ Login successful${NC}"
else
    echo -e "${YELLOW}⚠ Skipping login (GITHUB_PAT or CR_PAT not set)${NC}"
    echo "  If you encounter authentication errors, set GITHUB_PAT or CR_PAT environment variable"
fi
echo ""

# Step 2: Pull latest images
echo -e "${BLUE}[2/8]${NC} Pulling latest images..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT pull
echo -e "${GREEN}✓ Images pulled${NC}"
echo ""

# Step 3: Stop existing containers
echo -e "${BLUE}[3/8]${NC} Stopping existing containers..."

# Force stop and remove any existing SMTPy containers (even if not managed by current compose project)
echo "  Force stopping any existing SMTPy containers..."
docker ps -a --filter "name=smtpy-" --format "{{.Names}}" | xargs -r docker stop || true
docker ps -a --filter "name=smtpy-" --format "{{.Names}}" | xargs -r docker rm || true

# Stop and remove containers managed by compose
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT down --remove-orphans || true
echo -e "${GREEN}✓ Old containers stopped${NC}"
echo ""

# Step 4: Start database services
echo -e "${BLUE}[4/8]${NC} Starting database and Redis..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps db redis
echo -e "${GREEN}✓ Database services started${NC}"
echo ""

# Step 5: Wait for database
echo -e "${BLUE}[5/8]${NC} Waiting for database to be ready..."
sleep 10
MAX_RETRIES=30
RETRY_COUNT=0
until docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT exec -T db pg_isready -U postgres > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}✗ Database failed to become ready after $MAX_RETRIES attempts${NC}"
        exit 1
    fi
    echo "  Waiting for database... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
echo -e "${GREEN}✓ Database is ready${NC}"
echo ""

# Step 6: Start mailserver
echo -e "${BLUE}[6/8]${NC} Starting mailserver..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps mailserver
echo -e "${GREEN}✓ Mailserver started${NC}"
echo ""

# Step 7: Start backend services
echo -e "${BLUE}[7/8]${NC} Starting backend services..."

# Start SMTP server
echo "  Starting SMTP server..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps smtp-receiver

# Start API with 2 replicas
echo "  Starting API servers (2 replicas)..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --scale api=2 api

# Wait for API to be healthy
echo "  Waiting for API to be healthy..."
sleep 15

echo -e "${GREEN}✓ Backend services started${NC}"
echo ""

# Step 8: Start frontend
echo -e "${BLUE}[8/8]${NC} Starting frontend..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps front
echo -e "${GREEN}✓ Frontend started${NC}"
echo ""

# Cleanup
echo -e "${BLUE}Cleaning up...${NC}"
docker image prune -f > /dev/null 2>&1
echo -e "${GREEN}✓ Cleaned up unused Docker images${NC}"
echo ""

# Show running containers
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Running containers:${NC}"
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT ps
echo ""

# Health check summary
echo -e "${BLUE}Health Check Summary:${NC}"
echo ""

# Check database
if docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "  Database: ${GREEN}✓ Healthy${NC}"
else
    echo -e "  Database: ${RED}✗ Unhealthy${NC}"
fi

# Check Redis
if docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "  Redis: ${GREEN}✓ Healthy${NC}"
else
    echo -e "  Redis: ${RED}✗ Unhealthy${NC}"
fi

# Check Mailserver
MAILSERVER_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' mailserver 2>/dev/null || echo "unknown")
if [ "$MAILSERVER_HEALTH" = "healthy" ]; then
    echo -e "  Mailserver: ${GREEN}✓ Healthy${NC}"
elif [ "$MAILSERVER_HEALTH" = "starting" ]; then
    echo -e "  Mailserver: ${YELLOW}⚠ Starting (may take up to 2 minutes)${NC}"
elif [ "$MAILSERVER_HEALTH" = "unhealthy" ]; then
    echo -e "  Mailserver: ${RED}✗ Unhealthy${NC}"
else
    echo -e "  Mailserver: ${YELLOW}⚠ Status unknown${NC}"
fi

# Check API
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  API: ${GREEN}✓ Healthy${NC}"
else
    echo -e "  API: ${YELLOW}⚠ Not responding yet (may still be starting)${NC}"
fi

# Check Frontend
if curl -sf http://localhost:80 > /dev/null 2>&1; then
    echo -e "  Frontend: ${GREEN}✓ Healthy${NC}"
else
    echo -e "  Frontend: ${YELLOW}⚠ Not responding yet (may still be starting)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  • Monitor logs: docker compose -f $COMPOSE_FILE logs -f"
echo "  • Check API health: curl http://localhost:8000/health"
echo "  • View metrics: docker stats"
echo ""
