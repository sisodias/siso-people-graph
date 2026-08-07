from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DDL_DIR = ROOT / "schema" / "v3" / "ddl"
SAMPLE_DIR = ROOT / "schema" / "v3" / "sample"
SCHEMA_MANIFEST = ROOT / "schema" / "v3" / "people_graph_v3.sql"
SAMPLE_MANIFEST = ROOT / "schema" / "v3" / "sample_data.sql"


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _bundle(directory: Path) -> str:
    files = sorted(directory.glob("*.sql"))
    if not files:
        raise RuntimeError(f"no SQL modules in {directory}")
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


def connect(*, sample: bool = False) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(_bundle(DDL_DIR))
    if sample:
        con.executescript(_bundle(SAMPLE_DIR))
    return con


def add_observation(
    con: sqlite3.Connection,
    observation_id: str,
    record_native_id: str,
    label: str,
    *,
    kind: str = "person",
) -> None:
    con.execute(
        """INSERT INTO source_observation
           (observation_id,snapshot_id,envelope_receipt_id,record_native_id,
            observed_at,retrieved_at,subject_kind,subject_native_id,label,
            attributes_json,raw_pointer,payload_sha256,rights_state,
            privacy_state,publication_state)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            observation_id,
            "fixture-a-2026-08-06",
            None,
            record_native_id,
            "2026-08-05T12:00:00Z",
            "2026-08-06T00:00:00Z",
            kind,
            record_native_id,
            label,
            "{}",
            f"fixtures/{record_native_id}.json",
            digest(record_native_id),
            "open_data",
            "public",
            "public",
        ),
    )


def add_person(
    con: sqlite3.Connection,
    entity_id: str,
    observation_id: str,
    record_native_id: str,
    label: str,
) -> None:
    add_observation(con, observation_id, record_native_id, label)
    con.execute(
        """INSERT INTO entity
           (entity_id,entity_kind,canonical_label,label_observation_id,status,
            created_at,created_by)
           VALUES (?, 'person', ?, ?, 'active', '2026-08-06T02:00:00Z',
                   'schema-test')""",
        (entity_id, label, observation_id),
    )


def manifest_paths(manifest: Path) -> list[str]:
    return [
        line.removeprefix(".read ").strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.startswith(".read ")
    ]
