import logging
import smtplib
from email.message import EmailMessage

from config import SETTINGS

logger = logging.getLogger("smtpy.forwarder")

SMTP_HOST = SETTINGS.SMTP_HOST
SMTP_PORT = SETTINGS.SMTP_PORT


# TODO: Add support for SMTP authentication if needed


def forward_email(
        original_msg: EmailMessage, targets, mail_from="noreply@localhost"
):  # mail_from should be a valid sender
    """
    Forward the email to the target addresses, rewriting MAIL FROM as needed.
    Preserves headers and attachments.
    """
    msg = EmailMessage()
    # Handle plain or html body, fallback to get_content()
    body_part = original_msg.get_body(preferencelist=("plain", "html"))
    if body_part is not None:
        msg.set_content(body_part.get_content())
    else:
        msg.set_content(original_msg.get_content())
    msg["Subject"] = original_msg.get("Subject", "")
    # Preserve original visible From header; use mail_from only as SMTP envelope sender
    msg["From"] = original_msg.get("From", mail_from)
    msg["To"] = ", ".join(targets)
    # Copy other headers, but avoid MIME structural headers to prevent duplicates
    skip_headers = {"From", "To", "Subject", "Content-Type", "Content-Transfer-Encoding", "MIME-Version"}
    for k, v in original_msg.items():
        if k not in skip_headers:
            # Avoid adding duplicate header fields
            if k not in msg:
                msg[k] = v
    # Attachments
    if original_msg.is_multipart():
        for part in original_msg.iter_attachments():
            msg.add_attachment(
                part.get_content(),
                maintype=part.get_content_maintype(),
                subtype=part.get_content_subtype(),
                filename=part.get_filename(),
            )
    # TODO: DKIM sign here if enabled
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.send_message(msg, from_addr=mail_from, to_addrs=targets)
        logger.info(f"Forwarded email to {targets} via {SMTP_HOST}:{SMTP_PORT}")
    except Exception as e:
        logger.error(f"Failed to forward email: {e}")
        raise
