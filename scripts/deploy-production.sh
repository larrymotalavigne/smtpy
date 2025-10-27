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

# Step 1: Login to registry (if credentials available)
if [ -n "$GITHUB_PAT" ] || [ -n "$CR_PAT" ]; then
    echo -e "${BLUE}[1/7]${NC} Logging in to GitHub Container Registry..."
    PAT="${GITHUB_PAT:-$CR_PAT}"
    echo "$PAT" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin
    echo -e "${GREEN}✓ Login successful${NC}"
else
    echo -e "${YELLOW}⚠ Skipping login (GITHUB_PAT or CR_PAT not set)${NC}"
    echo "  If you encounter authentication errors, set GITHUB_PAT or CR_PAT environment variable"
fi
echo ""

# Step 2: Pull latest images
echo -e "${BLUE}[2/7]${NC} Pulling latest images..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT pull
echo -e "${GREEN}✓ Images pulled${NC}"
echo ""

# Step 3: Stop existing containers
echo -e "${BLUE}[3/7]${NC} Stopping existing containers..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT down --remove-orphans || true
echo -e "${GREEN}✓ Old containers stopped${NC}"
echo ""

# Step 4: Start database services
echo -e "${BLUE}[4/7]${NC} Starting database and Redis..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps db redis
echo -e "${GREEN}✓ Database services started${NC}"
echo ""

# Step 5: Wait for database
echo -e "${BLUE}[5/7]${NC} Waiting for database to be ready..."
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

# Step 6: Start backend services
echo -e "${BLUE}[6/7]${NC} Starting backend services..."

# Start SMTP server
echo "  Starting SMTP server..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps smtp

# Start API with 2 replicas
echo "  Starting API servers (2 replicas)..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --scale api=2 api

# Wait for API to be healthy
echo "  Waiting for API to be healthy..."
sleep 15

echo -e "${GREEN}✓ Backend services started${NC}"
echo ""

# Step 7: Start frontend
echo -e "${BLUE}[7/7]${NC} Starting frontend..."
docker compose -f $COMPOSE_FILE $COMPOSE_ENV_FILE_OPT up -d --no-deps frontend
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
