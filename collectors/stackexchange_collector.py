"""
collectors/stackexchange_collector.py — Stack Exchange API v2.3 (/search/excerpts).

Supporto date nativo: fromdate / todate (Unix timestamp).
Senza API key: 300 req/giorno per IP. Con key: 10.000 req/giorno.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import requests

from collectors.base import BaseCollector
from collectors.retry import http_get_with_retry
from config import STACKEXCHANGE_API_KEY
from models import RawRecord

log = logging.getLogger(__name__)

_BASE_URL          = "https://api.stackexchange.com/2.3"
_MAX_PAGESIZE      = 100
_DEFAULT_SITES     = ("stackoverflow",)
_INTER_REQUEST_DELAY = 0.5


def _date_to_unix(date_str: str, end_of_day: bool = False) -> int:
    """Converte 'YYYY-MM-DD' in Unix timestamp UTC."""
    hour, minute, second = (23, 59, 59) if end_of_day else (0, 0, 0)
    dt = datetime(
        *[int(x) for x in date_str.split("-")],
        hour, minute, second,
        tzinfo=timezone.utc,
    )
    return int(dt.timestamp())


class StackExchangeCollector(BaseCollector):
    source_id = "stackexchange"

    def collect(
        self,
        target: str,
        query: str,
        max_results: int = 20,
        date_from: str | None = None,
        date_until: str | None = None,
        **kwargs: object,
    ) -> list[RawRecord]:
        """kwargs: sites (list[str]) — lista di siti Stack Exchange da interrogare."""
        sites: tuple[str, ...] = tuple(kwargs.get("sites", _DEFAULT_SITES))  # type: ignore[arg-type]
        per_site = max(1, max_results // len(sites))

        all_records: list[RawRecord] = []
        for site in sites:
            records = self._collect_site(target, query, site, per_site, date_from, date_until)
            all_records.extend(records)
            time.sleep(_INTER_REQUEST_DELAY)

        self._log_collected(query, len(all_records))
        return all_records

    def _collect_site(
        self,
        target: str,
        query: str,
        site: str,
        max_results: int,
        date_from: str | None,
        date_until: str | None,
    ) -> list[RawRecord]:
        params: dict[str, object] = {
            "q":       query,
            "site":    site,
            "pagesize": min(max_results, _MAX_PAGESIZE),
            "order":   "desc",
            "sort":    "relevance",
        }
        if STACKEXCHANGE_API_KEY:
            params["key"] = STACKEXCHANGE_API_KEY

        # Filtro date nativo StackExchange (Unix timestamp).
        if date_from:
            params["fromdate"] = _date_to_unix(date_from)
        if date_until:
            params["todate"] = _date_to_unix(date_until, end_of_day=True)

        try:
            response = http_get_with_retry(
                f"{_BASE_URL}/search/excerpts",
                params=params,
                timeout=10,
                source_id=self.source_id,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self._log_error(query, e)
            return []

        # Gestione backoff suggerito dall'API.
        backoff = data.get("backoff")
        if backoff:
            log.warning("[%s] Backoff richiesto dall'API: %ss.", self.source_id, backoff)
            time.sleep(int(backoff) + 1)

        quota_remaining = data.get("quota_remaining")
        if quota_remaining is not None and quota_remaining < 10:
            log.warning("[%s] Quota residua bassa: %d.", self.source_id, quota_remaining)

        items = data.get("items", [])
        return [
            self._make_raw(target, query, {**item, "_site": site})
            for item in items
            if item.get("question_id") or item.get("link")
        ]
