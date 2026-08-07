from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from support import ROOT


class PeopleGraphV3AuditPackageTests(unittest.TestCase):
    def test_source_prompt_is_pinned_and_contains_lane_contract(self) -> None:
        path = ROOT / "docs" / "architecture" / "people-graph-v3-source-prompt.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("pg/v3-ontology-schema-20260806", text)
        self.assertIn("schema/v3/**", text)
        self.assertIn("pg-observation-0.1", text)
        self.assertIn("No silent name merge", text)
        self.assertIn("dd5dfe689c4b7f4e8617fcbd08d0355059ec98a2bfd7e222be952bda1932c57d", text)

    def test_decision_record_has_unique_stable_ids(self) -> None:
        path = ROOT / "docs" / "architecture" / "people-graph-v3-decision-record.md"
        ids = re.findall(r"^## (PGV3-D\d{3}) —", path.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertGreaterEqual(len(ids), 18)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids))

    def test_machine_provenance_is_parseable_and_pinned(self) -> None:
        path = ROOT / "schema" / "v3" / "PROVENANCE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "3.0.0-draft.1")
        self.assertEqual(data["branch"], "pg/v3-ontology-schema-20260806")
        self.assertEqual(data["base_commit"], "de048bb3b34bf931b56fd741cb46c1334acdfb98")
        self.assertEqual(data["initial_implementation_commit"], "2f66fbe1f4523399463d9e1ff8971879a84f5b88")
        self.assertEqual(data["prompt"]["prompt3_sha256"], "dd5dfe689c4b7f4e8617fcbd08d0355059ec98a2bfd7e222be952bda1932c57d")
        self.assertGreaterEqual(len(data["sources"]), 11)
        self.assertTrue(all(source["ref"] for source in data["sources"]))

    def test_artifact_manifest_matches_every_lane_file(self) -> None:
        manifest = ROOT / "schema" / "v3" / "ARTIFACTS.sha256"
        expected: dict[str, str] = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            digest, rel = line.split("  ", 1)
            expected[rel] = digest

        owned = []
        for base in (ROOT / "schema" / "v3", ROOT / "docs" / "architecture", ROOT / "tests" / "schema_v3"):
            for path in base.rglob("*"):
                if not path.is_file() or "__pycache__" in path.parts or path.name == "ARTIFACTS.sha256":
                    continue
                owned.append(path.relative_to(ROOT).as_posix())
        handoff = ROOT / "docs" / "handoffs" / "schema-v3.md"
        owned.append(handoff.relative_to(ROOT).as_posix())
        self.assertEqual(set(expected), set(owned))

        for rel, digest in expected.items():
            actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(actual, digest, rel)

    def test_no_forbidden_payload_or_out_of_scope_path_is_manifested(self) -> None:
        manifest = ROOT / "schema" / "v3" / "ARTIFACTS.sha256"
        forbidden_suffixes = (".sqlite", ".sqlite3", ".db", ".gz", ".tar", ".zip", ".7z")
        allowed_prefixes = ("schema/v3/", "docs/architecture/", "tests/schema_v3/")
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            _, rel = line.split("  ", 1)
            self.assertFalse(rel.endswith(forbidden_suffixes), rel)
            self.assertTrue(rel.startswith(allowed_prefixes) or rel == "docs/handoffs/schema-v3.md", rel)

    def test_relative_markdown_links_resolve(self) -> None:
        docs: list[Path] = []
        for base in (ROOT / "docs" / "architecture", ROOT / "schema" / "v3"):
            docs.extend(base.rglob("*.md"))
        docs.append(ROOT / "docs" / "handoffs" / "schema-v3.md")

        for doc in docs:
            text = doc.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
                target = target.strip()
                if not target or target.startswith("#") or "://" in target:
                    continue
                clean = target.split("#", 1)[0]
                resolved = (doc.parent / clean).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"{doc.relative_to(ROOT)} -> {target}",
                )
