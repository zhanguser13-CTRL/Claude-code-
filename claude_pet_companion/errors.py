"""
Claude Code Pet Companion - Error Handling and Logging System

This module provides:
- Custom exception classes for pet companion errors
- Centralized logging configuration
- Utility functions for error reporting
"""
import sys
import logging
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import traceback


# ============================================================================
# Exception Classes
# ============================================================================

class PetError(Exception):
    """Base exception for all pet companion errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message

    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback": traceback.format_exc()
        }


class StateError(PetError):
    """Exception raised for state-related errors."""

    def __init__(self, message: str, state_key: Optional[str] = None, **kwargs):
        details = {"state_key": state_key, **kwargs} if state_key else kwargs
        super().__init__(message, details)


class ConfigError(PetError):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = {"config_key": config_key, **kwargs} if config_key else kwargs
        super().__init__(message, details)


class RenderError(PetError):
    """Exception raised for rendering-related errors."""

    def __init__(self, message: str, render_module: Optional[str] = None, **kwargs):
        details = {"render_module": render_module, **kwargs} if render_module else kwargs
        super().__init__(message, details)


class IPCError(PetError):
    """Exception raised for IPC (Inter-Process Communication) errors."""

    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        details = {"endpoint": endpoint, **kwargs} if endpoint else kwargs
        super().__init__(message, details)


class ValidationError(PetError):
    """Exception raised for data validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        details = {"field": field, "value": str(value), **kwargs} if field else kwargs
        super().__init__(message, details)


class FileNotFoundError(PetError):
    """Exception raised when a required file is missing."""

    def __init__(self, message: str, file_path: Optional[Path] = None, **kwargs):
        details = {"file_path": str(file_path)} if file_path else kwargs
        super().__init__(message, details)


# ============================================================================
# Logging Configuration
# ============================================================================

# Default log format
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console: bool = True,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the pet companion system.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console: Whether to output to console
        format_string: Custom format string

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger("claude_pet_companion")

    # Clear existing handlers
    logger.handlers.clear()

    # Set log level
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        format_string or DEFAULT_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )

    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional logger name (defaults to "claude_pet_companion")

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"claude_pet_companion.{name}")
    return logging.getLogger("claude_pet_companion")


# ============================================================================
# Error Reporting Utilities
# ============================================================================

def log_error(
    error: Exception,
    logger: Optional[logging.Logger] = None,
    context: Optional[dict] = None
) -> None:
    """
    Log an error with optional context information.

    Args:
        error: The exception to log
        logger: Optional logger instance (creates default if not provided)
        context: Optional context dictionary
    """
    if logger is None:
        logger = get_logger()

    if isinstance(error, PetError):
        error_data = error.to_dict()
        if context:
            error_data["context"] = context
        logger.error(f"{error_data['type']}: {error.message}", extra=error_data)
    else:
        logger.error(f"Unexpected error: {error}", exc_info=True)
        if context:
            logger.error(f"Context: {context}")


def handle_error(
    error: Exception,
    logger: Optional[logging.Logger] = None,
    reraise: bool = False,
    default_return: Any = None
) -> Any:
    """
    Handle an error with logging and optional re-raising.

    Args:
        error: The exception to handle
        logger: Optional logger instance
        reraise: Whether to re-raise the exception
        default_return: Value to return if not re-raising

    Returns:
        default_return if not re-raising
    """
    log_error(error, logger)

    if reraise:
        raise error

    return default_return


def safe_execute(
    func,
    *args,
    logger: Optional[logging.Logger] = None,
    default_return: Any = None,
    error_callback: Optional callable = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        logger: Optional logger instance
        default_return: Default return value on error
        error_callback: Optional callback function for errors
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(e, logger)
        if error_callback:
            error_callback(e)
        return default_return


# ============================================================================
# Global Logger Instance
# ============================================================================

# Initialize default logger
_default_logger: Optional[logging.Logger] = None


def init_logging(data_dir: Optional[Path] = None) -> logging.Logger:
    """
    Initialize the default logging system.

    Args:
        data_dir: Optional data directory for log files

    Returns:
        Configured logger instance
    """
    global _default_logger

    log_file = None
    if data_dir:
        log_file = data_dir / "pet_companion.log"

    _default_logger = setup_logging(
        level="INFO",
        log_file=log_file,
        console=True
    )

    return _default_logger


def get_default_logger() -> logging.Logger:
    """
    Get the default logger, initializing if necessary.

    Returns:
        Default logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = init_logging()
    return _default_logger


# Convenience functions for direct logging
def debug(message: str, **kwargs) -> None:
    """Log a debug message."""
    get_default_logger().debug(message, extra=kwargs)


def info(message: str, **kwargs) -> None:
    """Log an info message."""
    get_default_logger().info(message, extra=kwargs)


def warning(message: str, **kwargs) -> None:
    """Log a warning message."""
    get_default_logger().warning(message, extra=kwargs)


def error(message: str, **kwargs) -> None:
    """Log an error message."""
    get_default_logger().error(message, extra=kwargs)


def critical(message: str, **kwargs) -> None:
    """Log a critical message."""
    get_default_logger().critical(message, extra=kwargs)


__all__ = [
    # Exceptions
    "PetError",
    "StateError",
    "ConfigError",
    "RenderError",
    "IPCError",
    "ValidationError",
    "FileNotFoundError",
    # Logging functions
    "setup_logging",
    "get_logger",
    "init_logging",
    "get_default_logger",
    "log_error",
    "handle_error",
    "safe_execute",
    # Convenience logging
    "debug",
    "info",
    "warning",
    "error",
    "critical",
]
