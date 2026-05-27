"""normalizers/news.py — Normalizer per NewsAPI /v2/everything (source_id: "news")."""

from __future__ import annotations

from models import RawRecord, Record
from normalizers.registry import register
from normalizers.utils import to_date, to_url, to_domain, first_non_empty


def _normalize(raw: RawRecord) -> Record:
    p = raw.payload
    url = to_url(p.get("url"))
    return Record(
        source=raw.source,
        title=first_non_empty(p.get("title")),
        text=first_non_empty(p.get("description"), p.get("content")),
        date=to_date(p.get("publishedAt")),
        url=url,
        query=raw.query,
        target=raw.target,
        # NewsAPI non include 'language' nella risposta per articolo (è un param di richiesta):
        # first_non_empty(None) ritorna "" che viola il contratto str | None del modello.
        language=p.get("language") or None,
        domain=to_domain(url) or first_non_empty(
            p.get("source", {}).get("name") if isinstance(p.get("source"), dict) else None
        ),
        retrieved_at=raw.retrieved_at,
    )


register("news", _normalize)
