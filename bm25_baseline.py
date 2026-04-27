
"""Backward-compatible wrapper around the package search engine."""

from __future__ import annotations

import sys

from textbook_search.search import TextbookSearchEngine


def search(query: str, k: int = 3):
    engine = TextbookSearchEngine()
    return [(result.doc_id, result.snippet, result.score) for result in engine.search(query, k=k)]


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "photosynthesis"
    print(f"Query: {query}\n")
    for doc_id, text, score in search(query):
        print(f"{doc_id} ({score:.2f}): {text[:100]}...")
