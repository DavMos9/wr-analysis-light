from __future__ import annotations

import html
import re

from models import RawRecord, Record
from normalizers.registry import register
from normalizers.utils import to_date, to_url, HTML_TAG_RE


def _html_to_text(content: str) -> str:
    """HTML Mastodon → testo pulito (br/paragrafi → newline, strip tag e entità)."""
    if not content:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", content)
    text = re.sub(r"</p>\s*<p>", "\n\n", text)
    text = HTML_TAG_RE.sub("", text)
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text.strip()


def _normalize(raw: RawRecord) -> Record:
    p = raw.payload
    instance = p.get("_instance", "mastodon.social")

    content_html = p.get("content", "")
    spoiler_text = p.get("spoiler_text", "")
    text = _html_to_text(content_html)

    title = spoiler_text.strip() if spoiler_text else ""
    post_url = to_url(p.get("url") or p.get("uri", ""))

    return Record(
        source=raw.source,
        title=title,
        text=text,
        date=to_date(p.get("created_at")),
        url=post_url,
        query=raw.query,
        target=raw.target,
        language=p.get("language"),
        domain=instance,
        retrieved_at=raw.retrieved_at,
    )


register("mastodon", _normalize)
