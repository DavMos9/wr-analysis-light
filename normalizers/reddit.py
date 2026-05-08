from __future__ import annotations

from models import RawRecord, Record
from normalizers.registry import register
from normalizers.utils import to_date, to_url, to_domain, first_non_empty, strip_html

_REDDIT_BASE = "https://www.reddit.com"
_REMOVED_TEXTS = {"[removed]", "[deleted]", ""}


def _normalize(raw: RawRecord) -> Record:
    p = raw.payload

    permalink = p.get("permalink", "")
    url = to_url(f"{_REDDIT_BASE}{permalink}") if permalink else ""

    selftext = str(p.get("selftext") or "").strip()
    text = strip_html(selftext) if selftext not in _REMOVED_TEXTS else ""

    # created_utc è float (epoch seconds); to_date non gestisce epoch, convertiamo prima.
    created_utc = p.get("created_utc")
    date_str: str | None = None
    if created_utc is not None:
        try:
            from datetime import datetime, timezone
            date_str = datetime.fromtimestamp(float(created_utc), tz=timezone.utc).strftime("%Y-%m-%d")
        except (ValueError, OSError, OverflowError):
            date_str = None

    return Record(
        source=raw.source,
        title=first_non_empty(p.get("title")),
        text=text,
        date=date_str,
        url=url,
        query=raw.query,
        target=raw.target,
        language=None,
        domain=to_domain(url),
        retrieved_at=raw.retrieved_at,
    )


register("reddit", _normalize)
