"""Optional OpenAI API comparison for the assignment's GPT-3.5 baseline.

This module intentionally uses the Python standard library instead of the
OpenAI SDK so the base project remains dependency-free.  Set OPENAI_API_KEY
before running it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from .env import load_env_file
from .gpt35_baseline import build_zero_shot_prompt
from .search import SearchResult, TextbookSearchEngine


CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-3.5-turbo"


@dataclass(frozen=True)
class OpenAIRanking:
    model: str
    raw_text: str
    ranked_doc_ids: list[str]


def rank_candidates_with_openai(
    query: str,
    candidates: list[SearchResult],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> OpenAIRanking:
    """Ask OpenAI to zero-shot rerank BM25 candidates for a query."""

    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required to call the OpenAI API")

    model = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
    prompt = build_zero_shot_prompt(query, candidates)
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 80,
        "messages": [
            {
                "role": "system",
                "content": "Rank candidate textbook sections. Return only section ids, separated by commas.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    response_json = _post_json(CHAT_COMPLETIONS_URL, payload, api_key)
    raw_text = response_json["choices"][0]["message"]["content"].strip()
    valid_ids = [candidate.doc_id for candidate in candidates]
    return OpenAIRanking(
        model=model,
        raw_text=raw_text,
        ranked_doc_ids=parse_ranked_doc_ids(raw_text, valid_ids),
    )


def parse_ranked_doc_ids(text: str, valid_ids: list[str]) -> list[str]:
    """Extract a de-duplicated ranking while preserving the model's order."""

    valid_set = set(valid_ids)
    seen: set[str] = set()
    ranked: list[str] = []
    for match in re.findall(r"[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+", text):
        if match in valid_set and match not in seen:
            ranked.append(match)
            seen.add(match)

    for doc_id in valid_ids:
        if doc_id not in seen:
            ranked.append(doc_id)
    return ranked


def _post_json(url: str, payload: dict, api_key: str) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API request failed with HTTP {exc.code}: {body}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the zero-shot GPT-3.5 comparison via OpenAI API.")
    parser.add_argument("query", help="Topic or question to rerank")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of BM25 candidates to send")
    parser.add_argument("--model", default=None, help="OpenAI model id; defaults to OPENAI_MODEL or gpt-3.5-turbo")
    parser.add_argument("--env-file", default=None, help="Optional .env file containing OPENAI_API_KEY")
    args = parser.parse_args()

    load_env_file(args.env_file)
    engine = TextbookSearchEngine()
    candidates = engine.search(args.query, k=args.top_k)
    ranking = rank_candidates_with_openai(args.query, candidates, model=args.model)

    print(f"Model: {ranking.model}")
    print(f"Raw API response: {ranking.raw_text}")
    print("Parsed ranking:")
    for rank, doc_id in enumerate(ranking.ranked_doc_ids, start=1):
        print(f"{rank}. {doc_id}")


if __name__ == "__main__":
    main()
