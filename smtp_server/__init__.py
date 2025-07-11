from aiosmtpd.controller import Controller
from .handler import SMTPHandler
import logging

logger = logging.getLogger("smtpy.smtp_server")

def start_smtp_server(host="127.0.0.1", port=1025):
    """
    Start the SMTP server. For production, use host='0.0.0.0' and a configurable port.
    """
    handler = SMTPHandler()
    controller = Controller(handler, hostname=host, port=port)
    controller.start()
    logger.info(f"SMTP server started on {host}:{port}")
    print(f"SMTP server running on {host}:{port}")
    return controller 