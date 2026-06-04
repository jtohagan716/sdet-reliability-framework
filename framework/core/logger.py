import logging
from pathlib import Path


LOG_DIRECTORY = Path("reports/logs")
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIRECTORY / "framework.log"


def get_logger():

    logger = logging.getLogger("sdet_framework")

    if not logger.handlers:

        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler = logging.FileHandler(LOG_FILE)

        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger