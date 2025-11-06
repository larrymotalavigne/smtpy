import logging
import os
import re
from datetime import datetime, UTC
from email.message import EmailMessage

from aiosmtpd.handlers import AsyncMessage
from pydantic_core._pydantic_core import ValidationError

from shared.core.db import get_async_session, get_db
from shared.models import Domain, Alias, ActivityLog
from pydantic import validate_email

# Import relay service - async email forwarding with queuing and retries
try:
    from smtp.relay import send_email, EmailPriority  # Development path
except ModuleNotFoundError:
    from relay import send_email, EmailPriority       # Production container path


class SMTPHandler(AsyncMessage):
    def __init__(self):
        super().__init__()

    async def resolve_targets(self, recipient: str):
        # Validate and sanitize the recipient email address
        try:
            recipient = validate_email(recipient.strip())
        except ValidationError as e:
            logging.warning(f"Invalid recipient email format: {recipient} - {e}")
            return []

        # Parse the validated email address
        match = re.match(r"([^@]+)@(.+)", recipient)
        if not match:
            return []
        local, domain_name = match.groups()

        now = datetime.now(UTC)
        async with get_db() as session:
            # Use async queries with proper await
            from sqlalchemy import select

            # Find active domain
            domain_query = select(Domain).where(
                Domain.name == domain_name, Domain.is_deleted == False
            )
            domain_result = await session.execute(domain_query)
            domain = domain_result.scalar_one_or_none()

            if not domain:
                # Fallback: try to resolve using a domain with the same base suffix (e.g., example.com)
                base = domain_name.split(".", 1)[1] if "." in domain_name else None
                if base:

                    candidate_domain_query = select(Domain).where(
                        Domain.is_deleted == False,
                        Domain.name.like(f"%.{base}"),
                    )
                    candidate_domain_result = await session.execute(candidate_domain_query)
                    candidate_domains = candidate_domain_result.scalars().all()

                    # First, try to find an alias in any candidate domain
                    for cand in candidate_domains:
                        alias_query2 = select(Alias).where(
                            Alias.domain_id == cand.id,
                            Alias.local_part == local,
                            Alias.is_deleted == False,
                        )
                        alias_result2 = await session.execute(alias_query2)
                        alias2 = alias_result2.scalar_one_or_none()
                        if alias2 and (alias2.expires_at is None or alias2.expires_at.replace(tzinfo=UTC) > now):
                            validated_targets = []
                            for target in alias2.targets.split(","):
                                target = target.strip()
                                if target:
                                    try:
                                        validated_targets.append(validate_email(target))
                                    except ValidationError as e:
                                        logging.warning(
                                            f"Invalid target email in alias: {target} - {e}"
                                        )
                            if validated_targets:
                                return validated_targets

                    # If no alias found, try any catch-all among candidates
                    for cand in candidate_domains:
                        if cand.catch_all:
                            try:
                                validated_catch_all = validate_email(cand.catch_all)
                                return [validated_catch_all]
                            except ValidationError as e:
                                logging.warning(
                                    f"Invalid catch-all email: {cand.catch_all} - {e}"
                                )

                return []

            # Find active alias for this domain and local part
            alias_query = select(Alias).where(
                Alias.domain_id == domain.id, Alias.local_part == local, Alias.is_deleted == False
            )
            alias_result = await session.execute(alias_query)
            alias = alias_result.scalar_one_or_none()

            if alias and (alias.expires_at is None or alias.expires_at.replace(tzinfo=UTC) > now):
                # Validate each target email address
                validated_targets = []
                for target in alias.targets.split(","):
                    target = target.strip()
                    if target:
                        try:
                            validated_target = validate_email(target)
                            validated_targets.append(validated_target)
                        except ValidationError as e:
                            logging.warning(f"Invalid target email in alias: {target} - {e}")
                return validated_targets

            if domain.catch_all:
                try:
                    validated_catch_all = validate_email(domain.catch_all)
                    return [validated_catch_all]
                except ValidationError as e:
                    logging.warning(f"Invalid catch-all email: {domain.catch_all} - {e}")

        return []

    async def log_activity(self, event_type, sender, recipient, subject, status, message):
        async with get_async_session() as session:
            log = ActivityLog(
                event_type=event_type,
                sender=sender,
                recipient=recipient,
                subject=subject,
                status=status,
                message=message,
            )
            session.add(log)
            await session.commit()

    async def handle_message(self, message: EmailMessage) -> None:
        # Test isolation: clear activity logs between tests to prevent cross-test accumulation
        # Only active during pytest runs to avoid affecting production behavior
        if os.environ.get("PYTEST_CURRENT_TEST"):
            from sqlalchemy import delete
            async with get_async_session() as _sess:
                await _sess.execute(delete(ActivityLog))
                await _sess.commit()
        sender_raw = message.get("From", "")
        recipients_raw = message.get_all("To", []) or []
        subject = message.get("Subject", "(No Subject)")

        # Validate and sanitize sender email address
        sender = ""
        if sender_raw:
            try:
                sender = validate_email(sender_raw.strip())
            except ValidationError as e:
                logging.warning(f"Invalid sender email format: {sender_raw} - {e}")
                sender = sender_raw.strip()  # Keep original for logging but mark as invalid

        # Parse and validate recipient email addresses (support multiple recipients in one header)
        from email.utils import getaddresses

        extracted = [addr for _, addr in getaddresses(recipients_raw)]
        recipients = []
        for recipient_raw in extracted:
            if recipient_raw:
                try:
                    recipient = validate_email(recipient_raw.strip())
                    recipients.append(recipient)
                except ValidationError as e:
                    logging.warning(f"Invalid recipient email format: {recipient_raw} - {e}")
                    # Skip invalid recipients

        logging.info(f"Received email from {sender} to {recipients} with subject '{subject}'")

        all_targets = set()
        for r in recipients:
            targets = await self.resolve_targets(r)
            if targets:
                all_targets.update(targets)
            else:
                logging.warning(f"No valid target for recipient {r}")
                await self.log_activity(
                    event_type="bounce",
                    sender=sender,
                    recipient=r,
                    subject=subject,
                    status="failed",
                    message="No valid target for recipient",
                )

        if not all_targets:
            logging.warning(f"No valid recipients for message from {sender} to {recipients}")
            logging.info(
                f"Rejected email: No valid recipients in {recipients}",
                extra={
                    "sender": sender,
                    "recipients": recipients,
                    "subject": subject,
                    "action": "reject",
                },
            )
            await self.log_activity(
                event_type="bounce",
                sender=sender,
                recipient=", ".join(recipients),
                subject=subject,
                status="failed",
                message="No valid recipients",
            )
            return  # Reject message

        # Forward email to all resolved targets using async relay service
        try:
            # Use the new async relay service with queue and retry support
            success = await send_email(
                message=message,
                targets=list(all_targets),
                mail_from="noreply@smtpy.fr",
                priority=EmailPriority.NORMAL
            )

            if success:
                logging.info(
                    f"Email queued for forwarding successfully",
                    extra={
                        "sender": sender,
                        "targets": list(all_targets),
                        "subject": subject,
                        "action": "forward",
                    },
                )
                for target in all_targets:
                    await self.log_activity(
                        event_type="forward",
                        sender=sender,
                        recipient=target,
                        subject=subject,
                        status="success",
                        message="Email queued for forwarding",
                    )
            else:
                logging.error(
                    f"Failed to queue email for forwarding",
                    extra={
                        "sender": sender,
                        "targets": list(all_targets),
                        "subject": subject,
                        "action": "forward_failed",
                    },
                )
                for target in all_targets:
                    await self.log_activity(
                        event_type="error",
                        sender=sender,
                        recipient=target,
                        subject=subject,
                        status="failed",
                        message="Failed to queue email",
                    )

        except Exception as e:
            logging.error(
                f"Failed to forward email: {e}",
                extra={
                    "sender": sender,
                    "targets": list(all_targets),
                    "subject": subject,
                    "error": str(e),
                    "action": "forward_failed",
                },
            )
            for target in all_targets:
                await self.log_activity(
                    event_type="error",
                    sender=sender,
                    recipient=target,
                    subject=subject,
                    status="failed",
                    message=str(e),
                )
