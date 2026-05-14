# runing the 3 search setups on the labeled queries and save the numbers.
# python -m src.eval 
# the above is th e command i just added to run 

import csv
import json
import math
import os
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.search import (
    load_corpus, load_queries, load_qrels,
    build_bm25, bm25_search, dense_rerank, gpt_rerank,
)


RESULTS = Path(__file__).resolve().parent.parent / "results"


def precision_at_3(ids, gold):
    top = ids[:3]
    hits = 0
    for x in top:
        if x in gold:
            hits += 1
    return hits / 3


def recall_at_5(ids, gold):
    if len(gold) == 0:
        return 0.0
    top = ids[:5]
    hits = 0
    for x in top:
        if x in gold:
            hits += 1
    return hits / len(gold)


def f1_at_5(ids, gold):
    if len(gold) == 0:
        return 0.0
    top = ids[:5]
    hits = 0
    for x in top:
        if x in gold:
            hits += 1
    p = hits / 5
    r = hits / len(gold)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def ndcg_at_5(ids, gold_scores):
    dcg = 0.0
    for i, x in enumerate(ids[:5]):
        if x in gold_scores:
            rel = gold_scores[x]
            dcg += (2 ** rel - 1) / math.log2(i + 2)

    best = sorted(gold_scores.values(), reverse=True)[:5]
    idcg = 0.0
    for i, rel in enumerate(best):
        if rel > 0:
            idcg += (2 ** rel - 1) / math.log2(i + 2)

    if idcg == 0:
        return 0.0
    return dcg / idcg


def run_system(system, bm25, corpus, queries, qrels, predictions):
    print(f"  running {system} ")
    p3_list = []
    r5_list = []
    f1_list = []
    n5_list = []
    time_list = []

    for q in queries:
        gold_scores = qrels.get(q["qid"], {})
        gold = set(gold_scores)
        if len(gold) == 0:
            continue

        start = time.time()
        hits = bm25_search(bm25, corpus, q["query"], k=25)

        if system == "bm25":
            hits = hits[:10]
        elif system == "bm25+minilm":
            hits = dense_rerank(q["query"], hits, k=10)
        elif system == "bm25+gpt-3.5":
            hits = gpt_rerank(q["query"], hits[:10], k=10)

        elapsed = time.time() - start
        ids = [d["id"] for d, _ in hits]

        p3_list.append(precision_at_3(ids, gold))
        r5_list.append(recall_at_5(ids, gold))
        f1_list.append(f1_at_5(ids, gold))
        n5_list.append(ndcg_at_5(ids, gold_scores))
        time_list.append(elapsed)

        predictions.append({
            "system": system,
            "qid": q["qid"],
            "query": q["query"],
            "top10": ids[:10],
            "gold": list(gold),
        })

    def avg(xs):
        if len(xs) == 0:
            return 0.0
        return round(sum(xs) / len(xs), 4)

    return {
        "system": system,
        "Precision@3": avg(p3_list),
        "Recall@5": avg(r5_list),
        "F1@5": avg(f1_list),
        "NDCG@5": avg(n5_list),
        "avg_seconds": avg(time_list),
        "n_queries": len(p3_list),
    }


def main():
    corpus = load_corpus()
    queries = load_queries()
    qrels = load_qrels()

    print(f"corpus: {len(corpus)} sections")
    print(f"queries: {len(queries)}")
    print(f"qrels: {sum(len(v) for v in qrels.values())}\n")

    # first 20 are dev, rest are test
    dev = queries[:20]
    test = queries[20:]
    print(f"dev: {len(dev)}    test: {len(test)}\n")

    bm25 = build_bm25(corpus)

    if os.getenv("OPENAI_API_KEY"):
        run_gpt = True
    else:
        run_gpt = False
        print("OPENAI_API_KEY not set, skipping gpt-3.5\n")

    systems = ["bm25", "bm25+minilm"]
    if run_gpt:
        systems.append("bm25+gpt-3.5")

    rows = []
    predictions = []

    print("dev split ")
    for s in systems:
        r = run_system(s, bm25, corpus, dev, qrels, predictions)
        r["split"] = "dev"
        rows.append(r)

    print("\ntest split ")
    for s in systems:
        r = run_system(s, bm25, corpus, test, qrels, predictions)
        r["split"] = "test"
        rows.append(r)

    ordered_rows = []
    for r in rows:
        new_row = {"split": r["split"]}
        for k, v in r.items():
            if k != "split":
                new_row[k] = v
        ordered_rows.append(new_row)

    RESULTS.mkdir(exist_ok=True)
    metrics_path = RESULTS / "metrics.csv"
    with open(metrics_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(ordered_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ordered_rows)
    print(f"\nsaved metrics to {metrics_path}")

    pred_path = RESULTS / "predictions.jsonl"
    with open(pred_path, "w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")
    print(f"saved predictions to {pred_path}\n")

    headers = list(ordered_rows[0].keys())
    widths = []
    for h in headers:
        w = len(h)
        for r in ordered_rows:
            if len(str(r[h])) > w:
                w = len(str(r[h]))
        widths.append(w)

    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    for r in ordered_rows:
        print("  ".join(str(r[h]).ljust(w) for h, w in zip(headers, widths)))


if __name__ == "__main__":
    main()
