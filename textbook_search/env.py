"""Minimal .env loading for optional API credentials."""

from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str | Path | None = None) -> Path | None:
    """Load KEY=VALUE pairs from a .env file if one is available.

    Existing environment variables win, so shell-provided secrets are never
    overwritten by a file. Values are intentionally not logged by callers.
    """

    candidates = [Path(path)] if path else [Path(".env")]
    for candidate in candidates:
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return candidate
    return None
