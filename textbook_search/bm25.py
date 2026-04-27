"""Pure-Python Okapi BM25 implementation.

Formula follows the standard BM25 scoring function described in Robertson and
Zaragoza (2009).  Implementing the compact scorer locally avoids an assignment
dependency on Java search stacks or NLTK data downloads.
"""

from __future__ import annotations

from collections import Counter
from math import log


class BM25Index:
    def __init__(self, tokenized_documents: list[list[str]], k1: float = 1.5, b: float = 0.75):
        if not tokenized_documents:
            raise ValueError("BM25Index requires at least one document")
        self.k1 = k1
        self.b = b
        self.doc_count = len(tokenized_documents)
        self.doc_lengths = [len(doc) for doc in tokenized_documents]
        self.avg_doc_length = sum(self.doc_lengths) / self.doc_count
        self.term_frequencies = [Counter(doc) for doc in tokenized_documents]
        self.idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        document_frequencies: Counter[str] = Counter()
        for frequencies in self.term_frequencies:
            document_frequencies.update(frequencies.keys())

        return {
            term: log(1 + (self.doc_count - df + 0.5) / (df + 0.5))
            for term, df in document_frequencies.items()
        }

    def score(self, query_tokens: list[str], doc_index: int) -> float:
        score = 0.0
        frequencies = self.term_frequencies[doc_index]
        doc_length = self.doc_lengths[doc_index]
        length_norm = self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)

        for term in query_tokens:
            term_frequency = frequencies.get(term, 0)
            if term_frequency == 0:
                continue
            numerator = term_frequency * (self.k1 + 1)
            denominator = term_frequency + length_norm
            score += self.idf.get(term, 0.0) * numerator / denominator
        return score

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        return [self.score(query_tokens, index) for index in range(self.doc_count)]
