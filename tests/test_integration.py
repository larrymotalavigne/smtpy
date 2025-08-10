"""Integration tests for email forwarding functionality."""

import pytest
import asyncio
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from smtp_server.handler import SMTPHandler
from database.models import User, Domain, Alias, ActivityLog
from utils.db import get_db
from forwarding.forwarder import forward_email


class TestEmailForwardingIntegration:
    """Integration tests for email forwarding functionality."""

    def setup_method(self):
        """Set up test fixtures for each test."""
        import uuid

        self.test_id = str(uuid.uuid4())[:8]
        self.handler = SMTPHandler()

        # Create test data with unique identifiers
        with get_db() as session:
            # Create test user
            self.test_user = User(
                username=f"testuser_{self.test_id}",
                email=f"testuser_{self.test_id}@example.com",
                hashed_password="hashed_password",
                is_active=True,
                email_verified=True,
            )
            session.add(self.test_user)
            session.commit()
            session.refresh(self.test_user)

            # Create test domain
            self.test_domain = Domain(
                name=f"test{self.test_id}.example.com",
                owner_id=self.test_user.id,
                catch_all="catchall@external.com",
            )
            session.add(self.test_domain)
            session.commit()
            session.refresh(self.test_domain)

            # Create test alias
            self.test_alias = Alias(
                local_part="forward",
                targets="target1@external.com, target2@external.com",
                domain_id=self.test_domain.id,
                owner_id=self.test_user.id,
            )
            session.add(self.test_alias)
            session.commit()
            session.refresh(self.test_alias)

    def teardown_method(self):
        """Clean up test data after each test."""
        with get_db() as session:
            # Clean up in reverse order of creation
            session.query(Alias).filter_by(domain_id=self.test_domain.id).delete()
            session.query(Domain).filter_by(id=self.test_domain.id).delete()
            session.query(User).filter_by(id=self.test_user.id).delete()
            session.query(ActivityLog).filter(ActivityLog.sender.like(f"%{self.test_id}%")).delete()
            session.commit()

    @pytest.mark.asyncio
    async def test_resolve_targets_with_valid_alias(self):
        """Test resolving targets for a valid alias."""
        targets = await self.handler.resolve_targets(f"forward@{self.test_domain.name}")

        assert len(targets) == 2
        assert "target1@external.com" in targets
        assert "target2@external.com" in targets

    @pytest.mark.asyncio
    async def test_resolve_targets_with_catch_all(self):
        """Test resolving targets using catch-all when no alias exists."""
        targets = await self.handler.resolve_targets(f"nonexistent@{self.test_domain.name}")

        assert len(targets) == 1
        assert "catchall@external.com" in targets

    @pytest.mark.asyncio
    async def test_resolve_targets_with_invalid_domain(self):
        """Test resolving targets for invalid domain."""
        targets = await self.handler.resolve_targets("test@invalid.domain.com")

        assert len(targets) == 0

    @pytest.mark.asyncio
    async def test_resolve_targets_with_expired_alias(self):
        """Test resolving targets for expired alias falls back to catch-all."""
        # Create expired alias
        with get_db() as session:
            expired_alias = Alias(
                local_part="expired",
                targets="expired@external.com",
                domain_id=self.test_domain.id,
                owner_id=self.test_user.id,
                expires_at=datetime.utcnow() - timedelta(days=1),
            )
            session.add(expired_alias)
            session.commit()

        targets = await self.handler.resolve_targets(f"expired@{self.test_domain.name}")

        # Should fall back to catch-all
        assert len(targets) == 1
        assert "catchall@external.com" in targets

    @pytest.mark.asyncio
    async def test_resolve_targets_with_invalid_email_format(self):
        """Test resolving targets with invalid email format."""
        targets = await self.handler.resolve_targets("invalid-email-format")

        assert len(targets) == 0

    @pytest.mark.asyncio
    async def test_resolve_targets_with_invalid_target_emails(self):
        """Test resolving targets when alias has invalid target emails."""
        # Create alias with invalid targets
        with get_db() as session:
            invalid_alias = Alias(
                local_part="invalid",
                targets="valid@external.com, invalid-email, another@valid.com",
                domain_id=self.test_domain.id,
                owner_id=self.test_user.id,
            )
            session.add(invalid_alias)
            session.commit()

        targets = await self.handler.resolve_targets(f"invalid@{self.test_domain.name}")

        # Should only return valid targets
        assert len(targets) == 2
        assert "valid@external.com" in targets
        assert "another@valid.com" in targets
        assert "invalid-email" not in targets

    @pytest.mark.asyncio
    async def test_log_activity(self):
        """Test activity logging functionality."""
        await self.handler.log_activity(
            event_type="test",
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Subject",
            status="success",
            message="Test message",
        )

        # Verify log was created
        with get_db() as session:
            log = session.query(ActivityLog).filter_by(event_type="test").first()
            assert log is not None
            assert log.sender == "sender@example.com"
            assert log.recipient == "recipient@example.com"
            assert log.subject == "Test Subject"
            assert log.status == "success"
            assert log.message == "Test message"

    @pytest.mark.asyncio
    @patch("forwarding.forwarder.forward_email")
    async def test_handle_message_successful_forwarding(self, mock_forward):
        """Test successful email forwarding through handle_message."""
        # Create test email message
        message = EmailMessage()
        message["From"] = "sender@external.com"
        message["To"] = "forward@test.example.com"
        message["Subject"] = "Test Email"
        message.set_content("This is a test email.")

        # Mock successful forwarding
        mock_forward.return_value = None

        # Handle the message
        await self.handler.handle_message(message)

        # Verify forward_email was called with correct parameters
        mock_forward.assert_called_once()
        call_args = mock_forward.call_args
        assert len(call_args[0][1]) == 2  # Two targets
        assert "target1@external.com" in call_args[0][1]
        assert "target2@external.com" in call_args[0][1]

        # Verify activity logs were created
        with get_db() as session:
            forward_logs = session.query(ActivityLog).filter_by(event_type="forward").all()
            assert len(forward_logs) == 2  # One for each target

            for log in forward_logs:
                assert log.sender == "sender@external.com"
                assert log.subject == "Test Email"
                assert log.status == "success"
                assert log.recipient in ["target1@external.com", "target2@external.com"]

    @pytest.mark.asyncio
    @patch("forwarding.forwarder.forward_email")
    async def test_handle_message_forwarding_failure(self, mock_forward):
        """Test email forwarding failure handling."""
        # Create test email message
        message = EmailMessage()
        message["From"] = "sender@external.com"
        message["To"] = "forward@test.example.com"
        message["Subject"] = "Test Email"
        message.set_content("This is a test email.")

        # Mock forwarding failure
        mock_forward.side_effect = Exception("SMTP connection failed")

        # Handle the message
        await self.handler.handle_message(message)

        # Verify error logs were created
        with get_db() as session:
            error_logs = session.query(ActivityLog).filter_by(event_type="error").all()
            assert len(error_logs) == 2  # One for each target

            for log in error_logs:
                assert log.sender == "sender@external.com"
                assert log.subject == "Test Email"
                assert log.status == "failed"
                assert "SMTP connection failed" in log.message

    @pytest.mark.asyncio
    async def test_handle_message_no_valid_recipients(self):
        """Test handling message with no valid recipients."""
        # Create test email message to invalid domain
        message = EmailMessage()
        message["From"] = "sender@external.com"
        message["To"] = "test@invalid.domain.com"
        message["Subject"] = "Test Email"
        message.set_content("This is a test email.")

        # Handle the message
        await self.handler.handle_message(message)

        # Verify bounce log was created
        with get_db() as session:
            bounce_logs = session.query(ActivityLog).filter_by(event_type="bounce").all()
            assert len(bounce_logs) >= 1

            bounce_log = bounce_logs[0]
            assert bounce_log.sender == "sender@external.com"
            assert bounce_log.subject == "Test Email"
            assert bounce_log.status == "failed"
            assert "No valid" in bounce_log.message

    @pytest.mark.asyncio
    async def test_handle_message_catch_all_forwarding(self):
        """Test email forwarding using catch-all domain."""
        # Create test email message to non-existent alias
        message = EmailMessage()
        message["From"] = "sender@external.com"
        message["To"] = "nonexistent@test.example.com"
        message["Subject"] = "Test Email"
        message.set_content("This is a test email.")

        with patch("forwarding.forwarder.forward_email") as mock_forward:
            mock_forward.return_value = None

            # Handle the message
            await self.handler.handle_message(message)

            # Verify forward_email was called with catch-all target
            mock_forward.assert_called_once()
            call_args = mock_forward.call_args
            assert len(call_args[0][1]) == 1  # One catch-all target
            assert "catchall@external.com" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_handle_message_multiple_recipients(self):
        """Test handling message with multiple recipients."""
        # Create test email message with multiple recipients
        message = EmailMessage()
        message["From"] = "sender@external.com"
        message["To"] = "forward@test.example.com, nonexistent@test.example.com"
        message["Subject"] = "Test Email"
        message.set_content("This is a test email.")

        with patch("forwarding.forwarder.forward_email") as mock_forward:
            mock_forward.return_value = None

            # Handle the message
            await self.handler.handle_message(message)

            # Verify forward_email was called with all targets
            mock_forward.assert_called_once()
            call_args = mock_forward.call_args
            targets = call_args[0][1]

            # Should include alias targets + catch-all
            assert len(targets) == 3
            assert "target1@external.com" in targets
            assert "target2@external.com" in targets
            assert "catchall@external.com" in targets

    @pytest.mark.asyncio
    async def test_handle_message_invalid_sender_email(self):
        """Test handling message with invalid sender email format."""
        # Create test email message with invalid sender
        message = EmailMessage()
        message["From"] = "invalid-sender-format"
        message["To"] = "forward@test.example.com"
        message["Subject"] = "Test Email"
        message.set_content("This is a test email.")

        with patch("forwarding.forwarder.forward_email") as mock_forward:
            mock_forward.return_value = None

            # Handle the message (should still work)
            await self.handler.handle_message(message)

            # Verify forwarding still occurred
            mock_forward.assert_called_once()

            # Verify activity logs use original sender for logging
            with get_db() as session:
                forward_logs = session.query(ActivityLog).filter_by(event_type="forward").all()
                assert len(forward_logs) == 2

                for log in forward_logs:
                    assert log.sender == "invalid-sender-format"  # Original kept for logging

    @pytest.mark.asyncio
    async def test_handle_message_invalid_recipient_emails(self):
        """Test handling message with some invalid recipient emails."""
        # Create test email message with mixed valid/invalid recipients
        message = EmailMessage()
        message["From"] = "sender@external.com"
        message["To"] = "forward@test.example.com, invalid-recipient-format"
        message["Subject"] = "Test Email"
        message.set_content("This is a test email.")

        with patch("forwarding.forwarder.forward_email") as mock_forward:
            mock_forward.return_value = None

            # Handle the message
            await self.handler.handle_message(message)

            # Verify forward_email was called only for valid recipients
            mock_forward.assert_called_once()
            call_args = mock_forward.call_args
            targets = call_args[0][1]

            # Should only include targets from valid recipient
            assert len(targets) == 2
            assert "target1@external.com" in targets
            assert "target2@external.com" in targets


class TestEmailForwardingEndToEnd:
    """End-to-end integration tests for complete email forwarding workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create test data similar to above
        with get_db() as session:
            self.test_user = User(
                username="e2euser",
                email="e2euser@example.com",
                hashed_password="hashed_password",
                is_active=True,
                email_verified=True,
            )
            session.add(self.test_user)
            session.commit()
            session.refresh(self.test_user)

            self.test_domain = Domain(name="e2e.example.com", owner_id=self.test_user.id)
            session.add(self.test_domain)
            session.commit()
            session.refresh(self.test_domain)

            self.test_alias = Alias(
                local_part="test",
                targets="final@destination.com",
                domain_id=self.test_domain.id,
                owner_id=self.test_user.id,
            )
            session.add(self.test_alias)
            session.commit()

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_complete_email_forwarding_workflow(self, mock_smtp_class):
        """Test complete email forwarding from SMTP handler to final delivery."""
        # Mock SMTP client
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        mock_smtp.send_message.return_value = {}

        # Create and handle email message
        handler = SMTPHandler()
        message = EmailMessage()
        message["From"] = "external@sender.com"
        message["To"] = "test@e2e.example.com"
        message["Subject"] = "End-to-End Test"
        message.set_content("This is an end-to-end test email.")

        # Process the message
        await handler.handle_message(message)

        # Verify SMTP client was used for forwarding
        mock_smtp_class.assert_called_once()
        mock_smtp.send_message.assert_called_once()

        # Verify the forwarded message
        forwarded_message = mock_smtp.send_message.call_args[0][0]
        assert forwarded_message["Subject"] == "End-to-End Test"
        assert forwarded_message["From"] == "external@sender.com"
        assert "final@destination.com" in forwarded_message["To"]

        # Verify activity was logged
        with get_db() as session:
            activity_logs = (
                session.query(ActivityLog)
                .filter_by(sender="external@sender.com", recipient="final@destination.com")
                .all()
            )
            assert len(activity_logs) >= 1

            success_log = next((log for log in activity_logs if log.event_type == "forward"), None)
            assert success_log is not None
            assert success_log.status == "success"
            assert success_log.subject == "End-to-End Test"
