from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from integration.contract import (
    ContractValidationError,
    assert_valid,
    iter_ndjson,
    repository_payload_resolver,
    validate_ndjson,
    validate_record,
    write_ndjson,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/integration_parallel/fixtures"


def fixture_record(index: int = 0) -> dict:
    return copy.deepcopy(list(iter_ndjson(FIXTURES / "valid_observations.ndjson"))[index][1])


class ObservationContractTests(unittest.TestCase):
    def test_valid_fixture_and_payload_digest(self) -> None:
        record = fixture_record(0)
        result = validate_record(
            record, payload_resolver=repository_payload_resolver(ROOT)
        )
        self.assertTrue(result.valid, result.to_dict())
        # A source's literal field called person_id is allowed as an attribute;
        # the contract bans canonical People Graph IDs, not source-native fields.
        self.assertEqual(record["subject"]["attributes"]["person_id"], "A123")

    def test_missing_rights_state_is_rejected(self) -> None:
        record = fixture_record()
        del record["source"]["rights_state"]
        result = validate_record(record)
        self.assertFalse(result.valid)
        self.assertIn("required.text", {issue.code for issue in result.errors})

    def test_payload_digest_mismatch_is_rejected(self) -> None:
        record = fixture_record()
        record["source"]["payload_sha256"] = "0" * 64
        result = validate_record(
            record, payload_resolver=repository_payload_resolver(ROOT)
        )
        self.assertIn(
            "payload.digest_mismatch", {issue.code for issue in result.errors}
        )

    def test_canonical_id_and_merge_directive_are_rejected_recursively(self) -> None:
        record = fixture_record()
        record["subject"]["attributes"]["canonical_person_id"] = "pg:person:1"
        record["evidence"].append({"kind": "model", "auto_merge": True})
        codes = {issue.code for issue in validate_record(record).errors}
        self.assertIn("identity.canonical_id_forbidden", codes)
        self.assertIn("identity.merge_directive_forbidden", codes)

    def test_non_unique_attributes_cannot_be_identifier_schemes(self) -> None:
        for scheme in ("name", "real_name", "company", "location", "bio", "topic"):
            with self.subTest(scheme=scheme):
                record = fixture_record()
                record["identifiers"] = [
                    {
                        "scheme": scheme,
                        "value": "shared literal",
                        "scope": "global",
                        "stability": "stable",
                        "uniqueness": "unique",
                        "evidence": "literal source field",
                    }
                ]
                codes = {issue.code for issue in validate_record(record).errors}
                self.assertIn("identifier.attribute_promoted", codes)

    def test_handles_are_mutable_source_aliases(self) -> None:
        record = fixture_record()
        record["identifiers"] = [
            {
                "scheme": "github_login",
                "value": "example",
                "scope": "global",
                "stability": "stable",
                "uniqueness": "unique",
                "evidence": "literal login field",
            }
        ]
        codes = {issue.code for issue in validate_record(record).errors}
        self.assertEqual(
            {"identifier.handle_global", "identifier.handle_stable", "identifier.handle_unique"},
            codes,
        )

    def test_identity_relationship_must_be_review_only_with_non_name_evidence(self) -> None:
        record = fixture_record()
        relationship = record["relationships"][0]
        relationship["review_state"] = "accepted"
        relationship["method"] = "exact_name"
        relationship["basis"] = ["name"]
        relationship["evidence"] = "same spelling"
        codes = {issue.code for issue in validate_record(record).errors}
        self.assertIn("identity.relationship_not_review_only", codes)
        self.assertIn("identity.name_only_merge", codes)

    def test_private_absolute_pointer_is_rejected(self) -> None:
        record = fixture_record()
        record["raw_pointer"] = "/Users/example/private/data.json"
        codes = {issue.code for issue in validate_record(record).errors}
        self.assertIn("pointer.private_path", codes)

    def test_assert_valid_raises_complete_contract_error(self) -> None:
        record = fixture_record()
        record["envelope_version"] = "future-version"
        with self.assertRaises(ContractValidationError) as context:
            assert_valid(record)
        self.assertIn("envelope.version", str(context.exception))

    def test_ndjson_roundtrip_is_logically_lossless(self) -> None:
        records = [record for _, record in iter_ndjson(FIXTURES / "valid_observations.ndjson")]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "roundtrip.ndjson"
            self.assertEqual(write_ndjson(output, records), 2)
            reread = [record for _, record in iter_ndjson(output)]
        self.assertEqual(records, reread)

    def test_invalid_ndjson_reports_line_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.ndjson"
            path.write_text('{"not": "closed"\n', encoding="utf-8")
            report = validate_ndjson(path)
        self.assertFalse(report["valid"])
        self.assertIn(":1:", report["file_error"])


if __name__ == "__main__":
    unittest.main()
