const form = document.querySelector("#search-form");
const queryInput = document.querySelector("#query");
const topKInput = document.querySelector("#top-k");
const useOpenAIInput = document.querySelector("#use-openai");
const statusEl = document.querySelector("#status");
const resultsEl = document.querySelector("#results");
const modeLabel = document.querySelector("#mode-label");

const metrics = {
  precision: document.querySelector("#precision"),
  recall: document.querySelector("#recall"),
  mrr: document.querySelector("#mrr"),
  ndcg: document.querySelector("#ndcg"),
};

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch();
});

document.querySelectorAll("[data-query]").forEach((button) => {
  button.addEventListener("click", () => {
    queryInput.value = button.dataset.query;
    runSearch();
  });
});

useOpenAIInput.addEventListener("change", () => {
  loadMetrics(useOpenAIInput.checked);
});

async function runSearch() {
  const query = queryInput.value.trim();
  const topK = topKInput.value || "5";
  const useOpenAI = useOpenAIInput.checked;

  if (!query) return;

  setStatus("Searching...");
  resultsEl.innerHTML = "";
  modeLabel.textContent = useOpenAI ? "GPT-3.5 rerank" : "BM25";

  const params = new URLSearchParams({
    q: query,
    k: topK,
    openai: String(useOpenAI),
  });

  try {
    const response = await fetch(`/api/search?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Search failed");
    renderResults(data.results);
    const detail = data.openai ? ` ${data.openai.model}` : "";
    setStatus(`${data.results.length} results.${detail}`);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function loadMetrics(useOpenAI = false) {
  const params = new URLSearchParams({ openai: String(useOpenAI) });
  try {
    const response = await fetch(`/api/evaluate?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Evaluation failed");
    metrics.precision.textContent = formatMetric(data.precision_at_3);
    metrics.recall.textContent = formatMetric(data.recall_at_5);
    metrics.mrr.textContent = formatMetric(data.mrr);
    metrics.ndcg.textContent = formatMetric(data.ndcg_at_5);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function renderResults(results) {
  if (!results.length) {
    resultsEl.innerHTML = `
      <li class="empty">
        No strong textbook matches found. Try a more specific topic, or add more textbook sections to the corpus.
      </li>
    `;
    return;
  }

  resultsEl.innerHTML = results
    .map(
      (result) => `
        <li class="result">
          <div class="rank">${result.rank}</div>
          <div>
            <h3>${escapeHtml(result.title)}</h3>
            <p class="meta">${escapeHtml(result.textbook)} - ${escapeHtml(result.chapter)}, ${escapeHtml(result.section)}</p>
            <p class="snippet">${escapeHtml(result.snippet)}</p>
            <div class="result-footer">
              <span>${escapeHtml(result.doc_id)}</span>
              <span>Score ${Number(result.score).toFixed(3)}</span>
              <a href="${escapeAttribute(result.source_url)}" target="_blank" rel="noreferrer">Source</a>
            </div>
          </div>
        </li>
      `
    )
    .join("");
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function formatMetric(value) {
  return Number(value || 0).toFixed(3);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

loadMetrics(false);
runSearch();
