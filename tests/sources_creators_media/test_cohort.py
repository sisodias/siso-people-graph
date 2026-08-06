from __future__ import annotations

import copy
import unittest
from pathlib import Path

from sources.creators.cohort import CohortError, build_manifest, observation_metrics, read_seeds
from sources.media.pilot import fixture_observations

FIXTURES = Path(__file__).parent / "fixtures"
GENERATED_AT = "2026-08-06T15:00:00Z"


class CohortTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seeds = read_seeds(FIXTURES / "seeds.ndjson")

    def test_manifest_is_deterministic_and_source_balanced(self) -> None:
        kwargs = {
            "target_size": 250,
            "source_targets": {"github_seed": 125, "modern_author_seed": 125},
            "generated_at": GENERATED_AT,
        }
        first = build_manifest(self.seeds, **kwargs)
        second = build_manifest(reversed(self.seeds), **kwargs)
        self.assertEqual(first, second)
        self.assertEqual(10, first["actual_size"])
        self.assertEqual(240, first["unfilled_slots"])
        self.assertEqual("fixture_only", first["status"])
        self.assertEqual({"github_seed": 5, "modern_author_seed": 5}, first["source_counts"])

    def test_name_only_seed_is_rejected(self) -> None:
        seed = copy.deepcopy(self.seeds[0])
        seed["seed_id"] = "fixture:bad"
        seed["stable_identifiers"] = []
        with self.assertRaisesRegex(CohortError, "name-only seeds are forbidden"):
            build_manifest([seed], target_size=1, generated_at=GENERATED_AT)

    def test_metrics_do_not_accept_identity(self) -> None:
        manifest = build_manifest(self.seeds, target_size=250, generated_at=GENERATED_AT)
        records = fixture_observations(FIXTURES, GENERATED_AT)
        metrics = observation_metrics(records, manifest=manifest)
        self.assertEqual(0, metrics["bridge_candidates"]["automatic_acceptance"])
        self.assertEqual(1.0, metrics["rights"]["completeness"])
        self.assertEqual(0, metrics["retention"]["transcript_or_media_payloads_persisted"])


if __name__ == "__main__":
    unittest.main()
