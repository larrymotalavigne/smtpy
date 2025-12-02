#!/bin/bash
#
# SMTP Configuration Test Script for SMTPy
# Tests mail.atomdev.fr SMTP server connectivity
#

set -e

echo "========================================"
echo "SMTPy SMTP Test - mail.atomdev.fr"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SMTP_HOST="${SMTP_HOST:-mail.atomdev.fr}"
SMTP_PORT_587=587
SMTP_PORT_465=465
SMTP_PORT_25=25

echo ""
echo -e "${BLUE}Testing SMTP server: $SMTP_HOST${NC}"
echo ""

# Test 1: DNS Resolution
echo "1. Testing DNS resolution..."
if IP=$(dig +short A $SMTP_HOST | head -1); then
    if [ -n "$IP" ]; then
        echo -e "   ${GREEN}✓${NC} DNS resolved: $SMTP_HOST -> $IP"
    else
        echo -e "   ${RED}✗${NC} DNS resolution failed"
        exit 1
    fi
else
    echo -e "   ${RED}✗${NC} dig command failed"
    exit 1
fi

# Test 2: Port 587 (STARTTLS)
echo ""
echo "2. Testing port 587 (STARTTLS - recommended)..."
if timeout 5 bash -c "echo > /dev/tcp/$SMTP_HOST/587" 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} Port 587 is accessible"
else
    echo -e "   ${YELLOW}⚠${NC} Port 587 is not accessible"
fi

# Test 3: Port 465 (SSL/TLS)
echo ""
echo "3. Testing port 465 (SSL/TLS)..."
if timeout 5 bash -c "echo > /dev/tcp/$SMTP_HOST/465" 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} Port 465 is accessible"
else
    echo -e "   ${YELLOW}⚠${NC} Port 465 is not accessible"
fi

# Test 4: Port 25 (Standard SMTP)
echo ""
echo "4. Testing port 25 (standard SMTP)..."
if timeout 5 bash -c "echo > /dev/tcp/$SMTP_HOST/25" 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} Port 25 is accessible"
else
    echo -e "   ${YELLOW}⚠${NC} Port 25 is not accessible"
fi

# Test 5: SMTP Banner
echo ""
echo "5. Testing SMTP banner (port 587)..."
if command -v nc &> /dev/null; then
    BANNER=$(timeout 5 sh -c "echo 'QUIT' | nc $SMTP_HOST 587 2>/dev/null" | head -1)
    if [ -n "$BANNER" ]; then
        echo -e "   ${GREEN}✓${NC} SMTP banner received:"
        echo "   $BANNER"
    else
        echo -e "   ${YELLOW}⚠${NC} No banner received (server might not respond to banner queries)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} nc (netcat) not installed, skipping banner test"
fi

# Test 6: EHLO command
echo ""
echo "6. Testing EHLO response..."
if command -v nc &> /dev/null; then
    EHLO_RESPONSE=$(timeout 5 sh -c "echo -e 'EHLO test.com\nQUIT' | nc $SMTP_HOST 587 2>/dev/null")
    if echo "$EHLO_RESPONSE" | grep -q "250"; then
        echo -e "   ${GREEN}✓${NC} SMTP server responds to EHLO"
        # Check for STARTTLS support
        if echo "$EHLO_RESPONSE" | grep -qi "STARTTLS"; then
            echo -e "   ${GREEN}✓${NC} STARTTLS is supported"
        fi
    else
        echo -e "   ${YELLOW}⚠${NC} Could not verify EHLO response"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} nc (netcat) not installed, skipping EHLO test"
fi

# Test 7: Environment variables check
echo ""
echo "7. Checking environment variables..."
ENV_WARNINGS=0

if [ -f ".env.production" ]; then
    echo -e "   ${GREEN}✓${NC} .env.production file exists"

    # Check for SMTP configuration
    if grep -q "EMAIL_SMTP_HOST" .env.production; then
        echo -e "   ${GREEN}✓${NC} EMAIL_SMTP_HOST is defined"
    else
        echo -e "   ${RED}✗${NC} EMAIL_SMTP_HOST is not defined"
        ENV_WARNINGS=$((ENV_WARNINGS + 1))
    fi

    if grep -q "EMAIL_SMTP_PORT" .env.production; then
        echo -e "   ${GREEN}✓${NC} EMAIL_SMTP_PORT is defined"
    else
        echo -e "   ${RED}✗${NC} EMAIL_SMTP_PORT is not defined"
        ENV_WARNINGS=$((ENV_WARNINGS + 1))
    fi

    if grep -q "EMAIL_SMTP_USERNAME" .env.production; then
        echo -e "   ${GREEN}✓${NC} EMAIL_SMTP_USERNAME is defined"
    else
        echo -e "   ${YELLOW}⚠${NC} EMAIL_SMTP_USERNAME is not defined (may be required)"
    fi

    if grep -q "EMAIL_SMTP_PASSWORD" .env.production; then
        echo -e "   ${GREEN}✓${NC} EMAIL_SMTP_PASSWORD is defined"
    else
        echo -e "   ${YELLOW}⚠${NC} EMAIL_SMTP_PASSWORD is not defined (may be required)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} .env.production file not found"
    echo "   Create it from: cp .env.production.template .env.production"
fi

# Summary
echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Configure .env.production with mail.atomdev.fr settings:"
echo "   EMAIL_SMTP_HOST=mail.atomdev.fr"
echo "   EMAIL_SMTP_PORT=587"
echo "   EMAIL_SMTP_USERNAME=your-username"
echo "   EMAIL_SMTP_PASSWORD=your-password"
echo "   EMAIL_SMTP_USE_TLS=true"
echo ""
echo "2. Test email sending with Python script:"
echo "   cd back && python scripts/test_smtp_config.py --check-config"
echo "   cd back && python scripts/test_smtp_config.py --test-transactional your@email.com"
echo ""
echo "3. Test SMTP relay:"
echo "   cd back && python scripts/test_smtp_config.py --test-relay sender@domain.com recipient@email.com"
echo ""
echo "========================================"
