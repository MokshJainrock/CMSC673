CMSC 673 - Textbook Search
==========================

A simple search tool for OpenStax Biology 2e. You type a topic or a
question and it returns the textbook sections that look most relevant.
It is the implementation track project for CMSC 673.

There are three ways the system can rank sections:

1. BM25 keyword search (rank_bm25)
2. BM25 + a small dense reranker (all-MiniLM-L6-v2)
3. BM25 + a zero-shot gpt-3.5 reranker (for comparison)


Files
-----
    data/
      corpus.jsonl       91 textbook sections
      queries.jsonl      100 student-style queries
      qrels.jsonl        relevance labels (graded 2 or 1)

    src/
      search.py          load data + bm25 + minilm + gpt rerankers
      clean.py           turn openstax html into corpus.jsonl
      main.py            one query in the terminal
      app.py             flask web app
      eval.py            run all systems, save metrics
      templates/index.html

    tests/
      test_basics.py     seven sanity checks

    results/
      metrics.csv        eval output
      predictions.jsonl  per-query top-10 from each system

    README.md
    Final_Report.pdf
    requirements.txt
    .env.example         template for OPENAI_API_KEY


How to run
----------
1. Install dependencies:

       pip install -r requirements.txt
       python -m nltk.downloader punkt punkt_tab stopwords

2. If you want the gpt-3.5 reranker, copy .env.example to .env and put
   your key in .env. The other parts work without a key.

3. Pick what to run:

       python -m tests.test_basics              # sanity checks
       python -m src.main "krebs cycle"         # one query
       python -m src.main "what is dna" --rerank
       python -m src.app                        # web app, then open
                                                # http://127.0.0.1:5050
       python -m src.eval                       # full eval, writes csv


Dataset
-------
Corpus is from OpenStax Biology 2e (CC BY 4.0). 91 sections covering
cells, membranes, metabolism, respiration, photosynthesis, the cell
cycle, meiosis, genetics, DNA, gene expression, evolution, body systems,
ecology, and more.

100 queries, mixing keyword and question styles. 129 relevance judgments
(score 2 = highly relevant, 1 = somewhat relevant).


Example queries
---------------
These should work well:

    krebs cycle
    what is photosynthesis
    how does dna replication work
    hydrogen bonding
    difference between mitosis and meiosis
    innate vs adaptive immunity

These are out of scope and trigger "no relevant sections found":

    what is nlp
    best pizza in baltimore
    how to write a python function


Notes
-----
- The corpus is only biology, so anything off-topic is filtered by the
  score threshold (top BM25 score < 0.5).
- The GPT reranker costs a few cents to run the full eval. Without the
  key, the eval just skips that row.
- First run downloads the MiniLM model (~90 MB) once.


References
----------
- Robertson and Zaragoza (2009), The Probabilistic Relevance Framework:
  BM25 and Beyond.
- rank_bm25, https://github.com/dorianbrown/rank_bm25
- NLTK, Bird, Klein, Loper (2009), https://www.nltk.org
- Reimers and Gurevych (2019), Sentence-BERT, EMNLP 2019.
- all-MiniLM-L6-v2, https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- OpenStax Biology 2e (CC BY 4.0),
  https://openstax.org/details/books/biology-2e
- OpenAI gpt-3.5-turbo.
- Beautiful Soup 4, https://www.crummy.com/software/BeautifulSoup
- Flask, https://flask.palletsprojects.com
- NumPy, https://numpy.org
