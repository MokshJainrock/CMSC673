from __future__ import annotations

from .search import SearchResult


def build_zero_shot_prompt(query: str, candidates: list[SearchResult]) -> str:
    lines = [
        "You are ranking textbook sections for a student search query.",
        "Return only a comma-separated list of section ids ordered from most to least useful.",
        f"Query: {query}",
        "Candidate sections:",
    ]
    for result in candidates:
        lines.append(
            f"- {result.doc_id}: {result.textbook}, {result.chapter}, {result.title}. {result.snippet}"
        )
    return "\n".join(lines)
