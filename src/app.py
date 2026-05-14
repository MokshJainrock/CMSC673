# run with: python -m src.app  then open http://127.0.0.1:5000 
# a small front end also I have added 2 ss in the final report how it looks like

from flask import Flask, render_template, request

from src.search import load_corpus, build_bm25, bm25_search, dense_rerank


app = Flask(__name__)

print("loading corpus...")
corpus = load_corpus()
bm25 = build_bm25(corpus)
print(f"got {len(corpus)} sections")

# below this top score we show "no results" instead of bad matches
THRESHOLD = 0.5


@app.route("/", methods=["GET"])
def home():
    query = request.args.get("q", "").strip()
    use_rerank = request.args.get("rerank") == "on"

    results = []
    no_match = False
    top_score = 0.0

    if query:
        hits = bm25_search(bm25, corpus, query, k=25)

        if len(hits) == 0:
            no_match = True
        elif hits[0][1] < THRESHOLD:
            no_match = True
            top_score = hits[0][1]
        else:
            if use_rerank:
                try:
                    hits = dense_rerank(query, hits, k=5)
                except Exception as e:
                    print("rerank failed, using bm25 only:", e)
                    hits = hits[:5]
            else:
                hits = hits[:5]

            for doc, score in hits:
                results.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "source": doc.get("source", ""),
                    "chapter": doc.get("chapter", ""),
                    "preview": doc["text"][:240] + "...",
                    "score": round(float(score), 3),
                })

    return render_template(
        "index.html",
        query=query,
        results=results,
        use_rerank=use_rerank,
        no_match=no_match,
        top_score=top_score,
        threshold=THRESHOLD,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5050)
