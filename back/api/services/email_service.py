"""Email service for sending transactional emails."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from pathlib import Path

from shared.core.config import SETTINGS

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails."""

    @staticmethod
    def _send_email(
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email using configured email backend.

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
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to

            # Attach plain text version (fallback)
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            else:
                # Create simple plain text version from HTML
                import re
                text_content = re.sub(r'<[^>]+>', '', html_content)
                msg.attach(MIMEText(text_content, "plain"))

            # Attach HTML version
            msg.attach(MIMEText(html_content, "html"))

            # Send email based on backend
            if SETTINGS.EMAIL_BACKEND == "smtp":
                return EmailService._send_via_smtp(msg, to)
            else:
                logger.warning(f"Unsupported email backend: {SETTINGS.EMAIL_BACKEND}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    @staticmethod
    def _send_via_smtp(msg: MIMEMultipart, to: str) -> bool:
        """Send email via SMTP."""
        try:
            # Connect to SMTP server
            if SETTINGS.EMAIL_SMTP_USE_SSL:
                smtp = smtplib.SMTP_SSL(
                    SETTINGS.EMAIL_SMTP_HOST,
                    SETTINGS.EMAIL_SMTP_PORT,
                    timeout=10
                )
            else:
                smtp = smtplib.SMTP(
                    SETTINGS.EMAIL_SMTP_HOST,
                    SETTINGS.EMAIL_SMTP_PORT,
                    timeout=10
                )

            # Use TLS if configured
            if SETTINGS.EMAIL_SMTP_USE_TLS and not SETTINGS.EMAIL_SMTP_USE_SSL:
                smtp.starttls()

            # Login if credentials provided
            if SETTINGS.EMAIL_SMTP_USERNAME and SETTINGS.EMAIL_SMTP_PASSWORD:
                smtp.login(SETTINGS.EMAIL_SMTP_USERNAME, SETTINGS.EMAIL_SMTP_PASSWORD)

            # Send email
            smtp.send_message(msg)
            smtp.quit()

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"SMTP error sending to {to}: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_email(
        to: str,
        username: str,
        reset_token: str,
    ) -> bool:
        """
        Send password reset email.

        Args:
            to: Recipient email address
            username: User's username
            reset_token: Password reset token

        Returns:
            True if email sent successfully
        """
        reset_link = f"{SETTINGS.APP_URL}/auth/reset-password?token={reset_token}"

        subject = "Reset Your SMTPy Password"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">SMTPy</h1>
    </div>

    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #667eea; margin-top: 0;">Password Reset Request</h2>

        <p>Hello <strong>{username}</strong>,</p>

        <p>We received a request to reset your SMTPy account password. Click the button below to create a new password:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}"
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white;
                      padding: 14px 30px;
                      text-decoration: none;
                      border-radius: 5px;
                      display: inline-block;
                      font-weight: bold;">
                Reset Password
            </a>
        </div>

        <p style="color: #666; font-size: 14px;">
            If the button doesn't work, copy and paste this link into your browser:
            <br>
            <a href="{reset_link}" style="color: #667eea; word-break: break-all;">{reset_link}</a>
        </p>

        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; color: #856404; font-size: 14px;">
                <strong>⚠️ Security Notice:</strong> This link will expire in <strong>1 hour</strong>.
                If you didn't request this password reset, you can safely ignore this email.
            </p>
        </div>

        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            Need help? Reply to this email or visit our support center.
        </p>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">

        <p style="color: #999; font-size: 12px; text-align: center;">
            You received this email because a password reset was requested for your SMTPy account.
            <br>
            © {2025} SMTPy. All rights reserved.
        </p>
    </div>
</body>
</html>
        """

        text_content = f"""
SMTPy - Password Reset Request

Hello {username},

We received a request to reset your SMTPy account password.

Reset your password by clicking this link:
{reset_link}

⚠️ Security Notice:
This link will expire in 1 hour. If you didn't request this password reset, you can safely ignore this email.

Need help? Reply to this email or visit our support center.

© {2025} SMTPy. All rights reserved.
        """

        return EmailService._send_email(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    @staticmethod
    def send_email_verification(
        to: str,
        username: str,
        verification_token: str,
    ) -> bool:
        """
        Send email verification email.

        Args:
            to: Recipient email address
            username: User's username
            verification_token: Email verification token

        Returns:
            True if email sent successfully
        """
        verification_link = f"{SETTINGS.APP_URL}/auth/verify-email?token={verification_token}"

        subject = "Verify Your SMTPy Email Address"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">SMTPy</h1>
    </div>

    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #667eea; margin-top: 0;">Verify Your Email Address</h2>

        <p>Hello <strong>{username}</strong>,</p>

        <p>Welcome to SMTPy! To get started with managing your email domains and aliases, please verify your email address by clicking the button below:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_link}"
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white;
                      padding: 14px 30px;
                      text-decoration: none;
                      border-radius: 5px;
                      display: inline-block;
                      font-weight: bold;">
                Verify Email Address
            </a>
        </div>

        <p style="color: #666; font-size: 14px;">
            If the button doesn't work, copy and paste this link into your browser:
            <br>
            <a href="{verification_link}" style="color: #667eea; word-break: break-all;">{verification_link}</a>
        </p>

        <div style="background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; color: #0c5460; font-size: 14px;">
                <strong>ℹ️ Note:</strong> This verification link will expire in <strong>24 hours</strong>.
            </p>
        </div>

        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            Need help getting started? Check out our <a href="{SETTINGS.APP_URL}/docs" style="color: #667eea;">documentation</a> or reply to this email.
        </p>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">

        <p style="color: #999; font-size: 12px; text-align: center;">
            You received this email because you created a SMTPy account.
            <br>
            © {2025} SMTPy. All rights reserved.
        </p>
    </div>
</body>
</html>
        """

        text_content = f"""
SMTPy - Verify Your Email Address

Hello {username},

Welcome to SMTPy! To get started with managing your email domains and aliases, please verify your email address.

Verify your email by clicking this link:
{verification_link}

ℹ️ Note: This verification link will expire in 24 hours.

Need help getting started? Check out our documentation at {SETTINGS.APP_URL}/docs or reply to this email.

© {2025} SMTPy. All rights reserved.
        """

        return EmailService._send_email(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    @staticmethod
    def send_welcome_email(
        to: str,
        username: str,
    ) -> bool:
        """
        Send welcome email after registration.

        Args:
            to: Recipient email address
            username: User's username

        Returns:
            True if email sent successfully
        """
        subject = "Welcome to SMTPy! 🎉"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to SMTPy</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🎉 Welcome to SMTPy!</h1>
    </div>

    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #667eea; margin-top: 0;">You're All Set, {username}!</h2>

        <p>Your SMTPy account is ready to go. Here's what you can do next:</p>

        <div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0;">
            <h3 style="color: #667eea; margin-top: 0; font-size: 16px;">✨ Getting Started</h3>
            <ol style="margin: 10px 0; padding-left: 20px;">
                <li style="margin: 8px 0;">Add your first domain</li>
                <li style="margin: 8px 0;">Configure DNS records for email forwarding</li>
                <li style="margin: 8px 0;">Create email aliases</li>
                <li style="margin: 8px 0;">Start forwarding emails!</li>
            </ol>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{SETTINGS.APP_URL}/dashboard"
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white;
                      padding: 14px 30px;
                      text-decoration: none;
                      border-radius: 5px;
                      display: inline-block;
                      font-weight: bold;
                      margin: 5px;">
                Go to Dashboard
            </a>

            <a href="{SETTINGS.APP_URL}/docs"
               style="background: #ffffff;
                      color: #667eea;
                      padding: 14px 30px;
                      text-decoration: none;
                      border-radius: 5px;
                      border: 2px solid #667eea;
                      display: inline-block;
                      font-weight: bold;
                      margin: 5px;">
                Read Documentation
            </a>
        </div>

        <div style="background: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; color: #004085; font-size: 14px;">
                <strong>💡 Pro Tip:</strong> Start with a test domain to familiarize yourself with the platform before adding your production domains.
            </p>
        </div>

        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            Need help? We're here for you:
        </p>
        <ul style="color: #666; font-size: 14px;">
            <li>📚 <a href="{SETTINGS.APP_URL}/docs" style="color: #667eea;">Documentation</a></li>
            <li>💬 Reply to this email for support</li>
            <li>🐛 Report issues on GitHub</li>
        </ul>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">

        <p style="color: #999; font-size: 12px; text-align: center;">
            © {2025} SMTPy. All rights reserved.
        </p>
    </div>
</body>
</html>
        """

        text_content = f"""
🎉 Welcome to SMTPy, {username}!

Your SMTPy account is ready to go. Here's what you can do next:

GETTING STARTED:
1. Add your first domain
2. Configure DNS records for email forwarding
3. Create email aliases
4. Start forwarding emails!

Visit your dashboard: {SETTINGS.APP_URL}/dashboard
Read documentation: {SETTINGS.APP_URL}/docs

💡 Pro Tip: Start with a test domain to familiarize yourself with the platform before adding your production domains.

NEED HELP?
- 📚 Documentation: {SETTINGS.APP_URL}/docs
- 💬 Reply to this email for support
- 🐛 Report issues on GitHub

© {2025} SMTPy. All rights reserved.
        """

        return EmailService._send_email(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
