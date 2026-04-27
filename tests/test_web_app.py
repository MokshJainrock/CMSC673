import json
import unittest
from urllib.parse import urlencode

from web_app import AppState, create_handler


class DummyHandler(create_handler(AppState())):
    def __init__(self):
        self.status = None
        self.payload = None

    def send_response(self, status):
        self.status = status

    def send_header(self, *_args):
        return None

    def end_headers(self):
        return None

    @property
    def wfile(self):
        class Writer:
            def __init__(self, outer):
                self.outer = outer

            def write(self, body):
                self.outer.payload = json.loads(body.decode("utf-8"))

        return Writer(self)


class WebAppTests(unittest.TestCase):
    def test_search_endpoint_returns_results(self):
        handler = DummyHandler()
        handler._handle_search(urlencode({"q": "rubisco carbon fixation", "k": "2"}))
        self.assertEqual(handler.status, 200)
        self.assertEqual(handler.payload["results"][0]["doc_id"], "bio2e_08_03_calvin_cycle")

    def test_search_endpoint_requires_query(self):
        handler = DummyHandler()
        handler._handle_search(urlencode({"q": ""}))
        self.assertEqual(handler.status, 400)
        self.assertIn("error", handler.payload)


if __name__ == "__main__":
    unittest.main()
