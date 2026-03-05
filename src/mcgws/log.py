"""Logging setup for mc-gws."""

import logging
from datetime import datetime
from mcgws.config import LOG_DIR


def setup_logging(level: int = logging.INFO):
    """Configure logging to file and console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"mcgws_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
