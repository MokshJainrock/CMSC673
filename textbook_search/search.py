"""Search API and command-line helpers for textbook section retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from .bm25 import BM25Index
from .loader import Document, load_corpus
from .tokenizer import tokenize


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    score: float
    textbook: str
    chapter: str
    section: str
    title: str
    source_url: str
    snippet: str


class TextbookSearchEngine:
    def __init__(self, documents: list[Document] | None = None):
        self.documents = documents if documents is not None else load_corpus()
        self._index = BM25Index([tokenize(doc.searchable_text) for doc in self.documents])

    def search(self, query: str, k: int = 5) -> list[SearchResult]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._index.get_scores(query_tokens)
        ranked = sorted(enumerate(scores), key=lambda item: (-item[1], self.documents[item[0]].doc_id))
        results: list[SearchResult] = []
        for doc_index, score in ranked:
            if score <= 0:
                continue
            document = self.documents[doc_index]
            results.append(
                SearchResult(
                    doc_id=document.doc_id,
                    score=score,
                    textbook=document.textbook,
                    chapter=document.chapter,
                    section=document.section,
                    title=document.title,
                    source_url=document.source_url,
                    snippet=_snippet(document.text),
                )
            )
            if len(results) >= k:
                break
        return results


def _snippet(text: str, max_chars: int = 220) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rsplit(" ", 1)[0] + "..."
