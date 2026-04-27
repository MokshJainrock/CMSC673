"""Small tokenizer for textbook retrieval.

The goal is deterministic matching rather than linguistic perfection.  This
keeps the project runnable without an external model download.
"""

from __future__ import annotations

import re


TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with",
}


def tokenize(text: str) -> list[str]:
    """Return lowercase word-like tokens from ``text`` without common stopwords."""

    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]
