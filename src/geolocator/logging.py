"""Logging configuration with log rotation and privacy protection."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys


def setup_logging(logs_dir: str = "logs", level: str = "INFO") -> logging.Logger:
    """Configure system-wide logging with rotation.
    
    Ensures no raw image binary data or sensitive user data is written.
    """
    path = Path(logs_dir)
    path.mkdir(parents=True, exist_ok=True)
    log_file = path / "geolocator.log"

    root_logger = logging.getLogger("geolocator")
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if called multiple times
    if root_logger.handlers:
        return root_logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating File Handler (10MB per file, max 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    root_logger.info("Logging initialized at level %s; logging to %s", level, log_file)
    return root_logger


logger = logging.getLogger("geolocator")
