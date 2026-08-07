from __future__ import annotations

from pathlib import Path
import unittest

from integration.lanes import (
    changed_paths_outside_lane,
    lane_by_branch,
    load_lane_registry,
    owner_for_path,
    validate_lane_registry,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = load_lane_registry(ROOT / "integration/lane_registry.json")


class LaneRegistryTests(unittest.TestCase):
    def test_all_thirteen_lanes_have_non_overlapping_ownership(self) -> None:
        report = validate_lane_registry(REGISTRY)
        self.assertTrue(report["valid"], report)
        self.assertEqual(report["lane_count"], 13)

    def test_integration_path_has_exactly_one_owner(self) -> None:
        owners = owner_for_path(
            REGISTRY,
            "sisodias/siso-people-graph",
            "integration/contract.py",
        )
        self.assertEqual([lane["id"] for lane in owners], [13])

    def test_lane_local_file_check_reports_escape(self) -> None:
        lane = lane_by_branch(
            REGISTRY,
            "sisodias/siso-people-graph",
            "pg/query-surface-parallel-20260806",
        )
        self.assertIsNotNone(lane)
        outside = changed_paths_outside_lane(
            lane,
            ["query_v3/library.py", "api/server.py", "schema/v3/schema.sql"],
        )
        self.assertEqual(outside, ["schema/v3/schema.sql"])


if __name__ == "__main__":
    unittest.main()
