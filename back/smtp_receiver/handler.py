"""SMTP handler for processing incoming emails from Docker mailserver."""

import logging
import email
from email import policy
from email.parser import BytesParser
from typing import Optional, List, Tuple
from aiosmtpd.smtp import SMTP as SMTPServer, Envelope, Session
import aiosmtplib
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from shared.core.config import SETTINGS
from shared.models.message import Message, MessageStatus
from shared.models.alias import Alias
from shared.models.domain import Domain
from shared.models.user import User
from shared.models.user_preferences import UserPreferences
from shared.models.forwarding_rule import ForwardingRule, RuleConditionType, RuleActionType
from api.services.email_service import EmailService

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

    async def _evaluate_rule(
        self,
        rule: ForwardingRule,
        sender: str,
        subject: str,
        message_size: int,
        has_attachments: bool
    ) -> bool:
        """
        Evaluate if a forwarding rule matches the current message.

        Args:
            rule: The forwarding rule to evaluate
            sender: Sender email address
            subject: Email subject
            message_size: Size of message in bytes
            has_attachments: Whether message has attachments

        Returns:
            True if rule matches, False otherwise
        """
        try:
            condition_value = rule.condition_value.lower() if rule.condition_value else ""

            if rule.condition_type == RuleConditionType.SENDER_CONTAINS:
                return condition_value in sender.lower()

            elif rule.condition_type == RuleConditionType.SENDER_EQUALS:
                return sender.lower() == condition_value

            elif rule.condition_type == RuleConditionType.SENDER_DOMAIN:
                sender_domain = sender.split('@')[-1].lower() if '@' in sender else ''
                return sender_domain == condition_value

            elif rule.condition_type == RuleConditionType.SUBJECT_CONTAINS:
                return condition_value in subject.lower()

            elif rule.condition_type == RuleConditionType.SUBJECT_EQUALS:
                return subject.lower() == condition_value

            elif rule.condition_type == RuleConditionType.SIZE_GREATER_THAN:
                try:
                    threshold = int(rule.condition_value)
                    return message_size > threshold
                except ValueError:
                    logger.error(f"Invalid size threshold: {rule.condition_value}")
                    return False

            elif rule.condition_type == RuleConditionType.SIZE_LESS_THAN:
                try:
                    threshold = int(rule.condition_value)
                    return message_size < threshold
                except ValueError:
                    logger.error(f"Invalid size threshold: {rule.condition_value}")
                    return False

            elif rule.condition_type == RuleConditionType.HAS_ATTACHMENTS:
                expected = rule.condition_value.lower() in ('true', '1', 'yes')
                return has_attachments == expected

            return False

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {str(e)}")
            return False

    async def _apply_forwarding_rules(
        self,
        session: AsyncSession,
        alias: Alias,
        sender: str,
        subject: str,
        message_size: int,
        has_attachments: bool
    ) -> Tuple[Optional[str], bool]:
        """
        Apply forwarding rules to determine target address(es).

        Args:
            session: Database session
            alias: The alias receiving the email
            sender: Sender email address
            subject: Email subject
            message_size: Size of message in bytes
            has_attachments: Whether message has attachments

        Returns:
            Tuple of (target_addresses, should_block)
            - target_addresses: Comma-separated email addresses or None if using default
            - should_block: True if email should be blocked
        """
        # Fetch active rules for this alias, ordered by priority
        rules_result = await session.execute(
            select(ForwardingRule)
            .where(
                ForwardingRule.alias_id == alias.id,
                ForwardingRule.is_active == True
            )
            .order_by(ForwardingRule.priority.asc())
        )
        rules = rules_result.scalars().all()

        if not rules:
            # No rules, use default alias targets
            return (alias.targets, False)

        # Evaluate rules in priority order
        for rule in rules:
            if await self._evaluate_rule(rule, sender, subject, message_size, has_attachments):
                # Rule matched! Increment match counter
                rule.match_count += 1
                await session.commit()

                logger.info(f"Rule '{rule.name}' matched for alias {alias.id}")

                if rule.action_type == RuleActionType.BLOCK:
                    return (None, True)

                elif rule.action_type == RuleActionType.FORWARD:
                    # Use default alias targets
                    return (alias.targets, False)

                elif rule.action_type == RuleActionType.REDIRECT:
                    # Use rule's custom targets
                    if rule.action_value:
                        return (rule.action_value, False)
                    else:
                        logger.warning(f"Rule {rule.id} has REDIRECT action but no action_value")
                        return (alias.targets, False)

        # No rules matched, use default targets
        return (alias.targets, False)

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
        Process email for a specific recipient (check aliases, apply rules, and forward).

        Args:
            sender: Sender email address
            recipient: Recipient email address
            raw_content: Raw email content
        """
        async with self.async_session() as session:
            try:
                # Parse message early to extract metadata
                parsed_message = BytesParser(policy=policy.default).parsebytes(raw_content)
                subject = str(parsed_message.get("Subject", ""))[:500]
                message_size = len(raw_content)
                has_attachments = any(
                    part.get_content_disposition() == "attachment"
                    for part in parsed_message.walk()
                )

                # Extract domain from recipient
                if "@" not in recipient:
                    logger.warning(f"Invalid recipient format: {recipient}")
                    return

                local_part, domain_name = recipient.split("@", 1)

                # Check if domain exists in our system
                domain_result = await session.execute(
                    select(Domain).where(Domain.name == domain_name.lower())
                )
                domain = domain_result.scalar_one_or_none()

                if not domain:
                    logger.info(f"Domain {domain_name} not found in system, skipping")
                    return

                # Get domain owner's user info for notifications
                user_result = await session.execute(
                    select(User).where(User.organization_id == domain.organization_id)
                )
                user = user_result.scalar_one_or_none()

                # Check for catch-all first
                forward_targets = None
                should_block = False
                alias = None

                if domain.catch_all_email:
                    forward_targets = domain.catch_all_email
                    logger.info(f"Using catch-all address: {forward_targets}")
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
                        # Apply forwarding rules
                        forward_targets, should_block = await self._apply_forwarding_rules(
                            session, alias, sender, subject, message_size, has_attachments
                        )

                        if should_block:
                            logger.info(f"Email blocked by forwarding rule for {recipient}")
                            await self._store_message(
                                session, sender, recipient, raw_content, None,
                                MessageStatus.REJECTED, "Blocked by forwarding rule"
                            )
                            return

                        logger.info(f"Found alias: {recipient} -> {forward_targets}")
                    else:
                        logger.info(f"No alias found for {recipient}")
                        await self._store_message(
                            session, sender, recipient, raw_content, None,
                            MessageStatus.REJECTED, "No alias found"
                        )
                        return

                # Forward the email to all targets
                if forward_targets:
                    # Split comma-separated targets
                    target_list = [t.strip() for t in forward_targets.split(',') if t.strip()]

                    all_success = True
                    failed_targets = []

                    for target in target_list:
                        # Pass the domain name so the forward function can use it
                        success = await self._forward_email(sender, target, raw_content, domain_name)
                        if not success:
                            all_success = False
                            failed_targets.append(target)

                    # Store message with appropriate status
                    status = MessageStatus.DELIVERED if all_success else MessageStatus.FAILED
                    error_msg = None if all_success else f"Failed to forward to: {', '.join(failed_targets)}"

                    await self._store_message(
                        session, sender, recipient, raw_content, forward_targets,
                        status, error_msg
                    )

                    # Send notification if forwarding failed and user wants notifications
                    if not all_success and user:
                        await self._send_failed_forward_notification(
                            session, user, recipient, sender, subject, error_msg
                        )

            except Exception as e:
                logger.error(f"Error processing recipient {recipient}: {str(e)}")

    async def _forward_email(self, sender: str, forward_to: str, raw_content: bytes, alias_domain: str) -> bool:
        """
        Forward email via Docker mailserver.

        Args:
            sender: Original sender
            forward_to: Destination address
            raw_content: Original email content
            alias_domain: Domain of the alias (used for envelope sender)

        Returns:
            True if forwarded successfully
        """
        try:
            # Parse original message
            message = BytesParser(policy=policy.default).parsebytes(raw_content)

            # Add forwarding headers to preserve original information
            message.add_header("X-Forwarded-By", "SMTPy")
            message.add_header("X-Original-To", message.get("To", ""))
            message.add_header("X-Original-Sender", sender)

            # Update To header to the forward destination
            del message["To"]
            message["To"] = forward_to

            # Determine envelope sender based on authentication configuration
            # If using authenticated SMTP (e.g., SendGrid, AWS SES), use the configured sender
            # If using a local/self-hosted mailserver without auth, try postmaster@domain
            if SETTINGS.MAILSERVER_USER:
                # Using authenticated SMTP relay - use the configured sender address
                envelope_sender = SETTINGS.EMAIL_FROM
            else:
                # No authentication - try postmaster@domain which is more standard than noreply@
                # Postmaster is required by RFC 5321 and more likely to exist
                envelope_sender = f"postmaster@{alias_domain}"

            logger.info(f"Forwarding email from {sender} to {forward_to} using envelope sender {envelope_sender}")

            # Send via mailserver with explicit sender
            await aiosmtplib.send(
                message,
                sender=envelope_sender,  # Envelope sender (MAIL FROM)
                recipients=[forward_to],  # Envelope recipients (RCPT TO)
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

    async def _send_failed_forward_notification(
        self,
        session: AsyncSession,
        user: User,
        alias: str,
        sender: str,
        subject: str,
        error: str
    ):
        """
        Send notification when email forwarding fails.

        Args:
            session: Database session
            user: User to notify
            alias: Alias that received the email
            sender: Original sender email
            subject: Email subject
            error: Error message
        """
        try:
            # Check if user wants forwarding failure notifications
            prefs_result = await session.execute(
                select(UserPreferences).where(UserPreferences.user_id == user.id)
            )
            prefs = prefs_result.scalar_one_or_none()

            # Default to sending notifications if preferences don't exist
            should_notify = True
            if prefs:
                # Check if user has email_on_new_message enabled (closest match for forward failures)
                should_notify = prefs.email_on_new_message

            if should_notify:
                await EmailService.send_failed_forward_notification(
                    to=user.email,
                    username=user.username,
                    alias=alias,
                    sender=sender,
                    subject=subject,
                    error=error or "Unknown error"
                )
                logger.info(f"Sent failed forward notification to {user.email}")
            else:
                logger.info(f"Skipping notification for {user.email} (disabled in preferences)")

        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
