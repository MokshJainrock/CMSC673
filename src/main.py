"""
Running  a single search from the command line to get rulkts below

Examples:
    python -m src.main "krebs cycle"
    python -m src.main "what is photosynthesis" --rerank
    python -m src.main "what is nlp"               # triggers no-results
"""

import argparse

from src.search import load_corpus, build_bm25, bm25_search, dense_rerank


THRESHOLD = 0.5


def main():
    p = argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("--rerank", action="store_true", help="use minilm reranker")
    p.add_argument("--k", type=int, default=5)
    args = p.parse_args()

    corpus = load_corpus()
    bm25 = build_bm25(corpus)
    hits = bm25_search(bm25, corpus, args.query, k=25)

    print(f"\nquery: {args.query}")

    if not hits or hits[0][1] < THRESHOLD:
        top = hits[0][1] if hits else 0.0
        print(f"\nNo relevant sections found. (top score {top:.3f} < {THRESHOLD})\n")
        return

    if args.rerank:
        hits = dense_rerank(args.query, hits, k=args.k)
    else:
        hits = hits[:args.k]

    print()
    for i, (d, score) in enumerate(hits, 1):
        print(f"{i}. [{d['id']}] {d['title']}   ({score:.3f})")
        print(f"   {d.get('source','')} - {d.get('chapter','')}")
        print(f"   {d['text'][:180]}...")
        print()


if __name__ == "__main__":
    main()
