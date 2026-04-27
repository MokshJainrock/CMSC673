"""Run the full textbook-search project workflow.

Examples:
    python3 scripts/run_full.py
    python3 scripts/run_full.py --with-openai
    python3 scripts/run_full.py --with-openai --env-file /path/to/.env
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUERY = "Krebs cycle acetyl CoA"
DEFAULT_ENV_FILES = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT.parent / "shrinkflation-detector" / ".env",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run tests, searches, evaluation, and optional OpenAI reranking.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Sample query for the search demos")
    parser.add_argument("--with-openai", action="store_true", help="Also run live OpenAI GPT-3.5 calls")
    parser.add_argument("--env-file", default=None, help="Optional .env file containing OPENAI_API_KEY")
    args = parser.parse_args()

    env_file = Path(args.env_file).expanduser() if args.env_file else _detect_env_file()

    steps = [
        ("Unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
        ("Main search", [sys.executable, "main.py", args.query, "-k", "5"]),
        ("Compatibility baseline", [sys.executable, "bm25_baseline.py", "photosynthesis"]),
        (
            "BM25 evaluation",
            [
                sys.executable,
                "-m",
                "textbook_search.evaluate",
                "--json-out",
                "reports/bm25_results.json",
            ],
        ),
        ("GPT prompt preview", [sys.executable, "main.py", args.query, "-k", "5", "--gpt-prompt"]),
    ]

    if args.with_openai:
        openai_args = ["--env-file", str(env_file)] if env_file else []
        steps.extend(
            [
                (
                    "OpenAI single-query rerank",
                    [sys.executable, "main.py", args.query, "-k", "5", "--gpt-api", *openai_args],
                ),
                (
                    "OpenAI full evaluation",
                    [
                        sys.executable,
                        "-m",
                        "textbook_search.evaluate",
                        "--openai-rerank",
                        "--json-out",
                        "reports/openai_rerank_results.json",
                        *openai_args,
                    ],
                ),
            ]
        )
    else:
        print("OpenAI API steps skipped. Add --with-openai to run them.\n")

    for title, command in steps:
        print(f"\n=== {title} ===", flush=True)
        print(" ".join(command), flush=True)
        completed = subprocess.run(command, cwd=PROJECT_ROOT, env=os.environ.copy())
        if completed.returncode != 0:
            print(f"\nFAILED: {title}", file=sys.stderr)
            return completed.returncode

    print("\nFull workflow completed.")
    return 0


def _detect_env_file() -> Path | None:
    if os.environ.get("OPENAI_API_KEY"):
        return None
    for path in DEFAULT_ENV_FILES:
        if path.exists():
            return path
    return None


if __name__ == "__main__":
    raise SystemExit(main())
