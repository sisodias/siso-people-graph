import json
import sqlite3
import unittest

from identity_v3.adapters import import_observation, import_v2
from identity_v3.engine import IdentityError

from common import make_v2_connection


class AdapterTests(unittest.TestCase):
    def test_v2_reclassifies_fields_and_quarantines_unsafe_accepted_claims(self):
        connection = make_v2_connection()
        connection.executemany(
            """INSERT INTO person
               (person_id,name,kind,state,origin,rank_score,built_at)
               VALUES (?,?,?,?,?,0,'2026-08-01T00:00:00Z')""",
            [
                ("registry:a", "Ada One", "human", "linked", "registry"),
                ("gh:a", "ada-one", "human", "linked", "github"),
                ("person:c", "Chris One", "human", "linked", "registry"),
                ("person:d", "Chris Two", "human", "linked", "registry"),
            ],
        )
        connection.executemany(
            """INSERT INTO external_ids(person_id,platform,value,confidence,source)
               VALUES (?,?,?,?,?)""",
            [
                ("registry:a", "github_id", "42", 1.0, "fixture"),
                ("registry:a", "github_login", "AdaOld", 1.0, "fixture"),
                ("registry:a", "company", "Shared Corp", 0.7, "fixture"),
                ("registry:a", "location", "London", 0.6, "fixture"),
                ("registry:a", "real_name", "Ada One", 1.0, "fixture"),
                ("registry:a", "followers", "100", 1.0, "fixture"),
                ("gh:a", "github_id", "42", 1.0, "fixture"),
                ("person:c", "company", "Shared Corp", 1.0, "fixture"),
                ("person:d", "company", "Shared Corp", 1.0, "fixture"),
            ],
        )
        connection.executemany(
            """INSERT INTO identity_claim
               (person_a,person_b,method,confidence,evidence,status,decided_by,created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            [
                (
                    "gh:a", "registry:a", "shared_external_id", 0.995,
                    json.dumps({
                        "method_version": "identity-v3.1.0",
                        "positive": [{"type": "eligible_identifier_match", "scheme": "github_id", "value": "42"}],
                    }),
                    "accepted", "identity_v3:auto", "2026-08-06T00:00:00Z",
                ),
                (
                    "person:c", "person:d", "shared_external_id", 0.98,
                    "company=shared corp", "accepted", "legacy:auto", "2026-08-06T00:00:00Z",
                ),
            ],
        )
        connection.commit()

        stats = import_v2(connection, observed_at="2026-08-06T01:00:00Z")
        self.assertEqual(stats["identifiers"], 2)
        self.assertEqual(stats["aliases"], 1)
        self.assertGreaterEqual(stats["attributes"], 6)
        self.assertEqual(stats["quarantined_claims"], 1)

        alias = connection.execute(
            """SELECT stable_identifier_scheme,stable_identifier_value
               FROM identity_v3_alias WHERE entity_id='registry:a' AND scheme='github_login'"""
        ).fetchone()
        self.assertEqual(tuple(alias), ("github_id", "42"))

        company_identifier_count = connection.execute(
            "SELECT COUNT(*) FROM identity_v3_identifier WHERE scheme='company'"
        ).fetchone()[0]
        self.assertEqual(company_identifier_count, 0)
        company_attribute_count = connection.execute(
            """SELECT COUNT(*) FROM identity_v3_attribute
               WHERE attribute='company' AND entity_id IN ('person:c','person:d')"""
        ).fetchone()[0]
        self.assertEqual(company_attribute_count, 2)

        accepted = connection.execute(
            """SELECT entity_a,entity_b FROM identity_v3_decision
               WHERE active=1 AND outcome='accepted'"""
        ).fetchall()
        self.assertEqual([tuple(row) for row in accepted], [("gh:a", "registry:a")])
        unsafe = connection.execute(
            """SELECT review_state,conflict_reasons_json FROM identity_v3_candidate
               WHERE entity_a='person:c' AND entity_b='person:d'"""
        ).fetchone()
        self.assertEqual(unsafe["review_state"], "proposed")
        self.assertIn("legacy_noneligible_external_id", unsafe["conflict_reasons_json"])

        generation = connection.execute(
            "SELECT MAX(generation) FROM identity_v3_generation"
        ).fetchone()[0]
        canonical = connection.execute(
            """SELECT canonical_entity_id FROM identity_v3_cluster_member
               WHERE generation=? AND entity_id='gh:a'""",
            (generation,),
        ).fetchone()[0]
        self.assertEqual(canonical, "registry:a")
        connection.close()

    def test_observation_import_never_assigns_canonical_identity(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        record = {
            "envelope_version": "pg-observation-0.1",
            "source": {
                "source_id": "pilot",
                "snapshot_id": "2026-08-06",
                "record_native_id": "person-7",
                "observed_at": "2026-08-06T00:00:00Z",
                "retrieved_at": "2026-08-06T00:01:00Z",
                "terms_revision": "fixture",
                "rights_state": "public_metadata",
                "payload_sha256": "0" * 64,
            },
            "subject": {
                "kind": "person",
                "source_native_id": "person-7",
                "label": "Élodie Durand",
                "attributes": {"company": "Shared Corp", "location": "Paris"},
            },
            "identifiers": [
                {
                    "scheme": "orcid",
                    "value": "0000-0001-2345-6789",
                    "scope": "global",
                    "stability": "stable",
                    "uniqueness": "unique",
                    "evidence": "literal field",
                },
                {
                    "scheme": "github_login",
                    "value": "elodie",
                    "scope": "source",
                    "stability": "mutable",
                    "uniqueness": "unique",
                    "evidence": "literal field",
                },
                {
                    "scheme": "company",
                    "value": "Shared Corp",
                    "scope": "global",
                    "stability": "stable",
                    "uniqueness": "unique",
                    "evidence": "source incorrectly declared this unique",
                },
            ],
            "contributions": [{"role": "author", "work": "work-1"}],
            "relationships": [],
            "evidence": [{"locator": "fixture:1"}],
            "raw_pointer": "tests/fixture.json",
        }

        first = import_observation(connection, record)
        second_record = json.loads(json.dumps(record))
        second_record["subject"]["label"] = "Élodie D."
        second = import_observation(connection, second_record)
        self.assertEqual(first["entity_id"], second["entity_id"])

        identifier_schemes = {
            row[0] for row in connection.execute(
                "SELECT scheme FROM identity_v3_identifier WHERE entity_id=?",
                (first["entity_id"],),
            )
        }
        alias_schemes = {
            row[0] for row in connection.execute(
                "SELECT scheme FROM identity_v3_alias WHERE entity_id=?",
                (first["entity_id"],),
            )
        }
        attributes = {
            row[0] for row in connection.execute(
                "SELECT attribute FROM identity_v3_attribute WHERE entity_id=?",
                (first["entity_id"],),
            )
        }
        self.assertEqual(identifier_schemes, {"orcid"})
        self.assertEqual(alias_schemes, {"github_login"})
        self.assertIn("observed_identifier:company", attributes)
        self.assertIn("company", attributes)
        self.assertIn("envelope:contributions", attributes)
        self.assertEqual(
            connection.execute("SELECT COUNT(*) FROM identity_v3_decision").fetchone()[0],
            0,
        )

        bad = json.loads(json.dumps(record))
        bad["canonical_person_id"] = "person:forbidden"
        with self.assertRaises(IdentityError):
            import_observation(connection, bad)
        connection.close()


if __name__ == "__main__":
    unittest.main()
