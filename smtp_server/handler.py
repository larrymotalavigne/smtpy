from aiosmtpd.handlers import AsyncMessage
from email.message import EmailMessage
import logging
from utils.db import get_session
from database.models import Domain, Alias, ActivityLog
from forwarding.forwarder import forward_email
import re
from datetime import datetime

logger = logging.getLogger("smtpy.smtp_handler")

class SMTPHandler(AsyncMessage):
    def __init__(self):
        super().__init__()

    def resolve_targets(self, recipient: str):
        match = re.match(r"([^@]+)@(.+)", recipient)
        if not match:
            return []
        local, domain_name = match.groups()
        now = datetime.utcnow()
        with get_session() as session:
            domain = session.query(Domain).filter_by(name=domain_name).first()
            if not domain:
                return []
            alias = session.query(Alias).filter_by(domain_id=domain.id, local_part=local).first()
            if alias and (alias.expires_at is None or alias.expires_at > now):
                return [a.strip() for a in alias.targets.split(",") if a.strip()]
            if domain.catch_all:
                return [domain.catch_all]
        return []

    def log_activity(self, event_type, sender, recipient, subject, status, message):
        with get_session() as session:
            log = ActivityLog(
                event_type=event_type,
                sender=sender,
                recipient=recipient,
                subject=subject,
                status=status,
                message=message
            )
            session.add(log)
            session.commit()

    async def handle_message(self, message: EmailMessage) -> None:
        sender = message.get("From", "")
        recipients = message.get_all("To", [])
        subject = message.get("Subject", "(No Subject)")
        logger.info(f"Received email from {sender} to {recipients} with subject '{subject}'")

        all_targets = set()
        for r in recipients:
            targets = self.resolve_targets(r)
            if targets:
                all_targets.update(targets)
            else:
                logger.warning(f"No valid target for recipient {r}")
                self.log_activity(
                    event_type="bounce",
                    sender=sender,
                    recipient=r,
                    subject=subject,
                    status="failed",
                    message="No valid target for recipient"
                )

        if not all_targets:
            logger.warning(f"No valid recipients for message from {sender} to {recipients}")
            print(f"Rejected email: No valid recipients in {recipients}")
            self.log_activity(
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
            print(f"Email forwarded: From={sender}, To={list(all_targets)}, Subject={subject}")
            for target in all_targets:
                self.log_activity(
                    event_type="forward",
                    sender=sender,
                    recipient=target,
                    subject=subject,
                    status="success",
                    message="Email forwarded successfully"
                )
        except Exception as e:
            logger.error(f"Failed to forward email: {e}")
            print(f"Failed to forward email: {e}")
            for target in all_targets:
                self.log_activity(
                    event_type="error",
                    sender=sender,
                    recipient=target,
                    subject=subject,
                    status="failed",
                    message=str(e)
                ) 