#!/bin/bash
# SSL/TLS Setup Script for SMTPy using Let's Encrypt
# This script sets up SSL certificates for smtpy.fr using certbot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="smtpy.fr"
EMAIL="your-email@example.com"  # CHANGE THIS
WEBROOT="/var/www/certbot"

echo -e "${GREEN}=== SMTPy SSL/TLS Setup ===${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Certbot not found. Installing...${NC}"

    # Detect OS and install certbot
    if [ -f /etc/debian_version ]; then
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    elif [ -f /etc/redhat-release ]; then
        yum install -y certbot python3-certbot-nginx
    else
        echo -e "${RED}Unsupported OS. Please install certbot manually.${NC}"
        exit 1
    fi
fi

# Create webroot directory for Let's Encrypt challenges
echo -e "${GREEN}Creating webroot directory...${NC}"
mkdir -p $WEBROOT

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}Error: Nginx is not installed${NC}"
    exit 1
fi

# Test nginx configuration
echo -e "${GREEN}Testing nginx configuration...${NC}"
nginx -t

# Option 1: Using certbot with nginx plugin (recommended)
echo -e "${GREEN}Obtaining SSL certificate using certbot...${NC}"
echo -e "${YELLOW}NOTE: Make sure your domain DNS is pointing to this server${NC}"
echo -e "${YELLOW}Press Ctrl+C to cancel, or Enter to continue...${NC}"
read

# Obtain certificate
certbot certonly \
    --nginx \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive \
    --expand

# Alternative Option 2: Using webroot mode
# Uncomment if you prefer webroot authentication
# certbot certonly \
#     --webroot \
#     -w $WEBROOT \
#     -d $DOMAIN \
#     -d www.$DOMAIN \
#     --email $EMAIL \
#     --agree-tos \
#     --non-interactive

# Check if certificates were created
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${GREEN}✓ SSL certificates obtained successfully${NC}"
else
    echo -e "${RED}✗ Failed to obtain SSL certificates${NC}"
    exit 1
fi

# Set up auto-renewal
echo -e "${GREEN}Setting up automatic certificate renewal...${NC}"

# Create renewal cron job
CRON_JOB="0 0,12 * * * certbot renew --quiet && systemctl reload nginx"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✓ Auto-renewal cron job created${NC}"
else
    echo -e "${YELLOW}ℹ Auto-renewal cron job already exists${NC}"
fi

# Test renewal
echo -e "${GREEN}Testing certificate renewal...${NC}"
certbot renew --dry-run

# Reload nginx
echo -e "${GREEN}Reloading nginx...${NC}"
systemctl reload nginx

echo -e "\n${GREEN}=== SSL Setup Complete ===${NC}"
echo -e "Certificates are located at: /etc/letsencrypt/live/$DOMAIN/"
echo -e "Auto-renewal is configured to run twice daily"
echo -e "\nNext steps:"
echo -e "1. Update the nginx configuration with the SSL certificate paths"
echo -e "2. Reload nginx: ${YELLOW}systemctl reload nginx${NC}"
echo -e "3. Test your HTTPS connection: ${YELLOW}https://$DOMAIN${NC}"
