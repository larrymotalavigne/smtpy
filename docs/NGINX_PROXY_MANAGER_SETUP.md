# Nginx Proxy Manager Setup for SMTPy

**Date**: 2025-10-27
**Proxy Manager**: Nginx-Proxy-Manager-Official
**Status**: ✅ Ready to Configure

## Overview

Since you're using Nginx Proxy Manager (NPM), the setup is much simpler than manual nginx configuration. NPM just needs to be connected to the SMTPy Docker network to route traffic to the containers.

## Architecture with NPM

```
Internet
   │
   └─> Nginx Proxy Manager (nginx.atomdev.fr)
           │ Port 80/443
           │
           └─> Docker Network: smtpy_smtpy-network
                   │
                   ├─> smtpy-front:80 (Angular app)
                   └─> smtpy-api-1:8000, smtpy-api-2:8000 (API servers)
```

## Quick Setup (3 Steps)

### Step 1: Connect NPM to SMTPy Network

```bash
# Find your Nginx Proxy Manager container name
docker ps | grep nginx-proxy-manager

# Connect NPM to SMTPy Docker network
docker network connect smtpy_smtpy-network <npm-container-name>

# Verify connection
docker network inspect smtpy_smtpy-network
```

You should see both NPM and SMTPy containers in the network.

### Step 2: Create Proxy Host in NPM UI

Login to your Nginx Proxy Manager web interface (usually `http://<server-ip>:81`).

#### **For Frontend (Main Application)**

1. **Navigate**: Hosts → Proxy Hosts → Add Proxy Host

2. **Details Tab**:
   - **Domain Names**: `smtpy.fr`, `www.smtpy.fr`
   - **Scheme**: `http` (internal communication)
   - **Forward Hostname/IP**: `smtpy-front`
   - **Forward Port**: `80`
   - **Cache Assets**: ✅ Enabled
   - **Block Common Exploits**: ✅ Enabled
   - **Websockets Support**: ✅ Enabled (if using real-time features)

3. **SSL Tab**:
   - **SSL Certificate**: Request a New SSL Certificate
   - **Force SSL**: ✅ Enabled
   - **HTTP/2 Support**: ✅ Enabled
   - **HSTS Enabled**: ✅ Enabled
   - **Email**: Your email for Let's Encrypt
   - **Agree to Terms**: ✅ Enabled

4. **Advanced Tab** (Optional):
   ```nginx
   # Custom Nginx Configuration (optional)
   client_max_body_size 20M;

   # Security headers
   add_header X-Frame-Options "SAMEORIGIN" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header Referrer-Policy "no-referrer-when-downgrade" always;
   ```

5. **Save**

#### **For API (Load Balanced)**

If you want to expose the API separately (e.g., `api.smtpy.fr`):

1. **Details Tab**:
   - **Domain Names**: `api.smtpy.fr`
   - **Scheme**: `http`
   - **Forward Hostname/IP**: `smtpy-api-1` (NPM will round-robin if you add both)
   - **Forward Port**: `8000`
   - **Block Common Exploits**: ✅ Enabled

2. **SSL Tab**: Same as frontend

3. **Advanced Tab**:
   ```nginx
   # Load balancing (if NPM supports upstream blocks)
   # OR rely on NPM's built-in failover

   # Rate limiting
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
   limit_req zone=api_limit burst=20 nodelay;

   # API-specific headers
   add_header Cache-Control "no-store, no-cache, must-revalidate";
   ```

**Note**: If your frontend already proxies API requests (e.g., `/api/*` routes), you may not need a separate API proxy host.

### Step 3: Verify Setup

```bash
# Test DNS resolution from NPM container
docker exec <npm-container-name> ping -c 1 smtpy-front
docker exec <npm-container-name> ping -c 1 smtpy-api-1
docker exec <npm-container-name> ping -c 1 smtpy-api-2

# Test HTTP connectivity
docker exec <npm-container-name> curl -f http://smtpy-front:80
docker exec <npm-container-name> curl -f http://smtpy-api-1:8000/health
docker exec <npm-container-name> curl -f http://smtpy-api-2:8000/health

# Test external access
curl -f https://smtpy.fr/
curl -f https://smtpy.fr/health
```

## NPM Configuration Recommendations

### **Option A: Frontend Only (Recommended)**

If your Angular app already proxies API requests internally:

**Create 1 Proxy Host**:
- Domain: `smtpy.fr`
- Forward to: `smtpy-front:80`

The frontend's internal nginx will handle API routing to the backend containers.

### **Option B: Separate Frontend + API**

If you want to expose the API on a subdomain:

**Create 2 Proxy Hosts**:

1. **Frontend**:
   - Domain: `smtpy.fr`
   - Forward to: `smtpy-front:80`

2. **API**:
   - Domain: `api.smtpy.fr`
   - Forward to: `smtpy-api-1:8000`
   - Add load balancing to `smtpy-api-2:8000` in Advanced config

### **Option C: NPM Handles All Routing**

Use NPM's location blocks to route everything:

**Create 1 Proxy Host** with custom config:
- Domain: `smtpy.fr`
- Default Forward to: `smtpy-front:80`

**Advanced Tab**:
```nginx
# API routes
location /api/ {
    proxy_pass http://smtpy-api-1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Disable caching for API
    add_header Cache-Control "no-store, no-cache, must-revalidate";
}

# Health check
location /health {
    access_log off;
    proxy_pass http://smtpy-api-1:8000/health;
}

# Everything else to frontend
location / {
    proxy_pass http://smtpy-front:80;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Troubleshooting

### Issue: "502 Bad Gateway"

**Symptom**: NPM shows 502 error when accessing `smtpy.fr`

**Causes & Fixes**:

1. **NPM not connected to Docker network**:
   ```bash
   docker network connect smtpy_smtpy-network <npm-container-name>
   ```

2. **Containers not running**:
   ```bash
   docker ps | grep smtpy
   # Should show all containers running
   ```

3. **Wrong forward hostname**:
   - Check that you used `smtpy-front` (container name), not `localhost` or IP

4. **Containers not healthy**:
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   # Check for "healthy" status
   ```

### Issue: "Could not resolve host"

**Symptom**: NPM can't find `smtpy-front`

**Fix**: Ensure NPM is on the same Docker network
```bash
# Check networks
docker inspect <npm-container-name> | grep -A 10 Networks

# Should show smtpy_smtpy-network
# If not:
docker network connect smtpy_smtpy-network <npm-container-name>

# Restart NPM
docker restart <npm-container-name>
```

### Issue: SSL Certificate Fails

**Symptom**: Let's Encrypt certificate request fails

**Common Causes**:
1. **Port 80/443 not accessible** from internet
2. **DNS not pointing to server** yet
3. **Firewall blocking** ports

**Fix**:
```bash
# Verify DNS
nslookup smtpy.fr
# Should point to your server's IP

# Check firewall
sudo iptables -L -n | grep -E "80|443"

# Test port 80 from outside
curl -I http://smtpy.fr
```

### Issue: API Requests Failing

**Symptom**: Frontend loads but API calls fail (CORS errors, 404, etc.)

**Causes**:
1. **CORS configuration**: API needs to allow your domain
2. **Wrong API URL** in frontend config
3. **Missing API routes** in NPM

**Fix**:

Check API CORS settings allow your domain:
```python
# In API settings
CORS_ORIGINS=https://smtpy.fr,https://www.smtpy.fr
```

Verify frontend is configured to use correct API endpoint:
- If using separate API domain: `https://api.smtpy.fr`
- If using same domain: `https://smtpy.fr/api`

## NPM-Specific Features

### **Access Lists**

Protect admin routes or staging environments:

1. **Create Access List**: Access Lists → Add Access List
   - **Name**: "Admin Only"
   - **Authorization**: Username/Password or OAuth
   - **Users**: Add allowed users

2. **Apply to Proxy Host**: Edit Proxy Host → Access List → Select "Admin Only"

### **Custom Locations**

For fine-grained control:

1. **Edit Proxy Host** → Custom Locations → Add Location
   - **Location**: `/admin/`
   - **Forward to**: `smtpy-api-1:8000`
   - **Advanced**: Add auth or rate limiting

### **Streaming**

If using WebSockets or SSE:

1. **Edit Proxy Host** → Details → ✅ **Websockets Support**

2. **Advanced Tab**:
   ```nginx
   proxy_read_timeout 3600s;
   proxy_send_timeout 3600s;
   proxy_buffering off;
   ```

## Security Best Practices

### 1. Enable Security Features

In NPM Proxy Host config:
- ✅ Block Common Exploits
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

### 2. Add Security Headers

**Advanced Tab**:
```nginx
# Security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;

# CSP for Stripe integration
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.stripe.com; frame-src https://js.stripe.com;" always;
```

### 3. Rate Limiting

**Advanced Tab**:
```nginx
# General rate limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=50r/s;
limit_req zone=general burst=20 nodelay;

# API rate limiting (stricter)
location /api/ {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    proxy_pass http://smtpy-api-1:8000;
}
```

### 4. Client Upload Limits

**Advanced Tab**:
```nginx
client_max_body_size 20M;
client_body_buffer_size 128k;
```

## Monitoring in NPM

### View Access Logs

1. **NPM UI**: Click on Proxy Host → "View Access Log"
2. **Docker Logs**:
   ```bash
   docker logs <npm-container-name> -f
   ```

### View Error Logs

```bash
docker logs <npm-container-name> -f | grep error
```

### Monitor Traffic

```bash
# Real-time stats
docker stats <npm-container-name>

# Connection counts
docker exec <npm-container-name> netstat -an | grep ESTABLISHED | wc -l
```

## Complete Setup Checklist

After deployment, verify:

- [ ] SMTPy containers running: `docker ps | grep smtpy`
- [ ] NPM connected to network: `docker network inspect smtpy_smtpy-network | grep npm`
- [ ] DNS resolving: `nslookup smtpy.fr` points to server
- [ ] NPM can ping containers: `docker exec <npm> ping smtpy-front`
- [ ] NPM can curl containers: `docker exec <npm> curl http://smtpy-api-1:8000/health`
- [ ] Proxy host created in NPM UI
- [ ] SSL certificate issued successfully
- [ ] External HTTPS works: `curl https://smtpy.fr/`
- [ ] API health check works: `curl https://smtpy.fr/health`
- [ ] Frontend loads in browser
- [ ] No console errors in browser dev tools

## Backup NPM Configuration

NPM stores config in its database. To backup:

```bash
# Find NPM data volume
docker inspect <npm-container-name> | grep -A 5 Mounts

# Backup the database
docker exec <npm-container-name> tar czf /tmp/npm-backup.tar.gz /data
docker cp <npm-container-name>:/tmp/npm-backup.tar.gz ./npm-backup-$(date +%Y%m%d).tar.gz
```

## Related Documentation

- [Port Conflict Resolution](./PORT_CONFLICT_RESOLUTION.md) - Why we removed port mappings
- [Nginx Docker Network Setup](./NGINX_DOCKER_NETWORK_SETUP.md) - Manual nginx alternative
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - General deployment
- [Deployment Fixes](./DEPLOYMENT_FIXES.md) - Troubleshooting

---

**Last Updated**: 2025-10-27
**Status**: ✅ Ready for NPM Configuration
**NPM Version**: Works with Nginx-Proxy-Manager-Official (any recent version)
