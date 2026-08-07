from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from integration.adapters import (
    BookLibraryObservationAdapter,
    NDJSONObservationAdapter,
    SourcePolicy,
    V2SQLiteAdapter,
    V3SQLiteAdapter,
    open_sqlite_adapter,
)
from integration.contract import iter_ndjson, validate_record


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/integration_parallel/fixtures"


def create_v2_fixture(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE person (
          person_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          sort_name TEXT,
          kind TEXT NOT NULL,
          state TEXT NOT NULL,
          merged_into TEXT,
          birth_year INTEGER,
          death_year INTEGER,
          primary_tier TEXT,
          rank_score REAL,
          origin TEXT NOT NULL,
          topics_json TEXT NOT NULL,
          built_at TEXT NOT NULL
        );
        CREATE TABLE external_ids (
          person_id TEXT NOT NULL,
          platform TEXT NOT NULL,
          value TEXT NOT NULL,
          confidence REAL NOT NULL,
          source TEXT,
          PRIMARY KEY (person_id, platform, value)
        );
        CREATE TABLE person_content (
          person_id TEXT NOT NULL,
          domain TEXT NOT NULL,
          content_ref TEXT NOT NULL,
          role TEXT NOT NULL,
          score REAL,
          title TEXT,
          source TEXT NOT NULL,
          observed_at TEXT,
          meta_json TEXT NOT NULL,
          PRIMARY KEY (person_id, domain, content_ref, role)
        );
        CREATE TABLE identity_claim (
          claim_id INTEGER PRIMARY KEY,
          person_a TEXT NOT NULL,
          person_b TEXT NOT NULL,
          method TEXT NOT NULL,
          confidence REAL NOT NULL,
          evidence TEXT NOT NULL,
          status TEXT NOT NULL,
          decided_by TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE person_topic (
          person_id TEXT NOT NULL,
          topic TEXT NOT NULL,
          scheme TEXT NOT NULL,
          weight REAL NOT NULL,
          source TEXT,
          PRIMARY KEY (person_id, topic, scheme)
        );
        """
    )
    con.executemany(
        "INSERT INTO person VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "gh:renee-example",
                "Renée Example",
                "Example, Renée",
                "human",
                "linked",
                None,
                1985,
                None,
                "A",
                101.0,
                "github",
                "[]",
                "2026-08-01T00:00:00Z",
            ),
            (
                "bk:renee-example",
                "Example, Renée",
                "Example, Renée",
                "human",
                "linked",
                None,
                1985,
                None,
                None,
                2.0,
                "books",
                "[]",
                "2026-08-01T00:00:00Z",
            ),
        ],
    )
    con.executemany(
        "INSERT INTO external_ids VALUES (?,?,?,?,?)",
        [
            ("gh:renee-example", "github_login", "renee-example", 1.0, "github"),
            ("gh:renee-example", "orcid", "0000-0002-1825-0097", 1.0, "openalex"),
            ("gh:renee-example", "company", "Example Research Lab", 0.8, "github"),
            ("gh:renee-example", "location", "Paris", 0.8, "github"),
            ("gh:renee-example", "real_name", "Renée Example", 0.8, "github"),
        ],
    )
    con.execute(
        "INSERT INTO person_content VALUES (?,?,?,?,?,?,?,?,?)",
        (
            "bk:renee-example",
            "book",
            "42",
            "translator",
            4.5,
            "A translated work",
            "gutenberg",
            "2026-08-01T00:00:00Z",
            '{"language":"fr"}',
        ),
    )
    con.execute(
        "INSERT INTO identity_claim VALUES (?,?,?,?,?,?,?,?,?)",
        (
            1,
            "bk:renee-example",
            "gh:renee-example",
            "shared_orcid",
            0.99,
            "literal ORCID 0000-0002-1825-0097",
            "accepted",
            "fixture-reviewer",
            "2026-08-02T00:00:00Z",
        ),
    )
    con.execute(
        "INSERT INTO person_topic VALUES (?,?,?,?,?)",
        ("bk:renee-example", "Graph theory", "lcsh", 2.0, "gutenberg"),
    )
    con.commit()
    con.close()


class AdapterTests(unittest.TestCase):
    def test_v2_adapter_preserves_facts_and_separates_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "people.sqlite"
            create_v2_fixture(database)
            policy = SourcePolicy(
                snapshot_id="fixture-snapshot",
                terms_revision="fixture-terms-v1",
                rights_state="open_data",
                retrieved_at="2026-08-06T00:00:00Z",
            )
            adapter = V2SQLiteAdapter(database, default_policy=policy)
            observations = list(adapter.iter_observations())
            decisions = list(adapter.iter_identity_decisions())

        self.assertEqual(len(observations), 4)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].status, "accepted")
        self.assertEqual(decisions[0].method, "shared_orcid")
        for record in observations:
            self.assertTrue(validate_record(record).valid)
            self.assertEqual(record["source"]["rights_state"], "open_data")
            encoded = json.dumps(record)
            self.assertNotIn("canonical_person_id", encoded)
            self.assertNotIn("canonical_id", encoded)

        person = next(
            record
            for record in observations
            if record["subject"]["source_native_id"].endswith("gh%3Arenee-example")
        )
        schemes = {identifier["scheme"] for identifier in person["identifiers"]}
        self.assertEqual(schemes, {"github_login", "orcid"})
        attributes = person["subject"]["attributes"]["legacy_external_attributes"]
        self.assertEqual(
            {item["field"] for item in attributes},
            {"company", "location", "real_name"},
        )

        work = next(record for record in observations if record["subject"]["kind"] == "work")
        self.assertEqual(work["contributions"][0]["role"], "translator")
        self.assertEqual(work["source"]["source_id"], "gutenberg")
        self.assertEqual(work["subject"]["attributes"]["legacy_meta"]["language"], "fr")

    def test_v2_export_roundtrips_without_identity_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "people.sqlite"
            output = Path(directory) / "observations.ndjson"
            create_v2_fixture(database)
            adapter = open_sqlite_adapter(database)
            count = adapter.export(output)
            exported = [record for _, record in iter_ndjson(output)]
            decisions = list(adapter.iter_identity_decisions())
        self.assertEqual(count, 4)
        self.assertEqual(len(exported), 4)
        self.assertEqual(len(decisions), 1)
        self.assertTrue(all(validate_record(record).valid for record in exported))

    def test_book_adapter_preserves_roles_rights_and_provenance(self) -> None:
        adapter = BookLibraryObservationAdapter(FIXTURES / "valid_observations.ndjson")
        summary = adapter.summary()
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["roles"], {"author": 1})
        self.assertEqual(summary["rights_states"], ["public_metadata"])
        self.assertEqual(list(adapter.iter_identity_decisions()), [])

    def test_v3_json_seam_is_detected_without_guessing_decision_schema(self) -> None:
        record = list(iter_ndjson(FIXTURES / "valid_observations.ndjson"))[0][1]
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "v3.sqlite"
            con = sqlite3.connect(database)
            con.execute("CREATE TABLE source_observation (envelope_json TEXT NOT NULL)")
            con.execute("CREATE TABLE canonical_entity (id TEXT PRIMARY KEY)")
            con.execute("CREATE TABLE claim (id TEXT PRIMARY KEY)")
            con.execute("CREATE TABLE work (id TEXT PRIMARY KEY)")
            con.execute(
                "INSERT INTO source_observation VALUES (?)",
                (json.dumps(record, ensure_ascii=False),),
            )
            con.commit()
            con.close()
            adapter = open_sqlite_adapter(database)
            observations = list(adapter.iter_observations())
            capabilities = adapter.capabilities().to_dict()
        self.assertIsInstance(adapter, V3SQLiteAdapter)
        self.assertEqual(observations, [record])
        self.assertEqual(list(adapter.iter_identity_decisions()), [])
        self.assertEqual(capabilities["identities"], "detected/separate")
        self.assertEqual(capabilities["claims"], "detected/separate")

    def test_ndjson_adapter_returns_fresh_observations(self) -> None:
        adapter = NDJSONObservationAdapter(FIXTURES / "valid_observations.ndjson")
        first = list(adapter.iter_observations())
        first[0]["subject"]["label"] = "mutated"
        second = list(adapter.iter_observations())
        self.assertEqual(second[0]["subject"]["label"], "Renée Example")


if __name__ == "__main__":
    unittest.main()
