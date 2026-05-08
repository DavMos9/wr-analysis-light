from __future__ import annotations

import logging
from dataclasses import replace
from types import MappingProxyType
from typing import Callable, Mapping

from models import RawRecord, Record
from normalizers.utils import first_non_empty, to_date, to_domain, to_url

log = logging.getLogger(__name__)

NormalizerFn = Callable[[RawRecord], Record | None]

_REGISTRY: dict[str, NormalizerFn] = {}
REGISTRY: Mapping[str, NormalizerFn] = MappingProxyType(_REGISTRY)

_TITLE_KEYS = ("title", "headline", "name", "subject", "webTitle")
_TEXT_KEYS  = ("text", "body", "content", "description", "trailText", "selftext")
_URL_KEYS   = ("url", "link", "webUrl", "ap_id", "uri", "shortUrl")
_DATE_KEYS  = ("date", "published", "published_at", "webPublicationDate",
               "pubDate", "created_at", "createdUtc")


def _fallback_normalize(raw: RawRecord) -> Record | None:
    p = raw.payload
    url = to_url(first_non_empty(*(str(p.get(k) or "") for k in _URL_KEYS)))
    if not url:
        log.warning("[fallback] Sorgente '%s': URL non trovato — record scartato.", raw.source)
        return None

    return Record(
        source=raw.source,
        title=first_non_empty(*(str(p.get(k) or "") for k in _TITLE_KEYS)),
        text=first_non_empty(*(str(p.get(k) or "") for k in _TEXT_KEYS)),
        date=to_date(first_non_empty(*(str(p.get(k) or "") for k in _DATE_KEYS)) or None),
        url=url,
        query=raw.query,
        target=raw.target,
        domain=to_domain(url),
        retrieved_at=raw.retrieved_at,
    )


def register(source_name: str, fn: NormalizerFn) -> None:
    if source_name in _REGISTRY:
        log.warning("Normalizer per '%s' già registrato — sovrascrittura.", source_name)
    _REGISTRY[source_name] = fn


def registered_sources() -> list[str]:
    return list(_REGISTRY.keys())


def _extract_topic(target: str, query: str) -> str:
    prefix = target + " "
    if query.lower().startswith(prefix.lower()):
        return query[len(prefix):]
    return query


def normalize(raw: RawRecord) -> Record | None:
    fn = _REGISTRY.get(raw.source)
    if fn is None:
        log.warning("Sorgente '%s': nessun normalizer, uso fallback.", raw.source)
        fn = _fallback_normalize

    try:
        record = fn(raw)
    except ValueError as e:
        log.warning("[%s] Record scartato: %s (query='%s')", raw.source, e, raw.query)
        return None
    except Exception as e:
        log.error("Errore normalizzando record da '%s': %s", raw.source, e)
        return None

    if record is None:
        return None

    if not record.url:
        log.warning("[%s] Record scartato: URL mancante (query='%s')", raw.source, raw.query)
        return None

    return replace(record, topic=_extract_topic(raw.target, raw.query))


def normalize_all(raws: list[RawRecord]) -> list[Record]:
    results: list[Record] = []
    for raw in raws:
        record = normalize(raw)
        if record is not None:
            results.append(record)
    log.info("Normalizzati %d/%d record.", len(results), len(raws))
    return results
