# Mail Server Testing Commands

Quick reference for testing mail.smtpy.fr manually.

## DNS Tests

### 1. Check A Record (IP Address)
```bash
dig +short A mail.smtpy.fr
# Expected: 45.80.25.57 (or your server IP)
```

### 2. Check Reverse DNS (PTR Record)
```bash
dig -x 45.80.25.57 +short
# Expected: mail.smtpy.fr.
```

### 3. Check MX Record
```bash
dig +short MX smtpy.fr
# Expected: Priority and mail.smtpy.fr
```

### 4. Check SPF Record
```bash
dig +short TXT smtpy.fr | grep spf
# Expected: "v=spf1 ip4:45.80.25.57 ~all" or similar
```

### 5. Check DMARC Record
```bash
dig +short TXT _dmarc.smtpy.fr
# Expected: "v=DMARC1; p=quarantine; ..."
```

### 6. Check DKIM Record
```bash
dig +short TXT default._domainkey.smtpy.fr
# Expected: "v=DKIM1; k=rsa; p=..." (if configured)
```

## SMTP Connectivity Tests

### 7. Test Port 25 with netcat
```bash
nc -zv mail.smtpy.fr 25
# Expected: Connection succeeded
```

### 8. Test Port 25 with telnet
```bash
telnet mail.smtpy.fr 25
# Commands to test:
# EHLO test.com
# QUIT
```

### 9. Get SMTP Banner
```bash
echo "QUIT" | nc mail.smtpy.fr 25
# Expected: 220 mail.smtpy.fr ESMTP ...
```

### 10. Test STARTTLS Support
```bash
echo "EHLO test.com" | openssl s_client -starttls smtp -connect mail.smtpy.fr:25 -brief
# Look for: 250-STARTTLS
```

### 11. Full SMTP Session Test
```bash
openssl s_client -starttls smtp -connect mail.smtpy.fr:25 -crlf -quiet
# After connection:
EHLO test.com
MAIL FROM:<test@example.com>
RCPT TO:<alias@smtpy.fr>
DATA
Subject: Test Email

This is a test.
.
QUIT
```

## Docker Container Tests

### 12. Check if SMTP container is running
```bash
docker ps | grep smtp
```

### 13. Check SMTP container logs
```bash
docker logs smtpy-smtp-prod --tail 100 -f
```

### 14. Test internal SMTP port (from host)
```bash
nc -zv localhost 1025
# Should work from the server, but NOT be publicly accessible
```

### 15. Execute command in SMTP container
```bash
docker exec -it smtpy-smtp-prod python -c "import socket; s=socket.socket(); s.connect(('localhost', 1025)); print('SMTP port accessible')"
```

## Email Deliverability Tests

### 16. Test with mail-tester.com
1. Visit: https://www.mail-tester.com/
2. Send a test email to the provided address from your mail server
3. Check the score and recommendations

### 17. Check Blacklist Status
```bash
# Visit these URLs and enter your IP (45.80.25.57)
# - https://mxtoolbox.com/blacklists.aspx
# - https://multirbl.valli.org/lookup/
# - https://www.spamhaus.org/lookup/
```

### 18. MXToolbox Comprehensive Check
```bash
# Visit: https://mxtoolbox.com/SuperTool.aspx
# Enter: mail.smtpy.fr
# Run SMTP Test, DNS Test, Blacklist Check
```

## Performance Tests

### 19. DNS Resolution Time
```bash
dig mail.smtpy.fr | grep "Query time"
# Good: < 100ms, Acceptable: < 500ms
```

### 20. SMTP Connection Time
```bash
time echo "QUIT" | nc mail.smtpy.fr 25
# Should be < 5 seconds
```

## Troubleshooting Commands

### 21. Check firewall rules (on server)
```bash
sudo ufw status | grep 25
# Should show: 25/tcp ALLOW
```

### 22. Check if port 25 is listening (on server)
```bash
sudo netstat -tlnp | grep :25
# or
sudo ss -tlnp | grep :25
```

### 23. Check DNS propagation
```bash
# Use multiple DNS servers
dig @8.8.8.8 mail.smtpy.fr +short
dig @1.1.1.1 mail.smtpy.fr +short
dig @8.8.4.4 mail.smtpy.fr +short
```

### 24. Trace route to mail server
```bash
traceroute mail.smtpy.fr
```

### 25. Check SSL/TLS certificate (if applicable)
```bash
openssl s_client -connect mail.smtpy.fr:25 -starttls smtp -showcerts
```

## Full Test Script

Run the comprehensive test script:
```bash
./test-mail-smtpy.sh
```

## Expected Results Summary

### DNS Records
- **A Record**: mail.smtpy.fr → 45.80.25.57 ✓
- **PTR Record**: 45.80.25.57 → mail.smtpy.fr ✓
- **MX Record**: smtpy.fr → mail.smtpy.fr ✓
- **SPF**: v=spf1 ip4:45.80.25.57 ~all ✓
- **DMARC**: v=DMARC1; p=quarantine; ... ✓
- **DKIM**: v=DKIM1; k=rsa; p=... ✓ (after setup)

### Ports
- **Port 25**: Open (SMTP) ✓
- **Port 587**: Optional (Submission)
- **Port 1025**: Internal only (not public) ✓

### SMTP Features
- **STARTTLS**: Supported ✓
- **EHLO Response**: Shows capabilities ✓
- **Banner**: 220 mail.smtpy.fr ESMTP ✓

## Quick Health Check (One-liner)

```bash
echo "A Record:" && dig +short A mail.smtpy.fr && \
echo "PTR Record:" && dig -x 45.80.25.57 +short && \
echo "MX Record:" && dig +short MX smtpy.fr && \
echo "Port 25:" && nc -zv mail.smtpy.fr 25 2>&1 | tail -1
```

## Continuous Monitoring

```bash
# Watch SMTP logs in real-time
docker logs -f smtpy-smtp-prod

# Monitor port 25
watch -n 5 'nc -zv mail.smtpy.fr 25 2>&1'
```

## Notes

- Replace `45.80.25.57` with your actual server IP if different
- Some tests require root/sudo access on the server
- DNS changes can take 24-48 hours to propagate fully
- Check logs in `docker logs smtpy-smtp-prod` for detailed error messages
