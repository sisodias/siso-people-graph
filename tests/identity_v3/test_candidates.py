from pathlib import Path
import os
import sqlite3
import tempfile
import unittest

from identity_v3.engine import IdentityEngine
from loaders.match_identities import propose

from common import load_adversarial, make_v2_connection, pair_key


class CandidateTests(unittest.TestCase):
    def test_adversarial_non_unique_fields_never_auto_resolve(self):
        with IdentityEngine(":memory:") as engine:
            fixture = load_adversarial(engine)
            candidates = engine.generate_candidates(apply=True)
            by_pair = {
                pair_key(str(candidate["entity_a"]), str(candidate["entity_b"])): candidate
                for candidate in candidates
            }

            alice = by_pair[pair_key("gh:alice-old", "gh:alice-new")]
            self.assertEqual(alice["method"], "shared_external_id")
            self.assertTrue(alice["auto_eligible"])

            common_name = by_pair[pair_key("gh:alex-lee-one", "book:alex-lee-two")]
            self.assertEqual(common_name["method"], "exact_name")
            self.assertFalse(common_name["auto_eligible"])

            organisation = by_pair[pair_key("org:marina-chen", "person:marina-chen")]
            self.assertFalse(organisation["auto_eligible"])
            self.assertIn("human_organisation_conflict", organisation["conflict_reasons"])

            surname = by_pair[pair_key("surname:one", "surname:two")]
            self.assertEqual(surname["method"], "surname_initial")
            self.assertFalse(surname["auto_eligible"])

            for distinct in fixture["known_distinct_pairs"]:
                candidate = by_pair.get(pair_key(*distinct))
                if candidate:
                    self.assertFalse(candidate["auto_eligible"], distinct)

    def test_current_matcher_accepts_only_registry_eligible_shared_ids(self):
        handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        handle.close()
        try:
            connection = make_v2_connection(handle.name)
            people = [
                ("a", "Coder One"),
                ("b", "Coder Uno"),
                ("c", "Employee One"),
                ("d", "Employee Two"),
            ]
            connection.executemany(
                """INSERT INTO person
                   (person_id,name,kind,state,origin,rank_score,built_at)
                   VALUES (?,?,'human','linked','github',0,'2026-08-01T00:00:00Z')""",
                people,
            )
            connection.executemany(
                """INSERT INTO external_ids(person_id,platform,value,confidence,source)
                   VALUES (?,?,?,?,?)""",
                [
                    ("a", "github_id", "777", 1.0, "fixture"),
                    ("b", "github_id", "777", 1.0, "fixture"),
                    ("c", "company", "Shared Corp", 1.0, "fixture"),
                    ("d", "company", "Shared Corp", 1.0, "fixture"),
                ],
            )
            connection.commit()
            connection.close()

            summary = propose(handle.name, True, "shared_external_id")
            self.assertEqual(summary["auto_accepted"], 1)

            check = sqlite3.connect(handle.name)
            rows = check.execute(
                "SELECT person_a,person_b,method,status,evidence FROM identity_claim ORDER BY claim_id"
            ).fetchall()
            check.close()
            self.assertEqual([(row[0], row[1], row[2], row[3]) for row in rows], [
                ("a", "b", "shared_external_id", "accepted")
            ])
            self.assertNotIn("Shared Corp", rows[0][4])
        finally:
            os.unlink(handle.name)

    def test_automatic_acceptance_rejects_review_method_flag(self):
        handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        handle.close()
        try:
            connection = make_v2_connection(handle.name)
            connection.executemany(
                """INSERT INTO person
                   (person_id,name,kind,state,origin,rank_score,built_at)
                   VALUES (?,?,'human','linked',?,0,'2026-08-01T00:00:00Z')""",
                [("a", "Alex Lee", "github"), ("b", "Alex Lee", "book")],
            )
            connection.commit()
            connection.close()
            summary = propose(handle.name, False, None)
            self.assertEqual(summary["by_method"].get("exact_name"), 1)
            with self.assertRaises(Exception):
                propose(handle.name, True, "exact_name")
        finally:
            os.unlink(handle.name)


if __name__ == "__main__":
    unittest.main()
