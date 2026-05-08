from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from models import RawRecord
from utils.slugify import slugify

log = logging.getLogger(__name__)

_RAW_DIR = "data/raw"


class RawStore:
    """Salva i RawRecord in un file JSON per esecuzione nella cartella data/raw/."""

    def __init__(self, base_dir: Path) -> None:
        self._raw_dir = base_dir / _RAW_DIR
        self._raw_dir.mkdir(parents=True, exist_ok=True)

    def save(self, records: list[RawRecord], target: str, timestamp: str) -> None:
        if not records:
            return
        filename = f"{slugify(target)}_{timestamp}_raw.json"
        path = self._raw_dir / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)
            log.info("Raw salvati: %s (%d record)", path.name, len(records))
        except OSError as e:
            log.error("Errore salvataggio raw '%s': %s", path, e)
