from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from integration.cli import main


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/integration_parallel/fixtures"


class CLITests(unittest.TestCase):
    def invoke(self, argv: list[str]) -> tuple[int, dict]:
        output = io.StringIO()
        with redirect_stdout(output):
            status = main(argv)
        return status, json.loads(output.getvalue())

    def test_check_command_passes_on_lane_local_fixtures(self) -> None:
        status, report = self.invoke(
            ["check", "--repo-root", str(ROOT), "--base-sha", "fixture-main"]
        )
        self.assertEqual(status, 0, report)
        self.assertTrue(report["valid"])
        self.assertEqual(report["blocking_risk_count"], 0)
        self.assertEqual(
            report["rerun_command"], "python3 -m integration check --repo-root ."
        )

    def test_roundtrip_command_emits_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "out.ndjson"
            status, report = self.invoke(
                [
                    "roundtrip",
                    str(FIXTURES / "valid_observations.ndjson"),
                    str(output_path),
                ]
            )
        self.assertEqual(status, 0, report)
        self.assertTrue(report["logical_roundtrip_equal"])
        self.assertEqual(len(report["output_sha256"]), 64)

    def test_risk_command_blocks_p0_fixture(self) -> None:
        status, report = self.invoke(
            [
                "risk",
                str(FIXTURES / "open_pr_snapshot_conflict.json"),
                "--registry",
                str(ROOT / "integration/lane_registry.json"),
            ]
        )
        self.assertEqual(status, 1)
        self.assertGreater(report["risk_counts"].get("P0", 0), 0)


if __name__ == "__main__":
    unittest.main()
