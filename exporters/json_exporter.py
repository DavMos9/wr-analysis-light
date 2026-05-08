from __future__ import annotations

import json
import logging
from pathlib import Path

from models import Record
from pipeline.deduplicator import deduplicate_against
from utils.filename import build_filename

log = logging.getLogger(__name__)

_FINAL_DIR = "data/final"


class JsonExporter:
    """
    Esporta i Record in JSON.
    Il file è unico per (target, topic) e accumula record di run successive.
    I nuovi record vengono deduplicati contro quelli esistenti e il file
    viene riscritto con l'insieme completo.
    """

    def __init__(self, base_dir: Path) -> None:
        self._final_dir = base_dir / _FINAL_DIR
        self._final_dir.mkdir(parents=True, exist_ok=True)

    def export(self, records: list[Record], target: str, topic: str,
               existing: list[Record] | None = None) -> tuple[list[Record], int]:
        """
        Scrive il JSON e restituisce (lista_finale, n_aggiunti).
        Deduplica i nuovi record contro quelli esistenti e riscrive il file completo.

        Se `existing` è fornito viene usato direttamente, evitando una lettura disco
        aggiuntiva (utile quando il chiamante ha già caricato il file in precedenza).
        """
        filename = build_filename(target, topic) + ".json"
        path = self._final_dir / filename

        if existing is None:
            existing = self.load_records(path)

        if existing:
            new_only = deduplicate_against(records, existing)
            merged = existing + new_only
            n_added = len(new_only)
            log.info("Merge: %d esistenti + %d nuovi = %d totali.",
                     len(existing), n_added, len(merged))
        else:
            merged = records
            n_added = len(merged)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in merged], f, ensure_ascii=False, indent=2)
            log.info("JSON esportato: %s (%d record)", path.name, len(merged))
        except OSError as e:
            log.error("Errore scrittura JSON '%s': %s", path, e)

        return merged, n_added

    def load_records(self, path: Path) -> list[Record]:
        if not path.exists():
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            records = []
            for item in data:
                try:
                    records.append(Record(
                        source=item.get("source", ""),
                        query=item.get("query", ""),
                        target=item.get("target", ""),
                        title=item.get("title", ""),
                        text=item.get("text", ""),
                        date=item.get("date"),
                        url=item.get("url", ""),
                        topic=item.get("topic", ""),
                        domain=item.get("domain", ""),
                        language=item.get("language"),
                        sentiment=item.get("sentiment"),
                        retrieved_at=item.get("retrieved_at", ""),
                    ))
                except (ValueError, TypeError) as e:
                    log.warning("Record esistente non valido, saltato: %s", e)
            log.info("Caricati %d record esistenti da '%s'.", len(records), path.name)
            return records
        except (OSError, json.JSONDecodeError) as e:
            log.error("Errore lettura file esistente '%s': %s", path, e)
            return []
