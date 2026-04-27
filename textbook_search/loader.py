"""Load textbook section corpora and evaluation queries."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "corpus.jsonl"
DEFAULT_EVAL_PATH = PROJECT_ROOT / "data" / "eval_queries.json"


@dataclass(frozen=True)
class Document:
    doc_id: str
    textbook: str
    chapter: str
    section: str
    title: str
    source_url: str
    text: str

    @property
    def searchable_text(self) -> str:
        return f"{self.textbook} {self.chapter} {self.section} {self.title} {self.text}"


def load_corpus(path: str | Path = DEFAULT_CORPUS_PATH) -> list[Document]:
    corpus_path = Path(path)
    documents: list[Document] = []
    with corpus_path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row: dict[str, Any] = json.loads(line)
            try:
                documents.append(
                    Document(
                        doc_id=row["id"],
                        textbook=row["textbook"],
                        chapter=row["chapter"],
                        section=row["section"],
                        title=row["title"],
                        source_url=row["source_url"],
                        text=row["text"],
                    )
                )
            except KeyError as exc:
                raise ValueError(f"Missing {exc.args[0]!r} in {corpus_path}:{line_number}") from exc
    if not documents:
        raise ValueError(f"No documents loaded from {corpus_path}")
    return documents


def load_eval_queries(path: str | Path = DEFAULT_EVAL_PATH) -> list[dict[str, Any]]:
    eval_path = Path(path)
    with eval_path.open(encoding="utf-8") as f:
        queries = json.load(f)
    if not isinstance(queries, list) or not queries:
        raise ValueError(f"Evaluation file must contain a non-empty list: {eval_path}")
    return queries
