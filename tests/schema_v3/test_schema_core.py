import json
import sqlite3
import unittest
from pathlib import Path

from support import (ROOT, SCHEMA_MANIFEST, SAMPLE_MANIFEST, add_person, connect, digest, manifest_paths)

class PeopleGraphV3CoreTests(unittest.TestCase):
    def test_schema_and_sample_apply_with_foreign_keys_clean(self) -> None:
        con = connect(sample=True)
        self.assertEqual(
            con.execute(
                "SELECT value FROM schema_metadata WHERE key='schema_version'"
            ).fetchone()[0],
            "3.0.0-draft.1",
        )
        self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(con.execute("SELECT COUNT(*) FROM entity").fetchone()[0], 7)
        expected_ddl = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "schema" / "v3" / "ddl").glob("*.sql"))]
        expected_sample = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "schema" / "v3" / "sample").glob("*.sql"))]
        self.assertEqual(manifest_paths(SCHEMA_MANIFEST), expected_ddl)
        self.assertEqual(manifest_paths(SAMPLE_MANIFEST), expected_sample)
        con.close()


    def test_foreign_keys_reject_orphan_observations(self) -> None:
        con = connect()
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO source_observation
                   (observation_id,snapshot_id,record_native_id,observed_at,
                    retrieved_at,subject_kind,subject_native_id,label,
                    attributes_json,raw_pointer,payload_sha256,rights_state,
                    privacy_state,publication_state)
                   VALUES ('obs:orphan','missing','x','2026-08-06','2026-08-06',
                           'person','x','X','{}','fixture://x',?,
                           'open_data','public','public')""",
                (digest("orphan"),),
            )
        con.close()


    def test_envelope_import_cannot_assign_a_canonical_id(self) -> None:
        con = connect(sample=True)
        columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info(observation_envelope_receipt)"
            ).fetchall()
        }
        self.assertNotIn("entity_id", columns)
        self.assertNotIn("canonical_id", columns)

        bad_payload = {
            "envelope_version": "pg-observation-0.1",
            "source": {
                "source_id": "fixture-a",
                "record_native_id": "bad-record",
            },
            "subject": {
                "kind": "person",
                "source_native_id": "bad-record",
                "label": "Bad fixture",
                "canonical_id": "pg:must-not-import",
            },
        }
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO observation_envelope_receipt
                   (envelope_receipt_id,envelope_version,source_id,snapshot_id,
                    record_native_id,payload_json,payload_sha256,received_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    "env:bad",
                    "pg-observation-0.1",
                    "fixture-a",
                    "fixture-a-2026-08-06",
                    "bad-record",
                    json.dumps(bad_payload),
                    digest("bad-envelope"),
                    "2026-08-06T02:00:00Z",
                ),
            )
        con.close()


    def test_source_observations_and_identity_decisions_are_append_only(self) -> None:
        con = connect(sample=True)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                "UPDATE source_observation SET label='changed' "
                "WHERE observation_id='obs:fixture-a:author-1'"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                "UPDATE identity_decision SET rationale='changed' "
                "WHERE decision_id='identity-decision:zoe-accept'"
            )
        con.close()


    def test_rights_privacy_and_publication_coverage(self) -> None:
        con = connect(sample=True)
        for table in (
            "source_snapshot",
            "source_observation",
            "work",
            "evidence",
            "assertion",
            "projection_run",
        ):
            columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
            for policy_column in ("rights_state", "publication_state"):
                self.assertIn(policy_column, columns, f"{table}.{policy_column}")
            self.assertEqual(
                con.execute(
                    f"SELECT COUNT(*) FROM {table} "
                    "WHERE rights_state IS NULL OR publication_state IS NULL"
                ).fetchone()[0],
                0,
            )

        con.execute(
            """INSERT INTO entity
               (entity_id,entity_kind,canonical_label,label_observation_id,status,
                created_at,created_by)
               VALUES ('pg:BAD-WORK','work','Bad Work','obs:fixture-a:work-2',
                       'active','2026-08-06','schema-test')"""
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO work
                   (work_id,work_type,title,original_language,
                    source_observation_id,rights_state,privacy_state,
                    publication_state,created_at)
                   VALUES ('pg:BAD-WORK','article','Bad Work','en',
                           'obs:fixture-a:work-2','unreviewed','public','public',
                           '2026-08-06')"""
            )
        con.close()


    def test_unicode_and_alias_search_preserve_non_latin_text(self) -> None:
        con = connect(sample=True)
        accent_hits = {
            row[0]
            for row in con.execute(
                "SELECT entity_id FROM entity_search WHERE entity_search MATCH ?",
                ("Zoe",),
            )
        }
        self.assertIn("pg:01H-PERSON-A", accent_hits)

        japanese_hits = {
            row[0]
            for row in con.execute(
                "SELECT entity_id FROM entity_search WHERE entity_search MATCH ?",
                ("田中",),
            )
        }
        self.assertIn("pg:01H-PERSON-A", japanese_hits)

        add_person(con, "pg:01H-PERSON-TOKYO", "obs:test:tokyo", "person-tokyo", "東京 太郎")
        tokyo_hits = con.execute(
            "SELECT entity_id FROM entity_search WHERE entity_search MATCH ?",
            ("東京",),
        ).fetchall()
        self.assertIn(("pg:01H-PERSON-TOKYO",), tokyo_hits)
        con.close()
