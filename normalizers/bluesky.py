from __future__ import annotations

from models import RawRecord, Record
from normalizers.registry import register
from normalizers.utils import to_date, to_url, first_non_empty


def _normalize(raw: RawRecord) -> Record:
    p = raw.payload
    record_data = p.get("record", {})

    uri = p.get("uri", "")
    handle = p.get("author", {}).get("handle", "")
    rkey = uri.rsplit("/", 1)[-1] if uri else ""

    url = to_url(
        f"https://bsky.app/profile/{handle}/post/{rkey}"
        if handle and rkey else ""
    )

    return Record(
        source=raw.source,
        title="",
        text=first_non_empty(record_data.get("text")),
        date=to_date(record_data.get("createdAt") or p.get("indexedAt")),
        url=url,
        query=raw.query,
        target=raw.target,
        language=None,
        domain="bsky.app",
        retrieved_at=raw.retrieved_at,
    )


register("bluesky", _normalize)
