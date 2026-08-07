from __future__ import annotations

import hashlib
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sources.software.envelope import (
    EnvelopeError,
    canonical_json,
    make_envelope,
    read_ndjson,
    validate_envelope,
    write_ndjson,
)
from sources.software.pilot import build_records, compute_metrics

FIXTURES = Path(__file__).parent / "fixtures"


def records_with(records, *, source=None, kind=None, work_type=None):
    selected = []
    for record in records:
        if source and record["source"]["source_id"] != source:
            continue
        if kind and record["subject"]["kind"] != kind:
            continue
        if work_type and record["subject"]["attributes"].get("work_type") != work_type:
            continue
        selected.append(record)
    return selected


class EnvelopeContractTests(unittest.TestCase):
    def test_rejects_canonical_or_rank_fields(self):
        base = make_envelope(
            source_id="fixture",
            snapshot_id="s1",
            record_native_id="r1",
            observed_at="2026-08-06T00:00:00Z",
            retrieved_at="2026-08-06T00:00:01Z",
            terms_revision="fixture",
            rights_state="public_metadata",
            raw_record={"id": 1},
            subject_kind="account",
            subject_native_id="fixture:1",
            subject_label="one",
            raw_pointer="fixture.json#1",
        )
        for key in ("canonical_id", "rank_score", "merged_into"):
            candidate = json.loads(json.dumps(base))
            candidate["subject"]["attributes"][key] = "forbidden"
            with self.subTest(key=key), self.assertRaises(EnvelopeError):
                validate_envelope(candidate)

    def test_rejects_name_company_and_location_as_identifiers(self):
        for scheme in ("name", "real_name", "company", "location", "bio"):
            with self.subTest(scheme=scheme), self.assertRaises(EnvelopeError):
                make_envelope(
                    source_id="fixture",
                    snapshot_id="s1",
                    record_native_id="r1",
                    observed_at="2026-08-06T00:00:00Z",
                    retrieved_at="2026-08-06T00:00:01Z",
                    terms_revision="fixture",
                    rights_state="public_metadata",
                    raw_record={"id": 1},
                    subject_kind="account",
                    subject_native_id="fixture:1",
                    subject_label="one",
                    identifiers=[
                        {
                            "scheme": scheme,
                            "value": "shared value",
                            "scope": "global",
                            "stability": "unknown",
                            "uniqueness": "unknown",
                            "evidence": "literal fixture field",
                        }
                    ],
                    raw_pointer="fixture.json#1",
                )

    def test_unicode_is_preserved_in_canonical_json(self):
        encoded = canonical_json({"label": "李小龍", "alias": "Renée"})
        self.assertIn("李小龍", encoded)
        self.assertIn("Renée", encoded)
        self.assertNotIn("\\u", encoded)


class AdapterPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")):
            cls.records = build_records(FIXTURES)
        cls.metrics = compute_metrics(cls.records, fixture_dir=FIXTURES)

    def test_all_records_validate_offline(self):
        self.assertEqual(31, len(self.records))
        for record in self.records:
            validate_envelope(record)
        self.assertEqual(0, self.metrics["network_calls"])

    def test_export_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.ndjson"
            second = Path(tmp) / "second.ndjson"
            write_ndjson(self.records, first)
            write_ndjson(reversed(self.records), second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            replayed = read_ndjson(first)
            self.assertEqual(len(self.records), len(replayed))

    def test_committed_manifest_and_metrics_match_replay(self):
        root = Path(__file__).parents[2]
        manifest_path = root / "docs/source-methods/software-ai/pilot-manifest.json"
        metrics_path = root / "docs/source-methods/software-ai/pilot-metrics.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        committed_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        self.assertEqual(self.metrics, committed_metrics)
        with tempfile.TemporaryDirectory() as tmp:
            emitted = Path(tmp) / "pilot.ndjson"
            write_ndjson(self.records, emitted)
            digest = hashlib.sha256(emitted.read_bytes()).hexdigest()
        self.assertEqual(manifest["logical_ndjson_sha256"], digest)
        self.assertEqual(manifest["record_count"], len(self.records))
        for fixture in manifest["fixtures"]:
            path = root / fixture["path"]
            data = path.read_bytes()
            self.assertEqual(fixture["bytes"], len(data))
            self.assertEqual(fixture["sha256"], hashlib.sha256(data).hexdigest())

    def test_github_login_rename_preserves_numeric_account_id(self):
        alice = [
            record
            for record in records_with(self.records, source="github_rest")
            if record["subject"]["source_native_id"] == "github:account:101"
        ]
        self.assertEqual(1, len(alice))
        schemes = {item["scheme"]: item for item in alice[0]["identifiers"]}
        self.assertEqual("101", schemes["github_account_id"]["value"])
        self.assertEqual("stable", schemes["github_account_id"]["stability"])
        self.assertEqual("mutable", schemes["github_login"]["stability"])
        self.assertEqual("alice-ai", schemes["github_login"]["value"])
        self.assertEqual("renamed_from", alice[0]["relationships"][0]["predicate"])
        self.assertEqual("alice-old", alice[0]["relationships"][0]["object"]["label"])

    def test_repository_transfer_uses_stable_repository_id(self):
        observations = [
            record
            for record in records_with(self.records, source="github_rest", work_type="software_repository")
            if record["subject"]["source_native_id"] == "github:repository:1001"
        ]
        self.assertEqual(2, len(observations))
        self.assertEqual(
            {"alice-ai/vectorforge", "vector-labs/vectorforge"},
            {record["subject"]["label"] for record in observations},
        )
        stable_ids = {
            identifier["value"]
            for record in observations
            for identifier in record["identifiers"]
            if identifier["scheme"] == "github_repository_id"
        }
        self.assertEqual({"1001"}, stable_ids)
        latest = max(observations, key=lambda record: record["source"]["observed_at"])
        owner = next(edge for edge in latest["contributions"] if edge["role"] == "repository_owner")
        self.assertEqual("organisation", owner["agent"]["kind"])
        self.assertTrue(any(edge["predicate"] == "transferred_from" for edge in latest["relationships"]))

    def test_organisations_are_first_class_observations(self):
        organisations = records_with(self.records, kind="organisation")
        native_ids = {record["subject"]["source_native_id"] for record in organisations}
        self.assertIn("github:account:202", native_ids)
        self.assertIn("huggingface:account:vector-labs", native_ids)

    def test_package_maintainers_are_contributions_not_aliases(self):
        packages = records_with(self.records, work_type="software_package")
        self.assertEqual(6, len(packages))
        for package in packages:
            self.assertEqual("work", package["subject"]["kind"])
            for contribution in package["contributions"]:
                self.assertIn(contribution["role"], {"owner", "maintainer", "publisher"})
                self.assertIn(contribution["agent"]["kind"], {"account", "organisation"})
        vectorforge = next(
            record
            for record in packages
            if record["source"]["source_id"] == "pypi"
            and record["subject"]["source_native_id"] == "pkg:pypi/vectorforge"
        )
        self.assertEqual(2, len(vectorforge["contributions"]))
        self.assertNotIn("aliases", vectorforge["subject"]["attributes"])

    def test_dependency_edges_cross_registries(self):
        dependencies = [
            edge
            for record in self.records
            for edge in record["relationships"]
            if edge["predicate"] == "depends_on"
        ]
        self.assertEqual(7, len(dependencies))
        targets = {edge["object"]["source_native_id"] for edge in dependencies}
        self.assertIn("pkg:pypi/numpy", targets)
        self.assertIn("pkg:cargo/vector-core", targets)
        self.assertIn("pkg:cargo/serde", targets)
        self.assertIn("pkg:npm/%40floating-ui/dom", targets)

    def test_software_heritage_ids_are_intrinsic_global_identifiers(self):
        archived = records_with(self.records, source="software_heritage")
        self.assertEqual(2, len(archived))
        for record in archived:
            identifier = record["identifiers"][0]
            self.assertEqual("swhid", identifier["scheme"])
            self.assertEqual("global", identifier["scope"])
            self.assertEqual("stable", identifier["stability"])
            self.assertEqual("unique", identifier["uniqueness"])
            self.assertTrue(record["relationships"])
            self.assertEqual("archives", record["relationships"][0]["predicate"])

    def test_huggingface_work_types_and_relationships_remain_distinct(self):
        hub_works = records_with(self.records, source="huggingface_hub", kind="work")
        work_types = {record["subject"]["attributes"]["work_type"] for record in hub_works}
        self.assertTrue({"ai_model", "ai_dataset", "ai_space"} <= work_types)
        space = next(
            record for record in hub_works if record["subject"]["attributes"]["work_type"] == "ai_space"
        )
        predicates = {edge["predicate"] for edge in space["relationships"]}
        self.assertEqual({"uses_model", "uses_dataset"}, predicates)
        model = next(
            record for record in hub_works if record["subject"]["attributes"]["work_type"] == "ai_model"
        )
        self.assertIn("trained_on", {edge["predicate"] for edge in model["relationships"]})

    def test_metrics_are_timestamped_observations_not_rank(self):
        self.assertEqual(43, self.metrics["metric_observations"])
        for record in self.records:
            serialized = canonical_json(record)
            self.assertNotIn("rank_score", serialized)
            self.assertNotIn("universal_score", serialized)
            for metric in record["subject"]["attributes"].get("metrics", []):
                self.assertIn("observed_at", metric)
                self.assertIn("name", metric)
                self.assertIn("value", metric)

    def test_cross_platform_identity_evidence_is_literal_and_not_a_merge(self):
        self.assertEqual(8, self.metrics["cross_platform_identity_evidence_receipts"])
        non_github = [
            record
            for record in self.records
            if record["source"]["source_id"] not in {"github_rest", "gh_archive"}
        ]
        receipts = []
        for record in non_github:
            for mapping in _walk(record):
                if mapping.get("scheme") == "github_account_id":
                    receipts.append(mapping)
                    self.assertIn("evidence", mapping)
                    self.assertEqual("stable", mapping["stability"])
        self.assertGreaterEqual(len(receipts), 8)
        self.assertTrue(all("canonical_id" not in canonical_json(record) for record in self.records))

    def test_conflicting_license_observations_are_preserved(self):
        self.assertEqual(1, self.metrics["source_conflict_count"])
        conflict = self.metrics["source_conflicts"][0]
        self.assertEqual("pkg:pypi/vectorforge", conflict["subject_native_id"])
        self.assertEqual(["Apache-2.0", "MIT"], conflict["distinct_values"])
        self.assertEqual("preserve_conflict_for_review", conflict["resolution"])

    def test_archived_and_abandoned_work_cases_exist(self):
        self.assertEqual(3, self.metrics["archived_works"])
        self.assertEqual(3, self.metrics["abandoned_works"])
        legacy = next(
            record
            for record in records_with(self.records, work_type="software_repository")
            if record["subject"]["source_native_id"] == "github:repository:1002"
        )
        self.assertTrue(legacy["subject"]["attributes"]["archived"])
        self.assertTrue(legacy["subject"]["attributes"]["abandoned"])

    def test_measured_fixture_summary(self):
        self.assertEqual(7, self.metrics["source_count"])
        self.assertEqual(36, self.metrics["stable_unique_identifiers"])
        self.assertEqual(30, self.metrics["contribution_edges"])
        self.assertEqual(35, self.metrics["relationship_edges"])
        self.assertEqual(100.0, self.metrics["rights_coverage"]["percent"])
        self.assertEqual(91.3, self.metrics["license_coverage"]["percent"])
        direct_npm = next(
            profile for profile in self.metrics["source_cost_profiles"] if profile["source"] == "npm_registry_direct"
        )
        self.assertEqual("deferred", direct_npm["acquisition"])


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


if __name__ == "__main__":
    unittest.main()
