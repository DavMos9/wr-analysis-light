"""
collectors/gdelt_collector.py — GDELT DOC 2.0. Gratuito, senza API key.

Supporto date nativo: STARTDATETIME / ENDDATETIME (formato YYYYMMDDHHMMSS).
"""

from __future__ import annotations

import logging
import random
import re
import time

import requests

from collectors.base import BaseCollector
from models import RawRecord

log = logging.getLogger(__name__)

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

_REQUEST_DELAY = 3.0
_MAX_RETRIES   = 3
_MAX_BACKOFF   = 60.0
_JITTER_RANGE  = (0.75, 1.25)
_BODY_PREVIEW  = 300
_MIN_TOKEN_LEN = 3


def _compute_backoff(attempt: int) -> float:
    base = _REQUEST_DELAY * (2 ** attempt)
    return min(base, _MAX_BACKOFF) * random.uniform(*_JITTER_RANGE)


def _sanitize_gdelt_query(query: str) -> str:
    tokens = query.strip().split()
    valid_tokens = [t for t in tokens if len(re.sub(r"[^\w]", "", t)) >= _MIN_TOKEN_LEN]
    if valid_tokens:
        sanitized = " ".join(valid_tokens)
    else:
        sanitized = f'"{query.strip()}"'
    if sanitized != query:
        log.debug("[gdelt] Query sanitizzata: '%s' → '%s'", query, sanitized)
    return sanitized


def _to_gdelt_dt(date_str: str, end_of_day: bool = False) -> str:
    """Converte 'YYYY-MM-DD' in 'YYYYMMDDHHMMSS' per GDELT."""
    d = date_str.replace("-", "")
    return f"{d}235959" if end_of_day else f"{d}000000"


class GdeltCollector(BaseCollector):
    source_id = "gdelt"

    def collect(
        self,
        target: str,
        query: str,
        max_results: int = 75,
        date_from: str | None = None,
        date_until: str | None = None,
        **kwargs: object,
    ) -> list[RawRecord]:
        sanitized_query = _sanitize_gdelt_query(query)

        params: dict[str, object] = {
            "query":      sanitized_query,
            "mode":       "artlist",
            "maxrecords": min(max_results, 250),
            "format":     "json",
            "sort":       "datedesc",
        }

        # Filtro date nativo GDELT.
        if date_from:
            params["STARTDATETIME"] = _to_gdelt_dt(date_from, end_of_day=False)
        if date_until:
            params["ENDDATETIME"] = _to_gdelt_dt(date_until, end_of_day=True)

        data = self._request_with_retry(params, query)
        if data is None:
            return []

        articles = data.get("articles", [])
        if not isinstance(articles, list):
            log.warning(
                "[%s] Campo 'articles' inatteso (tipo: %s). Query: '%s'",
                self.source_id, type(articles).__name__, query,
            )
            return []

        records = [
            self._make_raw(target, query, article)
            for article in articles
            if article.get("url")
        ]
        self._log_collected(query, len(records))
        return records

    def _request_with_retry(self, params: dict, query: str) -> dict | None:
        time.sleep(_REQUEST_DELAY)

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = requests.get(BASE_URL, params=params, timeout=15)

                if response.status_code == 429:
                    if attempt == _MAX_RETRIES:
                        log.warning("[%s] Rate limit persistente. Query saltata: '%s'", self.source_id, query)
                        return None
                    time.sleep(_compute_backoff(attempt))
                    continue

                response.raise_for_status()

                if not response.content:
                    if attempt == _MAX_RETRIES:
                        log.warning("[%s] Risposta vuota persistente. Query saltata: '%s'", self.source_id, query)
                        return None
                    time.sleep(_compute_backoff(attempt))
                    continue

                content_type = response.headers.get("Content-Type", "")
                if "json" not in content_type and "javascript" not in content_type:
                    log.warning(
                        "[%s] Content-Type inatteso '%s'. Anteprima: %r. Query: '%s'",
                        self.source_id, content_type, response.text[:_BODY_PREVIEW], query,
                    )
                    return None

                return response.json()

            except requests.exceptions.HTTPError as e:
                self._log_error(query, e)
                if attempt == _MAX_RETRIES:
                    return None
                time.sleep(_compute_backoff(attempt))

            except requests.RequestException as e:
                self._log_error(query, e)
                if attempt == _MAX_RETRIES:
                    return None
                time.sleep(_compute_backoff(attempt))

            except ValueError as e:
                log.error("[%s] JSON non valido. Errore: %s. Query: '%s'", self.source_id, e, query)
                return None

        return None
