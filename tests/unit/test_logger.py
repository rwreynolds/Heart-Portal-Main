"""
Unit tests for shared/logger.py
Tests centralized logging configuration
"""

import pytest
import logging
from shared.logger import setup_logger, get_logger


def test_setup_logger_default():
    """Test logger setup with default settings"""
    logger = setup_logger('test-app')

    assert logger.name == 'test-app'
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_setup_logger_debug_level():
    """Test logger setup with DEBUG level"""
    logger = setup_logger('test-debug', level='DEBUG')

    assert logger.level == logging.DEBUG


def test_setup_logger_no_duplicate_handlers():
    """Test that calling setup_logger twice doesn't add duplicate handlers"""
    logger1 = setup_logger('test-duplicate')
    handler_count1 = len(logger1.handlers)

    logger2 = setup_logger('test-duplicate')
    handler_count2 = len(logger2.handlers)

    assert handler_count1 == handler_count2


def test_get_logger_existing():
    """Test getting an existing logger"""
    setup_logger('test-existing')
    logger = get_logger('test-existing')

    assert logger.name == 'test-existing'
    assert len(logger.handlers) > 0


def test_get_logger_new():
    """Test getting a new logger that doesn't exist yet"""
    logger = get_logger('test-new-logger')

    assert logger.name == 'test-new-logger'
    assert len(logger.handlers) > 0


def test_logger_output(caplog):
    """Test that logger actually logs messages"""
    logger = setup_logger('test-output', level='INFO')

    with caplog.at_level(logging.INFO):
        logger.info('Test message')

    assert 'Test message' in caplog.text
