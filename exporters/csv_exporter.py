from __future__ import annotations

import csv
import logging
from pathlib import Path

from models import Record
from utils.filename import build_filename

log = logging.getLogger(__name__)

_FINAL_DIR = "data/final"

# Colonne aggiuntive di contesto run — stesse per tutti i record del file.
# Necessarie per DataStage: permettono di storicizzare la fact table
# senza dover inferire nulla dal filename.
_RUN_FIELDS = ("date_from", "date_until", "scan_timestamp")


class CsvExporter:
    """Scrive il CSV dai record già deduplicati forniti dal JsonExporter. Sempre overwrite."""

    def __init__(self, base_dir: Path) -> None:
        self._final_dir = base_dir / _FINAL_DIR
        self._final_dir.mkdir(parents=True, exist_ok=True)

    def export(self, records: list[Record], target: str, topic: str,
               date_from: str, date_until: str,
               scan_timestamp: str = "") -> None:
        """
        Scrive il CSV. Ogni riga include i campi record + date_from, date_until,
        scan_timestamp — metadati del run corrente utili come contesto di ricerca.
        Il file è unico per (target, topic) e viene riscritto a ogni run.
        """
        filename = build_filename(target, topic) + ".csv"
        path = self._final_dir / filename

        fieldnames = list(Record.csv_fields()) + list(_RUN_FIELDS)
        run_meta = {
            "date_from":      date_from,
            "date_until":     date_until,
            "scan_timestamp": scan_timestamp,
        }

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in records:
                    writer.writerow({**r.to_csv_dict(), **run_meta})
            log.info("CSV esportato: %s (%d record)", path.name, len(records))
        except OSError as e:
            log.error("Errore scrittura CSV '%s': %s", path, e)
