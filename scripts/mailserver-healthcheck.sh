#!/bin/bash
# Docker Mailserver Health Check Script
# This script verifies that critical mail services are running and responding
#
# Exit codes:
#   0 - All checks passed (healthy)
#   1 - One or more checks failed (unhealthy)

set -e

# Color output for better readability (when run manually)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a service is running
check_service() {
    local service=$1
    local process=$2

    if pgrep -x "$process" > /dev/null; then
        log "${GREEN}✓${NC} $service is running"
        return 0
    else
        log "${RED}✗${NC} $service is not running"
        return 1
    fi
}

# Function to check if a port is listening
check_port() {
    local service=$1
    local port=$2

    if timeout 5 bash -c "echo > /dev/tcp/127.0.0.1/$port" 2>/dev/null; then
        log "${GREEN}✓${NC} $service is listening on port $port"
        return 0
    else
        log "${RED}✗${NC} $service is not listening on port $port"
        return 1
    fi
}

# Function to check SMTP service with EHLO
check_smtp() {
    local port=$1
    local service_name=$2

    # Try to connect and follow proper SMTP protocol:
    # 1. Wait for server banner (220)
    # 2. Send EHLO with proper CRLF line ending
    # 3. Send QUIT to cleanly disconnect
    response=$(timeout 5 bash -c "
        exec 3<>/dev/tcp/127.0.0.1/$port
        # Read server banner
        read -u 3 banner
        # Send EHLO with CRLF
        printf 'EHLO healthcheck\r\n' >&3
        # Read response
        read -u 3 ehlo_response
        # Send QUIT with CRLF
        printf 'QUIT\r\n' >&3
        # Close connection
        exec 3<&-
        exec 3>&-
        # Output both banner and EHLO response for verification
        echo \"\$banner\"
        echo \"\$ehlo_response\"
    " 2>/dev/null)

    if echo "$response" | grep -q "220"; then
        log "${GREEN}✓${NC} $service_name (port $port) responded correctly"
        return 0
    else
        log "${RED}✗${NC} $service_name (port $port) did not respond correctly"
        return 1
    fi
}

# Function to check IMAP service
check_imap() {
    local port=$1
    local service_name=$2

    # Try to connect to IMAP and follow proper protocol:
    # 1. Wait for server banner (OK)
    # 2. Send LOGOUT with proper CRLF line ending
    response=$(timeout 5 bash -c "
        exec 3<>/dev/tcp/127.0.0.1/$port
        # Read server banner
        read -u 3 banner
        # Send LOGOUT with CRLF
        printf 'A1 LOGOUT\r\n' >&3
        # Read response
        read -u 3 logout_response
        # Close connection
        exec 3<&-
        exec 3>&-
        # Output both banner and logout response for verification
        echo \"\$banner\"
        echo \"\$logout_response\"
    " 2>/dev/null)

    if echo "$response" | grep -q "OK"; then
        log "${GREEN}✓${NC} $service_name (port $port) responded correctly"
        return 0
    else
        log "${RED}✗${NC} $service_name (port $port) did not respond correctly"
        return 1
    fi
}

# Initialize health check status
HEALTH_STATUS=0

log "Starting mailserver health check..."

# Check critical processes
log "Checking critical services..."

if ! check_service "Postfix (SMTP)" "master"; then
    HEALTH_STATUS=1
fi

if ! check_service "Dovecot (IMAP)" "dovecot"; then
    HEALTH_STATUS=1
fi

# Check if Rspamd is enabled and running
if [ "${ENABLE_RSPAMD:-1}" = "1" ]; then
    if ! check_service "Rspamd (Anti-spam)" "rspamd"; then
        HEALTH_STATUS=1
    fi
fi

# Check if ClamAV is enabled and running
if [ "${ENABLE_CLAMAV:-1}" = "1" ]; then
    if ! check_service "ClamAV (Anti-virus)" "clamd"; then
        log "${YELLOW}⚠${NC} ClamAV may still be initializing (this is normal on first start)"
        # Don't fail health check if ClamAV is not running yet during startup
        # HEALTH_STATUS=1
    fi
fi

# Check SMTP ports
log "Checking SMTP ports..."

if ! check_smtp 25 "SMTP (port 25)"; then
    HEALTH_STATUS=1
fi

if ! check_smtp 587 "Submission (port 587)"; then
    HEALTH_STATUS=1
fi

if ! check_smtp 465 "Submissions (port 465)"; then
    HEALTH_STATUS=1
fi

# Check IMAP ports if enabled
if [ "${ENABLE_IMAP:-1}" = "1" ]; then
    log "Checking IMAP ports..."

    if ! check_imap 143 "IMAP (port 143)"; then
        HEALTH_STATUS=1
    fi

    if ! check_imap 993 "IMAPS (port 993)"; then
        HEALTH_STATUS=1
    fi
fi

# Check mail queue status
log "Checking mail queue..."
QUEUE_SIZE=$(postqueue -p | tail -n 1 | awk '{print $5}')

if [ "$QUEUE_SIZE" = "empty" ]; then
    log "${GREEN}✓${NC} Mail queue is empty"
elif [ -n "$QUEUE_SIZE" ]; then
    log "${YELLOW}⚠${NC} Mail queue has $QUEUE_SIZE messages"
    # Don't fail health check for queue size
else
    log "${YELLOW}⚠${NC} Unable to check mail queue"
fi

# Check disk space
log "Checking disk space..."
DISK_USAGE=$(df /var/mail | tail -n 1 | awk '{print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -lt 90 ]; then
    log "${GREEN}✓${NC} Disk usage is ${DISK_USAGE}%"
else
    log "${RED}✗${NC} Disk usage is critically high: ${DISK_USAGE}%"
    HEALTH_STATUS=1
fi

# Final status
log "----------------------------------------"
if [ $HEALTH_STATUS -eq 0 ]; then
    log "${GREEN}✓ Health check passed - mailserver is healthy${NC}"
    exit 0
else
    log "${RED}✗ Health check failed - mailserver is unhealthy${NC}"
    exit 1
fi
