import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from loaders.enrich_owners import enrich, fixture_fetcher

from common import FIXTURES, make_v2_connection


class EnrichmentTests(unittest.TestCase):
    def test_fields_are_independent_replayable_and_do_not_overwrite_canonical_values(self):
        handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        handle.close()
        try:
            connection = make_v2_connection(handle.name)
            connection.executemany(
                """INSERT INTO person
                   (person_id,name,kind,state,origin,rank_score,built_at)
                   VALUES (?,?,?,?,?,?,?)""",
                [
                    (
                        "gh:oldalice", "Canonical Alice", "unknown", "linked", "github",
                        9999.0, "2026-08-01T00:00:00Z",
                    ),
                    (
                        "gh:nullprofile", "Canonical Null", "unknown", "linked", "github",
                        17.0, "2026-08-02T00:00:00Z",
                    ),
                ],
            )
            connection.executemany(
                """INSERT INTO external_ids(person_id,platform,value,confidence,source)
                   VALUES (?,?,?,?,?)""",
                [
                    ("gh:oldalice", "github_login", "oldalice", 1.0, "fixture"),
                    # This one pre-existing field must not block acquisition of
                    # every other independently missing profile field.
                    ("gh:oldalice", "real_name", "Already Observed", 1.0, "fixture"),
                    ("gh:nullprofile", "github_login", "nullprofile", 1.0, "fixture"),
                ],
            )
            connection.commit()
            connection.close()

            replay = fixture_fetcher(FIXTURES / "github_profiles.json")
            first = enrich(
                handle.name, limit=0, token=None, sleep=0,
                fetcher=replay, observed_at="2026-08-06T12:00:00Z",
            )
            self.assertEqual(first["considered"], 2)
            self.assertEqual(first["fetched"], 2)
            self.assertEqual(first["errors"], 0)
            self.assertEqual(first["renames"], 1)

            check = sqlite3.connect(handle.name)
            check.row_factory = sqlite3.Row
            canonical = check.execute(
                "SELECT name,kind,rank_score,built_at FROM person WHERE person_id='gh:oldalice'"
            ).fetchone()
            self.assertEqual(canonical["name"], "Canonical Alice")
            self.assertEqual(canonical["kind"], "human")
            self.assertEqual(canonical["rank_score"], 9999.0)
            self.assertEqual(canonical["built_at"], "2026-08-01T00:00:00Z")

            aliases = check.execute(
                """SELECT alias,valid_from,valid_to,stable_identifier_scheme,
                          stable_identifier_value
                   FROM identity_v3_alias
                   WHERE entity_id='gh:oldalice' AND scheme='github_login'
                   ORDER BY alias"""
            ).fetchall()
            self.assertEqual([row["alias"] for row in aliases], ["alice", "oldalice"])
            by_alias = {row["alias"]: row for row in aliases}
            self.assertIsNone(by_alias["alice"]["valid_to"])
            self.assertEqual(by_alias["oldalice"]["valid_to"], "2026-08-06T12:00:00Z")
            for row in aliases:
                self.assertEqual(row["stable_identifier_scheme"], "github_id")
                self.assertEqual(row["stable_identifier_value"], "101")

            location = check.execute(
                """SELECT value_json FROM identity_v3_attribute
                   WHERE entity_id='gh:oldalice' AND attribute='location'
                     AND source='github_api'"""
            ).fetchone()[0]
            self.assertEqual(json.loads(location), "Hà Nội")
            self.assertEqual(
                check.execute(
                    """SELECT COUNT(*) FROM identity_v3_enrichment_receipt
                       WHERE entity_id='gh:nullprofile' AND status='absent'"""
                ).fetchone()[0],
                6,
            )
            before = {
                "attributes": check.execute("SELECT COUNT(*) FROM identity_v3_attribute").fetchone()[0],
                "aliases": check.execute("SELECT COUNT(*) FROM identity_v3_alias").fetchone()[0],
                "receipts": check.execute("SELECT COUNT(*) FROM identity_v3_enrichment_receipt").fetchone()[0],
            }
            check.close()

            second = enrich(
                handle.name, limit=0, token=None, sleep=0,
                fetcher=replay, observed_at="2026-08-07T12:00:00Z",
            )
            self.assertEqual(second["considered"], 0)
            self.assertEqual(second["fetched"], 0)

            check = sqlite3.connect(handle.name)
            after = {
                "attributes": check.execute("SELECT COUNT(*) FROM identity_v3_attribute").fetchone()[0],
                "aliases": check.execute("SELECT COUNT(*) FROM identity_v3_alias").fetchone()[0],
                "receipts": check.execute("SELECT COUNT(*) FROM identity_v3_enrichment_receipt").fetchone()[0],
            }
            check.close()
            self.assertEqual(after, before)
        finally:
            os.unlink(handle.name)


if __name__ == "__main__":
    unittest.main()
