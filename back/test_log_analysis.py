#!/usr/bin/env python3
"""Test script for Postfix log analysis functionality.

This script demonstrates the log parser by analyzing a sample log file.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api.services.postfix_log_parser import PostfixLogParser, analyze_postfix_logs


# Sample Postfix log data from actual mailserver
SAMPLE_LOG = """2025-12-13T08:47:18.849735-05:00 mail postfix/postscreen[1080]: CONNECT from [91.92.240.37]:60382 to [172.30.0.2]:25
2025-12-13T08:47:18.916443-05:00 mail postfix/postscreen[1080]: PREGREET 11 after 0.07 from [91.92.240.37]:60382: EHLO User\\r\\n
2025-12-13T08:47:19.053214-05:00 mail postfix/postscreen[1080]: DISCONNECT [91.92.240.37]:60382
2025-12-13T08:59:29.692713-05:00 mail postfix/postscreen[3018]: CONNECT from [91.92.240.6]:64385 to [172.30.0.2]:25
2025-12-13T08:59:29.760812-05:00 mail postfix/postscreen[3018]: PREGREET 11 after 0.07 from [91.92.240.6]:64385: EHLO User\\r\\n
2025-12-13T08:59:29.902756-05:00 mail postfix/postscreen[3018]: DISCONNECT [91.92.240.6]:64385
2025-12-13T09:01:22.947843-05:00 mail postfix/postscreen[3018]: CONNECT from [3.134.148.59]:40782 to [172.30.0.2]:25
2025-12-13T09:01:22.948087-05:00 mail postfix/postscreen[3018]: PREGREET 186 after 0 from [3.134.148.59]:40782: GET / HTTP/1.1\\r\\nHost: 45.80.25.57:25\\r\\nUser-Agent: cypex.ai/scanning
2025-12-13T09:01:22.948178-05:00 mail postfix/postscreen[3018]: NON-SMTP COMMAND from [3.134.148.59]:40782 after CONNECT: GET / HTTP/1.1
2025-12-13T09:01:22.948208-05:00 mail postfix/postscreen[3018]: DISCONNECT [3.134.148.59]:40782
2025-12-13T09:11:55.918671-05:00 mail postfix/postscreen[5035]: CONNECT from [91.92.240.37]:53080 to [172.30.0.2]:25
2025-12-13T09:11:55.986448-05:00 mail postfix/postscreen[5035]: PREGREET 11 after 0.07 from [91.92.240.37]:53080: EHLO User\\r\\n
2025-12-13T09:11:56.122819-05:00 mail postfix/postscreen[5035]: DISCONNECT [91.92.240.37]:53080
2025-12-13T09:12:29.152208-05:00 mail postfix/postscreen[5035]: CONNECT from [91.92.240.6]:62353 to [172.30.0.2]:25
2025-12-13T09:12:29.219680-05:00 mail postfix/postscreen[5035]: PREGREET 11 after 0.07 from [91.92.240.6]:62353: EHLO User\\r\\n
2025-12-13T09:12:29.355687-05:00 mail postfix/postscreen[5035]: DISCONNECT [91.92.240.6]:62353
2025-12-13T09:37:24.243583-05:00 mail postfix/postscreen[8867]: CONNECT from [185.196.11.30]:64844 to [172.30.0.2]:25
2025-12-13T09:37:24.281806-05:00 mail postfix/postscreen[8867]: PREGREET 11 after 0.04 from [185.196.11.30]:64844: EHLO User\\r\\n
2025-12-13T09:37:24.353741-05:00 mail postfix/postscreen[8867]: DISCONNECT [185.196.11.30]:64844
2025-12-13T09:39:39.243371-05:00 mail postfix/postscreen[8867]: CONNECT from [23.132.164.173]:60393 to [172.30.0.2]:25
2025-12-13T09:39:39.267698-05:00 mail postfix/postscreen[8867]: PREGREET 11 after 0.02 from [23.132.164.173]:60393: EHLO User\\r\\n
2025-12-13T09:39:39.347466-05:00 mail postfix/postscreen[8867]: DISCONNECT [23.132.164.173]:60393
"""


def main():
    """Test the log parser with sample data."""
    print("=" * 80)
    print("Postfix Log Analysis Test")
    print("=" * 80)
    print()

    # Create a temporary log file with sample data
    test_log_file = Path("/tmp/test_postfix.log")
    test_log_file.write_text(SAMPLE_LOG)

    print(f"📝 Created test log file: {test_log_file}")
    print(f"📊 Analyzing {len(SAMPLE_LOG.splitlines())} log lines...")
    print()

    # Parse the logs
    parser = PostfixLogParser(str(test_log_file))
    events = parser.parse_log_file(hours=24)

    print(f"🔍 Found {len(events)} security events")
    print()

    # Display events
    if events:
        print("Security Events Detected:")
        print("-" * 80)
        for i, event in enumerate(events, 1):
            print(f"\n{i}. {event.event_type.upper()}")
            print(f"   IP: {event.ip_address}")
            print(f"   Severity: {event.severity}")
            print(f"   Time: {event.timestamp}")
            print(f"   Details: {event.details}")
            print(f"   Service: {event.service}")

    print()
    print("=" * 80)
    print("Analysis Summary")
    print("=" * 80)
    print()

    # Analyze events
    analysis = parser.analyze_events(events)

    print(f"📊 Total Events: {analysis['total_events']}")
    print()

    print("Event Types:")
    for event_type, count in analysis['event_types'].items():
        print(f"  - {event_type}: {count}")
    print()

    print("Severity Breakdown:")
    for severity, count in analysis['severity_breakdown'].items():
        print(f"  - {severity.upper()}: {count}")
    print()

    print(f"🔝 Top {len(analysis['top_offenders'])} Offending IPs:")
    for offender in analysis['top_offenders']:
        print(f"  - {offender['ip']}: {offender['count']} events")
    print()

    if analysis['recommendations']:
        print("⚠️  Security Recommendations:")
        for rec in analysis['recommendations']:
            print(f"\n  [{rec['severity'].upper()}] {rec['category']}")
            print(f"  {rec['message']}")
            if rec.get('action'):
                print(f"  Action: {rec['action']}")
    print()

    # Timeline
    if analysis['timeline']:
        print("📈 Event Timeline:")
        for time_key, count in sorted(analysis['timeline'].items()):
            print(f"  {time_key}: {count} events")
    print()

    print("=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80)

    # Cleanup
    test_log_file.unlink()


if __name__ == "__main__":
    main()
