from __future__ import annotations

import html
import logging
import re
import unicodedata
from dataclasses import replace

from config import MIN_TEXT_LENGTH, MIN_TITLE_LENGTH, BLOCKED_DOMAINS, MAX_TEXT_LENGTH
from models import Record

log = logging.getLogger(__name__)

_REQUIRED_STR = ("source", "title", "text", "url", "query", "target", "domain")
_OPTIONAL_STR = ("language",)


def _clean_str(value: str | None) -> str:
    if value is None:
        return ""
    raw = html.unescape(str(value).strip())
    raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f  ]", "", raw)
    raw = re.sub(r"[ \t\xa0]+", " ", raw)
    return unicodedata.normalize("NFC", raw.strip())


def _truncate_text(text: str) -> str:
    if not MAX_TEXT_LENGTH or len(text) <= MAX_TEXT_LENGTH:
        return text
    truncated = text[:MAX_TEXT_LENGTH]
    floor = MAX_TEXT_LENGTH // 2

    last_sentence = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
    if last_sentence > floor:
        return truncated[:last_sentence + 1]

    last_space = truncated.rfind(" ")
    if last_space > floor:
        return truncated[:last_space]

    return truncated


def clean(record: Record) -> Record:
    updates: dict = {}
    for f in _REQUIRED_STR:
        cleaned = _clean_str(getattr(record, f, ""))
        if f == "text":
            cleaned = _truncate_text(cleaned)
        if cleaned != getattr(record, f, ""):
            updates[f] = cleaned
    for f in _OPTIONAL_STR:
        val = _clean_str(getattr(record, f, None))
        result = val if val else None
        if result != getattr(record, f, None):
            updates[f] = result
    return replace(record, **updates) if updates else record


def clean_all(records: list[Record]) -> list[Record]:
    return [clean(r) for r in records]


def filter_quality(records: list[Record]) -> tuple[list[Record], int]:
    valid: list[Record] = []
    skipped = 0
    for r in records:
        if r.domain and r.domain in BLOCKED_DOMAINS:
            log.warning("[cleaner] Dominio bloccato [source=%s, domain=%s]", r.source, r.domain)
            skipped += 1
            continue
        text_len  = len(r.text  or "")
        title_len = len(r.title or "")
        if text_len < MIN_TEXT_LENGTH and title_len < MIN_TITLE_LENGTH:
            log.debug(
                "[cleaner] Scartato per qualità [source=%s, url=%s]: testo=%d, titolo=%d",
                r.source, r.url, text_len, title_len,
            )
            skipped += 1
        else:
            valid.append(r)
    if skipped:
        log.info("[cleaner] Scartati %d record per qualità insufficiente.", skipped)
    return valid, skipped
