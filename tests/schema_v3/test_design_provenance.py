from __future__ import annotations

import json
import re
import sqlite3
import unittest
from pathlib import Path

from support import ROOT

MANIFEST_PATH = ROOT / "schema" / "v3" / "design_provenance.json"
JOURNAL_PATH = ROOT / "docs" / "architecture" / "people-graph-v3-design-journal.md"
LEDGER_PATH = ROOT / "docs" / "architecture" / "people-graph-v3-source-ledger.md"
TRACE_PATH = ROOT / "docs" / "architecture" / "people-graph-v3-traceability.md"
BRIEF_PATH = ROOT / "docs" / "architecture" / "people-graph-v3-agent-brief.md"
HERE = Path(__file__).resolve().parent
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class PeopleGraphV3DesignProvenanceTests(unittest.TestCase):
    def test_public_reasoning_package_and_source_hashes_are_complete(self) -> None:
        manifest = load_manifest()
        self.assertEqual(
            manifest["manifest_version"],
            "people-graph-v3-design-provenance-1",
        )
        self.assertEqual(manifest["schema_version"], "3.0.0-draft.1")
        self.assertEqual(
            manifest["repository"]["base_commit"],
            "de048bb3b34bf931b56fd741cb46c1334acdfb98",
        )
        self.assertTrue(HEX64.fullmatch(manifest["brief"]["source_sha256"]))

        public_docs = manifest["public_reasoning_documents"]
        self.assertEqual(len(public_docs), len(set(public_docs)))
        for path in public_docs:
            self.assertTrue((ROOT / path).is_file(), path)

        sources = manifest["sources"]
        source_ids = [source["id"] for source in sources]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertEqual(source_ids, [f"SRC-{n:03d}" for n in range(1, 11)])
        for source in sources:
            if "git_blob_sha" in source:
                self.assertTrue(HEX40.fullmatch(source["git_blob_sha"]), source["id"])
            if "sha256" in source:
                self.assertTrue(HEX64.fullmatch(source["sha256"]), source["id"])

    def test_every_decision_has_evidence_artifacts_tests_and_rationale(self) -> None:
        manifest = load_manifest()
        known_sources = {source["id"] for source in manifest["sources"]}
        journal = JOURNAL_PATH.read_text(encoding="utf-8")
        decision_ids = [decision["id"] for decision in manifest["decisions"]]
        self.assertEqual(decision_ids, [f"D-{n:03d}" for n in range(1, 17)])

        for decision in manifest["decisions"]:
            self.assertEqual(decision["status"], "accepted")
            self.assertTrue(decision["evidence"], decision["id"])
            self.assertTrue(set(decision["evidence"]).issubset(known_sources))
            self.assertIn(decision["id"], journal)
            for path in decision["artifacts"] + decision["tests"]:
                self.assertTrue((ROOT / path).is_file(), f"{decision['id']}: {path}")

    def test_every_requirement_is_traceable_and_expected_set_is_present(self) -> None:
        manifest = load_manifest()
        trace = TRACE_PATH.read_text(encoding="utf-8")
        requirements = manifest["requirements"]
        requirement_ids = [requirement["id"] for requirement in requirements]
        self.assertEqual(requirement_ids, [f"R-{n:03d}" for n in range(1, 26)])

        for requirement in requirements:
            self.assertIn(requirement["status"], {"implemented", "documented", "out of lane"})
            self.assertIn(requirement["id"], trace)
            self.assertTrue(requirement["artifacts"], requirement["id"])
            self.assertTrue(requirement["tests"], requirement["id"])
            for path in requirement["artifacts"] + requirement["tests"]:
                self.assertTrue((ROOT / path).is_file(), f"{requirement['id']}: {path}")

    def test_manifested_artifacts_stay_inside_lane_and_exclude_payload_assets(self) -> None:
        manifest = load_manifest()
        prefixes = tuple(manifest["repository"]["owned_path_prefixes"])
        exact = set(manifest["repository"]["owned_exact_paths"])
        paths: set[str] = set(manifest["public_reasoning_documents"])
        paths.add(manifest["brief"]["committed_excerpt"])
        for collection in (manifest["decisions"], manifest["requirements"]):
            for item in collection:
                paths.update(item["artifacts"])
                paths.update(item["tests"])

        forbidden_suffixes = (
            ".sqlite",
            ".sqlite3",
            ".db",
            ".gz",
            ".tgz",
            ".tar",
            ".zip",
            ".7z",
            ".parquet",
        )
        for path in paths:
            self.assertFalse(Path(path).is_absolute(), path)
            self.assertTrue(path.startswith(prefixes) or path in exact, path)
            self.assertFalse(path.lower().endswith(forbidden_suffixes), path)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_ledger_and_brief_disclose_sources_non_sources_and_limits(self) -> None:
        manifest = load_manifest()
        ledger = LEDGER_PATH.read_text(encoding="utf-8")
        brief = BRIEF_PATH.read_text(encoding="utf-8")

        for source in manifest["sources"]:
            self.assertIn(source["id"], ledger)
        self.assertIn("Explicit non-sources and unproven claims", ledger)
        self.assertIn("No live production SQLite asset", ledger)
        self.assertIn("Prompt 3 — Additive People Graph v3 ontology and schema", brief)
        self.assertIn(manifest["brief"]["source_sha256"], brief)
        self.assertIn("pg-observation-0.1", brief)
        self.assertNotIn("Prompt 4 —", brief)

    def test_validation_record_matches_the_executable_suite_and_runtime_features(self) -> None:
        manifest = load_manifest()
        validation = manifest["validation"]
        last = validation["last_result"]
        discovered = unittest.defaultTestLoader.discover(
            str(HERE), pattern="test_*.py"
        ).countTestCases()

        self.assertEqual(last["status"], "passed")
        self.assertEqual(last["test_count"], discovered)
        self.assertEqual(last["foreign_key_check"], "clean")
        self.assertEqual(last["integrity_check"], "ok")
        self.assertGreaterEqual(sqlite3.sqlite_version_info, (3, 38, 0))

        con = sqlite3.connect(":memory:")
        self.assertEqual(
            con.execute("SELECT sqlite_compileoption_used('ENABLE_FTS5')").fetchone()[0],
            1,
        )
        self.assertEqual(con.execute("SELECT json_valid('{}')").fetchone()[0], 1)
        con.close()

    def test_expanded_audit_packet_and_machine_manifests_are_consistent(self) -> None:
        manifest = load_manifest()
        audit_index = ROOT / "docs" / "architecture" / "people-graph-v3-audit-index.md"
        compact_manifest = ROOT / "schema" / "v3" / "traceability.json"
        inventory = ROOT / "schema" / "v3" / "SCHEMA_INVENTORY.md"

        self.assertTrue(audit_index.is_file())
        self.assertTrue(compact_manifest.is_file())
        self.assertTrue(inventory.is_file())

        audit_text = audit_index.read_text(encoding="utf-8")
        for path in manifest["public_reasoning_documents"]:
            self.assertTrue((ROOT / path).is_file(), path)
            # The index need not contain a recursive link to itself; every
            # other public reasoning document must be discoverable from it.
            if path != "docs/architecture/people-graph-v3-audit-index.md":
                self.assertIn(Path(path).name, audit_text, path)

        compact = json.loads(compact_manifest.read_text(encoding="utf-8"))
        self.assertEqual(compact["manifest_version"], "people-graph-v3-traceability-1")
        self.assertEqual(compact["base_commit"], manifest["repository"]["base_commit"])
        self.assertEqual(compact["schema_version"], manifest["schema_version"])
        discovered = unittest.defaultTestLoader.discover(
            str(HERE), pattern="test_*.py"
        ).countTestCases()
        self.assertEqual(compact["validation"]["tests_run"], discovered)
        self.assertEqual(compact["validation"]["tests_passed"], discovered)
        self.assertEqual(compact["validation"]["schema_invariant_tests"], 13)
        self.assertEqual(
            compact["validation"]["provenance_audit_tests"], discovered - 13
        )
        self.assertEqual(len(compact["requirements"]), 12)
        self.assertEqual(len({r["id"] for r in compact["requirements"]}), 12)
        self.assertTrue(all(url.startswith("https://www.sqlite.org/") for url in compact["official_sqlite_sources"]))
        self.assertIn("no private token-by-token chain-of-thought", compact["transparency_boundary"].lower())

        # Resolve local Markdown links from the audit index. External links are
        # source citations and are intentionally not fetched by offline tests.
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", audit_text):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (audit_index.parent / target.split("#", 1)[0]).resolve()
            self.assertTrue(resolved.exists(), target)


if __name__ == "__main__":
    unittest.main()
