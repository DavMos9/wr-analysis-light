"""utils/logging_config.py — Configurazione centralizzata del logging."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configura il root logger con formato standard su stderr."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stderr,
        force=True,
    )
    # Sopprimi log rumorosi di librerie terze.
    for noisy in ("urllib3", "httpx", "httpcore", "transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
