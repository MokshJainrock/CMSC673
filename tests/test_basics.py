# quick checks to make sure the search code is not broken.
# run with: python -m tests.test_basics

from src.search import load_corpus, build_bm25, bm25_search, tokenize


def show(name, ok):
    # printing  PASS or FAIL with the test name 
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}")
    return ok


print("loading data")
corpus = load_corpus()
bm25 = build_bm25(corpus)
print(f"got {len(corpus)} sections\n")

passed = 0
total = 0


# test 1: if i search the title of a section, that section should be on top
total += 1
first = corpus[0]
top = bm25_search(bm25, corpus, first["title"], k=1)
ok = bool(top) and top[0][0]["id"] == first["id"]
passed += show("title search finds its own section", ok)


# test 2: tokenize should give the same tokens for upper case and lower cas
total += 1
up_tokens = tokenize("Krebs Cycle")
low_tokens = tokenize("krebs cycle")
passed += show("tokenizer gives same tokens for upper and lower case",up_tokens == low_tokens)


# test 3 : same query twice should give the same ids and the same scores
total += 1
a = bm25_search(bm25, corpus, "photosynthesis", k=5)
b = bm25_search(bm25, corpus, "photosynthesis", k=5)
same_ids = [d["id"] for d, _ in a] == [d["id"] for d, _ in b]
same_scores = [round(s, 6) for _, s in a] == [round(s, 6) for _, s in b]
passed += show("same query twice gives same ids and scores",same_ids and same_scores)


#  test 4: off-topic question should get a low top score
total += 1
top = bm25_search(bm25, corpus, "what is nlp", k=1)
score = top[0][1] if top else 0.0
passed += show(f"off-topic query has low score (got {score:.2f})", score < 1.0)


# test 5: real biology query should get a high top score
total += 1
top = bm25_search(bm25, corpus, "krebs cycle", k=1)
score = top[0][1] if top else 0.0
passed += show(f"biology query has high score (got {score:.2f})", score > 1.0)


# test 6: asking for k results should not return more than k
total += 1
got = bm25_search(bm25, corpus, "dna", k=3)
passed += show("k parameter is respected", len(got) <= 3)


# test 7: empty query should not crash 
total += 1
got = bm25_search(bm25, corpus, "", k=5)
passed += show("empty query does not crash", got == [])


print(f"\n{passed} of {total} checks passed")
