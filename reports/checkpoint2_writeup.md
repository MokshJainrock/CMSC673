---
title: "Initial Report: Document Ranking for Textbook Search"
subtitle: "CMSC 473/673 NLP - Implementation Track, Part (a)"
author: "Anonymous"
date: "April 28, 2026"
geometry: margin=1in
fontsize: 11pt
---

# 1. System Idea

I selected Implementation Track part (a): the user types a topic or query, and the app finds relevant textbooks or textbook sections. The current system is a command-line search engine for OpenStax-style textbook sections. A student can enter a topic such as "Krebs cycle acetyl CoA" or "Calvin cycle carbon fixation," and the system returns ranked sections with titles, chapter metadata, snippets, and source URLs.

For this checkpoint, I focused on making the retrieval pipeline complete and reproducible rather than adding a neural reranker prematurely. The repository now includes a corpus, a BM25 index, a search interface, an evaluation set, ranking metrics, unit tests, and a live OpenAI API comparison against a zero-shot GPT-3.5 prompt.

# 2. Methodology

The retrieval method is Okapi BM25, a sparse lexical ranking method from the probabilistic relevance framework. BM25 is appropriate for this project because many student queries include technical vocabulary that appears directly in textbook sections, such as "ATP synthase," "Okazaki fragments," or "Punnett square." It also does not require training data, which is useful because the assignment does not provide relevance judgments.

The original prototype used the `rank_bm25` package and NLTK tokenization. I replaced that dependency-heavy version with a compact pure-Python BM25 implementation in `textbook_search/bm25.py`. This makes the project easier to run in a clean environment and avoids NLTK model downloads. The tokenizer lowercases text and extracts deterministic word-like tokens. Each document is indexed using its textbook name, chapter, section, title, and body summary so that title words and section identifiers can also affect ranking.

The command-line app in `main.py` returns ranked results. The compatibility wrappers `bm25_baseline.py` and `data_loader.py` still support the original prototype interface, but they now call the package code.

# 3. Data

The current corpus contains 24 textbook sections derived from OpenStax Biology 2e, OpenStax Chemistry 2e, and OpenStax College Physics. I chose OpenStax because it is openly licensed, available online, and covers common introductory science topics that are likely to appear in student textbook searches. Each record in `data/corpus.jsonl` has an id, textbook, chapter, section, title, source URL, and concise searchable text.

For this checkpoint, I used short section summaries rather than raw PDF extraction. This avoids the header, footer, table, and figure-caption noise that often appears when textbook PDFs are converted directly to text. For the final version, the data pipeline should be expanded to automatically scrape or export a larger set of OpenStax sections while preserving the same JSONL format.

# 4. Implementation Progress

The repository now contains an end-to-end baseline:

- `textbook_search/loader.py` loads the corpus and evaluation queries.
- `textbook_search/tokenizer.py` normalizes query and document text.
- `textbook_search/bm25.py` computes BM25 scores.
- `textbook_search/search.py` exposes a reusable search engine API.
- `textbook_search/evaluate.py` reports Precision@3, Recall@5, MRR, and NDCG@5.
- `textbook_search/gpt35_baseline.py` builds the zero-shot GPT-3.5 comparison prompt.
- `textbook_search/openai_compare.py` calls the OpenAI API to run the zero-shot GPT-3.5 reranker when `OPENAI_API_KEY` is set.
- `tests/` checks loading, tokenization, deterministic ranking, metric behavior, and evaluation data consistency.

The GitHub repository has at least three non-trivial commits. The current code builds on that history by turning the initial BM25 idea into a runnable project with tests and documented evaluation.

# 5. Hurdles Encountered

The first hurdle was dependency fragility. The initial version required `rank_bm25` and NLTK, and NLTK often requires a separate tokenizer download. For a small BM25 baseline, those dependencies made the project harder to reproduce than necessary. I addressed this by implementing the BM25 formula directly and using a simple regular-expression tokenizer.

The second hurdle was data extraction. Raw textbook PDFs can mix body text with headers, footers, captions, page numbers, and tables. Because noisy extraction would make the current evaluation hard to interpret, I used curated OpenStax section summaries as the first corpus format. The limitation is that the corpus is still small and manually prepared.

The third hurdle was evaluation. There is no official relevance set, so I created a 12-query manual evaluation file. Each query maps to one or more relevant section ids with graded relevance. This is enough to test the system's behavior, although a larger final study should use more queries and ideally have a second person inspect the labels.

# 6. Evaluation Plan and Current Results

The evaluation uses standard ranking metrics:

- Precision@3 measures how many of the top three results are relevant.
- Recall@5 measures whether the system finds the manually labeled relevant sections in the top five.
- MRR rewards returning the first relevant result near rank one.
- NDCG@5 uses graded relevance, so highly relevant documents matter more than weakly related ones.

Current BM25 results on the 12-query evaluation set are:

| System | Precision@3 | Recall@5 | MRR | NDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| BM25 baseline | 0.500 | 0.875 | 1.000 | 0.978 |
| Zero-shot GPT-3.5 reranker | 0.500 | 0.875 | 1.000 | 0.978 |

The high MRR means the best relevant section is usually ranked first. Precision@3 is lower because BM25 sometimes gives partial credit to documents sharing generic terms such as "cycle" or "ATP." GPT-3.5 changed a few lower-ranked candidate orders, but it did not improve the aggregate metrics because the first relevant result was already usually ranked first by BM25. This suggests that the biggest future gain would come from expanding the corpus and improving candidate generation, not only reranking the current top five.

The zero-shot GPT-3.5 comparison was run with `python3 -m textbook_search.evaluate --openai-rerank`. The model receives the BM25 candidate list and returns a ranked list of section ids. The code defaults to `gpt-3.5-turbo` to match the assignment wording, but the model can be changed with `OPENAI_MODEL` if that model is unavailable.

# 7. Correctness Tests

The test suite checks five important behaviors:

- The corpus has at least 20 documents and every document includes an OpenStax source URL.
- Tokenization is case-insensitive.
- A direct Calvin cycle query returns the Calvin cycle section first.
- Running the same query twice produces identical rankings and scores.
- Evaluation queries only reference document ids that exist in the corpus.

The metric tests separately validate Precision@k, Recall@k, reciprocal rank, and NDCG on small controlled examples.

# 8. Retrospective

In retrospect, I would start by building the data ingestion step earlier. Most of the modeling code is compact, but the quality of the corpus controls the quality of the final search results. I would also add title-field boosting or phrase-aware scoring to reduce irrelevant lower-ranked matches. If time allowed, I would test a dense reranker such as `all-MiniLM-L6-v2` on the top BM25 candidates and report whether it improves NDCG@5.

# 9. References

Robertson, Stephen, and Hugo Zaragoza. 2009. "The Probabilistic Relevance Framework: BM25 and Beyond." *Foundations and Trends in Information Retrieval*.

OpenStax. *Biology 2e*. Rice University. CC BY 4.0. https://openstax.org/details/books/biology-2e

OpenStax. *Chemistry 2e*. Rice University. CC BY 4.0. https://openstax.org/details/books/chemistry-2e

OpenStax. *College Physics*. Rice University. CC BY 4.0. https://openstax.org/details/books/college-physics

