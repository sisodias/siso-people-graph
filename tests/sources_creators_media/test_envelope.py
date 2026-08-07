from __future__ import annotations

import copy
import unittest

from sources.creators.envelope import (
    EnvelopeError,
    evidence,
    identifier,
    make_envelope,
    payload_sha256,
    source_block,
    validate_envelope,
)


class EnvelopeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.envelope = make_envelope(
            source=source_block(
                source_id="fixture",
                snapshot_id="fixture-snapshot",
                record_native_id="record-1",
                observed_at="2026-08-01T00:00:00Z",
                retrieved_at="2026-08-02T00:00:00Z",
                terms_revision="fixture terms",
                rights_state="public_metadata",
                payload={"id": "record-1"},
            ),
            subject_kind="work",
            subject_native_id="record-1",
            label="Fixture work",
            attributes={"work_type": "article"},
            identifiers=[
                identifier(
                    scheme="doi",
                    value="10.5555/test",
                    scope="global",
                    stability="stable",
                    uniqueness="unique",
                    evidence="fixture DOI",
                )
            ],
            contributions=[],
            relationships=[],
            evidence_items=[
                evidence(kind="literal_source_field", locator="fixture#title", literal="Fixture work")
            ],
            raw_pointer="fixture://record-1",
        )

    def test_valid_envelope(self) -> None:
        validate_envelope(self.envelope)

    def test_payload_hash_is_deterministic_for_mappings(self) -> None:
        self.assertEqual(payload_sha256({"b": 2, "a": 1}), payload_sha256({"a": 1, "b": 2}))

    def test_canonical_identity_fields_are_rejected_recursively(self) -> None:
        invalid = copy.deepcopy(self.envelope)
        invalid["subject"]["attributes"]["canonical_id"] = "pg:someone"
        with self.assertRaisesRegex(EnvelopeError, "never assign canonical identity"):
            validate_envelope(invalid)

    def test_name_cannot_be_a_global_identifier(self) -> None:
        invalid = copy.deepcopy(self.envelope)
        invalid["identifiers"].append(
            identifier(
                scheme="name",
                value="Alex Rivera",
                scope="global",
                stability="unknown",
                uniqueness="unique",
                evidence="display name",
            )
        )
        with self.assertRaisesRegex(EnvelopeError, "never a global identifier"):
            validate_envelope(invalid)

    def test_contribution_identifier_uses_same_identity_rules(self) -> None:
        invalid = copy.deepcopy(self.envelope)
        invalid["contributions"] = [
            {
                "role": "author",
                "agent": {
                    "source_native_id": "label:Alex Rivera",
                    "label": "Alex Rivera",
                    "identifiers": [
                        identifier(
                            scheme="name",
                            value="Alex Rivera",
                            scope="global",
                            stability="unknown",
                            uniqueness="unknown",
                            evidence="display name only",
                        )
                    ],
                },
                "evidence": "fixture author",
            }
        ]
        with self.assertRaisesRegex(EnvelopeError, "never a global identifier"):
            validate_envelope(invalid)

    def test_model_receipt_requires_inference_flag(self) -> None:
        invalid = copy.deepcopy(self.envelope)
        invalid["evidence"].append(
            evidence(
                kind="classification",
                locator="fixture",
                inference=False,
                model={
                    "name": "fixture-model",
                    "version": "1",
                    "input_sha256": "0" * 64,
                },
            )
        )
        with self.assertRaisesRegex(EnvelopeError, "must be marked as inference"):
            validate_envelope(invalid)


if __name__ == "__main__":
    unittest.main()
