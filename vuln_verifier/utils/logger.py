# utils/logger.py
# Professional logging with colors and timestamps

import logging
from colorlog import ColoredFormatter
from config.settings import LOG_FILE

logger = logging.getLogger("VulnVerifier")
logger.setLevel(logging.INFO)

# Console handler with colors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "INFO": "cyan",
        "WARNING": "yellow",
        "ERROR": "red"
    }
)
console_handler.setFormatter(formatter)

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)