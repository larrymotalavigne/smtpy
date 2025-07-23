"""Logging configuration for SMTPy."""

import logging
import logging.config
import os
import sys
from typing import Dict, Any


def get_log_level() -> str:
    """Get log level from environment variable."""
    return os.environ.get("SMTPY_LOG_LEVEL", "INFO").upper()


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    log_level = get_log_level()
    
    # Determine if we're in production
    is_production = os.environ.get("SMTPY_ENV", "development").lower() == "production"
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(name)s - %(message)s"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(filename)s %(lineno)d %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if is_production else "detailed",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json" if is_production else "detailed",
                "filename": os.environ.get("SMTPY_LOG_FILE", "smtpy.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "smtpy": {
                "level": log_level,
                "handlers": ["console", "file"] if is_production else ["console"],
                "propagate": False
            },
            "smtpy.smtp_handler": {
                "level": log_level,
                "handlers": ["console", "file"] if is_production else ["console"],
                "propagate": False
            },
            "smtpy.auth": {
                "level": log_level,
                "handlers": ["console", "file"] if is_production else ["console"],
                "propagate": False
            },
            "smtpy.database": {
                "level": log_level,
                "handlers": ["console", "file"] if is_production else ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"]
        }
    }
    
    return config


def setup_logging():
    """Set up logging configuration."""
    config = get_logging_config()
    
    try:
        logging.config.dictConfig(config)
        logger = logging.getLogger("smtpy")
        logger.info("Logging configuration initialized successfully")
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger = logging.getLogger("smtpy")
        logger.error(f"Failed to configure logging: {e}")
        logger.info("Using fallback logging configuration")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(f"smtpy.{name}")


# Security-focused logging functions
def log_security_event(logger: logging.Logger, event_type: str, details: Dict[str, Any], 
                      client_ip: str = None, user_id: str = None):
    """Log security-related events with structured data."""
    log_data = {
        "event_type": event_type,
        "client_ip": client_ip,
        "user_id": user_id,
        **details
    }
    logger.warning(f"Security event: {event_type}", extra=log_data)


def log_authentication_attempt(logger: logging.Logger, username: str, success: bool, 
                              client_ip: str = None, reason: str = None):
    """Log authentication attempts."""
    event_type = "auth_success" if success else "auth_failure"
    details = {
        "username": username,
        "success": success,
        "reason": reason
    }
    log_security_event(logger, event_type, details, client_ip)


def log_rate_limit_exceeded(logger: logging.Logger, endpoint: str, client_ip: str, 
                           limit_type: str = None):
    """Log rate limit violations."""
    details = {
        "endpoint": endpoint,
        "limit_type": limit_type
    }
    log_security_event(logger, "rate_limit_exceeded", details, client_ip)