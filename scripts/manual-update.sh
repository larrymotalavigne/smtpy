#!/bin/bash
# Manual Update Script - Pull latest images and restart containers
# Use this when you want to immediately update to the latest built images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SMTPy Manual Update${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"

# Set required environment variables
export GHCR_OWNER="${GHCR_OWNER:-larrymotalavigne}"
export TAG="${TAG:-latest}"
export DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"

# Compose env-file option
COMPOSE_ENV_FILE_OPT=""
if [ -f "$ENV_FILE" ]; then
    COMPOSE_ENV_FILE_OPT="--env-file $ENV_FILE"
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  Registry: $DOCKER_REGISTRY"
echo "  Owner: $GHCR_OWNER"
echo "  Tag: $TAG"
echo ""

# Step 1: Login to registry (if credentials available)
if [ -n "$GITHUB_PAT" ] || [ -n "$CR_PAT" ]; then
    echo -e "${BLUE}[1/5]${NC} Logging in to GitHub Container Registry..."
    PAT="${GITHUB_PAT:-$CR_PAT}"
    echo "$PAT" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin
    echo -e "${GREEN}✓ Login successful${NC}"
else
    echo -e "${YELLOW}⚠ Skipping login (GITHUB_PAT or CR_PAT not set)${NC}"
fi
echo ""

# Step 2: Pull latest images
echo -e "${BLUE}[2/5]${NC} Pulling latest images from registry..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT pull
echo -e "${GREEN}✓ Latest images pulled${NC}"
echo ""

# Step 3: Stop all containers
echo -e "${BLUE}[3/5]${NC} Stopping all SMTPy containers..."

# Force stop all smtpy containers
docker ps -a --filter "name=smtpy-" --format "{{.Names}}" | xargs -r docker stop || true
docker ps -a --filter "name=smtpy-" --format "{{.Names}}" | xargs -r docker rm || true

# Also use compose down for cleanup
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT down --remove-orphans || true

echo -e "${GREEN}✓ All containers stopped${NC}"
echo ""

# Step 4: Start all services
echo -e "${BLUE}[4/5]${NC} Starting all services with latest images..."

# Start database services first
echo "  Starting database and Redis..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps db redis

# Wait for database
echo "  Waiting for database to be ready..."
sleep 10
until docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT exec -T db pg_isready -U postgres > /dev/null 2>&1; do
    echo "  Waiting for database..."
    sleep 2
done
echo -e "${GREEN}✓ Database ready${NC}"

# Start SMTP server
echo "  Starting SMTP server..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps smtp

# Start API with 2 replicas
echo "  Starting API servers (2 replicas)..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --scale api=2 api

# Wait for API
echo "  Waiting for API to be healthy..."
sleep 15

# Start frontend
echo "  Starting frontend..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps frontend

echo -e "${GREEN}✓ All services started${NC}"
echo ""

# Step 5: Show status
echo -e "${BLUE}[5/5]${NC} Checking container status..."
echo ""
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT ps
echo ""

# Check logs for errors
echo -e "${BLUE}Checking for errors in logs...${NC}"
echo ""

echo "API logs (last 5 lines):"
docker logs smtpy-api-1 --tail 5 2>&1 | grep -i error || echo "  No errors found"
echo ""

echo "SMTP logs (last 5 lines):"
docker logs smtpy-smtp-prod --tail 5 2>&1 | grep -i error || echo "  No errors found"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Update completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  • Check full logs: docker logs smtpy-api-1 -f"
echo "  • Test API: docker exec smtpy-api-1 curl http://localhost:8000/health"
echo "  • Monitor: docker stats"
echo ""
