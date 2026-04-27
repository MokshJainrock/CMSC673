"""CLI entry point for textbook search."""

from __future__ import annotations

import argparse

from textbook_search.env import load_env_file
from textbook_search.gpt35_baseline import build_zero_shot_prompt
from textbook_search.openai_compare import rank_candidates_with_openai
from textbook_search.search import TextbookSearchEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Search an OpenStax-style textbook section corpus.")
    parser.add_argument("query", help="Topic or question to search for")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of results to print")
    parser.add_argument("--gpt-prompt", action="store_true", help="Print a zero-shot GPT-3.5 ranking prompt")
    parser.add_argument("--gpt-api", action="store_true", help="Call OpenAI API to rerank the BM25 candidates")
    parser.add_argument("--model", default=None, help="OpenAI model id for --gpt-api")
    parser.add_argument("--env-file", default=None, help="Optional .env file containing OPENAI_API_KEY")
    args = parser.parse_args()

    load_env_file(args.env_file)
    engine = TextbookSearchEngine()
    results = engine.search(args.query, k=args.top_k)

    if args.gpt_prompt:
        print(build_zero_shot_prompt(args.query, results))
        return

    if args.gpt_api:
        ranking = rank_candidates_with_openai(args.query, results, model=args.model)
        print(f"OpenAI model: {ranking.model}")
        print(f"Raw API response: {ranking.raw_text}\n")
        print("GPT-3.5 zero-shot ranking:")
        for rank, doc_id in enumerate(ranking.ranked_doc_ids, start=1):
            print(f"{rank}. {doc_id}")
        return

    print(f"Query: {args.query}\n")
    for rank, result in enumerate(results, start=1):
        print(f"{rank}. {result.doc_id} | {result.score:.3f} | {result.title}")
        print(f"   {result.textbook} - {result.chapter}, {result.section}")
        print(f"   {result.snippet}")
        print(f"   Source: {result.source_url}\n")


if __name__ == "__main__":
    main()
