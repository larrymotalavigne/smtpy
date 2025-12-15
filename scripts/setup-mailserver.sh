#!/bin/bash
# Mailserver Setup Script
# This script runs inside the mailserver container to perform initial setup
# and generate required database files

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[SETUP]${NC} $1"
}

log_error() {
    echo -e "${RED}[SETUP]${NC} $1"
}

log_info "Starting mailserver setup..."

# Wait for Postfix to be ready
log_info "Waiting for Postfix to start..."
MAX_WAIT=30
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    if pgrep -x "master" > /dev/null; then
        log_info "Postfix is running"
        break
    fi
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -ge $MAX_WAIT ]; then
    log_error "Timeout waiting for Postfix to start"
    exit 1
fi

# Generate postfix database files if they don't exist
log_info "Checking Postfix database files..."

# Generate virtual alias database
if [ -f /tmp/docker-mailserver/postfix-virtual.cf ]; then
    log_info "Generating virtual alias database..."
    postmap /tmp/docker-mailserver/postfix-virtual.cf
    if [ -f /tmp/docker-mailserver/postfix-virtual.cf.db ]; then
        log_info "✓ Virtual alias database created"
    else
        log_error "Failed to create virtual alias database"
    fi
else
    log_warn "postfix-virtual.cf not found, skipping"
fi

# Generate transport database
if [ -f /tmp/docker-mailserver/postfix-transport ]; then
    log_info "Generating transport database..."
    postmap /tmp/docker-mailserver/postfix-transport
    if [ -f /tmp/docker-mailserver/postfix-transport.db ]; then
        log_info "✓ Transport database created"
    else
        log_error "Failed to create transport database"
    fi
else
    log_warn "postfix-transport not found, skipping"
fi

# Reload Postfix to apply changes
log_info "Reloading Postfix configuration..."
if postfix reload; then
    log_info "✓ Postfix configuration reloaded"
else
    log_warn "Failed to reload Postfix (this may be normal on first start)"
fi

# Wait for Rspamd if enabled
if [ "${ENABLE_RSPAMD:-1}" = "1" ]; then
    log_info "Waiting for Rspamd to start..."
    MAX_WAIT=60
    COUNTER=0
    while [ $COUNTER -lt $MAX_WAIT ]; do
        if pgrep -x "rspamd" > /dev/null; then
            log_info "✓ Rspamd is running"

            # Check if milter port is listening
            if timeout 2 bash -c "echo > /dev/tcp/localhost/11332" 2>/dev/null; then
                log_info "✓ Rspamd milter is ready"
            else
                log_warn "Rspamd milter port not ready yet"
            fi
            break
        fi
        sleep 1
        COUNTER=$((COUNTER + 1))
    done

    if [ $COUNTER -ge $MAX_WAIT ]; then
        log_warn "Rspamd did not start within ${MAX_WAIT}s (may still be initializing)"
    fi
fi

# Check ClamAV if enabled
if [ "${ENABLE_CLAMAV:-1}" = "1" ]; then
    log_info "Checking ClamAV status..."
    if pgrep -x "clamd" > /dev/null; then
        log_info "✓ ClamAV is running"
    else
        log_warn "ClamAV not running yet (may still be initializing virus database)"
    fi
fi

log_info "Setup complete!"
