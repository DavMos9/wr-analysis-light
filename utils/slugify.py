"""utils/slugify.py — Conversione di stringhe in slug sicuri per filesystem."""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str, separator: str = "_") -> str:
    """
    Converte una stringa in uno slug filesystem-safe.

    "Jacob Elordi" → "jacob_elordi"
    "Euphoria & Fame" → "euphoria_fame"

    Args:
        text:      Stringa da convertire.
        separator: Carattere separatore (default: '_').

    Returns:
        Slug in minuscolo, senza caratteri speciali.
    """
    # Normalizza unicode (NFD) e rimuove i diacritici (Mn = Mark, Nonspacing).
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    # Porta tutto in minuscolo.
    lower = ascii_text.lower()

    # Sostituisce qualsiasi sequenza di caratteri non alfanumerici con il separatore.
    slug = re.sub(r"[^a-z0-9]+", separator, lower)

    # Rimuove separatori iniziali/finali.
    return slug.strip(separator)
