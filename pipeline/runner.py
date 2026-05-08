from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from models import RawRecord, Record
from normalizers.registry import normalize_all
from pipeline.cleaner import clean_all, filter_quality
from pipeline.date_filter import filter_by_date_range, parse_date
from pipeline.deduplicator import deduplicate
from pipeline.enricher import Enricher

log = logging.getLogger(__name__)


@runtime_checkable
class RawStoreProtocol(Protocol):
    def save(self, records: list[RawRecord], target: str, timestamp: str) -> None: ...



@dataclass
class PipelineConfig:
    target:     str
    topic:      str
    query:      str
    sources:    list[str]          = field(default_factory=list)
    max_results: int               = 20
    save_raw:   bool               = True
    date_from:  str | None         = None
    date_until: str | None         = None
    collector_kwargs: dict[str, dict] = field(default_factory=dict)
    parallel_collectors: bool      = True
    max_workers: int               = 8
    dry_run:    bool               = False

    def __post_init__(self) -> None:
        if not self.target:
            raise ValueError("PipelineConfig.target non può essere vuoto")
        if not self.topic:
            raise ValueError("PipelineConfig.topic non può essere vuoto")
        if not self.query:
            raise ValueError("PipelineConfig.query non può essere vuota")
        if self.max_results < 1:
            raise ValueError(f"max_results deve essere >= 1, ricevuto: {self.max_results}")
        if self.date_from:
            self.date_from = parse_date(self.date_from)
        if self.date_until:
            self.date_until = parse_date(self.date_until)


class PipelineRunner:

    def __init__(
        self,
        registry: dict,
        raw_store: RawStoreProtocol | None = None,
        enricher: Enricher | None = None,
    ) -> None:
        self._registry  = registry
        self._raw_store = raw_store
        self._enricher  = enricher or Enricher()

    def run(
        self,
        config: PipelineConfig,
        timestamp: str = "",
        run_date: str = "",   # mantenuto per compatibilità, non usato internamente
    ) -> list[Record]:
        """Esegue collect → normalize → clean → dedup → enrich. Ritorna i record finali."""
        if config.sources:
            unknown = [s for s in config.sources if s not in self._registry]
            if unknown:
                raise ValueError(f"Sorgenti sconosciute: {unknown}. Disponibili: {sorted(self._registry)}")

        log.info("=== Pipeline avviata: target='%s', topic='%s' ===", config.target, config.topic)

        raw_records = self._collect(config)
        log.info("Raccolti %d RawRecord.", len(raw_records))
        if not raw_records:
            log.warning("Nessun record raccolto.")
            return []

        if config.save_raw and self._raw_store:
            try:
                self._raw_store.save(raw_records, config.target, timestamp)
            except Exception as e:
                log.error("Errore salvataggio raw: %s", e)

        records = normalize_all(raw_records)
        records = clean_all(records)
        records, skipped = filter_quality(records)
        log.info("Puliti: %d validi, %d scartati.", len(records), skipped)

        if config.date_from or config.date_until:
            records, dropped = filter_by_date_range(records, config.date_from, config.date_until)
            log.info("Filtro date [%s, %s]: %d mantenuti, %d scartati.",
                     config.date_from, config.date_until, len(records), dropped)

        records, n_removed = deduplicate(records)
        log.info("Deduplicati: %d rimossi, %d unici.", n_removed, len(records))

        if not records:
            log.warning("Nessun record dopo deduplicazione.")
            return []

        records = self._enricher.enrich_all(records)

        log.info("=== Pipeline completata: %d record finali ===", len(records))
        return records

    def _collect(self, config: PipelineConfig) -> list[RawRecord]:
        active = config.sources if config.sources else list(self._registry)
        tasks: list[tuple[int, str, dict]] = [
            (i, src, config.collector_kwargs.get(src, {}))
            for i, src in enumerate(active)
            if src in self._registry
        ]
        if not tasks:
            return []

        if config.parallel_collectors and config.max_workers > 1:
            return self._collect_parallel(config, tasks)
        return self._collect_serial(config, tasks)

    def _run_task(self, config: PipelineConfig, source_id: str, extra: dict) -> list[RawRecord]:
        collector = self._registry[source_id]
        n = 1 if config.dry_run else config.max_results
        log.info("Raccolta da '%s' per query: '%s'", source_id, config.query)
        try:
            return collector.collect(
                target=config.target,
                query=config.query,
                max_results=n,
                date_from=config.date_from,
                date_until=config.date_until,
                **extra,
            )
        except Exception as e:
            log.error("Errore collector '%s': %s", source_id, e)
            return []

    def _collect_serial(self, config: PipelineConfig, tasks: list) -> list[RawRecord]:
        out: list[RawRecord] = []
        for _, src, extra in tasks:
            out.extend(self._run_task(config, src, extra))
        return out

    def _collect_parallel(self, config: PipelineConfig, tasks: list) -> list[RawRecord]:
        workers = min(config.max_workers, len(tasks))
        results: list[tuple[int, list[RawRecord]]] = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(self._run_task, config, src, extra): idx
                for idx, src, extra in tasks
            }
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results.append((idx, fut.result()))
                except Exception as e:
                    log.error("Future fallito (idx=%d): %s", idx, e)

        results.sort(key=lambda x: x[0])
        out: list[RawRecord] = []
        for _, raws in results:
            out.extend(raws)
        return out
