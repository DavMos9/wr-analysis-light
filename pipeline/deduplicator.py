from __future__ import annotations

import logging
import re

from models import Record

log = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _normalize_title(title: str) -> str:
    t = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", " ", t).strip()


def deduplicate(records: list[Record]) -> tuple[list[Record], int]:
    """
    Deduplicazione content-based:
    - Se il record ha testo: chiave = testo normalizzato.
    - Se il record non ha testo: chiave = titolo normalizzato (fallback).
    Record senza né testo né titolo vengono sempre mantenuti.
    """
    seen: set[str] = set()
    unique: list[Record] = []
    removed = 0

    for r in records:
        text = (r.text or "").strip()
        title = (r.title or "").strip()

        if text:
            key = _normalize_text(text)
        elif title:
            key = f"__title__{_normalize_title(title)}"
        else:
            unique.append(r)
            continue

        if key in seen:
            removed += 1
        else:
            seen.add(key)
            unique.append(r)

    log.info("Deduplicazione: %d rimossi, %d unici.", removed, len(unique))
    return unique, removed


def deduplicate_against(
    new_records: list[Record],
    existing_records: list[Record],
) -> list[Record]:
    """
    Filtra new_records scartando quelli già presenti in existing_records.
    Usato nel merge intraday: i record esistenti non vengono restituiti,
    si ottiene solo la lista dei nuovi record non duplicati.
    """
    seen: set[str] = set()

    for r in existing_records:
        text = (r.text or "").strip()
        title = (r.title or "").strip()
        if text:
            seen.add(_normalize_text(text))
        elif title:
            seen.add(f"__title__{_normalize_title(title)}")

    result: list[Record] = []
    for r in new_records:
        text = (r.text or "").strip()
        title = (r.title or "").strip()
        if text:
            key = _normalize_text(text)
        elif title:
            key = f"__title__{_normalize_title(title)}"
        else:
            result.append(r)
            continue

        if key not in seen:
            seen.add(key)
            result.append(r)

    return result
