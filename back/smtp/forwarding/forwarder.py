import logging
import smtplib
from email.message import EmailMessage
from typing import List, Optional
import dkim

from shared.core.config import SETTINGS

SMTP_HOST = SETTINGS.SMTP_HOST
SMTP_PORT = SETTINGS.SMTP_PORT

logger = logging.getLogger(__name__)


def forward_email(
        original_msg: EmailMessage,
        targets: List[str],
        mail_from: str = "noreply@localhost",
        dkim_private_key: Optional[str] = None,
        dkim_selector: str = "default",
        dkim_domain: Optional[str] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = False,
        use_ssl: bool = False
):
    """
    Forward the email to the target addresses with DKIM signing and SMTP authentication support.

    Args:
        original_msg: Original email message to forward
        targets: List of recipient email addresses
        mail_from: SMTP envelope sender address
        dkim_private_key: Optional DKIM private key in PEM format for signing
        dkim_selector: DKIM selector for signing (default: 'default')
        dkim_domain: Domain for DKIM signing (extracted from mail_from if not provided)
        smtp_username: Optional SMTP username for authentication
        smtp_password: Optional SMTP password for authentication
        use_tls: Use STARTTLS after connecting
        use_ssl: Use SMTP_SSL instead of SMTP

    Raises:
        smtplib.SMTPException: If email forwarding fails
    """
    # Build the forwarded message
    msg = EmailMessage()

    # Handle plain or html body, fallback to get_content()
    body_part = original_msg.get_body(preferencelist=("plain", "html"))
    if body_part is not None:
        msg.set_content(body_part.get_content())
    else:
        try:
            msg.set_content(original_msg.get_content())
        except Exception as e:
            logger.warning(f"Failed to get email content: {e}")
            msg.set_content("(Email content could not be forwarded)")

    # Set headers
    msg["Subject"] = original_msg.get("Subject", "(No Subject)")
    # Preserve original visible From header; use mail_from only as SMTP envelope sender
    msg["From"] = original_msg.get("From", mail_from)
    msg["To"] = ", ".join(targets)

    # Add forwarding headers
    msg["X-Forwarded-By"] = "SMTPy Email Forwarder"
    msg["X-Original-To"] = original_msg.get("To", "")

    # Copy other headers, but avoid MIME structural headers to prevent duplicates
    skip_headers = {
        "From", "To", "Subject", "Content-Type", "Content-Transfer-Encoding",
        "MIME-Version", "X-Forwarded-By", "X-Original-To"
    }
    for k, v in original_msg.items():
        if k not in skip_headers:
            # Avoid adding duplicate header fields
            if k not in msg:
                msg[k] = v

    # Handle attachments
    if original_msg.is_multipart():
        try:
            for part in original_msg.iter_attachments():
                msg.add_attachment(
                    part.get_content(),
                    maintype=part.get_content_maintype(),
                    subtype=part.get_content_subtype(),
                    filename=part.get_filename(),
                )
        except Exception as e:
            logger.warning(f"Failed to process attachments: {e}")

    # DKIM Signing (if enabled)
    if dkim_private_key:
        try:
            # Extract domain from mail_from if not provided
            if not dkim_domain:
                dkim_domain = mail_from.split('@')[-1] if '@' in mail_from else None

            if dkim_domain:
                # Convert message to bytes for DKIM signing
                msg_bytes = msg.as_bytes()

                # Sign the message
                signature = dkim.sign(
                    message=msg_bytes,
                    selector=dkim_selector.encode(),
                    domain=dkim_domain.encode(),
                    privkey=dkim_private_key.encode(),
                    include_headers=[b'from', b'to', b'subject', b'date']
                )

                # Add DKIM signature header
                msg['DKIM-Signature'] = signature.decode().split(': ', 1)[1]
                logger.info(f"DKIM signature added for domain {dkim_domain}")
            else:
                logger.warning("DKIM signing requested but domain could not be determined")
        except Exception as e:
            logger.error(f"DKIM signing failed: {e}")
            # Continue without DKIM signature rather than failing

    # Send the email
    try:
        # Choose SMTP class based on SSL setting
        smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP

        with smtp_class(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            # Enable debug logging in development
            if not SETTINGS.is_production:
                smtp.set_debuglevel(1)

            # Use STARTTLS if requested (not needed if using SMTP_SSL)
            if use_tls and not use_ssl:
                smtp.starttls()

            # Authenticate if credentials provided
            if smtp_username and smtp_password:
                try:
                    smtp.login(smtp_username, smtp_password)
                    logger.info(f"SMTP authentication successful for {smtp_username}")
                except smtplib.SMTPAuthenticationError as e:
                    logger.error(f"SMTP authentication failed: {e}")
                    raise

            # Send the message
            smtp.send_message(msg, from_addr=mail_from, to_addrs=targets)
            logger.info(f"Successfully forwarded email to {len(targets)} recipient(s) via {SMTP_HOST}:{SMTP_PORT}")

    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"All recipients refused: {e}")
        raise
    except smtplib.SMTPSenderRefused as e:
        logger.error(f"Sender refused: {e}")
        raise
    except smtplib.SMTPDataError as e:
        logger.error(f"SMTP data error: {e}")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error while forwarding email: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while forwarding email: {e}")
        raise
