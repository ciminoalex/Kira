"""
Configurazione logging strutturato (JSON) per produzione.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Formatter che produce log in formato JSON strutturato."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO", json_format: bool = True) -> None:
    """
    Configura il logging per l'applicazione.

    Args:
        level: Livello di logging (DEBUG, INFO, WARNING, ERROR)
        json_format: Se True, usa formato JSON (produzione).
                     Se False, usa formato leggibile (sviluppo).
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))

    # Rimuovi handler esistenti
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
            )
        )

    root.addHandler(handler)

    # Riduci verbosità di librerie esterne
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
