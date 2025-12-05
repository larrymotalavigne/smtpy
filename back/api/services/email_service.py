"""Email service for sending transactional emails via Docker mailserver."""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import aiosmtplib

from shared.core.config import SETTINGS

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails through Docker mailserver."""

    @staticmethod
    async def _send_email(
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email using Docker mailserver.

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (fallback)
            from_email: Sender email (defaults to EMAIL_FROM)
            from_name: Sender name (defaults to EMAIL_FROM_NAME)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not SETTINGS.EMAIL_ENABLED:
            logger.info(f"Email sending disabled. Would have sent: {subject} to {to}")
            return True

        from_email = from_email or SETTINGS.EMAIL_FROM
        from_name = from_name or SETTINGS.EMAIL_FROM_NAME
        sender = f"{from_name} <{from_email}>" if from_name else from_email

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = to

            # Add text version
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                message.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html", "utf-8")
            message.attach(part2)

            # Send via Docker mailserver
            await aiosmtplib.send(
                message,
                hostname=SETTINGS.MAILSERVER_HOST,
                port=SETTINGS.MAILSERVER_PORT,
                username=SETTINGS.MAILSERVER_USER if SETTINGS.MAILSERVER_USER else None,
                password=SETTINGS.MAILSERVER_PASSWORD if SETTINGS.MAILSERVER_PASSWORD else None,
                use_tls=SETTINGS.MAILSERVER_USE_TLS,
                start_tls=SETTINGS.MAILSERVER_USE_TLS,
            )

            logger.info(f"Email sent successfully to {to}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    @staticmethod
    async def send_password_reset_email(
        to: str,
        username: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email.

        Args:
            to: Recipient email address
            username: Username
            reset_token: Password reset token

        Returns:
            True if sent successfully
        """
        reset_url = f"{SETTINGS.APP_URL}/auth/reset-password?token={reset_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Password Reset Request</h2>
                <p>Hello {username},</p>
                <p>You requested to reset your password for your SMTPy account.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}"
                       style="background-color: #3498db; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #7f8c8d;">{reset_url}</p>
                <p style="margin-top: 30px; color: #7f8c8d; font-size: 14px;">
                    This link will expire in 1 hour. If you didn't request this, you can safely ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                <p style="color: #95a5a6; font-size: 12px;">
                    SMTPy - Email Aliasing Service
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        Hello {username},

        You requested to reset your password for your SMTPy account.

        Click this link to reset your password:
        {reset_url}

        This link will expire in 1 hour. If you didn't request this, you can safely ignore this email.

        ---
        SMTPy - Email Aliasing Service
        """

        return await EmailService._send_email(
            to=to,
            subject="Password Reset Request - SMTPy",
            html_content=html_content,
            text_content=text_content
        )

    @staticmethod
    async def send_email_verification(
        to: str,
        username: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification email.

        Args:
            to: Recipient email address
            username: Username
            verification_token: Email verification token

        Returns:
            True if sent successfully
        """
        verification_url = f"{SETTINGS.APP_URL}/auth/verify-email?token={verification_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Welcome to SMTPy!</h2>
                <p>Hello {username},</p>
                <p>Thanks for signing up! Please verify your email address to complete your registration.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}"
                       style="background-color: #27ae60; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #7f8c8d;">{verification_url}</p>
                <p style="margin-top: 30px; color: #7f8c8d; font-size: 14px;">
                    This link will expire in 24 hours.
                </p>
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                <p style="color: #95a5a6; font-size: 12px;">
                    SMTPy - Email Aliasing Service
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to SMTPy!

        Hello {username},

        Thanks for signing up! Please verify your email address to complete your registration.

        Click this link to verify your email:
        {verification_url}

        This link will expire in 24 hours.

        ---
        SMTPy - Email Aliasing Service
        """

        return await EmailService._send_email(
            to=to,
            subject="Verify Your Email - SMTPy",
            html_content=html_content,
            text_content=text_content
        )
