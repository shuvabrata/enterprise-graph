#!/usr/bin/env python3
"""
Test script for common/logger.py

Tests different log levels, exception handling, and LogContext usage.
Run from project root: python3 tests/test_logger.py
"""

import sys
import os

# Add project root to path to import common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.logger import logger, LogContext


def test_basic_log_levels():
    """Test all log levels without context."""
    print("=" * 70)
    print("TEST 1: Basic Log Levels (No Context)")
    print("=" * 70)
    
    logger.debug("This is a DEBUG message - detailed diagnostic info")
    logger.info("This is an INFO message - general information")
    logger.warning("This is a WARNING message - something unexpected happened")
    logger.error("This is an ERROR message - something failed")
    logger.critical("This is a CRITICAL message - serious error")
    print()


def test_logs_with_context():
    """Test logging with LogContext."""
    print("=" * 70)
    print("TEST 2: Logs with LogContext")
    print("=" * 70)
    
    with LogContext(project_id="proj-123", user_id="alice", request_id="req-abc-456"):
        logger.info("Processing user request")
        logger.debug("Fetching data from database")
        logger.warning("Cache miss - fetching from source")
        logger.info("Request completed successfully")
    print()


def test_nested_contexts():
    """Test nested LogContext usage."""
    print("=" * 70)
    print("TEST 3: Nested LogContext")
    print("=" * 70)
    
    with LogContext(project_id="proj-999"):
        logger.info("Outer context - project level")
        
        with LogContext(user_id="bob", request_id="req-xyz-789"):
            logger.info("Inner context - user and request added")
            logger.debug("Processing nested operation")
        
        logger.info("Back to outer context - only project_id")
    print()


def test_partial_context():
    """Test LogContext with only some fields set."""
    print("=" * 70)
    print("TEST 4: Partial LogContext (only request_id)")
    print("=" * 70)
    
    with LogContext(request_id="req-partial-123"):
        logger.info("Only request_id is set in context")
        logger.warning("Other context fields are empty")
    print()


def test_exception_logging():
    """Test exception logging with logger.exception()."""
    print("=" * 70)
    print("TEST 5: Exception Logging")
    print("=" * 70)
    
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.exception("Division by zero error occurred")
    print()


def test_exception_with_context():
    """Test exception logging with LogContext."""
    print("=" * 70)
    print("TEST 6: Exception with LogContext")
    print("=" * 70)
    
    with LogContext(project_id="proj-error", user_id="charlie", request_id="req-err-001"):
        try:
            data = {"key": "value"}
            value = data["missing_key"]
        except KeyError as e:
            logger.exception("Failed to access dictionary key")
    print()


def test_error_method_with_exception():
    """Test logger.error() with exception object."""
    print("=" * 70)
    print("TEST 7: logger.error() with Exception Object")
    print("=" * 70)
    
    with LogContext(project_id="proj-custom", request_id="req-custom-999"):
        try:
            numbers = [1, 2, 3]
            item = numbers[10]
        except IndexError as e:
            # Note: Using logger.error() with exception object triggers custom SecopsLogger.error()
            logger.error(e)
    print()


def test_multi_line_messages():
    """Test logging with multi-line messages."""
    print("=" * 70)
    print("TEST 8: Multi-line Messages")
    print("=" * 70)
    
    with LogContext(project_id="proj-multiline"):
        long_message = """
        This is a multi-line log message.
        It spans multiple lines.
        Useful for detailed error descriptions.
        """
        logger.info(long_message)
        
        logger.warning("Processing items:\n  - Item 1\n  - Item 2\n  - Item 3")
    print()


def test_complex_scenario():
    """Test a complex real-world scenario."""
    print("=" * 70)
    print("TEST 9: Complex Real-World Scenario")
    print("=" * 70)
    
    with LogContext(project_id="github-sync", user_id="system"):
        logger.info("Starting GitHub repository sync")
        
        repos = ["repo-1", "repo-2", "repo-3"]
        for repo in repos:
            with LogContext(request_id=f"sync-{repo}"):
                logger.info(f"Syncing repository: {repo}")
                logger.debug(f"Fetching commits for {repo}")
                
                if repo == "repo-2":
                    logger.warning(f"Repository {repo} has no recent commits")
                else:
                    logger.info(f"Successfully synced {repo}")
        
        logger.info("GitHub sync completed")
    print()


def test_no_context():
    """Test logging without any context."""
    print("=" * 70)
    print("TEST 10: Logs Without Context (Baseline)")
    print("=" * 70)
    
    logger.info("This log has no context variables")
    logger.debug("Debugging without context")
    logger.warning("Warning without context")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LOGGER TEST SUITE")
    print("=" * 70)
    print(f"LOG_FORMAT: {os.getenv('LOG_FORMAT', 'JSON')}")
    print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
    print("=" * 70)
    print()
    
    # Run all tests
    test_basic_log_levels()
    test_logs_with_context()
    test_nested_contexts()
    test_partial_context()
    test_exception_logging()
    test_exception_with_context()
    test_error_method_with_exception()
    test_multi_line_messages()
    test_complex_scenario()
    test_no_context()
    
    print("=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
    print("\nTry running with different configurations:")
    print("  LOG_FORMAT=TEXT python3 tests/test_logger.py")
    print("  LOG_FORMAT=JSON python3 tests/test_logger.py")
    print("  LOG_LEVEL=DEBUG python3 tests/test_logger.py")
    print("  LOG_LEVEL=WARNING python3 tests/test_logger.py")
