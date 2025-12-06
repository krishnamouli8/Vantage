"""
Structured logging utilities for Vantage Agent.

Provides consistent, structured logging across the agent.
"""

import logging
import sys
from typing import Optional


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
        record.levelname = f"{level_color}{record.levelname}{Colors.RESET}"
        
        # Add color to logger name
        record.name = f"{Colors.MAGENTA}{record.name}{Colors.RESET}"
        
        return super().format(record)


def get_logger(name: str, debug: bool = False) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        debug: Enable debug logging
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set level
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Create formatter
    formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def configure_root_logger(debug: bool = False) -> None:
    """
    Configure the root logger for the entire application.
    
    Args:
        debug: Enable debug logging
    """
    root_logger = logging.getLogger("vantage_agent")
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add new handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    
    formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)
    root_logger.propagate = False
