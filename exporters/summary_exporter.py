from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from models import Record
from utils.filename import build_filename

log = logging.getLogger(__name__)

_FINAL_DIR = "data/final"


def _build_summary(
    records: list[Record],
    target: str,
    topic: str,
    run_date: str,
    scan_timestamp: str,
) -> dict:
    dates = [r.date for r in records if r.date]
    source_counts = dict(Counter(r.source for r in records))

    return {
        "target":         target,
        "topic":          topic,
        "execution_date": run_date,
        "scan_timestamp": scan_timestamp,
        "total_records":  len(records),
        "date_range": {
            "from":  min(dates) if dates else None,
            "to":    max(dates) if dates else None,
        },
        "sources": source_counts,
    }


class SummaryExporter:
    """
    Esporta il JSON di riepilogo. Il summary viene ricalcolato sull'insieme
    completo dei record (passati dall'esporter JSON).
    """

    def __init__(self, base_dir: Path) -> None:
        self._final_dir = base_dir / _FINAL_DIR
        self._final_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        records: list[Record],
        target: str,
        topic: str,
        run_date: str,
        scan_timestamp: str | None = None,
    ) -> None:
        if scan_timestamp is None:
            scan_timestamp = datetime.now(tz=timezone.utc).isoformat()

        filename = build_filename(target, topic) + "_summary.json"
        path = self._final_dir / filename
        summary = _build_summary(records, target, topic, run_date, scan_timestamp)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            log.info("Summary esportato: %s", path.name)
        except OSError as e:
            log.error("Errore scrittura summary '%s': %s", path, e)
