import unittest

from textbook_search.evaluate import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


class MetricTests(unittest.TestCase):
    def test_precision_at_k(self):
        relevance = {"a": 3, "b": 0, "c": 1}
        self.assertAlmostEqual(precision_at_k(relevance, ["a", "b", "c"], 3), 2 / 3)

    def test_recall_at_k(self):
        relevance = {"a": 3, "c": 1}
        self.assertAlmostEqual(recall_at_k(relevance, ["a", "b", "c"], 2), 0.5)

    def test_reciprocal_rank(self):
        self.assertAlmostEqual(reciprocal_rank({"c": 1}, ["a", "b", "c"]), 1 / 3)

    def test_ndcg_is_one_for_ideal_ranking(self):
        relevance = {"a": 3, "b": 2, "c": 1}
        self.assertAlmostEqual(ndcg_at_k(relevance, ["a", "b", "c"], 3), 1.0)


if __name__ == "__main__":
    unittest.main()
