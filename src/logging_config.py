import logging
import sys
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """Configure structured logging for the pipeline."""
    os.makedirs("logs", exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file = f"logs/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )

    return logging.getLogger(__name__)

def get_logger(name):
    """Get logger instance for a module."""
    return logging.getLogger(name)
