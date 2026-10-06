import logging
import os
from config.settings import LOGS_DIR

os.makedirs(LOGS_DIR, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """INFO logger writing to stderr and logs/pipeline.log."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # getLogger is process-global; a second call must not add another handler

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(os.path.join(LOGS_DIR, "pipeline.log"))
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger