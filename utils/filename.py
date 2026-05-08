"""utils/filename.py — Generazione nomi file canonici per output e raw."""

from __future__ import annotations

import re
import unicodedata


def _to_camel_words(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    words = re.split(r"[^a-zA-Z0-9]+", ascii_text)
    return "".join(w.capitalize() for w in words if w)


def build_filename(target: str, topic: str) -> str:
    """
    Genera il nome base del file (senza estensione) nel formato:
        {TargetCamelCase}{TopicCamelCase}

    Il file è unico per (target, topic) e cresce nel tempo accumulando
    record di run successive. Le date di ricerca sono metadato per riga,
    non parte del nome file.

    Esempi:
        build_filename("Zendaya", "Euphoria")       → "ZendayaEuphoria"
        build_filename("Jacob Elordi", "Saltburn")  → "JacobElordiSaltburn"

    Args:
        target: Nome del target.
        topic:  Topic di ricerca.

    Returns:
        Stringa nome file senza estensione.
    """
    return f"{_to_camel_words(target)}{_to_camel_words(topic)}"
