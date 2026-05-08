"""
wr-analysis-light — Entry point CLI

Uso:
    python main.py --target "Zendaya" --topic "Euphoria" --date-from 2026-04-01 --date-to 2026-05-07

Il programma compone la query come "{target} {topic}" (o usa il topic as-is se contiene
già parole del target). Supporta merge: il file di output è unico per (target, topic)
e accumula i record di run successive deduplicati per URL/contenuto.
--date-from è obbligatorio. --date-to è opzionale; se assente, il range arriva alla data odierna.
"""

import argparse
import logging
from datetime import date
from pathlib import Path

from collectors import build_registry
from exporters import JsonExporter, CsvExporter, SummaryExporter
from pipeline import PipelineRunner, PipelineConfig
from pipeline.date_filter import parse_date
from storage import RawStore
from utils import configure_logging, now_timestamp, build_filename

configure_logging()
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
REGISTRY = build_registry()
ALL_SOURCES = list(REGISTRY.keys())

OPT_IN_SOURCES = frozenset({"stackexchange", "hackernews"})
DEFAULT_SOURCES = [s for s in ALL_SOURCES if s not in OPT_IN_SOURCES]


def _build_query(target: str, topic: str) -> str:
    target_words = set(target.lower().split())
    if any(w in topic.lower() for w in target_words):
        return topic
    return f"{target} {topic}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Web Reputational Analysis (light) — pipeline dati da fonti web"
    )
    parser.add_argument("--target", required=True,
                        help="Entità da analizzare (es. 'Zendaya')")
    parser.add_argument("--topic", required=True,
                        help="Topic di ricerca (es. 'Euphoria')")
    parser.add_argument("--date-from", dest="date_from", required=True, metavar="YYYY-MM-DD",
                        help="Data inizio range di ricerca (inclusa, obbligatoria)")
    parser.add_argument("--date-to", dest="date_until", default=None, metavar="YYYY-MM-DD",
                        help="Data fine range di ricerca (inclusa, default: oggi)")
    parser.add_argument("--sources", nargs="+", default=DEFAULT_SOURCES, choices=ALL_SOURCES,
                        help=f"Fonti da interrogare (default: tutte tranne {sorted(OPT_IN_SOURCES)})")
    parser.add_argument("--max-results", type=int, default=20,
                        help="Risultati massimi per fonte (default: 20)")
    parser.add_argument("--no-raw", action="store_true",
                        help="Non salvare i payload grezzi in data/raw/")
    parser.add_argument("--news-language", default="en", metavar="LANG",
                        help="Lingua per NewsAPI ISO 639-1 (default: 'en')")
    parser.add_argument("--dry-run", action="store_true",
                        help="max_results=1 per fonte — verifica le API senza consumare quota")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        parse_date(args.date_from)
    except ValueError as e:
        log.error("--date-from non valido: %s", e)
        raise SystemExit(1)

    if args.date_until:
        try:
            parse_date(args.date_until)
        except ValueError as e:
            log.error("--date-to non valido: %s", e)
            raise SystemExit(1)

    ts       = now_timestamp()
    run_date = date.today().strftime("%Y-%m-%d")
    query    = _build_query(args.target, args.topic)

    # L'estremo superiore del range: esplicito o oggi.
    effective_date_until = args.date_until or run_date

    filename = build_filename(args.target, args.topic)

    log.info("Query composta: '%s'", query)
    log.info("Range date: %s → %s", args.date_from, effective_date_until)
    log.info("File output: %s", filename)

    json_exporter    = JsonExporter(BASE_DIR)
    csv_exporter     = CsvExporter(BASE_DIR)
    summary_exporter = SummaryExporter(BASE_DIR)

    # Fonti statiche (is_static=True) già presenti nel file finale: skip.
    # Wikipedia/WikiTalk restituiscono sempre lo stesso contenuto per lo stesso target;
    # se il file esiste già e contiene record da quelle fonti, non vale la pena riinterrogarle.
    _existing_path    = BASE_DIR / "data/final" / (filename + ".json")
    _existing_records = json_exporter.load_records(_existing_path)
    _existing_sources = {r.source for r in _existing_records}
    _static_sources   = {sid for sid, c in REGISTRY.items() if getattr(c, "is_static", False)}
    _skip_sources     = _static_sources & _existing_sources
    active_sources    = [s for s in args.sources if s not in _skip_sources]
    if _skip_sources:
        log.info("Fonti statiche già presenti, saltate: %s", sorted(_skip_sources))

    if not active_sources:
        log.info("Nessuna fonte attiva da interrogare (tutte statiche e già presenti). Uscita.")
        print(f"\nAggiunti in questo run: 0  |  Totale nel file: {len(_existing_records)}")
        print(f"Output: data/final/{filename}.json | .csv | _summary.json")
        return

    config = PipelineConfig(
        target=args.target,
        topic=args.topic,
        query=query,
        sources=active_sources,
        max_results=args.max_results,
        save_raw=not args.no_raw,
        date_from=args.date_from,
        date_until=effective_date_until,
        collector_kwargs={"news": {"language": args.news_language}},
        dry_run=args.dry_run,
    )

    runner = PipelineRunner(
        registry=REGISTRY,
        raw_store=RawStore(BASE_DIR) if not args.no_raw else None,
    )

    new_records = runner.run(config, timestamp=ts, run_date=run_date)

    # JSON: merge su file unico (target, topic) + dedup → restituisce (insieme_completo, n_aggiunti).
    # Passa _existing_records già caricati per evitare una seconda lettura disco.
    final_records, n_added = json_exporter.export(
        new_records, args.target, args.topic,
        existing=_existing_records,
    )

    # CSV e summary derivano dal JSON già deduplicato.
    # date_from/date_until nel CSV sono metadato del run corrente.
    csv_exporter.export(final_records, args.target, args.topic, args.date_from, effective_date_until,
                        scan_timestamp=ts)
    summary_exporter.export(
        final_records, args.target, args.topic,
        run_date, ts,
    )

    print(f"\nAggiunti in questo run: {n_added}  |  Totale nel file: {len(final_records)}")
    print(f"Output: data/final/{filename}.json | .csv | _summary.json")


if __name__ == "__main__":
    main()
