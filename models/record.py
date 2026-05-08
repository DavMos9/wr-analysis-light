"""models/record.py — RawRecord (payload grezzo dai collector) e Record (modello normalizzato)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, ClassVar

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class RawRecord:
    """Payload grezzo di un collector. Il normalizer legge da payload senza trasformazioni."""

    source:       str
    query:        str
    target:       str
    payload:      dict[str, Any]
    retrieved_at: str

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("RawRecord.source non può essere vuoto")
        if not self.target:
            raise ValueError("RawRecord.target non può essere vuoto")
        if not isinstance(self.payload, dict):
            raise TypeError(
                f"RawRecord.payload deve essere un dict, ricevuto: {type(self.payload)}"
            )


@dataclass
class Record:
    """
    Modello normalizzato della pipeline light.

    Campi esportati (JSON): source, title, text, domain, language, sentiment,
                            date, url, target, topic, retrieved_at.
    Campi CSV:              source, date, target, topic, language, sentiment, url.
    """

    source:       str
    query:        str
    target:       str
    title:        str
    text:         str
    date:         str | None
    url:          str

    topic:        str          = ""
    domain:       str          = ""
    language:     str | None   = None
    sentiment:    float | None = None   # [-1.0, 1.0]
    retrieved_at: str          = ""

    # Ordine canonico campi export JSON — usato da to_dict() e json_exporter.
    _EXPORT_FIELDS: ClassVar[tuple[str, ...]] = (
        "source", "title", "text", "domain",
        "language", "sentiment", "date", "url",
        "target", "topic", "retrieved_at",
    )

    # Colonne CSV nell'ordine richiesto.
    _CSV_FIELDS: ClassVar[tuple[str, ...]] = (
        "source", "date", "target", "topic", "language", "sentiment", "url", "retrieved_at",
    )

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("Record.source non può essere vuoto")
        if not self.target:
            raise ValueError("Record.target non può essere vuoto")
        if not self.url:
            raise ValueError("Record.url non può essere vuoto")
        if self.date is not None and not _DATE_RE.match(self.date):
            raise ValueError(
                f"Record.date deve essere 'YYYY-MM-DD', ricevuto: '{self.date}'"
            )
        if self.sentiment is not None and not (-1.0 <= self.sentiment <= 1.0):
            raise ValueError(
                f"Record.sentiment deve essere in [-1.0, 1.0], ricevuto: {self.sentiment}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Dizionario JSON-safe con i campi nell'ordine canonico di export."""
        return {k: getattr(self, k) for k in self._EXPORT_FIELDS}

    def to_csv_dict(self) -> dict[str, Any]:
        """Dizionario con i soli campi CSV nell'ordine richiesto."""
        return {k: getattr(self, k) for k in self._CSV_FIELDS}

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    @classmethod
    def export_fields(cls) -> tuple[str, ...]:
        return cls._EXPORT_FIELDS

    @classmethod
    def csv_fields(cls) -> tuple[str, ...]:
        return cls._CSV_FIELDS
