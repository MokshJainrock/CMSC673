---
title: "Document Ranking for Textbook Search"
subtitle: "CMSC 473/673 NLP - Implementation Track, Part (a)"
author: "Moksh Jain"
date: "May 14, 2026"
geometry: margin=1in
fontsize: 11pt
---

# 1. Task and System Overview

I selected Implementation Track part (a): the user types a topic or query, and the app finds relevant textbooks or textbook sections. The completed system is a search engine for OpenStax-style textbook sections with both a command-line interface and a local browser frontend. A user can enter a query such as "Krebs cycle acetyl CoA," "Calvin cycle carbon fixation," or "mathematics is hard," and the system returns ranked sections with titles, chapter metadata, snippets, and source URLs.

The system has two ranking modes. The first is a deterministic BM25 baseline implemented locally in Python. The second is a zero-shot GPT-3.5 comparison that sends the top BM25 candidates to the OpenAI API and asks the model to return a ranked list of section ids. This design keeps the main system reproducible while still satisfying the required comparison against a prompted GPT-3.5 model.

# 2. Methodology

The main retrieval method is Okapi BM25, a sparse lexical ranking method from the probabilistic relevance framework. BM25 is a good fit because textbook search queries often contain exact technical vocabulary, such as "ATP synthase," "Okazaki fragments," "Punnett square," or "Bronsted-Lowry." BM25 also requires no training data, which matters because the assignment does not provide relevance judgments.

The original prototype depended on the `rank_bm25` package and NLTK tokenization. I replaced that with a compact local implementation in `textbook_search/bm25.py` and a deterministic regular-expression tokenizer in `textbook_search/tokenizer.py`. The tokenizer removes common stopwords such as "is" and "the," which prevents broad queries from matching irrelevant sections only because of common function words. Each indexed document combines textbook name, chapter, section, title, and body summary so that both metadata and content can influence ranking.

The OpenAI comparison is implemented in `textbook_search/openai_compare.py`. It uses the Chat Completions API with `gpt-3.5-turbo` by default. The prompt asks the model to rank candidate textbook sections and return only comma-separated section ids. This makes the output easy to parse and evaluate with the same metrics as BM25.

# 3. Data

The corpus contains 27 textbook sections derived from OpenStax Biology 2e, OpenStax Chemistry 2e, OpenStax College Physics, OpenStax College Algebra 2e, and OpenStax Calculus Volume 1. I chose OpenStax because it is openly licensed, available online, and covers common introductory topics. Each record in `data/corpus.jsonl` includes an id, textbook, chapter, section, title, source URL, and concise searchable text.

I used section-level summaries rather than raw PDF extraction. Raw textbook PDFs often mix body text with page headers, footers, captions, and tables; using curated section records keeps this project's retrieval behavior interpretable. The tradeoff is that the corpus is smaller than a production search system. The same JSONL schema can be extended to a much larger OpenStax scrape later.

The evaluation set in `data/eval_queries.json` contains 14 manually labeled queries. Each query has one or more relevant section ids with graded relevance. For example, a query about the Calvin cycle gives the Calvin cycle section high relevance and the broader photosynthesis overview lower relevance.

# 4. Implementation

The completed repository contains:

- `main.py`, the user-facing command-line app.
- `textbook_search/loader.py`, which loads the corpus and evaluation queries.
- `textbook_search/tokenizer.py`, which normalizes query and document text.
- `textbook_search/bm25.py`, which computes BM25 scores.
- `textbook_search/search.py`, which exposes a reusable search engine API.
- `textbook_search/openai_compare.py`, which runs the zero-shot GPT-3.5 reranker.
- `textbook_search/evaluate.py`, which reports Precision@3, Recall@5, MRR, and NDCG@5.
- `web_app.py` and `web/`, which provide a local browser frontend.
- `tests/`, which checks loading, tokenization, deterministic search, metric correctness, API-output parsing, and the web search endpoint.

The main search command is:

```bash
python3 main.py "Krebs cycle acetyl CoA" -k 5
```

The GPT-3.5 comparison command is:

```bash
python3 main.py "Krebs cycle acetyl CoA" -k 5 --gpt-api --env-file /path/to/.env
```

# 5. Evaluation

I evaluated both BM25 and the GPT-3.5 reranker using the same 14 labeled queries. BM25 produced the candidate list. GPT-3.5 then reranked the top five candidates with a zero-shot prompt. I used four metrics:

- Precision@3: the fraction of top-three results that are relevant.
- Recall@5: the fraction of relevant sections retrieved in the top five.
- MRR: the reciprocal rank of the first relevant result.
- NDCG@5: graded ranking quality in the top five.

| System | Precision@3 | Recall@5 | MRR | NDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| BM25 baseline | 0.726 | 0.857 | 1.000 | 0.975 |
| Zero-shot GPT-3.5 reranker | 0.726 | 0.857 | 1.000 | 0.975 |

The results show that BM25 is already strong on this small technical corpus. The first relevant section is ranked first for every labeled query, which explains the perfect MRR. GPT-3.5 changed some lower-ranked ordering decisions, but it did not improve aggregate metrics because the candidate generator had already placed the most relevant result at the top. Precision@3 is lower than MRR because some queries have only one or two labeled relevant sections, so returning three results can include partially related candidates.

# 6. Hurdles

The first hurdle was dependency fragility. The initial prototype required external packages and tokenizer downloads, so I rewrote the BM25 and tokenizer components locally. This made the code easier to run and test.

The second hurdle was data cleaning. Direct PDF extraction would have required removing headers, footers, captions, tables, and page numbers. I avoided that noise by using structured section records with source URLs. This made evaluation cleaner, but it limited corpus size.

The third hurdle was broad user phrasing. A query like "mathematics is hard" originally matched irrelevant biology sections because common words were scored. I addressed this with stopword filtering, zero-score filtering, and a small set of math sections.

The final hurdle was fair GPT comparison. GPT-3.5 cannot reasonably receive a whole textbook corpus in one prompt, so I compared it as a reranker over the same top-five BM25 candidates. This makes the comparison reproducible and keeps the prompt small, but it means GPT-3.5 cannot recover a relevant section that BM25 failed to retrieve.

# 7. Retrospective

If I were extending this project, I would invest first in a larger automated OpenStax ingestion pipeline. Search quality depends heavily on corpus coverage, and 27 sections are enough for a prototype but not enough for a real textbook finder. I would also test title boosting, phrase matching, and a dense sentence-transformer reranker over the BM25 candidate pool. A larger evaluation set, ideally labeled by more than one person, would make the comparison more reliable.

# 8. References

Robertson, Stephen, and Hugo Zaragoza. 2009. "The Probabilistic Relevance Framework: BM25 and Beyond." *Foundations and Trends in Information Retrieval*.

OpenStax. *Biology 2e*. Rice University. CC BY 4.0. https://openstax.org/details/books/biology-2e

OpenStax. *Chemistry 2e*. Rice University. CC BY 4.0. https://openstax.org/details/books/chemistry-2e

OpenStax. *College Physics*. Rice University. CC BY 4.0. https://openstax.org/details/books/college-physics

OpenStax. *College Algebra 2e*. Rice University. CC BY 4.0. https://openstax.org/details/books/college-algebra-2e

OpenStax. *Calculus Volume 1*. Rice University. CC BY 4.0. https://openstax.org/details/books/calculus-volume-1

OpenAI. Chat Completions API documentation. https://platform.openai.com/docs/api-reference/chat
