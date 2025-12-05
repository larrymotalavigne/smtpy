"""SMTP handler for processing incoming emails from Docker mailserver."""

import logging
import email
from email import policy
from email.parser import BytesParser
from typing import Optional
from aiosmtpd.smtp import SMTP as SMTPServer, Envelope, Session
import aiosmtplib
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.core.config import SETTINGS
from shared.models.message import Message, MessageStatus
from shared.models.alias import Alias
from shared.models.domain import Domain

logger = logging.getLogger(__name__)


class SMTPHandler:
    """Handler for processing incoming SMTP messages."""

    def __init__(self):
        """Initialize SMTP handler with database connection."""
        # Create async engine for database operations
        self.engine = create_async_engine(SETTINGS.DATABASE_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def handle_DATA(self, server: SMTPServer, session: Session, envelope: Envelope):
        """
        Handle incoming email data from mailserver.

        Args:
            server: SMTP server instance
            session: SMTP session
            envelope: Email envelope with mail_from, rcpt_tos, and content

        Returns:
            '250 OK' on success, error message otherwise
        """
        try:
            # Parse email
            message = BytesParser(policy=policy.default).parsebytes(envelope.content)

            sender = envelope.mail_from
            recipients = envelope.rcpt_tos

            logger.info(f"Received email from {sender} to {recipients}")

            # Process each recipient
            for recipient in recipients:
                await self._process_recipient(sender, recipient, envelope.content)

            return "250 Message accepted for delivery"

        except Exception as e:
            logger.error(f"Error handling email: {str(e)}")
            return f"451 Requested action aborted: error processing message - {str(e)}"

    async def _process_recipient(self, sender: str, recipient: str, raw_content: bytes):
        """
        Process email for a specific recipient (check aliases and forward).

        Args:
            sender: Sender email address
            recipient: Recipient email address
            raw_content: Raw email content
        """
        async with self.async_session() as session:
            try:
                # Extract domain from recipient
                if "@" not in recipient:
                    logger.warning(f"Invalid recipient format: {recipient}")
                    return

                local_part, domain_name = recipient.split("@", 1)

                # Check if domain exists in our system
                from sqlalchemy import select
                domain_result = await session.execute(
                    select(Domain).where(Domain.name == domain_name.lower())
                )
                domain = domain_result.scalar_one_or_none()

                if not domain:
                    logger.info(f"Domain {domain_name} not found in system, skipping")
                    return

                # Check for catch-all first
                forward_to = None
                if domain.catch_all_email:
                    forward_to = domain.catch_all_email
                    logger.info(f"Using catch-all address: {forward_to}")
                else:
                    # Look up alias
                    alias_result = await session.execute(
                        select(Alias).where(
                            Alias.domain_id == domain.id,
                            Alias.local_part == local_part.lower(),
                            Alias.is_deleted == False
                        )
                    )
                    alias = alias_result.scalar_one_or_none()

                    if alias:
                        forward_to = alias.forward_to
                        logger.info(f"Found alias: {recipient} -> {forward_to}")
                    else:
                        logger.info(f"No alias found for {recipient}")
                        # Store as received but not forwarded
                        await self._store_message(
                            session, sender, recipient, raw_content, None,
                            MessageStatus.REJECTED, "No alias found"
                        )
                        return

                # Forward the email
                if forward_to:
                    success = await self._forward_email(sender, forward_to, raw_content)

                    # Store message
                    await self._store_message(
                        session, sender, recipient, raw_content, forward_to,
                        MessageStatus.DELIVERED if success else MessageStatus.FAILED,
                        None if success else "Failed to forward email"
                    )

            except Exception as e:
                logger.error(f"Error processing recipient {recipient}: {str(e)}")

    async def _forward_email(self, sender: str, forward_to: str, raw_content: bytes) -> bool:
        """
        Forward email via Docker mailserver.

        Args:
            sender: Original sender
            forward_to: Destination address
            raw_content: Original email content

        Returns:
            True if forwarded successfully
        """
        try:
            # Parse original message
            message = BytesParser(policy=policy.default).parsebytes(raw_content)

            # Add forwarding headers
            message.add_header("X-Forwarded-By", "SMTPy")
            message.add_header("X-Original-To", message.get("To", ""))

            # Update To header
            del message["To"]
            message["To"] = forward_to

            # Send via mailserver
            await aiosmtplib.send(
                message,
                hostname=SETTINGS.MAILSERVER_HOST,
                port=SETTINGS.MAILSERVER_PORT,
                username=SETTINGS.MAILSERVER_USER if SETTINGS.MAILSERVER_USER else None,
                password=SETTINGS.MAILSERVER_PASSWORD if SETTINGS.MAILSERVER_PASSWORD else None,
                use_tls=SETTINGS.MAILSERVER_USE_TLS,
                start_tls=SETTINGS.MAILSERVER_USE_TLS,
            )

            logger.info(f"Successfully forwarded email to {forward_to}")
            return True

        except Exception as e:
            logger.error(f"Failed to forward email to {forward_to}: {str(e)}")
            return False

    async def _store_message(
        self,
        session: AsyncSession,
        sender: str,
        recipient: str,
        raw_content: bytes,
        forwarded_to: Optional[str],
        status: MessageStatus,
        error_message: Optional[str]
    ):
        """Store message in database."""
        try:
            # Parse message for metadata
            parsed = BytesParser(policy=policy.default).parsebytes(raw_content)

            subject = str(parsed.get("Subject", ""))[:500]
            message_id = parsed.get("Message-ID", f"<generated-{hash(raw_content)}@smtpy.local>")

            # Get domain
            domain_name = recipient.split("@")[1] if "@" in recipient else ""
            from sqlalchemy import select
            domain_result = await session.execute(
                select(Domain).where(Domain.name == domain_name.lower())
            )
            domain = domain_result.scalar_one_or_none()

            if not domain:
                logger.warning(f"Cannot store message: domain {domain_name} not found")
                return

            # Create message record
            message = Message(
                message_id=message_id,
                domain_id=domain.id,
                sender_email=sender[:320],
                recipient_email=recipient[:320],
                subject=subject,
                body_preview=None,  # Could extract body preview here
                status=status,
                error_message=error_message,
                size_bytes=len(raw_content),
                has_attachments=any(part.get_content_disposition() == "attachment"
                                   for part in parsed.walk())
            )

            session.add(message)
            await session.commit()

            logger.info(f"Stored message: {message_id}")

        except Exception as e:
            logger.error(f"Failed to store message: {str(e)}")
            await session.rollback()
