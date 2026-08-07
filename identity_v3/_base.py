"""Storage primitives and shared helpers for identity_v3."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Iterable, Mapping

from .registry import normalize_identifier, rule_for

METHOD_VERSION = "identity-v3.1.0"

class IdentityError(RuntimeError):
    """Raised when a requested identity operation violates an invariant."""

def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def stable_id(prefix: str, *parts: object, length: int = 24) -> str:
    payload = "\x1f".join(stable_json(part) for part in parts)
    return f"{prefix}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:length]}"

class UnionFind:
    def __init__(self, items: Iterable[str] = ()) -> None:
        self.parent: dict[str, str] = {item: item for item in items}
    def add(self, item: str) -> None:
        self.parent.setdefault(item, item)
    def find(self, item: str) -> str:
        self.add(item)
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]
    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return
        if root_a < root_b:
            self.parent[root_b] = root_a
        else:
            self.parent[root_a] = root_b
    def components(self) -> list[list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in sorted(self.parent):
            grouped[self.find(item)].append(item)
        return [grouped[root] for root in sorted(grouped)]

class BaseMixin:

    def __init__(self, database: str | Path | sqlite3.Connection):
        self._owns_connection = not isinstance(database, sqlite3.Connection)
        if isinstance(database, sqlite3.Connection):
            self.connection = database
        else:
            self.connection = sqlite3.connect(str(database))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys = ON')
        self.ensure_schema()

    def close(self) -> None:
        if self._owns_connection:
            self.connection.close()

    def __enter__(self) -> 'IdentityEngine':
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.close()

    def ensure_schema(self) -> None:
        schema_path = Path(__file__).with_name('fixtures') / 'schema.sql'
        self.connection.executescript(schema_path.read_text(encoding='utf-8'))
        self.connection.commit()

    def table_exists(self, table: str) -> bool:
        row = self.connection.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (table,)).fetchone()
        return row is not None

    def upsert_entity(self, entity_id: str, *, label: str | None=None, kind: str='unknown', origin: str | None=None, source_native_id: str | None=None, birth_year: int | None=None, death_year: int | None=None, source_state: str | None=None, created_at: str | None=None) -> None:
        if not entity_id:
            raise IdentityError('entity_id must be non-empty')
        now = created_at or utc_now()
        self.connection.execute("\n            INSERT INTO identity_v3_entity\n              (entity_id,label,kind,origin,source_native_id,birth_year,death_year,source_state,created_at)\n            VALUES (?,?,?,?,?,?,?,?,?)\n            ON CONFLICT(entity_id) DO UPDATE SET\n              label=COALESCE(excluded.label, identity_v3_entity.label),\n              kind=CASE WHEN excluded.kind!='unknown' THEN excluded.kind ELSE identity_v3_entity.kind END,\n              origin=COALESCE(excluded.origin, identity_v3_entity.origin),\n              source_native_id=COALESCE(excluded.source_native_id, identity_v3_entity.source_native_id),\n              birth_year=COALESCE(excluded.birth_year, identity_v3_entity.birth_year),\n              death_year=COALESCE(excluded.death_year, identity_v3_entity.death_year),\n              source_state=COALESCE(excluded.source_state, identity_v3_entity.source_state)\n            ", (entity_id, label, kind or 'unknown', origin, source_native_id, birth_year, death_year, source_state, now))

    def record_identifier(self, entity_id: str, scheme: str, value: object, *, source: str, observed_at: str | None=None, valid_from: str='', valid_to: str | None=None, evidence: Mapping[str, object] | None=None) -> bool:
        rule = rule_for(scheme)
        if rule.category != 'identifier':
            raise IdentityError(f'{scheme!r} is {rule.category}, not an identifier')
        normalized = normalize_identifier(scheme, value)
        if not normalized:
            return False
        self.upsert_entity(entity_id)
        self.connection.execute('\n            INSERT INTO identity_v3_identifier\n              (entity_id,scheme,value,normalized_value,scope,uniqueness_class,mutability,\n               authority,auto_resolution_eligible,source,evidence_json,valid_from,valid_to,observed_at)\n            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)\n            ON CONFLICT(entity_id,scheme,normalized_value,valid_from) DO UPDATE SET\n              value=excluded.value,\n              source=excluded.source,\n              evidence_json=excluded.evidence_json,\n              valid_to=excluded.valid_to,\n              observed_at=excluded.observed_at\n            ', (entity_id, rule.scheme, str(value), normalized, rule.scope, rule.uniqueness, rule.mutability, rule.authority, int(rule.auto_resolution_eligible), source, stable_json(evidence or {}), valid_from, valid_to, observed_at or utc_now()))
        return True

    def record_alias(self, entity_id: str, scheme: str, alias: object, *, source: str, observed_at: str | None=None, valid_from: str='', valid_to: str | None=None, stable_identifier_scheme: str | None=None, stable_identifier_value: str | None=None, evidence: Mapping[str, object] | None=None) -> bool:
        text = str(alias or '').strip()
        if not text:
            return False
        normalized = normalize_identifier(scheme, text)
        self.upsert_entity(entity_id)
        self.connection.execute('\n            INSERT INTO identity_v3_alias\n              (entity_id,scheme,alias,normalized_alias,valid_from,valid_to,source,\n               stable_identifier_scheme,stable_identifier_value,observed_at,evidence_json)\n            VALUES (?,?,?,?,?,?,?,?,?,?,?)\n            ON CONFLICT(entity_id,scheme,normalized_alias,valid_from) DO UPDATE SET\n              alias=excluded.alias,\n              valid_to=excluded.valid_to,\n              source=excluded.source,\n              stable_identifier_scheme=COALESCE(excluded.stable_identifier_scheme,\n                                                identity_v3_alias.stable_identifier_scheme),\n              stable_identifier_value=COALESCE(excluded.stable_identifier_value,\n                                               identity_v3_alias.stable_identifier_value),\n              observed_at=excluded.observed_at,\n              evidence_json=excluded.evidence_json\n            ', (entity_id, scheme, text, normalized, valid_from, valid_to, source, stable_identifier_scheme, stable_identifier_value, observed_at or utc_now(), stable_json(evidence or {})))
        return True

    def record_account_alias(self, entity_id: str, scheme: str, alias: object, *, stable_identifier_scheme: str, stable_identifier_value: object, source: str, observed_at: str | None=None, evidence: Mapping[str, object] | None=None) -> bool:
        """Record a mutable alias and close prior aliases when a rename is seen."""
        when = observed_at or utc_now()
        normalized = normalize_identifier(scheme, alias)
        stable_normalized = normalize_identifier(stable_identifier_scheme, stable_identifier_value)
        if not normalized:
            return False
        current = self.connection.execute('SELECT alias_id, normalized_alias FROM identity_v3_alias\n               WHERE entity_id=? AND scheme=? AND valid_to IS NULL\n                 AND stable_identifier_scheme=? AND stable_identifier_value=?', (entity_id, scheme, stable_identifier_scheme, stable_normalized)).fetchall()
        for row in current:
            if row['normalized_alias'] != normalized:
                self.connection.execute('UPDATE identity_v3_alias SET valid_to=? WHERE alias_id=?', (when, row['alias_id']))
        return self.record_alias(entity_id, scheme, alias, source=source, observed_at=when, valid_from=when, stable_identifier_scheme=stable_identifier_scheme, stable_identifier_value=stable_normalized, evidence=evidence)

    def record_attribute(self, entity_id: str, attribute: str, value: object, *, source: str, observed_at: str | None=None, payload_sha256: str='', evidence: Mapping[str, object] | None=None) -> None:
        self.upsert_entity(entity_id)
        self.connection.execute('\n            INSERT OR REPLACE INTO identity_v3_attribute\n              (entity_id,source,attribute,value_json,observed_at,payload_sha256,evidence_json)\n            VALUES (?,?,?,?,?,?,?)\n            ', (entity_id, source, attribute, stable_json(value), observed_at or utc_now(), payload_sha256, stable_json(evidence or {})))

    def record_enrichment_receipt(self, entity_id: str, field: str, *, source: str, observed_at: str, payload_sha256: str, present: bool) -> None:
        self.upsert_entity(entity_id)
        self.connection.execute('INSERT OR REPLACE INTO identity_v3_enrichment_receipt\n               (entity_id,source,field,observed_at,payload_sha256,status)\n               VALUES (?,?,?,?,?,?)', (entity_id, source, field, observed_at, payload_sha256, 'present' if present else 'absent'))

    def field_observed(self, entity_id: str, source: str, field: str) -> bool:
        row = self.connection.execute('SELECT 1 FROM identity_v3_enrichment_receipt\n               WHERE entity_id=? AND source=? AND field=? LIMIT 1', (entity_id, source, field)).fetchone()
        return row is not None
