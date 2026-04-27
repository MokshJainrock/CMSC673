---
title: "Summary of Changes"
subtitle: "CMSC 473/673 NLP Graduate Assignment"
author: "Moksh Jain"
date: "May 14, 2026"
geometry: margin=1in
fontsize: 11pt
---

# Summary

The project changed from a very small BM25 prototype into an end-to-end textbook search system. The current version includes structured data, deterministic BM25 retrieval, a command-line interface, evaluation metrics, tests, and a live zero-shot GPT-3.5 comparison through the OpenAI API.

# Changes Made

- Replaced the dependency-heavy prototype with a local Python package under `textbook_search/`.
- Added a pure-Python BM25 implementation and deterministic tokenizer.
- Added a 24-section OpenStax-derived corpus in `data/corpus.jsonl`.
- Added 12 manually labeled evaluation queries in `data/eval_queries.json`.
- Added Precision@3, Recall@5, MRR, and NDCG@5 evaluation.
- Added an OpenAI API reranker for the required GPT-3.5 comparison.
- Added JSON result files for BM25 and GPT-3.5 reranking.
- Added unit tests for search behavior, metrics, environment loading, and GPT output parsing.
- Updated README instructions with search, evaluation, testing, and API usage examples.

# Feedback Use

No peer-review feedback was available at the time of this revision. The changes above were made proactively to address the assignment requirements: completeness of implementation, clear data description, evaluation results, correctness testing, GPT-3.5 comparison, and documentation.

# Current Results

| System | Precision@3 | Recall@5 | MRR | NDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| BM25 baseline | 0.500 | 0.875 | 1.000 | 0.978 |
| Zero-shot GPT-3.5 reranker | 0.500 | 0.875 | 1.000 | 0.978 |

