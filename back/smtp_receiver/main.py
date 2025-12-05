"""Main entry point for SMTP receiver service."""

import asyncio
import logging
from aiosmtpd.controller import Controller

from shared.core.config import SETTINGS
from .handler import SMTPHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Start the SMTP receiver server."""
    handler = SMTPHandler()

    controller = Controller(
        handler,
        hostname=SETTINGS.SMTP_RECEIVER_HOST,
        port=SETTINGS.SMTP_RECEIVER_PORT,
    )

    logger.info(
        f"Starting SMTP receiver on {SETTINGS.SMTP_RECEIVER_HOST}:{SETTINGS.SMTP_RECEIVER_PORT}"
    )

    controller.start()

    try:
        # Keep running
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down SMTP receiver...")
        controller.stop()


if __name__ == "__main__":
    asyncio.run(main())
