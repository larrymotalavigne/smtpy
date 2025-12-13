# Postfix Log Analysis

## Overview

SMTPy includes comprehensive Postfix mail server log analysis to detect and track security threats. The system automatically parses Postfix logs to identify:

- **PREGREET violations** - Spam bots sending commands before server greeting
- **Failed authentication attempts** - Brute force attacks
- **Email rejections** - Spam/malware blocks
- **DNS blocklist hits** - Known malicious IPs
- **Suspicious connection patterns** - Port scanning, protocol abuse

## Architecture

### Components

1. **Log Parser Service** (`api/services/postfix_log_parser.py`)
   - Parses Postfix log files using regex patterns
   - Extracts security events with timestamps, IPs, and details
   - Generates analysis reports and recommendations

2. **Database Model** (`shared/models/security_event.py`)
   - Stores security events for historical tracking
   - Indexes for fast querying by IP, type, severity, timestamp
   - Supports pagination and filtering

3. **Admin API Endpoints** (`api/views/admin_view.py`)
   - `/admin/security/logs/analyze` - Analyze logs in real-time
   - `/admin/security/events` - Query stored security events
   - `/admin/security/stats` - Security statistics dashboard

## Security Events

### Event Types

| Type | Description | Severity |
|------|-------------|----------|
| `pregreet_violation` | Client sends SMTP commands before greeting | High |
| `auth_failure` | SASL authentication failed | Medium |
| `rejection` | Email rejected by Postfix | Medium-High |
| `dnsbl_hit` | IP found in DNS blocklist | High |
| `spam_detected` | Spam detected by filters | Medium |
| `malware_detected` | Malware found in attachment | Critical |

### Severity Levels

- **Low** - Informational, no action needed
- **Medium** - Monitor, may require action
- **High** - Security threat, consider blocking
- **Critical** - Active attack, immediate action required

## API Usage

### Analyze Logs in Real-Time

```bash
# Analyze last 24 hours of logs
curl -X GET "http://localhost:8000/admin/security/logs/analyze?hours=24" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Analyze with line limit for performance
curl -X GET "http://localhost:8000/admin/security/logs/analyze?hours=48&max_lines=10000" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_period_hours": 24,
    "total_events": 156,
    "event_types": {
      "pregreet_violation": 142,
      "auth_failure": 8,
      "rejection": 6
    },
    "severity_breakdown": {
      "high": 142,
      "medium": 14
    },
    "top_offenders": [
      {
        "ip": "91.92.240.37",
        "count": 45,
        "events": [...]
      }
    ],
    "timeline": {
      "2025-12-13 08:00": 23,
      "2025-12-13 09:00": 31,
      ...
    },
    "recommendations": [
      {
        "severity": "high",
        "category": "firewall",
        "message": "IP 91.92.240.37 has 45 security events. Consider blocking at firewall level.",
        "action": "iptables -A INPUT -s 91.92.240.37 -j DROP"
      }
    ]
  }
}
```

### Query Stored Security Events

```bash
# Get recent events with pagination
curl -X GET "http://localhost:8000/admin/security/events?page=1&page_size=50" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Filter by event type
curl -X GET "http://localhost:8000/admin/security/events?event_type=pregreet_violation" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Filter by severity and time window
curl -X GET "http://localhost:8000/admin/security/events?severity=high&hours=24" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Filter by specific IP address
curl -X GET "http://localhost:8000/admin/security/events?ip_address=91.92.240.37" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Get Security Statistics

```bash
# Get stats for last 24 hours
curl -X GET "http://localhost:8000/admin/security/stats?hours=24" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Get stats for last 7 days
curl -X GET "http://localhost:8000/admin/security/stats?hours=168" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "time_window_hours": 24,
    "total_events": 156,
    "event_types": {
      "pregreet_violation": 142,
      "auth_failure": 14
    },
    "severity_breakdown": {
      "high": 142,
      "medium": 14
    },
    "top_offending_ips": [
      {"ip": "91.92.240.37", "count": 45},
      {"ip": "91.92.240.6", "count": 38},
      ...
    ]
  }
}
```

## Log File Configuration

### Docker Mailserver Integration

The log parser expects logs at `/var/log/mail/mail.log`. In production, mount the mailserver logs to the API container:

```yaml
# docker-compose.prod.yml
api:
  volumes:
    - mailserver_logs:/var/log/mail:ro  # Read-only access to mail logs
```

### Supported Log Formats

The parser supports both Docker Mailserver log formats:

1. **ISO 8601 with timezone** (default):
   ```
   2025-12-13T09:48:20.816552-05:00 mail postfix/postscreen[10883]: PREGREET...
   ```

2. **Syslog format**:
   ```
   Dec 13 09:48:20 mail postfix/postscreen[10883]: PREGREET...
   ```

## Performance Considerations

### Log File Size

For large log files, use the `max_lines` parameter to limit processing:

```bash
# Process only the last 50,000 lines
curl -X GET "http://localhost:8000/admin/security/logs/analyze?max_lines=50000"
```

### Database Storage

Security events are stored in the `security_events` table with indexes on:
- `event_timestamp` - Fast time-based queries
- `ip_address, event_type` - IP threat analysis
- `severity, event_timestamp` - High-priority event queries

### Recommended Maintenance

```sql
-- Delete old security events (older than 90 days)
DELETE FROM security_events WHERE event_timestamp < NOW() - INTERVAL '90 days';

-- Vacuum table to reclaim space
VACUUM ANALYZE security_events;
```

## Security Recommendations

Based on log analysis, the system generates actionable recommendations:

### High-Frequency Attacks
When an IP has >10 events:
```bash
# Block at firewall level
iptables -A INPUT -s 91.92.240.37 -j DROP

# Or use fail2ban
fail2ban-client set postfix-pregreet banip 91.92.240.37
```

### PREGREET Violations (>50)
Postscreen is working correctly, consider:
- Enable DNSBL checks in Postfix
- Increase postscreen greet delay
- Enable fail2ban for persistent offenders

### Authentication Failures (>20)
Possible brute-force attack:
- Enable fail2ban for postfix-sasl
- Review user passwords
- Consider 2FA for email accounts

## Testing

Test the log parser with sample data:

```bash
cd back
uv run python test_log_analysis.py
```

The test script demonstrates:
- Log parsing and event extraction
- Event analysis and statistics
- Top offenders identification
- Security recommendations

## Migration

Apply the database migration to create the `security_events` table:

```bash
cd back
alembic upgrade head
```

Migration file: `migrations/versions/008_add_security_events_table.py`

## Monitoring Integration

### Grafana Dashboard

Create alerts for security events:

```sql
-- High-severity events in last hour
SELECT COUNT(*) FROM security_events
WHERE severity = 'high'
  AND event_timestamp > NOW() - INTERVAL '1 hour';

-- Top 10 attacking IPs today
SELECT ip_address, COUNT(*) as count
FROM security_events
WHERE event_timestamp > DATE_TRUNC('day', NOW())
GROUP BY ip_address
ORDER BY count DESC
LIMIT 10;
```

### Alerting

Set up alerts for critical events:

```python
# Example: Send alert for >100 PREGREET violations/hour
if event_types.get('pregreet_violation', 0) > 100:
    send_alert(
        severity='high',
        message=f'High PREGREET attack volume: {count} events in last hour'
    )
```

## Example: Real-World Analysis

From actual mailserver logs (December 13, 2025):

```
Total Events: 156
├── PREGREET violations: 142 (91%)
├── Auth failures: 8 (5%)
└── Rejections: 6 (4%)

Top Attacking IPs:
1. 91.92.240.37 (45 events) - PREGREET bot
2. 91.92.240.6 (38 events) - PREGREET bot
3. 3.134.148.59 (12 events) - cypex.ai scanner
4. 185.196.11.30 (8 events) - PREGREET bot
5. 23.132.164.173 (7 events) - PREGREET bot

Recommendations:
→ Block 91.92.240.37 and 91.92.240.6 at firewall (persistent attackers)
→ Postscreen is working correctly (all PREGREET attacks blocked)
→ Consider enabling DNSBL checks for additional protection
```

## Future Enhancements

Planned features:
- [ ] Automatic IP blocking integration
- [ ] GeoIP lookup for threat intelligence
- [ ] Machine learning for anomaly detection
- [ ] Real-time log streaming with WebSockets
- [ ] Integration with threat intelligence feeds
- [ ] Custom alert rules and notifications
- [ ] Export reports (PDF, CSV)

## Troubleshooting

### Log File Not Found

```
Error: Mail log file not found. Ensure mailserver logs are accessible.
```

**Solution:** Mount mailserver logs to API container:
```yaml
volumes:
  - mailserver_logs:/var/log/mail:ro
```

### Permission Denied

**Solution:** Ensure API container has read permissions:
```bash
docker exec mailserver chmod -R 755 /var/log/mail
```

### No Events Detected

Check:
1. Log file format matches expected patterns
2. Time window is correct (logs may be older than `hours` parameter)
3. Log level in Postfix is sufficient (should be `info` or `debug`)

## References

- [Postfix Postscreen Documentation](http://www.postfix.org/POSTSCREEN_README.html)
- [Docker Mailserver](https://docker-mailserver.github.io/)
- [SMTP Security Best Practices](https://www.rfc-editor.org/rfc/rfc7817.html)
