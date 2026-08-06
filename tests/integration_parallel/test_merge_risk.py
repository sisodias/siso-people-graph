from __future__ import annotations

from pathlib import Path
import unittest

from integration.lanes import load_lane_registry
from integration.merge_risk import analyze_merge_risks, load_pr_snapshot


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/integration_parallel/fixtures"
REGISTRY = load_lane_registry(ROOT / "integration/lane_registry.json")


class MergeRiskTests(unittest.TestCase):
    def test_launch_snapshot_records_no_open_prs_without_invented_risks(self) -> None:
        report = analyze_merge_risks(
            load_pr_snapshot(FIXTURES / "open_pr_snapshot_empty.json"), REGISTRY
        )
        self.assertTrue(report["valid"])
        self.assertEqual(report["open_pr_count"], 0)
        self.assertEqual(report["launch_state"], "no_open_prs")
        self.assertEqual(report["risks"], [])

    def test_conflict_fixture_finds_overlap_and_ownership_escape(self) -> None:
        report = analyze_merge_risks(
            load_pr_snapshot(FIXTURES / "open_pr_snapshot_conflict.json"), REGISTRY
        )
        codes = {risk["risk_id"] for risk in report["risks"]}
        categories = {risk["category"] for risk in report["risks"]}
        self.assertIn("path_overlap", categories)
        self.assertIn("ownership", categories)
        self.assertTrue(any(code.startswith("MR-PATH-OVERLAP") for code in codes))
        self.assertTrue(any(code.startswith("MR-OUTSIDE-OWNERSHIP") for code in codes))
        self.assertTrue(any(risk["severity"] == "P0" for risk in report["risks"]))


if __name__ == "__main__":
    unittest.main()
