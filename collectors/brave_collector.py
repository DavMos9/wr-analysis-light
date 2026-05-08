"""
collectors/brave_collector.py — Brave Search API.

Date: Brave non supporta range esatti. Si approssima date_from con
il parametro 'freshness' per ridurre risultati fuori range.
Il filtro esatto viene applicato a livello di pipeline (post-filter).

Piano gratuito: 2.000 query/mese.
"""

from __future__ import annotations

import logging
from datetime import date

import requests

from collectors.base import BaseCollector
from collectors.retry import http_get_with_retry
from config import BRAVE_API_KEY
from models import RawRecord

log = logging.getLogger(__name__)

BASE_URL = "https://api.search.brave.com/res/v1/web/search"
MAX_RESULTS_PER_REQUEST = 20


def _approx_freshness(date_from: str | None) -> str | None:
    """
    Approssima date_from al valore freshness Brave più conservativo (più ampio).
    Preferisce includere più risultati: il post-filter applica il range esatto.

    pd=past day, pw=past week, pm=past month, py=past year, None=tutto.
    """
    if not date_from:
        return None

    days_ago = (date.today() - date.fromisoformat(date_from)).days

    if days_ago <= 1:
        return "pd"
    if days_ago <= 7:
        return "pw"
    if days_ago <= 30:
        return "pm"
    if days_ago <= 365:
        return "py"
    return None   # oltre un anno: nessun filtro (Brave non supporta range più ampi)


class BraveCollector(BaseCollector):
    source_id = "brave"

    def collect(
        self,
        target: str,
        query: str,
        max_results: int = 20,
        date_from: str | None = None,
        date_until: str | None = None,
        **kwargs: object,
    ) -> list[RawRecord]:
        """
        kwargs: country, search_lang, safesearch.
        date_from viene approssimato al parametro 'freshness'; post-filter in pipeline.
        """
        if not BRAVE_API_KEY:
            self._log_skip("BRAVE_API_KEY non configurata")
            return []

        params: dict[str, object] = {
            "q":     query,
            "count": min(max_results, MAX_RESULTS_PER_REQUEST),
        }

        for optional in ("country", "search_lang", "safesearch"):
            value = kwargs.get(optional)
            if value:
                params[optional] = str(value)

        # Approssimazione date con freshness (post-filter applica range esatto).
        freshness = _approx_freshness(date_from)
        if freshness:
            params["freshness"] = freshness
            log.debug(
                "[brave] date_from='%s' → freshness='%s' (approssimazione; post-filter in pipeline).",
                date_from, freshness,
            )

        headers = {
            "Accept":               "application/json",
            "Accept-Encoding":      "gzip",
            "X-Subscription-Token": BRAVE_API_KEY,
        }

        try:
            response = http_get_with_retry(
                BASE_URL, params=params, headers=headers, timeout=10, source_id=self.source_id
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self._log_error(query, e)
            return []

        results = data.get("web", {}).get("results", [])
        records = [
            self._make_raw(target, query, {**item, "_rank": rank})
            for rank, item in enumerate(results, start=1)
            if item.get("url")
        ]
        self._log_collected(query, len(records))
        return records
