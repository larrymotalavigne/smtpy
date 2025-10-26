# Nginx Reverse Proxy Deployment Guide

This guide explains how to deploy SMTPy behind an existing nginx reverse proxy server.

## Architecture Overview

```
Internet
    ↓
nginx.atomdev.fr (Reverse Proxy on :443)
    ↓
    ├─→ Frontend Container (:80) - Angular App
    ├─→ API Container (:8000) - FastAPI Backend
    └─→ SMTP Container (:1025) - SMTP Server
```

## Prerequisites

1. Existing nginx server running at `nginx.atomdev.fr`
2. Domain `smtpy.fr` with DNS pointing to the nginx server
3. Docker and Docker Compose installed on the host
4. Root/sudo access to the nginx server

## Deployment Steps

### 1. Deploy SMTPy Application Stack

On your host server (where Docker containers will run):

```bash
# Set environment variables
export GHCR_OWNER=larrymotalavigne
export TAG=latest
export DOCKER_REGISTRY=ghcr.io

# Pull latest images
cd /srv/smtpy
docker compose -f docker-compose.prod.yml pull

# Start services
docker compose -f docker-compose.prod.yml up -d
```

The application will expose:
- Frontend: `http://localhost:80`
- API: `http://localhost:8000`
- SMTP: `localhost:1025`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### 2. Configure Nginx Reverse Proxy

#### Step 2.1: Copy nginx configuration

Copy the configuration file to your nginx server:

```bash
# Copy from local machine to nginx server
scp nginx/smtpy.conf user@nginx.atomdev.fr:/tmp/

# On nginx server
sudo cp /tmp/smtpy.conf /etc/nginx/sites-available/smtpy.conf
sudo ln -s /etc/nginx/sites-available/smtpy.conf /etc/nginx/sites-enabled/

# Or if using conf.d:
sudo cp /tmp/smtpy.conf /etc/nginx/conf.d/smtpy.conf
```

#### Step 2.2: Adjust upstream servers

Edit `/etc/nginx/sites-available/smtpy.conf` and update the upstream definitions if your Docker containers are on a different host:

```nginx
upstream smtpy_frontend {
    server your-docker-host:80;  # Change if needed
}

upstream smtpy_api {
    server your-docker-host:8000;  # Change if needed
}
```

If running on the same host, use `localhost` (already configured).

#### Step 2.3: Test nginx configuration

```bash
sudo nginx -t
```

### 3. Set Up SSL/TLS Certificates

#### Option A: Automated Setup (Recommended)

```bash
# Copy and run the SSL setup script
scp nginx/ssl-setup.sh user@nginx.atomdev.fr:/tmp/
ssh user@nginx.atomdev.fr

# Edit the script to set your email
sudo nano /tmp/ssl-setup.sh
# Change: EMAIL="your-email@example.com"

# Make executable and run
chmod +x /tmp/ssl-setup.sh
sudo /tmp/ssl-setup.sh
```

#### Option B: Manual Setup

```bash
# Install certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx \
    -d smtpy.fr \
    -d www.smtpy.fr \
    --email your-email@example.com \
    --agree-tos

# Set up auto-renewal
sudo crontab -e
# Add: 0 0,12 * * * certbot renew --quiet && systemctl reload nginx
```

### 4. Reload Nginx

```bash
sudo systemctl reload nginx

# Or if configuration was changed significantly:
sudo systemctl restart nginx
```

### 5. Verify Deployment

#### Check Services

```bash
# Check Docker containers
docker compose -f docker-compose.prod.yml ps

# Check nginx status
sudo systemctl status nginx

# Check nginx logs
sudo tail -f /var/log/nginx/smtpy-access.log
sudo tail -f /var/log/nginx/smtpy-error.log
```

#### Test Endpoints

```bash
# Test frontend (should return Angular app)
curl https://smtpy.fr/

# Test API health
curl https://smtpy.fr/api/health

# Test API docs
curl https://smtpy.fr/api/docs
```

#### Browser Testing

1. Navigate to `https://smtpy.fr`
2. Check that the Angular application loads
3. Verify API calls work (check browser console)
4. Test SSL certificate (should show valid, green lock)

## Configuration Details

### Port Mapping

The default configuration exposes the following ports from Docker:

- **Frontend**: Host `80` → Container `80`
- **API**: Host `8000` → Container `8000`
- **SMTP**: Host `1025` → Container `1025`
- **PostgreSQL**: Host `5432` → Container `5432` (internal only)
- **Redis**: Host `6379` → Container `6379` (internal only)

### Security Considerations

1. **SSL/TLS**: All traffic is encrypted with Let's Encrypt certificates
2. **Rate Limiting**: API requests are rate-limited (10 req/s per IP)
3. **Headers**: Security headers (HSTS, CSP, etc.) are configured
4. **Firewall**: Only ports 80, 443 should be exposed externally

### Recommended Firewall Rules

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if needed)
sudo ufw allow 22/tcp

# Block direct access to backend services (if on different hosts)
# Internal services should only be accessible via nginx
sudo ufw deny 8000/tcp  # API
sudo ufw deny 1025/tcp  # SMTP
sudo ufw deny 5432/tcp  # PostgreSQL
sudo ufw deny 6379/tcp  # Redis

# Enable firewall
sudo ufw enable
```

## Monitoring

### Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/smtpy-access.log

# Error logs
sudo tail -f /var/log/nginx/smtpy-error.log

# Filter for errors only
sudo grep "error" /var/log/nginx/smtpy-error.log
```

### Application Logs

```bash
# Docker container logs
docker compose -f docker-compose.prod.yml logs -f

# Individual service logs
docker logs smtpy-api-prod -f
docker logs smtpy-frontend-prod -f
docker logs smtpy-smtp-prod -f
```

### Health Checks

```bash
# Create a monitoring script
cat > /usr/local/bin/smtpy-health-check.sh << 'EOF'
#!/bin/bash
echo "Checking SMTPy services..."

# Check API
if curl -sf https://smtpy.fr/api/health > /dev/null; then
    echo "✓ API: Healthy"
else
    echo "✗ API: Unhealthy"
fi

# Check Frontend
if curl -sf https://smtpy.fr/ > /dev/null; then
    echo "✓ Frontend: Healthy"
else
    echo "✗ Frontend: Unhealthy"
fi

# Check containers
docker compose -f /srv/smtpy/docker-compose.prod.yml ps
EOF

chmod +x /usr/local/bin/smtpy-health-check.sh
```

## Troubleshooting

### Frontend Not Loading

1. Check frontend container logs:
   ```bash
   docker logs smtpy-frontend-prod
   ```

2. Verify nginx can reach the frontend:
   ```bash
   curl http://localhost:80/
   ```

3. Check nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/smtpy-error.log
   ```

### API Requests Failing

1. Check API container logs:
   ```bash
   docker logs smtpy-api-prod
   ```

2. Verify API is responding:
   ```bash
   curl http://localhost:8000/health
   ```

3. Check database connection:
   ```bash
   docker exec smtpy-api-prod python -c "from database import engine; engine.connect()"
   ```

### SSL Certificate Issues

1. Check certificate status:
   ```bash
   sudo certbot certificates
   ```

2. Test renewal:
   ```bash
   sudo certbot renew --dry-run
   ```

3. Renew manually if needed:
   ```bash
   sudo certbot renew --force-renewal
   sudo systemctl reload nginx
   ```

### Nginx Configuration Errors

1. Test configuration:
   ```bash
   sudo nginx -t
   ```

2. Check for port conflicts:
   ```bash
   sudo netstat -tlnp | grep :443
   sudo netstat -tlnp | grep :80
   ```

3. Verify upstream servers are accessible:
   ```bash
   curl http://localhost:80/
   curl http://localhost:8000/health
   ```

## Maintenance

### Update Application

```bash
# Pull latest images
cd /srv/smtpy
export GHCR_OWNER=larrymotalavigne
export TAG=latest
docker compose -f docker-compose.prod.yml pull

# Rolling update
docker compose -f docker-compose.prod.yml up -d --no-deps --build
```

### Renew SSL Certificates

Certificates auto-renew via cron job. To renew manually:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

### Backup

```bash
# Backup database
docker exec smtpy-db-prod pg_dump -U postgres smtpy > backup-$(date +%Y%m%d).sql

# Backup nginx configuration
sudo tar -czf nginx-config-backup-$(date +%Y%m%d).tar.gz /etc/nginx/

# Backup SSL certificates
sudo tar -czf letsencrypt-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt/
```

## Performance Tuning

### Nginx Worker Processes

Edit `/etc/nginx/nginx.conf`:

```nginx
worker_processes auto;  # Use number of CPU cores
worker_connections 2048;  # Increase if needed
```

### API Scaling

Increase API workers in `docker-compose.prod.yml`:

```yaml
environment:
  - API_WORKERS=8  # Increase based on CPU cores
```

### Connection Pooling

For high traffic, configure nginx upstream keepalive:

```nginx
upstream smtpy_api {
    server localhost:8000;
    keepalive 64;  # Increase connection pool
}
```

## Support

For issues or questions:
1. Check application logs: `docker compose logs`
2. Check nginx logs: `/var/log/nginx/smtpy-*.log`
3. Review this documentation
4. Check GitHub issues: https://github.com/larrymotalavigne/smtpy/issues
