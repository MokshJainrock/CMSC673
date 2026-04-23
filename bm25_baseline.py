
import sys
from rank_bm25 import BM25Okapi
from data_loader import get_corpus
import nltk
nltk.download('punkt', quiet=True)
from nltk.tokenize import word_tokenize

def tokenize(text):
    return word_tokenize(text.lower())

def search(query, k=3):
    ids, docs = get_corpus()
    tokenized_docs = [tokenize(d) for d in docs]
    bm25 = BM25Okapi(tokenized_docs)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(ids, docs, scores), key=lambda x: x[2], reverse=True)
    return ranked[:k]

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "photosynthesis"
    results = search(query)
    print(f"Query: {query}\n")
    for doc_id, text, score in results:
        print(f"{doc_id} ({score:.2f}): {text[:100]}...")
