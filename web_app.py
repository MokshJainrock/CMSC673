"""Local web frontend for the textbook search project."""

from __future__ import annotations

import argparse
import json
import mimetypes
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from textbook_search.env import load_env_file
from textbook_search.evaluate import evaluate
from textbook_search.openai_compare import rank_candidates_with_openai
from textbook_search.search import SearchResult, TextbookSearchEngine


PROJECT_ROOT = Path(__file__).resolve().parent
WEB_ROOT = PROJECT_ROOT / "web"
DEFAULT_ENV_FILE = PROJECT_ROOT.parent / "shrinkflation-detector" / ".env"


class AppState:
    def __init__(self):
        self.engine = TextbookSearchEngine()


def create_handler(state: AppState):
    class TextbookSearchHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_file(WEB_ROOT / "index.html")
            elif parsed.path == "/api/search":
                self._handle_search(parsed.query)
            elif parsed.path == "/api/evaluate":
                self._handle_evaluate(parsed.query)
            elif parsed.path.startswith("/static/"):
                self._send_file(WEB_ROOT / parsed.path.removeprefix("/static/"))
            else:
                self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args) -> None:
            return

        def _handle_search(self, query_string: str) -> None:
            params = parse_qs(query_string)
            query = params.get("q", [""])[0].strip()
            top_k = _parse_int(params.get("k", ["5"])[0], default=5, minimum=1, maximum=10)
            use_openai = params.get("openai", ["false"])[0].lower() == "true"

            if not query:
                self._send_json({"error": "Query is required"}, status=HTTPStatus.BAD_REQUEST)
                return

            bm25_results = state.engine.search(query, k=top_k)
            results = bm25_results
            openai = None

            if use_openai:
                try:
                    ranking = rank_candidates_with_openai(query, bm25_results)
                    by_id = {result.doc_id: result for result in bm25_results}
                    results = [by_id[doc_id] for doc_id in ranking.ranked_doc_ids if doc_id in by_id]
                    openai = {"model": ranking.model, "raw_text": ranking.raw_text}
                except Exception as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)
                    return

            self._send_json(
                {
                    "query": query,
                    "mode": "openai_rerank" if use_openai else "bm25",
                    "openai": openai,
                    "results": [_result_to_dict(result, rank) for rank, result in enumerate(results, start=1)],
                }
            )

        def _handle_evaluate(self, query_string: str) -> None:
            params = parse_qs(query_string)
            use_openai = params.get("openai", ["false"])[0].lower() == "true"
            try:
                report = evaluate(openai_rerank=use_openai)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)
                return
            self._send_json(report["summary"])

        def _send_file(self, path: Path) -> None:
            try:
                resolved = path.resolve()
                resolved.relative_to(WEB_ROOT.resolve())
            except ValueError:
                self._send_json({"error": "Forbidden"}, status=HTTPStatus.FORBIDDEN)
                return

            if not resolved.exists() or not resolved.is_file():
                self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
                return

            content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
            data = resolved.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return TextbookSearchHandler


def _result_to_dict(result: SearchResult, rank: int) -> dict:
    data = asdict(result)
    data["rank"] = rank
    return data


def _parse_int(value: str, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(minimum, min(maximum, parsed))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the textbook search web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Optional .env file for OpenAI API calls")
    args = parser.parse_args()

    load_env_file(args.env_file)
    server = ThreadingHTTPServer((args.host, args.port), create_handler(AppState()))
    url = f"http://{args.host}:{args.port}"
    print(f"Textbook Search UI running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
