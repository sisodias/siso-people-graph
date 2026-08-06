import unittest

from measure_precision import measure


class PrecisionTests(unittest.TestCase):
    def test_adversarial_fixture_policy_measurements(self):
        result = measure()
        automatic = result["automatic_candidates"]
        review = result["review_only_candidates"]
        policy = result["automatic_acceptance_policy"]
        self.assertEqual(automatic["precision"], 1.0)
        self.assertEqual(automatic["false_positive"], 0)
        self.assertEqual(automatic["true_positive"], 4)
        self.assertEqual(automatic["unknown_or_conflict_fixture"], 2)
        self.assertEqual(review["true_positive"], 1)
        self.assertEqual(review["false_positive"], 5)
        self.assertAlmostEqual(review["precision"], 1 / 6, places=6)
        self.assertEqual(policy["blocked_by_cluster_conflict"], 1)
        self.assertTrue(policy["cluster_invariants_ok"])


if __name__ == "__main__":
    unittest.main()
