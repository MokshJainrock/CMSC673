# Textbook Search for CMSC 473/673

Implementation Track, part (a): the user types a topic or query, and the app finds relevant textbook sections.

This repository contains a complete BM25-based retrieval system over a small OpenStax-derived textbook corpus. It includes a command-line app, a browser frontend, a reproducible evaluation set, ranking metrics, tests, and a zero-shot GPT-3.5 API comparison.

## Project Structure

```text
.
├── data/
│   ├── corpus.jsonl          # Textbook section metadata and searchable text
│   └── eval_queries.json     # Manually labeled retrieval queries
├── textbook_search/
│   ├── bm25.py               # Pure-Python BM25 scorer
│   ├── evaluate.py           # Precision@3, Recall@5, MRR, NDCG@5
│   ├── gpt35_baseline.py     # Zero-shot GPT-3.5 comparison prompt
│   ├── loader.py             # Corpus and eval loading
│   ├── openai_compare.py     # Live OpenAI API call for GPT-3.5 reranking
│   ├── search.py             # Search engine API
│   └── tokenizer.py          # Deterministic tokenizer
├── tests/                    # Unit tests
├── web/                      # Browser frontend assets
├── scripts/run_full.py       # One-command project runner
├── main.py                   # Main CLI
├── web_app.py                # Local web server and JSON API
├── bm25_baseline.py          # Compatibility wrapper for original baseline
├── data_loader.py            # Compatibility wrapper for original loader
└── reports/
    ├── final_writeup.pdf
    └── summary_of_changes.pdf
```

## Run Search

No third-party packages are required.

Run the full local workflow:

```bash
python3 scripts/run_full.py
```

Run the full workflow including live OpenAI API calls:

```bash
python3 scripts/run_full.py --with-openai
```

Run the browser frontend:

```bash
python3 web_app.py
```

Then open `http://127.0.0.1:8000`.

```bash
python3 main.py "Krebs cycle acetyl CoA" -k 3
```

Print the prompt used for the zero-shot GPT-3.5 comparison:

```bash
python3 main.py "Krebs cycle acetyl CoA" -k 5 --gpt-prompt
```

Call the OpenAI API for the zero-shot GPT-3.5 comparison:

```bash
export OPENAI_API_KEY="your-api-key"
python3 main.py "Krebs cycle acetyl CoA" -k 5 --gpt-api
```

If the key is in a file, pass it without committing the secret:

```bash
python3 main.py "Krebs cycle acetyl CoA" -k 5 --gpt-api --env-file /path/to/.env
```

The API call is in `textbook_search/openai_compare.py`, in `rank_candidates_with_openai()`. It uses the Chat Completions endpoint with `gpt-3.5-turbo` by default to match the assignment wording. If that model is unavailable on the account, override it:

```bash
OPENAI_MODEL="gpt-4o-mini" python3 main.py "Krebs cycle acetyl CoA" --gpt-api
```

## Evaluate

```bash
python3 -m textbook_search.evaluate
```

Current BM25 results on the 14-query evaluation set:

| Metric | Value |
| --- | ---: |
| Precision@3 | 0.726 |
| Recall@5 | 0.857 |
| MRR | 1.000 |
| NDCG@5 | 0.975 |

To evaluate the OpenAI reranker on all labeled queries:

```bash
export OPENAI_API_KEY="your-api-key"
python3 -m textbook_search.evaluate --openai-rerank
```

Write reproducible JSON results:

```bash
python3 -m textbook_search.evaluate --openai-rerank --env-file /path/to/.env --json-out reports/openai_rerank_results.json
```

Completed comparison results are saved in `reports/bm25_results.json` and `reports/openai_rerank_results.json`:

| System | Precision@3 | Recall@5 | MRR | NDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| BM25 baseline | 0.726 | 0.857 | 1.000 | 0.975 |
| Zero-shot GPT-3.5 reranker | 0.726 | 0.857 | 1.000 | 0.975 |

## Test

```bash
python3 -m unittest discover -s tests
```

## Data Sources

The corpus contains concise section summaries and metadata derived from OpenStax textbooks:

- OpenStax Biology 2e, CC BY 4.0
- OpenStax Chemistry 2e, CC BY 4.0
- OpenStax College Physics, CC BY 4.0
- OpenStax College Algebra 2e, CC BY 4.0
- OpenStax Calculus Volume 1, CC BY 4.0

Each document in `data/corpus.jsonl` includes the source URL for its textbook section.
