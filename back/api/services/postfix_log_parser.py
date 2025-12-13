"""Postfix log parser service for security analysis.

Analyzes Postfix mail server logs to detect and categorize security threats:
- PREGREET violations (spam bots)
- Failed authentication attempts
- Connection patterns
- Blacklisted IPs
- DNS blocklist hits
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SecurityEvent:
    """Represents a security event detected in mail logs."""

    def __init__(
        self,
        event_type: str,
        timestamp: datetime,
        ip_address: str,
        details: str,
        severity: str = "medium",
        service: str = "postfix"
    ):
        self.event_type = event_type
        self.timestamp = timestamp
        self.ip_address = ip_address
        self.details = details
        self.severity = severity
        self.service = service

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "details": self.details,
            "severity": self.severity,
            "service": self.service
        }


class PostfixLogParser:
    """Parser for Postfix mail server logs."""

    # Regex patterns for different log types
    PREGREET_PATTERN = re.compile(
        r'PREGREET \d+ after [\d.]+ from \[([^\]]+)\]:(\d+): (.+)'
    )
    CONNECT_PATTERN = re.compile(
        r'CONNECT from \[([^\]]+)\]:(\d+) to \[([^\]]+)\]:(\d+)'
    )
    DISCONNECT_PATTERN = re.compile(
        r'DISCONNECT \[([^\]]+)\]:(\d+)'
    )
    REJECT_PATTERN = re.compile(
        r'reject: .+ from \[([^\]]+)\](?::(\d+))?: (.+)'
    )
    SASL_AUTH_FAIL_PATTERN = re.compile(
        r'warning: .+\[([^\]]+)\]: SASL .+ authentication failed'
    )
    DNSBL_PATTERN = re.compile(
        r'blocked using (.+); (.+) from \[([^\]]+)\]'
    )

    def __init__(self, log_path: Optional[str] = None):
        """Initialize the parser.

        Args:
            log_path: Path to Postfix log file. If None, uses default Docker Mailserver location.
        """
        self.log_path = log_path or "/var/log/mail/mail.log"

    def parse_timestamp(self, log_line: str) -> Optional[datetime]:
        """Extract timestamp from log line.

        Args:
            log_line: Raw log line

        Returns:
            Datetime object or None if parsing fails
        """
        try:
            # Docker Mailserver format: "2025-12-13T09:48:20.816552-05:00"
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2})', log_line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                # Parse ISO format with timezone
                return datetime.fromisoformat(timestamp_str)

            # Alternative format: "Dec 13 09:48:20"
            timestamp_match = re.match(r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', log_line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                # Parse with current year (syslog format doesn't include year)
                current_year = datetime.now().year
                return datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
        except Exception as e:
            logger.debug(f"Failed to parse timestamp from line: {log_line[:50]}... Error: {e}")

        return None

    def parse_pregreet(self, line: str, timestamp: datetime) -> Optional[SecurityEvent]:
        """Parse PREGREET violation.

        PREGREET occurs when a client sends SMTP commands before waiting
        for the server's greeting banner - typical spam/bot behavior.
        """
        match = self.PREGREET_PATTERN.search(line)
        if match:
            ip = match.group(1)
            port = match.group(2)
            command = match.group(3).strip()

            return SecurityEvent(
                event_type="pregreet_violation",
                timestamp=timestamp,
                ip_address=ip,
                details=f"Sent command before greeting: {command} (port {port})",
                severity="high",
                service="postfix/postscreen"
            )
        return None

    def parse_auth_failure(self, line: str, timestamp: datetime) -> Optional[SecurityEvent]:
        """Parse SASL authentication failure."""
        match = self.SASL_AUTH_FAIL_PATTERN.search(line)
        if match:
            ip = match.group(1)

            return SecurityEvent(
                event_type="auth_failure",
                timestamp=timestamp,
                ip_address=ip,
                details="SASL authentication failed",
                severity="medium",
                service="postfix/smtpd"
            )
        return None

    def parse_rejection(self, line: str, timestamp: datetime) -> Optional[SecurityEvent]:
        """Parse email rejection."""
        match = self.REJECT_PATTERN.search(line)
        if match:
            ip = match.group(1)
            port = match.group(2) or "unknown"
            reason = match.group(3)

            # Determine severity based on rejection reason
            severity = "medium"
            if "spam" in reason.lower() or "blacklist" in reason.lower():
                severity = "high"

            return SecurityEvent(
                event_type="rejection",
                timestamp=timestamp,
                ip_address=ip,
                details=f"Rejected: {reason}",
                severity=severity,
                service="postfix/smtpd"
            )
        return None

    def parse_dnsbl(self, line: str, timestamp: datetime) -> Optional[SecurityEvent]:
        """Parse DNS blocklist hit."""
        match = self.DNSBL_PATTERN.search(line)
        if match:
            blocklist = match.group(1)
            reason = match.group(2)
            ip = match.group(3)

            return SecurityEvent(
                event_type="dnsbl_hit",
                timestamp=timestamp,
                ip_address=ip,
                details=f"Blocked by {blocklist}: {reason}",
                severity="high",
                service="postfix/smtpd"
            )
        return None

    def parse_log_file(
        self,
        hours: int = 24,
        max_lines: Optional[int] = None
    ) -> List[SecurityEvent]:
        """Parse log file and extract security events.

        Args:
            hours: Number of hours to look back (default: 24)
            max_lines: Maximum number of lines to process (None = all)

        Returns:
            List of SecurityEvent objects
        """
        events = []
        # Use UTC for timezone-aware comparison
        from datetime import timezone
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            log_file = Path(self.log_path)
            if not log_file.exists():
                logger.warning(f"Log file not found: {self.log_path}")
                return events

            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if max_lines and line_num > max_lines:
                        break

                    # Parse timestamp
                    timestamp = self.parse_timestamp(line)
                    if not timestamp:
                        continue

                    # Skip old entries
                    if timestamp < cutoff_time:
                        continue

                    # Try each parser
                    event = (
                        self.parse_pregreet(line, timestamp) or
                        self.parse_auth_failure(line, timestamp) or
                        self.parse_rejection(line, timestamp) or
                        self.parse_dnsbl(line, timestamp)
                    )

                    if event:
                        events.append(event)

        except Exception as e:
            logger.error(f"Error parsing log file {self.log_path}: {e}")

        return events

    def analyze_events(self, events: List[SecurityEvent]) -> Dict:
        """Analyze security events and generate statistics.

        Args:
            events: List of SecurityEvent objects

        Returns:
            Dictionary with analysis results
        """
        if not events:
            return {
                "total_events": 0,
                "event_types": {},
                "severity_breakdown": {},
                "top_offenders": [],
                "timeline": {},
                "recommendations": []
            }

        # Count by event type
        event_types = Counter(e.event_type for e in events)

        # Count by severity
        severity_breakdown = Counter(e.severity for e in events)

        # Count attacks per IP
        ip_counter = Counter(e.ip_address for e in events)
        top_offenders = [
            {
                "ip": ip,
                "count": count,
                "events": [e.to_dict() for e in events if e.ip_address == ip][:5]  # First 5 events
            }
            for ip, count in ip_counter.most_common(10)
        ]

        # Timeline (events per hour)
        timeline = defaultdict(int)
        for event in events:
            hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
            timeline[hour_key] += 1

        # Generate recommendations
        recommendations = self._generate_recommendations(events, event_types, ip_counter)

        return {
            "total_events": len(events),
            "event_types": dict(event_types),
            "severity_breakdown": dict(severity_breakdown),
            "top_offenders": top_offenders,
            "timeline": dict(sorted(timeline.items())),
            "recommendations": recommendations
        }

    def _generate_recommendations(
        self,
        events: List[SecurityEvent],
        event_types: Counter,
        ip_counter: Counter
    ) -> List[Dict]:
        """Generate security recommendations based on analysis."""
        recommendations = []

        # Check for high-frequency attacks from single IPs
        for ip, count in ip_counter.most_common(5):
            if count > 10:
                recommendations.append({
                    "severity": "high",
                    "category": "firewall",
                    "message": f"IP {ip} has {count} security events. Consider blocking at firewall level.",
                    "action": f"iptables -A INPUT -s {ip} -j DROP"
                })

        # Check for PREGREET attacks
        pregreet_count = event_types.get("pregreet_violation", 0)
        if pregreet_count > 50:
            recommendations.append({
                "severity": "medium",
                "category": "postscreen",
                "message": f"{pregreet_count} PREGREET violations detected. Postscreen is working correctly.",
                "action": "Continue monitoring. Consider enabling DNSBL checks if not already enabled."
            })

        # Check for auth failures
        auth_fail_count = event_types.get("auth_failure", 0)
        if auth_fail_count > 20:
            recommendations.append({
                "severity": "high",
                "category": "authentication",
                "message": f"{auth_fail_count} authentication failures. Possible brute-force attack.",
                "action": "Enable fail2ban for postfix-sasl or increase postscreen greet delay."
            })

        # General recommendation
        if len(events) > 100:
            recommendations.append({
                "severity": "medium",
                "category": "monitoring",
                "message": f"{len(events)} total security events detected.",
                "action": "Review logs regularly and ensure fail2ban is enabled and configured."
            })

        return recommendations


def analyze_postfix_logs(
    log_path: Optional[str] = None,
    hours: int = 24,
    max_lines: Optional[int] = None
) -> Dict:
    """Convenience function to parse and analyze Postfix logs.

    Args:
        log_path: Path to log file (default: /var/log/mail/mail.log)
        hours: Number of hours to analyze (default: 24)
        max_lines: Maximum lines to process (default: None = all)

    Returns:
        Dictionary with analysis results
    """
    parser = PostfixLogParser(log_path)
    events = parser.parse_log_file(hours=hours, max_lines=max_lines)
    return parser.analyze_events(events)
