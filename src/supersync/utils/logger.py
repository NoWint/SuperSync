import logging
from datetime import datetime
from pathlib import Path


def get_logger(name: str = "supersync") -> logging.Logger:
    """Get a logger that writes to ~/.supersync/logs/."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_dir = Path.home() / ".supersync" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{date_str}.log"

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger
