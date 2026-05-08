from __future__ import annotations

import logging
import threading
from dataclasses import replace
from typing import Any

from config import (
    SENTIMENT_MODEL as _SENTIMENT_MODEL,
    SENTIMENT_SUPPORTED_LANGS as _SENTIMENT_SUPPORTED_LANGS,
    NLP_MIN_LEN_DETECT as _MIN_LEN_DETECT,
    NLP_MIN_LEN_SENTIMENT as _MIN_LEN_SENTIMENT,
    NLP_LANG_DETECT_MIN_CONFIDENCE as _MIN_DETECT_CONFIDENCE,
)
from models import Record
from normalizers.utils import normalize_language_code as _normalize_lang

log = logging.getLogger(__name__)

try:
    from langdetect import DetectorFactory as _DF, detect_langs as _detect_langs
    _DF.seed = 0
    del _DF
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _detect_langs = None  # type: ignore[assignment]
    _LANGDETECT_AVAILABLE = False
    log.warning("langdetect non installato — language detection disabilitata.")

_UNSET: object = object()


def _build_analysis_text(record: Record) -> str:
    parts = [p.strip() for p in (record.title, record.text) if p and p.strip()]
    return " ".join(parts)


def _detect_language(text: str) -> str | None:
    if not _LANGDETECT_AVAILABLE or len(text) < _MIN_LEN_DETECT:
        return None
    try:
        results = _detect_langs(text)  # type: ignore[misc]
        if not results:
            return None
        top = results[0]
        if top.prob < _MIN_DETECT_CONFIDENCE:
            return None
        return _normalize_lang(top.lang)
    except Exception:
        return None


def _resolve_language(record: Record, text: str) -> str | None:
    existing = _normalize_lang(record.language)
    return existing if existing else _detect_language(text)


class Enricher:
    """Language detection e sentiment analysis per record. Modello caricato lazy al primo uso."""

    def __init__(self, sentiment_pipeline: Any = _UNSET) -> None:
        if sentiment_pipeline is _UNSET:
            self._pipeline: Any = None
            self._initialized = False
        else:
            self._pipeline = sentiment_pipeline
            self._initialized = True
        self._lock = threading.Lock()

    def _get_pipeline(self) -> Any | None:
        if self._initialized:
            return self._pipeline
        with self._lock:
            if self._initialized:
                return self._pipeline
            try:
                import os as _os, logging as _logging
                from transformers import pipeline as hf_pipeline

                for name in ("transformers", "transformers.modeling_utils"):
                    logging.getLogger(name).setLevel(_logging.ERROR)
                _os.environ["TQDM_DISABLE"] = "1"

                log.info("Caricamento modello sentiment '%s'...", _SENTIMENT_MODEL)
                self._pipeline = hf_pipeline(
                    task="sentiment-analysis",
                    model=_SENTIMENT_MODEL,
                    top_k=None,
                    truncation=True,
                    max_length=512,
                )
                log.info("Modello sentiment caricato.")
            except ImportError:
                log.warning("transformers/torch non installati — sentiment disabilitato.")
                self._pipeline = None
            except Exception as e:
                log.error("Errore caricamento modello: %s", e)
                self._pipeline = None
            finally:
                self._initialized = True
        return self._pipeline

    def _score(self, raw: list[dict]) -> float | None:
        label_scores = raw[0] if raw and isinstance(raw[0], list) else raw
        score_map = {item["label"].lower(): float(item["score"]) for item in label_scores}
        p = score_map.get("positive", 0.0)
        n = score_map.get("negative", 0.0)
        return round(max(-1.0, min(1.0, p - n)), 6)

    def enrich_all(self, records: list[Record]) -> list[Record]:
        if not records:
            return []

        pipe = self._get_pipeline()

        texts:  list[str]      = []
        langs:  list[str | None] = []
        for r in records:
            t = _build_analysis_text(r)
            texts.append(t)
            langs.append(_resolve_language(r, t))

        sentiment_map: dict[int, float | None] = {}
        if pipe is not None:
            batch_idx   = [
                i for i, (t, lang) in enumerate(zip(texts, langs))
                if t and len(t) >= _MIN_LEN_SENTIMENT
                and (lang is None or lang in _SENTIMENT_SUPPORTED_LANGS)
            ]
            batch_texts = [texts[i] for i in batch_idx]

            if batch_texts:
                try:
                    results = pipe(batch_texts)
                    for i, raw in zip(batch_idx, results):
                        sentiment_map[i] = self._score(raw)
                except Exception as e:
                    log.error("Errore batch sentiment: %s — fallback record-by-record.", e)
                    for i, text in zip(batch_idx, batch_texts):
                        try:
                            sentiment_map[i] = self._score(pipe(text))
                        except Exception as e2:
                            log.error("Errore sentiment record %d: %s", i, e2)

        enriched: list[Record] = []
        for i, (r, lang, _) in enumerate(zip(records, langs, texts)):
            updates: dict = {}
            if lang != r.language:
                updates["language"] = lang
            sentiment = sentiment_map.get(i)
            if sentiment != r.sentiment:
                updates["sentiment"] = sentiment
            enriched.append(replace(r, **updates) if updates else r)

        with_lang = sum(1 for r in enriched if r.language is not None)
        with_sent = sum(1 for r in enriched if r.sentiment is not None)
        log.info("Enrichment: %d/%d lingua, %d/%d sentiment.", with_lang, len(enriched), with_sent, len(enriched))
        return enriched
