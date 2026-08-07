PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS identity_v3_entity (
  entity_id        TEXT PRIMARY KEY,
  label            TEXT,
  kind             TEXT NOT NULL DEFAULT 'unknown',
  origin           TEXT,
  source_native_id TEXT,
  birth_year       INTEGER,
  death_year       INTEGER,
  source_state     TEXT,
  created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS identity_v3_identifier (
  entity_id                  TEXT NOT NULL,
  scheme                     TEXT NOT NULL,
  value                      TEXT NOT NULL,
  normalized_value           TEXT NOT NULL,
  scope                      TEXT NOT NULL,
  uniqueness_class           TEXT NOT NULL,
  mutability                 TEXT NOT NULL,
  authority                  TEXT NOT NULL,
  auto_resolution_eligible   INTEGER NOT NULL CHECK (auto_resolution_eligible IN (0, 1)),
  source                     TEXT NOT NULL,
  evidence_json              TEXT NOT NULL DEFAULT '{}',
  valid_from                 TEXT NOT NULL DEFAULT '',
  valid_to                   TEXT,
  observed_at                TEXT NOT NULL,
  PRIMARY KEY (entity_id, scheme, normalized_value, valid_from),
  FOREIGN KEY (entity_id) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_identity_v3_identifier_lookup
  ON identity_v3_identifier(scheme, normalized_value);

CREATE TABLE IF NOT EXISTS identity_v3_alias (
  alias_id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id                  TEXT NOT NULL,
  scheme                     TEXT NOT NULL,
  alias                      TEXT NOT NULL,
  normalized_alias           TEXT NOT NULL,
  valid_from                 TEXT NOT NULL DEFAULT '',
  valid_to                   TEXT,
  source                     TEXT NOT NULL,
  stable_identifier_scheme   TEXT,
  stable_identifier_value    TEXT,
  observed_at                TEXT NOT NULL,
  evidence_json              TEXT NOT NULL DEFAULT '{}',
  UNIQUE (entity_id, scheme, normalized_alias, valid_from),
  FOREIGN KEY (entity_id) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_identity_v3_alias_lookup
  ON identity_v3_alias(scheme, normalized_alias, valid_to);

CREATE TABLE IF NOT EXISTS identity_v3_attribute (
  entity_id       TEXT NOT NULL,
  source          TEXT NOT NULL,
  attribute       TEXT NOT NULL,
  value_json      TEXT NOT NULL,
  observed_at     TEXT NOT NULL,
  payload_sha256  TEXT NOT NULL DEFAULT '',
  evidence_json   TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (entity_id, source, attribute, observed_at, payload_sha256),
  FOREIGN KEY (entity_id) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_identity_v3_attribute_entity
  ON identity_v3_attribute(entity_id, source, attribute);

CREATE TABLE IF NOT EXISTS identity_v3_enrichment_receipt (
  entity_id       TEXT NOT NULL,
  source          TEXT NOT NULL,
  field           TEXT NOT NULL,
  observed_at     TEXT NOT NULL,
  payload_sha256  TEXT NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('present', 'absent', 'error')),
  PRIMARY KEY (entity_id, source, field, payload_sha256),
  FOREIGN KEY (entity_id) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_identity_v3_receipt_latest
  ON identity_v3_enrichment_receipt(entity_id, source, field, observed_at);

CREATE TABLE IF NOT EXISTS identity_v3_candidate (
  candidate_id            TEXT PRIMARY KEY,
  entity_a                TEXT NOT NULL,
  entity_b                TEXT NOT NULL,
  method                  TEXT NOT NULL,
  method_version          TEXT NOT NULL,
  confidence              REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
  auto_eligible           INTEGER NOT NULL CHECK (auto_eligible IN (0, 1)),
  positive_evidence_json  TEXT NOT NULL DEFAULT '[]',
  negative_evidence_json  TEXT NOT NULL DEFAULT '[]',
  conflict_reasons_json   TEXT NOT NULL DEFAULT '[]',
  review_state            TEXT NOT NULL DEFAULT 'proposed'
                            CHECK (review_state IN ('proposed', 'accepted', 'rejected', 'superseded')),
  created_at              TEXT NOT NULL,
  updated_at              TEXT NOT NULL,
  CHECK (entity_a < entity_b),
  UNIQUE (entity_a, entity_b, method, method_version),
  FOREIGN KEY (entity_a) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE,
  FOREIGN KEY (entity_b) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_identity_v3_candidate_state
  ON identity_v3_candidate(review_state, auto_eligible, confidence);

CREATE TABLE IF NOT EXISTS identity_v3_decision (
  decision_id    TEXT PRIMARY KEY,
  candidate_id   TEXT NOT NULL,
  entity_a       TEXT NOT NULL,
  entity_b       TEXT NOT NULL,
  outcome        TEXT NOT NULL CHECK (outcome IN ('accepted', 'rejected')),
  active         INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  decided_by     TEXT NOT NULL,
  decided_at     TEXT NOT NULL,
  rationale      TEXT NOT NULL DEFAULT '',
  reverted_at    TEXT,
  FOREIGN KEY (candidate_id) REFERENCES identity_v3_candidate(candidate_id) ON DELETE CASCADE,
  FOREIGN KEY (entity_a) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE,
  FOREIGN KEY (entity_b) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_identity_v3_decision_active
  ON identity_v3_decision(active, outcome, decided_at);

CREATE TABLE IF NOT EXISTS identity_v3_generation (
  generation       INTEGER PRIMARY KEY AUTOINCREMENT,
  reason           TEXT NOT NULL,
  decision_digest  TEXT NOT NULL,
  created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS identity_v3_cluster_member (
  generation          INTEGER NOT NULL,
  entity_id           TEXT NOT NULL,
  cluster_id          TEXT NOT NULL,
  canonical_entity_id TEXT NOT NULL,
  PRIMARY KEY (generation, entity_id),
  FOREIGN KEY (generation) REFERENCES identity_v3_generation(generation) ON DELETE CASCADE,
  FOREIGN KEY (entity_id) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE,
  FOREIGN KEY (canonical_entity_id) REFERENCES identity_v3_entity(entity_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_identity_v3_cluster_lookup
  ON identity_v3_cluster_member(generation, cluster_id);

CREATE TABLE IF NOT EXISTS identity_v3_audit_event (
  event_id      TEXT PRIMARY KEY,
  event_type    TEXT NOT NULL,
  severity      TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
  entity_id     TEXT,
  candidate_id  TEXT,
  details_json  TEXT NOT NULL,
  created_at    TEXT NOT NULL
);
