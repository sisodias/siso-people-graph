from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from integration.capabilities import capability_report, detect_repository_capabilities


class CapabilityTests(unittest.TestCase):
    def test_current_main_like_tree_is_reported_as_declared_not_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "schema").mkdir()
            (root / "loaders").mkdir()
            (root / "schema/people_schema_v2.sql").write_text("-- fixture\n")
            (root / "loaders/build_people_graph_v2.py").write_text("# fixture\n")
            (root / "loaders/build_people_graph_books.py").write_text("# fixture\n")
            (root / "loaders/match_identities.py").write_text("# fixture\n")
            (root / "loaders/ask.py").write_text("# fixture\n")
            items = {item.key: item for item in detect_repository_capabilities(root)}
        self.assertEqual(items["v2.schema"].status, "declared")
        self.assertEqual(items["v2.build"].status, "declared")
        self.assertEqual(items["v2.identity_claims"].status, "declared")
        self.assertEqual(items["v2.query"].status, "declared")
        self.assertEqual(items["v3.schema"].status, "missing")
        self.assertEqual(items["reasoning.claims"].status, "missing")

    def test_partial_lane_merge_is_detected_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in (
                "integration/contract.py",
                "integration/pg_observation_0_1.schema.json",
                "integration/adapters.py",
                "integration/merge_risk.py",
                "integration/lane_registry.json",
                "schema/v3/schema.sql",
                "identity_v3/engine.py",
                "query_v3/library.py",
                "api/server.py",
            ):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture\n")
            report = capability_report(root)
        items = {item["key"]: item for item in report["repository"]}
        self.assertEqual(items["integration.observation_contract"]["status"], "available")
        self.assertEqual(items["v3.schema"]["status"], "declared")
        self.assertEqual(items["v3.identity_resolution"]["status"], "available")
        self.assertEqual(items["v3.query_library"]["status"], "available")
        self.assertEqual(items["v3.http_api"]["status"], "available")
        self.assertEqual(items["v3.mcp"]["status"], "missing")


if __name__ == "__main__":
    unittest.main()
