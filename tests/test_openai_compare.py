import unittest

from textbook_search.env import load_env_file
from textbook_search.openai_compare import parse_ranked_doc_ids


class OpenAICompareTests(unittest.TestCase):
    def test_parse_ranked_doc_ids_keeps_valid_ids_in_model_order(self):
        valid_ids = ["bio2e_08_03_calvin_cycle", "bio2e_08_01_photosynthesis_intro"]
        raw_text = "1. bio2e_08_01_photosynthesis_intro, 2. bio2e_08_03_calvin_cycle"
        self.assertEqual(
            parse_ranked_doc_ids(raw_text, valid_ids),
            ["bio2e_08_01_photosynthesis_intro", "bio2e_08_03_calvin_cycle"],
        )

    def test_parse_ranked_doc_ids_appends_missing_candidates(self):
        valid_ids = ["a_doc", "b_doc", "c_doc"]
        self.assertEqual(parse_ranked_doc_ids("b_doc", valid_ids), ["b_doc", "a_doc", "c_doc"])

    def test_missing_env_file_is_noop(self):
        self.assertIsNone(load_env_file("/path/that/does/not/exist/.env"))


if __name__ == "__main__":
    unittest.main()
