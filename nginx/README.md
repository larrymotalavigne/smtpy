# Nginx Configuration for SMTPy

This directory contains nginx configuration files for deploying SMTPy with a reverse proxy.

## Files

- **smtpy.conf** - Complete nginx reverse proxy configuration for smtpy.fr
- **ssl-setup.sh** - Automated SSL/TLS certificate setup script using Let's Encrypt

## Quick Start

### 1. Deploy Application Stack

```bash
cd /srv/smtpy
export GHCR_OWNER=larrymotalavigne
export TAG=latest
docker compose -f docker-compose.prod.yml up -d
```

### 2. Configure Nginx

```bash
# Copy configuration to nginx server
sudo cp smtpy.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/smtpy.conf /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t
```

### 3. Set Up SSL

```bash
# Edit email in script
nano ssl-setup.sh
# Change: EMAIL="your-email@example.com"

# Run setup
chmod +x ssl-setup.sh
sudo ./ssl-setup.sh
```

### 4. Reload Nginx

```bash
sudo systemctl reload nginx
```

## Configuration Overview

### Upstream Servers

The configuration defines two upstream server pools:

- **smtpy_frontend** - Angular application (port 80)
- **smtpy_api** - FastAPI backend (port 8000)

### URL Routing

- `https://smtpy.fr/` → Frontend (Angular)
- `https://smtpy.fr/api/*` → Backend API
- `https://smtpy.fr/health` → API health check

### Security Features

1. **SSL/TLS**
   - TLS 1.2 and 1.3 only
   - Modern cipher suites
   - OCSP stapling enabled

2. **Security Headers**
   - HSTS (HTTP Strict Transport Security)
   - X-Frame-Options
   - X-Content-Type-Options
   - CSP (Content Security Policy)
   - Referrer-Policy

3. **Rate Limiting**
   - API: 10 requests/second per IP
   - General: 50 requests/second per IP
   - Burst allowance: 20 requests

### Performance Features

- HTTP/2 enabled
- Gzip compression
- Connection keepalive
- Proxy buffering
- Static asset caching (1 year)

## Customization

### Different Host Setup

If your Docker containers run on a different host than nginx:

```nginx
upstream smtpy_frontend {
    server docker-host.example.com:80;
}

upstream smtpy_api {
    server docker-host.example.com:8000;
}
```

### Load Balancing

For multiple API instances:

```nginx
upstream smtpy_api {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    keepalive 32;
}
```

### Custom Rate Limits

Adjust rate limiting zones:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;  # 20 req/s
```

### Additional Domains

Add more server names:

```nginx
server {
    listen 443 ssl http2;
    server_name smtpy.fr www.smtpy.fr app.smtpy.fr;
    # ...
}
```

## Testing

### Test nginx configuration

```bash
sudo nginx -t
```

### Test SSL certificate

```bash
# Using openssl
openssl s_client -connect smtpy.fr:443 -servername smtpy.fr

# Using curl
curl -vI https://smtpy.fr/
```

### Test endpoints

```bash
# Frontend
curl https://smtpy.fr/

# API health
curl https://smtpy.fr/api/health

# API with rate limiting
for i in {1..15}; do curl -w "\n" https://smtpy.fr/api/health; done
```

### Check SSL rating

Visit: https://www.ssllabs.com/ssltest/analyze.html?d=smtpy.fr

## Monitoring

### View logs

```bash
# Access logs
sudo tail -f /var/log/nginx/smtpy-access.log

# Error logs
sudo tail -f /var/log/nginx/smtpy-error.log

# Filter for specific status codes
sudo grep " 500 " /var/log/nginx/smtpy-access.log
sudo grep " 404 " /var/log/nginx/smtpy-access.log
```

### Monitor rate limiting

```bash
sudo grep "limiting requests" /var/log/nginx/smtpy-error.log
```

## Troubleshooting

### 502 Bad Gateway

1. Check if upstream servers are running:
   ```bash
   curl http://localhost:80/
   curl http://localhost:8000/health
   ```

2. Check Docker containers:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

3. Check nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/smtpy-error.log
   ```

### SSL Certificate Not Found

1. Verify certificate exists:
   ```bash
   sudo ls -la /etc/letsencrypt/live/smtpy.fr/
   ```

2. Re-run SSL setup:
   ```bash
   sudo ./ssl-setup.sh
   ```

### Rate Limiting Issues

1. Adjust rate limits in configuration
2. Check client IP detection:
   ```bash
   sudo grep "limiting requests" /var/log/nginx/smtpy-error.log
   ```

## Maintenance

### Reload Configuration

After making changes:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Certificate Renewal

Automatic renewal is configured. To renew manually:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

### Rotate Logs

Nginx logs are automatically rotated by logrotate. Manual rotation:

```bash
sudo logrotate -f /etc/logrotate.d/nginx
```

## See Also

- [Full Deployment Guide](../docs/NGINX_DEPLOYMENT.md)
- [Production Configuration](../docker-compose.prod.yml)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
