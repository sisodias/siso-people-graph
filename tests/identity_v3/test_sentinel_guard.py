"""Regression tests for the sentinel-identifier guard.

Measured on the shipped graph-v2 asset (SHA-256 9938237a…b919b): 22 crates.io
derived rows carry `github_id` values of 0 or -1, a "no GitHub account"
sentinel. Without this guard they produced 159 auto-eligible
`shared_external_id` candidates at 0.995 confidence, all false, and applying
the documented automatic policy fused 18 distinct humans into one canonical
cluster and 4 into another.
"""
from __future__ import annotations

import sqlite3
import unittest

from identity_v3.engine import IdentityEngine, IdentityError
from identity_v3.registry import is_sentinel_value


def _engine() -> IdentityEngine:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    engine = IdentityEngine(conn)
    engine.ensure_schema()
    return engine


SENTINELS = [
        ("github_id", "0"),
        ("github_id", "-1"),
        ("github_id", "-42"),
        ("github_id", "ghost"),
        ("github_node_id", "0"),
        ("orcid", "0000-0000-0000-0000"),
        ("wikidata", "Q0"),
        ("github_id", ""),
        ("github_id", "none"),
        ("github_id", "deleted-user"),
]

REAL_IDS = [
        ("github_id", "1"),
        ("github_id", "583231"),          # octocat, a real account
        ("orcid", "0000-0002-1825-0097"),
        ("wikidata", "Q42"),
        ("youtube_channel_id", "UCXuqSBlHAE6Xw-yeJA0Tunw"),
]


class SentinelGuardTest(unittest.TestCase):
    def test_sentinels_are_rejected(self) -> None:
        for scheme, value in SENTINELS:
            with self.subTest(scheme=scheme, value=value):
                self.assertIs(is_sentinel_value(scheme, value), True)

    def test_real_identifiers_are_not_sentinels(self) -> None:
        for scheme, value in REAL_IDS:
            with self.subTest(scheme=scheme, value=value):
                self.assertIs(is_sentinel_value(scheme, value), False)


    def test_sentinel_never_generates_auto_candidate(self) -> None:
        """The exact production failure: distinct humans sharing github_id=0."""
        engine = _engine()
        for entity_id, label in (
            ("gh:ghost_a", "Aaron Weiss"),
            ("gh:ghost_b", "Huo Linhe"),
            ("gh:ghost_c", "Mohammad Aliyan"),
        ):
            engine.upsert_entity(entity_id, label=label, kind="unknown", origin="crates_io")
            engine.record_identifier(entity_id, "github_id", "0", source="test")

        candidates = engine.generate_candidates(apply=True)
        auto = [c for c in candidates if c["auto_eligible"]]
        assert auto == [], f"sentinel produced auto-eligible candidates: {auto}"


    def test_real_shared_id_still_generates_auto_candidate(self) -> None:
        """The guard must not suppress genuine matches."""
        engine = _engine()
        for entity_id in ("a", "b"):
            engine.upsert_entity(entity_id, label="Real Person", kind="human", origin="github")
            engine.record_identifier(entity_id, "github_id", "583231", source="test")

        candidates = engine.generate_candidates(apply=True)
        auto = [c for c in candidates if c["auto_eligible"]]
        assert len(auto) == 1
        assert auto[0]["method"] == "shared_external_id"


    def test_accept_gate_blocks_sentinel_candidate_defence_in_depth(self) -> None:
        """A candidate minted before the guard existed must still not auto-accept."""
        engine = _engine()
        for entity_id, label in (("x", "Person X"), ("y", "Person Y")):
            engine.upsert_entity(entity_id, label=label, kind="unknown", origin="crates_io")
        now = "2026-08-08T00:00:00Z"
        engine.connection.execute(
            "INSERT INTO identity_v3_candidate (candidate_id,entity_a,entity_b,method,"
            "method_version,confidence,auto_eligible,positive_evidence_json,"
            "negative_evidence_json,conflict_reasons_json,review_state,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("cand:legacy", "x", "y", "shared_external_id", "identity-v3.1.0", 0.995, 1,
             '[{"type":"eligible_identifier_match","scheme":"github_id","value":"0"}]',
             "[]", "[]", "proposed", now, now),
        )
        engine.connection.commit()

        with self.assertRaisesRegex(IdentityError, "sentinel"):
                engine.accept_candidate("cand:legacy", decided_by="test", automatic=True)


if __name__ == "__main__":
    unittest.main()
