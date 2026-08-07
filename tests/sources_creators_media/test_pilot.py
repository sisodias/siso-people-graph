from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sources.media.pilot import main

FIXTURES = Path(__file__).parent / "fixtures"
RETRIEVED_AT = "2026-08-06T15:00:00Z"


class PilotCliTests(unittest.TestCase):
    def test_export_and_validate_offline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            rc = main(
                [
                    "export-fixtures",
                    "--fixture-dir",
                    str(FIXTURES),
                    "--out-dir",
                    str(out),
                    "--retrieved-at",
                    RETRIEVED_AT,
                    "--target-size",
                    "250",
                ]
            )
            self.assertEqual(0, rc)
            self.assertEqual(0, main(["validate", str(out / "observations.ndjson")]))
            metrics = json.loads((out / "pilot-metrics.json").read_text())
            self.assertEqual(16, metrics["records"])
            self.assertEqual(4, metrics["bridge_candidates"]["all"])
            self.assertEqual(0, metrics["quota_and_cost"]["network_requests_made"])
            manifest = json.loads((out / "cohort-manifest.json").read_text())
            self.assertEqual(250, manifest["target_size"])
            self.assertEqual(10, manifest["actual_size"])
            self.assertEqual(1.0, metrics["removal_coverage"]["coverage"])
            self.assertEqual([], metrics["removal_coverage"]["missing_source_policies"])
            self.assertEqual(0, main(["policies", "--out", str(out / "source-policies.json")]))
            policies = json.loads((out / "source-policies.json").read_text())
            self.assertEqual(9, len(policies["sources"]))


if __name__ == "__main__":
    unittest.main()
