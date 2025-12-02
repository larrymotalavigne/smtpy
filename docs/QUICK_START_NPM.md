# Quick Start: SMTPy with Nginx Proxy Manager

**For**: Unraid users with Nginx-Proxy-Manager-Official
**Time**: ~5 minutes after deployment completes

## Step 1: Wait for Deployment

After pushing to GitHub, the CI/CD pipeline will deploy automatically. Monitor at:
https://github.com/larrymotalavigne/smtpy/actions

Wait until all containers are running:
```bash
docker ps | grep smtpy
```

You should see:
- `smtpy-front`
- `smtpy-api-1`
- `smtpy-api-2`
- `smtpy-smtp-prod`
- `smtpy-db-prod`
- `smtpy-redis-prod`

## Step 2: Connect NPM to SMTPy Network (One-Time)

```bash
# SSH into your Unraid server

# Find your NPM container name
docker ps | grep nginx-proxy-manager
# Example output: Nginx-Proxy-Manager-Official

# Connect NPM to SMTPy Docker network
docker network connect smtpy_smtpy-network Nginx-Proxy-Manager-Official

# Verify (should show both NPM and SMTPy containers)
docker network inspect smtpy_smtpy-network
```

## Step 3: Create Proxy Host in NPM

1. **Open NPM**: `http://<unraid-ip>:81`
2. **Login** with your NPM credentials
3. **Navigate**: Hosts → Proxy Hosts → "Add Proxy Host"

### Configuration:

**Details Tab**:
```
Domain Names:      smtpy.fr
                   www.smtpy.fr

Scheme:            http
Forward Host/IP:   smtpy-front
Forward Port:      80

☑ Cache Assets
☑ Block Common Exploits
☑ Websockets Support
```

**SSL Tab**:
```
SSL Certificate:   Request a New SSL Certificate

☑ Force SSL
☑ HTTP/2 Support
☑ HSTS Enabled

Email:             your-email@example.com
☑ I Agree to the Let's Encrypt Terms of Service
```

**Click "Save"**

## Step 4: Verify

```bash
# Test from NPM container
docker exec Nginx-Proxy-Manager-Official curl http://smtpy-front:80
docker exec Nginx-Proxy-Manager-Official curl http://smtpy-api-1:8000/health

# Test external access
curl https://smtpy.fr/
curl https://smtpy.fr/health
```

Open browser: `https://smtpy.fr`

## Done! 🎉

Your SMTPy application is now live at `https://smtpy.fr` with:
- ✅ Automatic SSL certificate from Let's Encrypt
- ✅ Load balancing across 2 API instances
- ✅ No port conflicts with other Unraid apps
- ✅ Secure internal Docker networking

## Troubleshooting

### "502 Bad Gateway"

Check containers are running:
```bash
docker ps | grep smtpy
```

Check NPM can reach containers:
```bash
docker exec Nginx-Proxy-Manager-Official ping smtpy-front
```

### "Could not resolve host"

Reconnect NPM to network:
```bash
docker network connect smtpy_smtpy-network Nginx-Proxy-Manager-Official
docker restart Nginx-Proxy-Manager-Official
```

### SSL Certificate Failed

Check DNS is pointing to your server:
```bash
nslookup smtpy.fr
```

Ensure ports 80/443 are forwarded to your Unraid server.

## Full Documentation

See [NGINX_PROXY_MANAGER_SETUP.md](./NGINX_PROXY_MANAGER_SETUP.md) for detailed configuration options, security hardening, and advanced features.

---

**Last Updated**: 2025-10-27
