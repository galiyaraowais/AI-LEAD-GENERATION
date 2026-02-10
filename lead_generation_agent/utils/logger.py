"""Logging utility for the lead generation agent."""

# Import Python's built-in logging package.
import logging
# Import RotatingFileHandler to keep log files manageable.
from logging.handlers import RotatingFileHandler


def setup_logger(log_file_path: str) -> logging.Logger:
    """Create and configure the shared application logger."""
    # Create/get a logger instance with a readable app-specific name.
    logger = logging.getLogger("lead_generation_agent")
    # If handlers already exist, return existing logger to avoid duplicate logs.
    if logger.handlers:
        # Return the already-configured logger.
        return logger

    # Set the minimum logging level to INFO for normal operations.
    logger.setLevel(logging.INFO)

    # Build a rotating file handler to store logs on disk.
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1_000_000, backupCount=3)
    # Build a text format that includes timestamp, level, and message.
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    # Apply the formatter to the file handler.
    file_handler.setFormatter(formatter)

    # Build a stream handler so logs also appear in the terminal.
    console_handler = logging.StreamHandler()
    # Apply the same format for terminal output consistency.
    console_handler.setFormatter(formatter)

    # Attach file handler to the logger.
    logger.addHandler(file_handler)
    # Attach console handler to the logger.
    logger.addHandler(console_handler)

    # Return the configured logger instance.
    return logger
