"""
Logging configuration for TGTS Tender Scraper
"""

import logging
import os
from config import LOG_FILE, LOG_LEVEL

# Create logs directory if not exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LOG_LEVEL))

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(getattr(logging, LOG_LEVEL))
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, LOG_LEVEL))
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(console_formatter)

# Add handlers
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)
