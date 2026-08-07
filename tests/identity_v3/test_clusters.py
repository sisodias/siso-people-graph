import unittest

from identity_v3.engine import IdentityEngine, IdentityError

from common import load_adversarial, pair_key


class ClusterTests(unittest.TestCase):
    def test_transitive_closure_redirect_and_undo_are_deterministic(self):
        with IdentityEngine(":memory:") as engine:
            for entity_id, origin in (
                ("registry:alpha", "registry"),
                ("github:alpha", "github"),
                ("youtube:alpha", "youtube"),
            ):
                engine.upsert_entity(entity_id, label="Alpha Person", kind="human", origin=origin)
                engine.record_identifier(
                    entity_id, "orcid", "0000-0003-0000-0001",
                    source="fixture", observed_at="2026-08-06T00:00:00Z",
                )
            candidates = engine.generate_candidates(apply=True)
            by_pair = {
                pair_key(str(candidate["entity_a"]), str(candidate["entity_b"])): candidate
                for candidate in candidates
            }
            first = engine.accept_candidate(
                str(by_pair[pair_key("registry:alpha", "github:alpha")]["candidate_id"]),
                decided_by="test:auto", automatic=True,
            )
            second = engine.accept_candidate(
                str(by_pair[pair_key("github:alpha", "youtube:alpha")]["candidate_id"]),
                decided_by="test:auto", automatic=True,
            )
            resolved = engine.resolve_entity("youtube:alpha")
            self.assertEqual(resolved["canonical_entity_id"], "registry:alpha")
            self.assertEqual(resolved["members"], ["github:alpha", "registry:alpha", "youtube:alpha"])

            undo = engine.undo_decision(second["decision_id"])
            self.assertEqual(undo["undone_decision_id"], second["decision_id"])
            split = engine.resolve_entity("youtube:alpha")
            self.assertEqual(split["members"], ["youtube:alpha"])
            preserved = engine.connection.execute(
                "SELECT COUNT(*) FROM identity_v3_entity"
            ).fetchone()[0]
            self.assertEqual(preserved, 3)

    def test_prospective_conflicting_stable_ids_block_automatic_cluster(self):
        with IdentityEngine(":memory:") as engine:
            load_adversarial(engine)
            candidates = engine.generate_candidates(apply=True)
            by_pair = {
                pair_key(str(candidate["entity_a"]), str(candidate["entity_b"])): candidate
                for candidate in candidates
            }
            ab = by_pair[pair_key("impossible:a", "impossible:b")]
            bc = by_pair[pair_key("impossible:b", "impossible:c")]
            engine.accept_candidate(str(ab["candidate_id"]), decided_by="test:auto", automatic=True)
            with self.assertRaises(IdentityError):
                engine.accept_candidate(str(bc["candidate_id"]), decided_by="test:auto", automatic=True)

            forced = engine.accept_candidate(
                str(bc["candidate_id"]), decided_by="test:manual",
                rationale="Fixture intentionally creates an impossible cluster",
                allow_conflicts=True,
            )
            audit = engine.audit()
            self.assertFalse(audit["invariants_ok"])
            self.assertEqual(audit["cluster_conflicts"][0]["conflicts"][0]["scheme"], "orcid")

            engine.undo_decision(forced["decision_id"])
            self.assertTrue(engine.audit()["invariants_ok"])


if __name__ == "__main__":
    unittest.main()
