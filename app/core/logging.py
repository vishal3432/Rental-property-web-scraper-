import logging
import sys
import json
from datetime import datetime
from typing import Any

from app.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for better parsing in production."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in ["name", "msg", "args", "created", "filename", "funcName", 
                              "levelname", "levelno", "lineno", "module", "msecs", "message",
                              "pathname", "process", "processName", "relativeCreated", 
                              "thread", "threadName", "exc_info", "exc_text", "stack_info"]:
                    try:
                        log_obj[key] = value
                    except (TypeError, ValueError):
                        log_obj[key] = str(value)
        
        return json.dumps(log_obj, default=str)


class PlainFormatter(logging.Formatter):
    """Format logs as plain text for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as plain text."""
        return (
            f"{record.asctime} | {record.levelname:8s} | {record.name:30s} | "
            f"{record.funcName}:{record.lineno} | {record.getMessage()}"
        )


def configure_logging() -> None:
    """Configure logging based on environment settings."""
    settings = get_settings()
    
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Choose formatter based on log format setting
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = PlainFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log startup info
    root_logger.info(
        f"Logging configured: level={settings.log_level}, format={settings.log_format}, "
        f"debug={settings.debug}"
    )
    
    # Suppress verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)

