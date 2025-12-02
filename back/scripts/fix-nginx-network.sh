#!/bin/bash
# Script to connect Nginx Proxy Manager to SMTPy network
# This enables NPM to access SMTPy containers by name

set -e

echo "=== SMTPy Nginx Network Fix ==="
echo ""

# Find the SMTPy network
echo "Looking for SMTPy network..."
SMTPY_NETWORK=$(docker network ls --filter "name=smtpy" --format "{{.Name}}" | grep -E "smtpy.*network" | head -n1)

if [ -z "$SMTPY_NETWORK" ]; then
    echo "❌ SMTPy network not found"
    echo "Available networks:"
    docker network ls
    echo ""
    echo "Run docker compose up first to create the network"
    exit 1
fi

echo "Found SMTPy network: $SMTPY_NETWORK"
echo ""

# Find the Nginx Proxy Manager container
echo "Looking for Nginx Proxy Manager container..."
NPM_CONTAINER=$(docker ps --filter "name=nginx" --format "{{.Names}}" | head -n1)

if [ -z "$NPM_CONTAINER" ]; then
    echo "❌ Nginx Proxy Manager container not found"
    echo "Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

echo "Found NPM container: $NPM_CONTAINER"
echo ""

# Check if already connected
echo "Checking current network connections..."
ALREADY_CONNECTED=$(docker inspect "$NPM_CONTAINER" | grep -c "$SMTPY_NETWORK" || true)

if [ "$ALREADY_CONNECTED" -gt 0 ]; then
    echo "✓ NPM is already connected to $SMTPY_NETWORK"
else
    echo "Connecting $NPM_CONTAINER to $SMTPY_NETWORK..."
    docker network connect "$SMTPY_NETWORK" "$NPM_CONTAINER"
    echo "✓ Successfully connected!"
fi

echo ""
echo "=== Verification ==="
echo ""

# Test connectivity
echo "Testing connectivity from NPM to SMTPy containers..."
echo ""

# Test API containers
for container in smtpy-api-1 smtpy-api-2; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "Testing $container..."
        if docker exec "$NPM_CONTAINER" curl -sf -m 5 "http://${container}:8000/health" > /dev/null 2>&1; then
            echo "  ✓ ${container}:8000 is accessible"
        else
            echo "  ✗ ${container}:8000 is NOT accessible"
        fi
    fi
done

# Test frontend
if docker ps --format "{{.Names}}" | grep -q "^smtpy-front$"; then
    echo "Testing smtpy-front..."
    if docker exec "$NPM_CONTAINER" curl -sf -m 5 "http://smtpy-front:80" > /dev/null 2>&1; then
        echo "  ✓ smtpy-front:80 is accessible"
    else
        echo "  ✗ smtpy-front:80 is NOT accessible"
    fi
fi

echo ""
echo "=== Network Configuration Complete ==="
echo ""
echo "Next steps:"
echo "1. Configure proxy host in NPM UI for api.smtpy.fr"
echo "   - Forward to: smtpy-api-1:8000 (or smtpy-api-2:8000)"
echo "   - Enable SSL"
echo ""
echo "2. Verify external access:"
echo "   curl https://api.smtpy.fr/health"
