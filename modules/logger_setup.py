"""
==============================================================================
  Voice Assistant — Logger Setup
  Oasis Infobyte Internship | Task 1
==============================================================================
"""

import logging
import os
import json
from logging.handlers import RotatingFileHandler

def setup_logger(config_path: str = None) -> None:
    """
    Configure root logger based on settings.json.

    - Writes to logs/assistant.log (rotating, max 1 MB, 3 backups).
    - Also streams INFO+ messages to console.
    """
    cfg = {}
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
    try:
        with open(config_path) as f:
            cfg = json.load(f).get("logging", {})
    except Exception:
        pass

    enabled  = cfg.get("enabled", True)
    log_file = cfg.get("log_file", "logs/assistant.log")
    level    = getattr(logging, cfg.get("level", "INFO").upper(), logging.INFO)

    # Resolve log file path relative to project root
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    log_path = os.path.join(root_dir, log_file)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)   # Only warnings+ to console (keeps output clean)
    ch.setFormatter(fmt)
    root_logger.addHandler(ch)

    # File handler (rotating)
    if enabled:
        fh = RotatingFileHandler(log_path, maxBytes=1_024_000, backupCount=3)
        fh.setLevel(level)
        fh.setFormatter(fmt)
        root_logger.addHandler(fh)
