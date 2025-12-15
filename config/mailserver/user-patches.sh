#!/bin/bash
# Docker Mailserver User Patches Script
# This script is automatically executed by docker-mailserver on startup
# It generates required Postfix database files from configuration files
#
# Documentation: https://docker-mailserver.github.io/docker-mailserver/latest/config/advanced/override-defaults/user-patches/

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[USER-PATCHES]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[USER-PATCHES]${NC} $1"
}

log_error() {
    echo -e "${RED}[USER-PATCHES]${NC} $1"
}

log_info "Running user patches for SMTPy mailserver setup..."

# Wait for Postfix to be ready
log_info "Waiting for Postfix to start..."
MAX_WAIT=60
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    if pgrep -x "master" > /dev/null; then
        log_info "✓ Postfix is running"
        break
    fi
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -ge $MAX_WAIT ]; then
    log_error "Timeout waiting for Postfix to start"
    exit 1
fi

# Generate postfix database files
log_info "Generating Postfix database files..."

# Generate virtual alias database
if [ -f /tmp/docker-mailserver/postfix-virtual.cf ]; then
    log_info "Compiling virtual alias database from postfix-virtual.cf..."
    if postmap /tmp/docker-mailserver/postfix-virtual.cf; then
        if [ -f /tmp/docker-mailserver/postfix-virtual.cf.db ]; then
            log_info "✓ Virtual alias database created successfully"
            ls -lh /tmp/docker-mailserver/postfix-virtual.cf.db
        else
            log_error "Failed to create virtual alias database"
            exit 1
        fi
    else
        log_error "postmap command failed for virtual aliases"
        exit 1
    fi
else
    log_warn "postfix-virtual.cf not found at /tmp/docker-mailserver/postfix-virtual.cf"
fi

# Generate transport database
if [ -f /tmp/docker-mailserver/postfix-transport ]; then
    log_info "Compiling transport database from postfix-transport..."
    if postmap /tmp/docker-mailserver/postfix-transport; then
        if [ -f /tmp/docker-mailserver/postfix-transport.db ]; then
            log_info "✓ Transport database created successfully"
            ls -lh /tmp/docker-mailserver/postfix-transport.db
        else
            log_error "Failed to create transport database"
            exit 1
        fi
    else
        log_error "postmap command failed for transport maps"
        exit 1
    fi
else
    log_warn "postfix-transport not found at /tmp/docker-mailserver/postfix-transport"
fi

# Reload Postfix to apply changes
log_info "Reloading Postfix configuration..."
if postfix reload; then
    log_info "✓ Postfix configuration reloaded successfully"
else
    log_warn "Failed to reload Postfix (this may be normal during initial startup)"
fi

# Wait for Rspamd if enabled
if [ "${ENABLE_RSPAMD:-1}" = "1" ]; then
    log_info "Waiting for Rspamd to start..."
    MAX_WAIT=90
    COUNTER=0
    while [ $COUNTER -lt $MAX_WAIT ]; do
        if pgrep -x "rspamd" > /dev/null; then
            log_info "✓ Rspamd process is running"

            # Check if milter port is listening
            if timeout 2 bash -c "echo > /dev/tcp/localhost/11332" 2>/dev/null; then
                log_info "✓ Rspamd milter is ready on port 11332"
                break
            else
                log_warn "Rspamd milter port not ready yet, waiting... ($COUNTER/$MAX_WAIT)"
            fi
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
        log_warn "ClamAV not running yet (may still be initializing virus database - this can take several minutes)"
    fi
fi

log_info "✓ User patches completed successfully!"
log_info "Mailserver setup is complete and ready to accept mail"
