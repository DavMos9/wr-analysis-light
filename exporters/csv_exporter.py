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


def _date_range(records: list[Record]) -> tuple[str | None, str | None]:
    """Restituisce (min_date, max_date) calcolati sui record con data non nulla."""
    dates = [r.date for r in records if r.date]
    return (min(dates) if dates else None, max(dates) if dates else None)


class CsvExporter:
    """Scrive il CSV dai record già deduplicati forniti dal JsonExporter. Sempre overwrite."""

    def __init__(self, base_dir: Path) -> None:
        self._final_dir = base_dir / _FINAL_DIR
        self._final_dir.mkdir(parents=True, exist_ok=True)

    def export(self, records: list[Record], target: str, topic: str,
               scan_timestamp: str = "") -> None:
        """
        Scrive il CSV. Ogni riga include i campi record + date_from, date_until,
        scan_timestamp. date_from e date_until sono il range effettivo dei dati
        (min/max della colonna date sui record), non i parametri CLI del run.
        Il file è unico per (target, topic) e viene riscritto a ogni run.
        """
        filename = build_filename(target, topic) + ".csv"
        path = self._final_dir / filename

        date_from, date_until = _date_range(records)

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
