"""
collectors/guardian_collector.py — The Guardian Open Platform.

Supporto date nativo: from-date / to-date (formato YYYY-MM-DD).
Piano gratuito: 5.000 richieste/giorno, archivio dal 1999.
"""

from __future__ import annotations

import logging

import requests

from collectors.base import BaseCollector
from collectors.retry import http_get_with_retry
from config import GUARDIAN_API_KEY
from models import RawRecord

log = logging.getLogger(__name__)

BASE_URL = "https://content.guardianapis.com/search"


class GuardianCollector(BaseCollector):
    source_id = "guardian"

    def collect(
        self,
        target: str,
        query: str,
        max_results: int = 20,
        date_from: str | None = None,
        date_until: str | None = None,
        **kwargs: object,
    ) -> list[RawRecord]:
        if not GUARDIAN_API_KEY:
            self._log_skip("GUARDIAN_API_KEY non configurata")
            return []

        params: dict[str, object] = {
            "q":           query,
            "api-key":     GUARDIAN_API_KEY,
            "page-size":   min(max_results, 200),
            "order-by":    "relevance",
            "show-fields": "headline,trailText,bodyText,byline,shortUrl",
        }

        # Filtro date nativo Guardian.
        if date_from:
            params["from-date"] = date_from
        if date_until:
            params["to-date"] = date_until

        try:
            response = http_get_with_retry(
                BASE_URL, params=params, timeout=10, source_id=self.source_id
            )
            if response.status_code == 429:
                log.warning("[GuardianCollector] Limite giornaliero raggiunto (HTTP 429).")
                return []
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self._log_error(query, e)
            return []

        results = data.get("response", {}).get("results", [])
        records = [
            self._make_raw(target, query, {**article, "_rank": rank})
            for rank, article in enumerate(results, start=1)
        ]
        self._log_collected(query, len(records))
        return records
