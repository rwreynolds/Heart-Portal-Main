"""
Centralized logging configuration for Heart Portal
Replaces print() statements with proper structured logging
"""

import logging
import sys
import os
from typing import Optional

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting across all components

    Args:
        name: Logger name (typically component name like 'heart-portal-main')
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Get log level from environment or use provided level
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler for stdout (systemd captures this)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level))

    # Detailed format for debugging, simpler for production
    if level == 'DEBUG':
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create new one

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name) if logging.getLogger(name).handlers else setup_logger(name)
