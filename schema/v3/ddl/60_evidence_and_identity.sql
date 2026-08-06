-- ---------------------------------------------------------------------------
-- Evidence, identity decisions, assertions and relationships.
-- ---------------------------------------------------------------------------
CREATE TABLE evidence (
  evidence_id          TEXT PRIMARY KEY,
  observation_id       TEXT REFERENCES source_observation(observation_id),
  evidence_kind        TEXT NOT NULL CHECK(evidence_kind IN
    ('source_record','source_span','manual_review','model_output','derived')),
  locator              TEXT NOT NULL,
  excerpt              TEXT,
  excerpt_sha256       TEXT CHECK(excerpt_sha256 IS NULL OR
    (length(excerpt_sha256) = 64 AND excerpt_sha256 NOT GLOB '*[^0-9a-f]*')),
  observed_at          TEXT NOT NULL,
  extraction_method    TEXT NOT NULL,
  model_name           TEXT,
  model_version        TEXT,
  input_sha256         TEXT,
  generated_by_model   INTEGER NOT NULL DEFAULT 0 CHECK(generated_by_model IN (0,1)),
  rights_state         TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  privacy_state        TEXT NOT NULL REFERENCES privacy_state_definition(privacy_state),
  publication_state    TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  CHECK(
    (evidence_kind IN ('source_record','source_span')
      AND observation_id IS NOT NULL AND generated_by_model = 0)
    OR (evidence_kind = 'model_output'
      AND generated_by_model = 1 AND model_name IS NOT NULL
      AND model_version IS NOT NULL AND input_sha256 IS NOT NULL)
    OR (evidence_kind IN ('manual_review','derived'))
  )
) WITHOUT ROWID;

CREATE TABLE identity_candidate (
  candidate_id         TEXT PRIMARY KEY,
  entity_a             TEXT NOT NULL REFERENCES entity(entity_id),
  entity_b             TEXT NOT NULL REFERENCES entity(entity_id),
  method_name          TEXT NOT NULL,
  method_version       TEXT NOT NULL,
  confidence           REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  review_state         TEXT NOT NULL DEFAULT 'proposed' CHECK(review_state IN
    ('proposed','in_review','decided','withdrawn')),
  conflict_summary     TEXT,
  created_at           TEXT NOT NULL,
  created_by           TEXT NOT NULL,
  rights_state         TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  publication_state    TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  CHECK(entity_a < entity_b),
  UNIQUE(entity_a, entity_b, method_name, method_version)
) WITHOUT ROWID;

CREATE TABLE identity_candidate_evidence (
  candidate_id TEXT NOT NULL REFERENCES identity_candidate(candidate_id),
  evidence_id  TEXT NOT NULL REFERENCES evidence(evidence_id),
  polarity     TEXT NOT NULL CHECK(polarity IN ('positive','negative','conflict')),
  weight       REAL NOT NULL,
  note         TEXT,
  PRIMARY KEY(candidate_id, evidence_id)
) WITHOUT ROWID;

CREATE TABLE identity_conflict (
  conflict_id          TEXT PRIMARY KEY,
  candidate_id         TEXT NOT NULL REFERENCES identity_candidate(candidate_id),
  conflict_type        TEXT NOT NULL,
  left_identifier_id   TEXT REFERENCES entity_identifier(entity_identifier_id),
  right_identifier_id  TEXT REFERENCES entity_identifier(entity_identifier_id),
  description          TEXT NOT NULL,
  status               TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','resolved','waived')),
  created_at           TEXT NOT NULL,
  resolved_at          TEXT,
  resolution_note      TEXT
) WITHOUT ROWID;

CREATE TABLE identity_decision (
  decision_id           TEXT PRIMARY KEY,
  candidate_id          TEXT NOT NULL REFERENCES identity_candidate(candidate_id),
  decision              TEXT NOT NULL CHECK(decision IN
    ('accepted','rejected','deferred','revoked')),
  decision_evidence_id  TEXT NOT NULL REFERENCES evidence(evidence_id),
  decided_by            TEXT NOT NULL,
  decided_at            TEXT NOT NULL,
  rationale             TEXT NOT NULL,
  supersedes_decision_id TEXT REFERENCES identity_decision(decision_id),
  rights_state          TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  publication_state     TEXT NOT NULL REFERENCES publication_state_definition(publication_state)
) WITHOUT ROWID;

CREATE TRIGGER identity_decision_no_update
BEFORE UPDATE ON identity_decision
BEGIN
  SELECT RAISE(ABORT, 'identity decisions are append-only');
END;
CREATE TRIGGER identity_decision_no_delete
BEFORE DELETE ON identity_decision
BEGIN
  SELECT RAISE(ABORT, 'identity decisions are append-only');
END;
CREATE TRIGGER identity_accept_rejects_open_conflict
BEFORE INSERT ON identity_decision
WHEN NEW.decision = 'accepted' AND EXISTS(
  SELECT 1 FROM identity_conflict
  WHERE candidate_id = NEW.candidate_id AND status = 'open'
)
BEGIN
  SELECT RAISE(ABORT, 'cannot accept identity candidate with unresolved conflict');
END;

CREATE TABLE identity_cluster (
  cluster_id             TEXT PRIMARY KEY,
  canonical_entity_id    TEXT NOT NULL REFERENCES entity(entity_id),
  created_by_decision_id TEXT NOT NULL REFERENCES identity_decision(decision_id),
  created_at             TEXT NOT NULL,
  status                 TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','superseded','revoked'))
) WITHOUT ROWID;

CREATE TABLE identity_cluster_membership (
  membership_id TEXT PRIMARY KEY,
  cluster_id    TEXT NOT NULL REFERENCES identity_cluster(cluster_id),
  entity_id     TEXT NOT NULL REFERENCES entity(entity_id),
  decision_id   TEXT NOT NULL REFERENCES identity_decision(decision_id),
  valid_from    TEXT NOT NULL,
  valid_to      TEXT,
  CHECK(valid_to IS NULL OR valid_to >= valid_from)
) WITHOUT ROWID;
CREATE UNIQUE INDEX uq_active_identity_membership
  ON identity_cluster_membership(entity_id) WHERE valid_to IS NULL;

CREATE TABLE entity_redirect (
  redirect_id    TEXT PRIMARY KEY,
  from_entity_id TEXT NOT NULL REFERENCES entity(entity_id),
  to_entity_id   TEXT NOT NULL REFERENCES entity(entity_id),
  decision_id    TEXT NOT NULL REFERENCES identity_decision(decision_id),
  valid_from     TEXT NOT NULL,
  valid_to       TEXT,
  CHECK(from_entity_id <> to_entity_id),
  CHECK(valid_to IS NULL OR valid_to >= valid_from)
) WITHOUT ROWID;
CREATE UNIQUE INDEX uq_active_entity_redirect
  ON entity_redirect(from_entity_id) WHERE valid_to IS NULL;

