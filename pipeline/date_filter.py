from __future__ import annotations

import logging
from datetime import date

from models import Record

log = logging.getLogger(__name__)


def parse_date(value: str) -> str:
    """Valida 'YYYY-MM-DD'. Lancia ValueError se invalido."""
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"formato atteso 'YYYY-MM-DD', ricevuto {value!r}") from e
    return value


def filter_by_date_range(
    records: list[Record],
    date_from: str | None,
    date_until: str | None,
) -> tuple[list[Record], int]:
    """
    Filtra i record al di fuori del range [date_from, date_until].
    Record con date=None vengono sempre mantenuti.
    """
    if not date_from and not date_until:
        return records, 0

    from_date  = date.fromisoformat(date_from)  if date_from  else None
    until_date = date.fromisoformat(date_until) if date_until else None

    kept: list[Record] = []
    dropped = 0

    for r in records:
        if not r.date:
            kept.append(r)
            continue
        try:
            record_date = date.fromisoformat(r.date)
        except (ValueError, TypeError):
            kept.append(r)
            continue

        if from_date  and record_date < from_date:
            dropped += 1
            continue
        if until_date and record_date > until_date:
            dropped += 1
            continue
        kept.append(r)

    if dropped:
        log.info("[date_filter] Scartati %d record fuori dal range [%s, %s].", dropped, date_from, date_until)
    return kept, dropped
