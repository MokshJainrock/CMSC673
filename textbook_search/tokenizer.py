"""Small tokenizer for textbook retrieval.

The goal is deterministic matching rather than linguistic perfection.  This
keeps the project runnable without an external model download.
"""

from __future__ import annotations

import re


TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")


def tokenize(text: str) -> list[str]:
    """Return lowercase word-like tokens from ``text``."""

    return TOKEN_RE.findall(text.lower())
