"""
config.py — Configurazione centralizzata della pipeline (versione light).
Costanti NLP, soglie di qualità, chiavi API.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

YOUTUBE_API_KEY:       str | None = os.getenv("YOUTUBE_API_KEY")
NEWS_API_KEY:          str | None = os.getenv("NEWS_API_KEY")
GUARDIAN_API_KEY:      str | None = os.getenv("GUARDIAN_API_KEY")
NYT_API_KEY:           str | None = os.getenv("NYT_API_KEY")
STACKEXCHANGE_API_KEY: str | None = os.getenv("STACKEXCHANGE_API_KEY")
BRAVE_API_KEY:         str | None = os.getenv("BRAVE_API_KEY")

BLUESKY_HANDLE:        str | None = os.getenv("BLUESKY_HANDLE")
BLUESKY_APP_PASSWORD:  str | None = os.getenv("BLUESKY_APP_PASSWORD")

MASTODON_ACCESS_TOKEN:   str | None = os.getenv("MASTODON_ACCESS_TOKEN")
MASTODON_TOKEN_INSTANCE: str        = os.getenv("MASTODON_TOKEN_INSTANCE", "mastodon.social")

_mastodon_instances_env = os.getenv("MASTODON_INSTANCES")
MASTODON_INSTANCES: tuple[str, ...] = (
    tuple(i.strip() for i in _mastodon_instances_env.split(",") if i.strip())
    if _mastodon_instances_env
    else ("mastodon.social", "mastodon.online", "techhub.social")
)

_lemmy_instances_env = os.getenv("LEMMY_INSTANCES")
LEMMY_INSTANCES: tuple[str, ...] = (
    tuple(i.strip() for i in _lemmy_instances_env.split(",") if i.strip())
    if _lemmy_instances_env
    else ("lemmy.world", "lemmy.ml", "sh.itjust.works")
)

_hf_token = os.getenv("HF_TOKEN")
if _hf_token:
    os.environ["HF_TOKEN"] = _hf_token

APP_USER_AGENT: str = "wr-analysis-light/1.0 (academic research pipeline)"

# ---------------------------------------------------------------------------
# NLP — sentiment e language detection
# ---------------------------------------------------------------------------

# XLM-RoBERTa fine-tuned su Twitter in 8 lingue.
# Ref: https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment
SENTIMENT_MODEL: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

SENTIMENT_SUPPORTED_LANGS: frozenset[str] = frozenset({
    "ar", "en", "fr", "de", "hi", "it", "pt", "es",
})

NLP_MIN_LEN_DETECT:     int   = 15
NLP_MIN_LEN_SENTIMENT:  int   = 15

# Soglia di confidenza minima per langdetect. Sotto soglia → language=None.
NLP_LANG_DETECT_MIN_CONFIDENCE: float = 0.80

# ---------------------------------------------------------------------------
# Quality thresholds — usate da pipeline/cleaner.py
# ---------------------------------------------------------------------------

# Un record viene scartato solo se ENTRAMBI i campi sono sotto soglia.
MIN_TEXT_LENGTH:  int = 30
MIN_TITLE_LENGTH: int = 5

# Tetto massimo per `text` dopo la pulizia (XLM-RoBERTa: limite 512 token ≈ 350-600 char).
# 1500 char garantisce copertura NLP completa mantenendo file leggibili.
# Impostare a 0 per disabilitare il troncamento.
MAX_TEXT_LENGTH: int = 1500

BLOCKED_DOMAINS: frozenset[str] = frozenset({
    "consent.yahoo.com",
    "consent.google.com",
    "amp.google.com",
    "smartnews.com",
})
