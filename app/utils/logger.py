"""
utils/logger.py
---------------
Sets up structured logging using loguru.

Structured logging means logs include consistent fields like timestamp,
log level, and request IDs - making it easier to search and filter logs
in production monitoring tools.
"""

import sys
from loguru import logger

# Remove the default loguru handler
logger.remove()

# Add a new handler that writes to stdout (console)
# The format includes: timestamp, log level, file location, and the message
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="INFO",
    colorize=True,
)

# Export the logger for use throughout the app
__all__ = ["logger"]
