"""utils/timestamp.py — Timestamp ISO 8601 UTC per naming dei file raw."""

from __future__ import annotations

from datetime import datetime, timezone


def now_timestamp() -> str:
    """Restituisce il timestamp UTC corrente in formato ISO 8601: '20260508T143200Z'."""
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
