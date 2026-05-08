"""
collectors/nyt_collector.py — NYT Article Search API.

Supporto date nativo: begin_date / end_date (formato YYYYMMDD).
Piano gratuito: 10 req/min, 4.000 req/giorno. Archivio dal 1851.
"""

from __future__ import annotations

import logging

import requests

from collectors.base import BaseCollector
from collectors.retry import http_get_with_retry
from config import NYT_API_KEY
from models import RawRecord

log = logging.getLogger(__name__)

BASE_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"


def _to_nyt_date(date_str: str) -> str:
    """Converte 'YYYY-MM-DD' in 'YYYYMMDD' per NYT API."""
    return date_str.replace("-", "")


class NytCollector(BaseCollector):
    source_id = "nyt"

    def collect(
        self,
        target: str,
        query: str,
        max_results: int = 10,
        date_from: str | None = None,
        date_until: str | None = None,
        **kwargs: object,
    ) -> list[RawRecord]:
        if not NYT_API_KEY:
            self._log_skip("NYT_API_KEY non configurata")
            return []

        params: dict[str, object] = {
            "q":       query,
            "api-key": NYT_API_KEY,
            "sort":    "relevance",
        }

        # Filtro date nativo NYT.
        if date_from:
            params["begin_date"] = _to_nyt_date(date_from)
        if date_until:
            params["end_date"] = _to_nyt_date(date_until)

        try:
            response = http_get_with_retry(
                BASE_URL, params=params, timeout=10, source_id=self.source_id
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self._log_error(query, e)
            return []

        docs = data.get("response", {}).get("docs", [])
        records = [
            self._make_raw(target, query, {**doc, "_rank": rank})
            for rank, doc in enumerate(docs[:max_results], start=1)
            if doc.get("web_url")
        ]
        self._log_collected(query, len(records))
        return records
