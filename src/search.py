"""
All the search code here. Three thingds:
  - loading the corpus / queries / qrels from jsonl files
  - bm25 keyword search
  - optional dense reranker (minilm) and gpt-3.5 reranker

The rerankers are imported only when used, so the basic bm25 search runs
without sentence-transformers or an openai key installed.
"""

import json
import os
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi


DATA = Path(__file__).resolve().parent.parent / "data"


# ---------- loading ----------

def read_jsonl(path):
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_corpus():
    return read_jsonl(DATA / "corpus.jsonl")


def load_queries():
    return read_jsonl(DATA / "queries.jsonl")


def load_qrels():
    # qid -> {doc_id: score}
    out = {}
    for row in read_jsonl(DATA / "qrels.jsonl"):
        out.setdefault(row["qid"], {})[row["doc_id"]] = int(row["score"])
    return out


# tokenizing 

for pkg in ["punkt", "punkt_tab", "stopwords"]:
    try:
        if pkg == "stopwords":
            stopwords.words("english")
        else:
            word_tokenize("hi")
    except LookupError:
        nltk.download(pkg, quiet=True)

STOP = set(stopwords.words("english"))


def tokenize(text):
    return [t for t in word_tokenize(text.lower())
            if t.isalnum() and t not in STOP]


# bm25

def build_bm25(corpus):
    """returns the bm25 object and the same corpus list (handy for calling code)."""
    tokens = [tokenize(d["title"] + " " + d["text"]) for d in corpus]
    return BM25Okapi(tokens, k1=1.5, b=0.75)


def bm25_search(bm25, corpus, query, k=10):
    q = tokenize(query)
    if not q:
        return []
    scores = bm25.get_scores(q)
    pairs = list(zip(corpus, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return [(d, float(s)) for d, s in pairs[:k]]


# minilm reranker 

_dense_model = None
_doc_vec_cache = {}


def _get_dense_model():
    global _dense_model
    if _dense_model is None:
        from sentence_transformers import SentenceTransformer
        print("loading minilm...")
        _dense_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _dense_model


def dense_rerank(query, candidates, k=5):
    import numpy as np
    if not candidates:
        return []
    model = _get_dense_model()
    q_vec = model.encode(query, normalize_embeddings=True)
    scored = []
    for doc, _ in candidates:
        if doc["id"] not in _doc_vec_cache:
            text = doc["title"] + ". " + doc["text"][:1200]
            _doc_vec_cache[doc["id"]] = model.encode(text, normalize_embeddings=True)
        v = _doc_vec_cache[doc["id"]]
        scored.append((doc, float(np.dot(q_vec, v))))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# gpt zero-shot reranker 

_openai_client = None

GPT_PROMPT = """You are helping a student search a biology textbook.
Query: {query}

Candidate sections (id and title):
{listing}

Rank the candidates from most to least relevant to the query.
Reply with only a JSON array of ids, in ranked order. No explanation."""


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        from openai import OpenAI
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set (put it in .env)")
        _openai_client = OpenAI()
    return _openai_client


def gpt_rerank(query, candidates, k=5, model="gpt-3.5-turbo"):
    import re
    if not candidates:
        return []
    client = _get_openai_client()
    listing = "\n".join(f"- {d['id']}: {d['title']}" for d, _ in candidates)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": GPT_PROMPT.format(query=query, listing=listing)}],
        temperature=0,
    )
    text = resp.choices[0].message.content.strip()

    # parsing the json array of ids out of the response
    ids = []
    m = re.search(r"\[.*\]", text, re.S)
    if m:
        try:
            ids = json.loads(m.group(0))
        except Exception:
            ids = re.findall(r"[\w\-]+", text)
    else:
        ids = re.findall(r"[\w\-]+", text)

    order = {i: pos for pos, i in enumerate(ids)}
    ordered = sorted(candidates, key=lambda x: order.get(x[0]["id"], 999))
    return [(d, 0.0) for d, _ in ordered[:k]]
