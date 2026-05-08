"""
collectors/hackernews_collector.py — Algolia Search API per Hacker News.

Supporto date nativo: numericFilters su created_at_i (Unix timestamp).
Nessuna API key richiesta.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from collectors.base import BaseCollector
from collectors.retry import http_get_with_retry
from models import RawRecord

log = logging.getLogger(__name__)

_BASE_URL_RELEVANCE = "https://hn.algolia.com/api/v1/search"
_BASE_URL_DATE      = "https://hn.algolia.com/api/v1/search_by_date"
_MAX_RESULTS_CAP    = 50


def _date_to_unix(date_str: str, end_of_day: bool = False) -> int:
    """Converte 'YYYY-MM-DD' in Unix timestamp UTC."""
    hour, minute, second = (23, 59, 59) if end_of_day else (0, 0, 0)
    dt = datetime(
        *[int(x) for x in date_str.split("-")],
        hour, minute, second,
        tzinfo=timezone.utc,
    )
    return int(dt.timestamp())


class HackerNewsCollector(BaseCollector):
    source_id = "hackernews"

    def collect(
        self,
        target: str,
        query: str,
        max_results: int = 20,
        date_from: str | None = None,
        date_until: str | None = None,
        **kwargs: object,
    ) -> list[RawRecord]:
        """kwargs: search_by_date (bool) — usa /search_by_date invece di /search."""
        search_by_date: bool = bool(kwargs.get("search_by_date", False))
        base_url = _BASE_URL_DATE if search_by_date else _BASE_URL_RELEVANCE

        params: dict[str, object] = {
            "query":     query,
            "hitsPerPage": min(max_results, _MAX_RESULTS_CAP),
            "tags":      "(story,comment)",
        }

        # Filtro date nativo tramite numericFilters su Unix timestamp.
        filters: list[str] = []
        if date_from:
            filters.append(f"created_at_i>={_date_to_unix(date_from)}")
        if date_until:
            filters.append(f"created_at_i<={_date_to_unix(date_until, end_of_day=True)}")
        if filters:
            params["numericFilters"] = ",".join(filters)

        try:
            response = http_get_with_retry(
                base_url, params=params, timeout=10, source_id=self.source_id
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self._log_error(query, e)
            return []

        hits = data.get("hits", [])
        records = [
            self._make_raw(target, query, hit)
            for hit in hits
            if hit.get("objectID")
        ]
        self._log_collected(query, len(records))
        return records
