from aiosmtpd.handlers import AsyncMessage
from email.message import EmailMessage
import logging
from utils.db import get_session, get_async_session
from database.models import Domain, Alias, ActivityLog
from forwarding.forwarder import forward_email
from utils.validation import validate_email, ValidationError
from utils.soft_delete import get_active_domains, get_active_aliases
import re
from datetime import datetime

logger = logging.getLogger("smtpy.smtp_handler")

class SMTPHandler(AsyncMessage):
    def __init__(self):
        super().__init__()

    async def resolve_targets(self, recipient: str):
        # Validate and sanitize the recipient email address
        try:
            recipient = validate_email(recipient.strip())
        except ValidationError as e:
            logger.warning(f"Invalid recipient email format: {recipient} - {e}")
            return []
        
        # Parse the validated email address
        match = re.match(r"([^@]+)@(.+)", recipient)
        if not match:
            return []
        local, domain_name = match.groups()
        
        now = datetime.utcnow()
        async with get_async_session() as session:
            # Use async queries with proper await
            from sqlalchemy import select
            
            # Find active domain
            domain_query = select(Domain).where(
                Domain.name == domain_name,
                Domain.is_deleted == False
            )
            domain_result = await session.execute(domain_query)
            domain = domain_result.scalar_one_or_none()
            
            if not domain:
                return []
            
            # Find active alias for this domain and local part
            alias_query = select(Alias).where(
                Alias.domain_id == domain.id,
                Alias.local_part == local,
                Alias.is_deleted == False
            )
            alias_result = await session.execute(alias_query)
            alias = alias_result.scalar_one_or_none()
            
            if alias and (alias.expires_at is None or alias.expires_at > now):
                # Validate each target email address
                validated_targets = []
                for target in alias.targets.split(","):
                    target = target.strip()
                    if target:
                        try:
                            validated_target = validate_email(target)
                            validated_targets.append(validated_target)
                        except ValidationError as e:
                            logger.warning(f"Invalid target email in alias: {target} - {e}")
                return validated_targets
            
            if domain.catch_all:
                try:
                    validated_catch_all = validate_email(domain.catch_all)
                    return [validated_catch_all]
                except ValidationError as e:
                    logger.warning(f"Invalid catch-all email: {domain.catch_all} - {e}")
        
        return []

    async def log_activity(self, event_type, sender, recipient, subject, status, message):
        async with get_async_session() as session:
            log = ActivityLog(
                event_type=event_type,
                sender=sender,
                recipient=recipient,
                subject=subject,
                status=status,
                message=message
            )
            session.add(log)
            await session.commit()

    async def handle_message(self, message: EmailMessage) -> None:
        sender_raw = message.get("From", "")
        recipients_raw = message.get_all("To", []) or []
        subject = message.get("Subject", "(No Subject)")
        
        # Validate and sanitize sender email address
        sender = ""
        if sender_raw:
            try:
                sender = validate_email(sender_raw.strip())
            except ValidationError as e:
                logger.warning(f"Invalid sender email format: {sender_raw} - {e}")
                sender = sender_raw.strip()  # Keep original for logging but mark as invalid
        
        # Validate and sanitize recipient email addresses
        recipients = []
        for recipient_raw in recipients_raw:
            if recipient_raw:
                try:
                    recipient = validate_email(recipient_raw.strip())
                    recipients.append(recipient)
                except ValidationError as e:
                    logger.warning(f"Invalid recipient email format: {recipient_raw} - {e}")
                    # Skip invalid recipients
        
        logger.info(f"Received email from {sender} to {recipients} with subject '{subject}'")

        all_targets = set()
        for r in recipients:
            targets = await self.resolve_targets(r)
            if targets:
                all_targets.update(targets)
            else:
                logger.warning(f"No valid target for recipient {r}")
                await self.log_activity(
                    event_type="bounce",
                    sender=sender,
                    recipient=r,
                    subject=subject,
                    status="failed",
                    message="No valid target for recipient"
                )

        if not all_targets:
            logger.warning(f"No valid recipients for message from {sender} to {recipients}")
            logger.info(f"Rejected email: No valid recipients in {recipients}", extra={
                "sender": sender,
                "recipients": recipients,
                "subject": subject,
                "action": "reject"
            })
            await self.log_activity(
                event_type="bounce",
                sender=sender,
                recipient=", ".join(recipients),
                subject=subject,
                status="failed",
                message="No valid recipients"
            )
            return  # Reject message

        # Forward email to all resolved targets
        try:
            forward_email(message, list(all_targets), mail_from="noreply@localhost")
            logger.info(f"Email forwarded successfully", extra={
                "sender": sender,
                "targets": list(all_targets),
                "subject": subject,
                "action": "forward"
            })
            for target in all_targets:
                await self.log_activity(
                    event_type="forward",
                    sender=sender,
                    recipient=target,
                    subject=subject,
                    status="success",
                    message="Email forwarded successfully"
                )
        except Exception as e:
            logger.error(f"Failed to forward email: {e}", extra={
                "sender": sender,
                "targets": list(all_targets),
                "subject": subject,
                "error": str(e),
                "action": "forward_failed"
            })
            for target in all_targets:
                await self.log_activity(
                    event_type="error",
                    sender=sender,
                    recipient=target,
                    subject=subject,
                    status="failed",
                    message=str(e)
                )