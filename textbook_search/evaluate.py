"""Evaluate textbook retrieval with Precision@k, Recall@k, MRR, and NDCG."""

from __future__ import annotations

import argparse
import json
import math
from typing import Any

from .env import load_env_file
from .loader import load_eval_queries
from .openai_compare import rank_candidates_with_openai
from .search import TextbookSearchEngine


def precision_at_k(relevance: dict[str, int], retrieved: list[str], k: int) -> float:
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    relevant_count = sum(1 for doc_id in top_k if relevance.get(doc_id, 0) > 0)
    return relevant_count / len(top_k)


def recall_at_k(relevance: dict[str, int], retrieved: list[str], k: int) -> float:
    relevant_total = sum(1 for grade in relevance.values() if grade > 0)
    if relevant_total == 0:
        return 0.0
    found = sum(1 for doc_id in retrieved[:k] if relevance.get(doc_id, 0) > 0)
    return found / relevant_total


def reciprocal_rank(relevance: dict[str, int], retrieved: list[str]) -> float:
    for rank, doc_id in enumerate(retrieved, start=1):
        if relevance.get(doc_id, 0) > 0:
            return 1 / rank
    return 0.0


def ndcg_at_k(relevance: dict[str, int], retrieved: list[str], k: int) -> float:
    def dcg(grades: list[int]) -> float:
        return sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(grades))

    gains = [relevance.get(doc_id, 0) for doc_id in retrieved[:k]]
    ideal = sorted(relevance.values(), reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    return 0.0 if ideal_dcg == 0 else dcg(gains) / ideal_dcg


def evaluate(k: int = 5, openai_rerank: bool = False, model: str | None = None) -> dict[str, Any]:
    engine = TextbookSearchEngine()
    queries = load_eval_queries()
    per_query: list[dict[str, Any]] = []

    for item in queries:
        relevance = {doc_id: int(grade) for doc_id, grade in item["relevance"].items()}
        candidates = engine.search(item["query"], k=k)
        openai_model = None
        openai_raw_text = None
        if openai_rerank:
            ranking = rank_candidates_with_openai(item["query"], candidates, model=model)
            retrieved = ranking.ranked_doc_ids
            openai_model = ranking.model
            openai_raw_text = ranking.raw_text
        else:
            retrieved = [result.doc_id for result in candidates]
        row = {
            "query": item["query"],
            "retrieved": retrieved,
            "precision_at_3": precision_at_k(relevance, retrieved, 3),
            "recall_at_5": recall_at_k(relevance, retrieved, 5),
            "mrr": reciprocal_rank(relevance, retrieved),
            "ndcg_at_5": ndcg_at_k(relevance, retrieved, 5),
        }
        if openai_rerank:
            row["openai_model"] = openai_model
            row["openai_raw_text"] = openai_raw_text
        per_query.append(row)

    summary = {
        "system": "openai_reranker" if openai_rerank else "bm25",
        "candidate_count": k,
        "queries": len(per_query),
        "precision_at_3": _mean(row["precision_at_3"] for row in per_query),
        "recall_at_5": _mean(row["recall_at_5"] for row in per_query),
        "mrr": _mean(row["mrr"] for row in per_query),
        "ndcg_at_5": _mean(row["ndcg_at_5"] for row in per_query),
    }
    return {"summary": summary, "per_query": per_query}


def _mean(values) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the textbook BM25 retriever.")
    parser.add_argument("--k", type=int, default=5, help="Number of retrieved documents to evaluate")
    parser.add_argument("--openai-rerank", action="store_true", help="Use OpenAI API to rerank BM25 candidates")
    parser.add_argument("--model", default=None, help="OpenAI model id for --openai-rerank")
    parser.add_argument("--env-file", default=None, help="Optional .env file containing OPENAI_API_KEY")
    parser.add_argument("--json-out", default=None, help="Optional path to write machine-readable results")
    args = parser.parse_args()
    load_env_file(args.env_file)
    report = evaluate(k=args.k, openai_rerank=args.openai_rerank, model=args.model)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    summary = report["summary"]
    label = "OpenAI reranker" if args.openai_rerank else "BM25"
    print(f"System: {label}")
    print(f"Queries: {summary['queries']}")
    print(f"Precision@3: {summary['precision_at_3']:.3f}")
    print(f"Recall@5: {summary['recall_at_5']:.3f}")
    print(f"MRR: {summary['mrr']:.3f}")
    print(f"NDCG@5: {summary['ndcg_at_5']:.3f}")
    print("\nPer-query top results:")
    for row in report["per_query"]:
        print(f"- {row['query']}: {', '.join(row['retrieved'])}")


if __name__ == "__main__":
    main()
