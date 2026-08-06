-- SISO People Graph v3 — additive evidence ontology
--
-- This schema is intentionally additive. It does not alter or depend on the v2
-- tables. It separates source observations, canonical entities, identity
-- decisions, evidence-backed assertions, temporal relationships, Works, and
-- named derived projections.
--
-- Target: SQLite 3.38+ with JSON1 and FTS5 enabled.

PRAGMA foreign_keys = ON;
PRAGMA recursive_triggers = ON;

BEGIN;

CREATE TABLE schema_metadata (
  key         TEXT PRIMARY KEY,
  value       TEXT NOT NULL,
  recorded_at TEXT NOT NULL
) WITHOUT ROWID;

INSERT INTO schema_metadata(key, value, recorded_at) VALUES
  ('schema_name', 'siso-people-graph', '2026-08-06T00:00:00Z'),
  ('schema_version', '3.0.0-draft.1', '2026-08-06T00:00:00Z'),
  ('observation_envelope', 'pg-observation-0.1', '2026-08-06T00:00:00Z');

-- ---------------------------------------------------------------------------
-- Shared policy vocabularies. Rows are referenced instead of repeating brittle
-- CHECK lists on every evidence-bearing table.
-- ---------------------------------------------------------------------------
CREATE TABLE rights_state_definition (
  rights_state TEXT PRIMARY KEY,
  description  TEXT NOT NULL
) WITHOUT ROWID;

INSERT INTO rights_state_definition VALUES
  ('public_metadata', 'Publicly reusable metadata; underlying payload may differ'),
  ('open_data', 'Open-data terms permit the recorded use'),
  ('public_domain', 'Public-domain material'),
  ('licensed', 'Use governed by a recorded licence'),
  ('restricted', 'Access or reuse is restricted'),
  ('discovery_only', 'May be used to discover a locator, not retained as corpus'),
  ('pending', 'Rights review has not completed'),
  ('unknown', 'Rights state is explicitly unknown');

CREATE TABLE privacy_state_definition (
  privacy_state TEXT PRIMARY KEY,
  description   TEXT NOT NULL
) WITHOUT ROWID;

INSERT INTO privacy_state_definition VALUES
  ('public', 'Public, non-sensitive record'),
  ('personal_data', 'Contains personal data requiring policy controls'),
  ('sensitive', 'Sensitive personal or protected data'),
  ('restricted', 'Access-restricted for privacy reasons'),
  ('unknown', 'Privacy state is explicitly unknown');

CREATE TABLE publication_state_definition (
  publication_state TEXT PRIMARY KEY,
  description       TEXT NOT NULL
) WITHOUT ROWID;

INSERT INTO publication_state_definition VALUES
  ('public', 'May appear in public-safe projections'),
  ('internal', 'Internal research use only'),
  ('embargoed', 'Publication delayed until a recorded condition'),
  ('suppressed', 'Must not be published'),
  ('tombstoned', 'Retained only as a removal/tombstone receipt');

