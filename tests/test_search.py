import unittest

from textbook_search.loader import load_corpus, load_eval_queries
from textbook_search.search import TextbookSearchEngine
from textbook_search.tokenizer import tokenize


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = TextbookSearchEngine()

    def test_corpus_has_realistic_size_and_metadata(self):
        documents = load_corpus()
        self.assertGreaterEqual(len(documents), 20)
        self.assertTrue(all(document.source_url.startswith("https://openstax.org/") for document in documents))

    def test_tokenization_is_case_insensitive(self):
        self.assertEqual(tokenize("Krebs CYCLE"), tokenize("krebs cycle"))

    def test_exact_topic_returns_expected_section_first(self):
        top = self.engine.search("Calvin cycle carbon fixation", k=1)[0]
        self.assertEqual(top.doc_id, "bio2e_08_03_calvin_cycle")

    def test_search_is_deterministic(self):
        first = self.engine.search("ATP synthase proton gradient", k=5)
        second = self.engine.search("ATP synthase proton gradient", k=5)
        self.assertEqual(first, second)

    def test_eval_queries_reference_existing_documents(self):
        ids = {document.doc_id for document in load_corpus()}
        for query in load_eval_queries():
            self.assertTrue(set(query["relevance"]).issubset(ids))


if __name__ == "__main__":
    unittest.main()
