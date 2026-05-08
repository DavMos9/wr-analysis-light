"""
collectors/reddit_collector.py — Reddit /search.json non autenticato.

Date: Reddit API non supporta range esatti. Si approssima date_from con
il parametro 't' (time filter relativo) per ridurre risultati fuori range.
Il filtro esatto viene applicato a livello di pipeline (post-filter).

Limiti: ~30 req/min, max 100 risultati.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import requests

from collectors.base import BaseCollector
from collectors.retry import http_get_with_retry
from config import APP_USER_AGENT
from models import RawRecord

log = logging.getLogger(__name__)

_BASE_URL        = "https://www.reddit.com/search.json"
_MAX_RESULTS_CAP = 100


def _approx_time_filter(date_from: str | None) -> str:
    """
    Approssima date_from al filtro temporale Reddit più conservativo (più ampio).
    Preferisce includere più risultati piuttosto che perderne: il post-filter
    applica il range esatto in pipeline.

    'all' → nessun filtro (default quando date_from=None).
    """
    if not date_from:
        return "all"

    days_ago = (date.today() - date.fromisoformat(date_from)).days

    if days_ago <= 1:
        return "day"
    if days_ago <= 7:
        return "week"
    if days_ago <= 30:
        return "month"
    if days_ago <= 365:
        return "year"
    return "all"


class RedditCollector(BaseCollector):
    source_id = "reddit"

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
        kwargs: sort ("relevance"|"new"|"hot"|"top").
        date_from viene approssimato al parametro 't'; post-filter in pipeline.
        """
        sort: str = str(kwargs.get("sort", "relevance"))
        time_filter = _approx_time_filter(date_from)

        if date_from and time_filter != "all":
            log.debug(
                "[reddit] date_from='%s' → t='%s' (approssimazione; post-filter in pipeline).",
                date_from, time_filter,
            )

        params = {
            "q":     query,
            "sort":  sort,
            "t":     time_filter,
            "limit": min(max_results, _MAX_RESULTS_CAP),
            "type":  "link",
        }
        headers = {"User-Agent": APP_USER_AGENT}

        try:
            response = http_get_with_retry(
                _BASE_URL,
                params=params,
                headers=headers,
                timeout=15,
                source_id=self.source_id,
            )
            if response.status_code == 403:
                log.warning("[RedditCollector] Accesso negato (HTTP 403).")
                return []
            if response.status_code == 429:
                log.warning("[RedditCollector] Rate limit (HTTP 429).")
                return []
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self._log_error(query, e)
            return []

        children = data.get("data", {}).get("children", [])
        records = [
            self._make_raw(target, query, child.get("data", {}))
            for child in children
            if child.get("data", {}).get("permalink")
        ]
        self._log_collected(query, len(records))
        return records
