"""Structured JSON logging configuration for SMTPy API."""
import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from shared.core.config import SETTINGS


def setup_logging() -> None:
    """Configure JSON structured logging for the application."""
    # Create JSON formatter
    log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"

    if SETTINGS.is_production:
        # Production: JSON logs to stdout
        formatter = JsonFormatter(log_format)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        log_level = logging.INFO
    else:
        # Development: Human-readable logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        log_level = logging.DEBUG if SETTINGS.DEBUG else logging.INFO

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Application logger
    app_logger = logging.getLogger("smtpy")
    app_logger.setLevel(log_level)

    logging.info(
        "Logging configured",
        extra={
            "environment": "production" if SETTINGS.is_production else "development",
            "log_level": logging.getLevelName(log_level),
            "format": "json" if SETTINGS.is_production else "text"
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"smtpy.{name}")
