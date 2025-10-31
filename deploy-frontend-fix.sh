#!/bin/bash

# SMTPy Frontend Environment Fix Deployment Script
# This script rebuilds the frontend with the correct production environment configuration
#
# Usage:
#   ./deploy-frontend-fix.sh          # Build locally and deploy
#   ./deploy-frontend-fix.sh --pull   # Pull from GHCR and deploy

set -e

PULL_MODE=false
if [ "$1" = "--pull" ]; then
    PULL_MODE=true
fi

echo "=========================================="
echo "SMTPy Frontend Environment Fix"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: docker-compose.prod.yml not found. Please run this script from the project root."
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "Error: .env.production not found. Please create it from .env.production.template"
    exit 1
fi

if [ "$PULL_MODE" = true ]; then
    echo "Step 1: Pulling frontend image from GHCR..."
    # Load environment variables for GHCR_OWNER and TAG
    export $(grep -v '^#' .env.production | xargs)
    export GHCR_OWNER=${GHCR_OWNER:-larrymotalavigne}
    export TAG=${TAG:-latest}
    export DOCKER_REGISTRY=${DOCKER_REGISTRY:-ghcr.io}

    docker compose --env-file .env.production -f docker-compose.prod.yml pull frontend
    echo "✓ Frontend image pulled successfully"
else
    echo "Step 1: Building new frontend Docker image locally..."
    cd front

    # Build with GHCR tags for consistency
    export GHCR_OWNER=${GHCR_OWNER:-larrymotalavigne}
    export TAG=${TAG:-latest}
    docker build -f Dockerfile.prod \
        -t ghcr.io/${GHCR_OWNER}/smtpy-frontend:${TAG} \
        -t smtpy-frontend:latest \
        .
    cd ..
    echo "✓ Frontend image built successfully"
fi
echo ""

echo "Step 2: Stopping frontend container..."
docker compose --env-file .env.production -f docker-compose.prod.yml stop frontend
echo "✓ Frontend container stopped"
echo ""

echo "Step 3: Removing old frontend container..."
docker compose --env-file .env.production -f docker-compose.prod.yml rm -f frontend
echo "✓ Old container removed"
echo ""

echo "Step 4: Starting new frontend container..."
docker compose --env-file .env.production -f docker-compose.prod.yml up -d frontend
echo "✓ New frontend container started"
echo ""

echo "Step 5: Checking container status..."
sleep 3
docker compose --env-file .env.production -f docker-compose.prod.yml ps frontend
echo ""

echo "Step 6: Checking container logs..."
docker compose --env-file .env.production -f docker-compose.prod.yml logs --tail 20 frontend
echo ""

echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "The frontend now uses the correct production environment:"
echo "  - API URL: /api (relative path)"
echo "  - Nginx will proxy API requests to the backend"
echo ""
echo "Please test your application at https://smtpy.fr"
echo "The CORS errors should now be resolved."
