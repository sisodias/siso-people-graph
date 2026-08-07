from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
from typing import Iterator

from identity_v3.engine import IdentityEngine
from identity_v3.registry import rule_for

FIXTURES = Path(__file__).with_name("fixtures")


V2_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE person (
  person_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  sort_name TEXT,
  kind TEXT NOT NULL DEFAULT 'unknown',
  state TEXT NOT NULL DEFAULT 'linked',
  merged_into TEXT,
  birth_year INTEGER,
  death_year INTEGER,
  primary_tier TEXT,
  rank_score REAL,
  origin TEXT NOT NULL,
  topics_json TEXT NOT NULL DEFAULT '[]',
  built_at TEXT NOT NULL
);
CREATE TABLE external_ids (
  person_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  value TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  source TEXT,
  PRIMARY KEY (person_id,platform,value)
);
CREATE TABLE identity_claim (
  claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
  person_a TEXT NOT NULL,
  person_b TEXT NOT NULL,
  method TEXT NOT NULL,
  confidence REAL NOT NULL,
  evidence TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'proposed',
  decided_by TEXT,
  created_at TEXT NOT NULL,
  CHECK (person_a < person_b)
);
"""


def make_v2_connection(path: str | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(path or ":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(V2_SCHEMA)
    return connection


def load_adversarial(engine: IdentityEngine) -> dict:
    fixture = json.loads((FIXTURES / "adversarial_identities.json").read_text(encoding="utf-8"))
    for entity in fixture["entities"]:
        engine.upsert_entity(
            entity["entity_id"],
            label=entity["label"],
            kind=entity.get("kind", "unknown"),
            origin=entity.get("origin"),
            birth_year=entity.get("birth_year"),
            death_year=entity.get("death_year"),
        )
        for identifier in entity.get("identifiers", []):
            engine.record_identifier(
                entity["entity_id"], identifier["scheme"], identifier["value"],
                source="adversarial_fixture", observed_at="2026-08-06T00:00:00Z",
            )
        for alias in entity.get("aliases", []):
            engine.record_alias(
                entity["entity_id"], alias["scheme"], alias["value"],
                source="adversarial_fixture", observed_at="2026-08-06T00:00:00Z",
            )
        for attribute, value in entity.get("attributes", {}).items():
            engine.record_attribute(
                entity["entity_id"], attribute, value,
                source="adversarial_fixture", observed_at="2026-08-06T00:00:00Z",
            )
    engine.connection.commit()
    return fixture


def pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))
