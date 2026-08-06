CREATE TABLE assertion (
  assertion_id          TEXT PRIMARY KEY,
  subject_entity_id     TEXT NOT NULL REFERENCES entity(entity_id),
  predicate_namespace   TEXT NOT NULL,
  predicate             TEXT NOT NULL,
  object_entity_id      TEXT REFERENCES entity(entity_id),
  value_json            TEXT CHECK(value_json IS NULL OR json_valid(value_json)),
  topic_term_id         TEXT REFERENCES vocabulary_term(term_id),
  scope_json            TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(scope_json)),
  confidence            REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  status                TEXT NOT NULL CHECK(status IN
    ('proposed','accepted','rejected','contested','withdrawn')),
  valid_from            TEXT,
  valid_to              TEXT,
  observed_at           TEXT NOT NULL,
  extraction_method     TEXT NOT NULL,
  model_name            TEXT,
  model_version         TEXT,
  input_sha256          TEXT,
  deciding_authority    TEXT,
  primary_evidence_id   TEXT NOT NULL REFERENCES evidence(evidence_id),
  rights_state          TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  privacy_state         TEXT NOT NULL REFERENCES privacy_state_definition(privacy_state),
  publication_state     TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  CHECK((object_entity_id IS NOT NULL) <> (value_json IS NOT NULL)),
  CHECK(valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
  CHECK(model_name IS NULL OR (model_version IS NOT NULL AND input_sha256 IS NOT NULL))
) WITHOUT ROWID;

CREATE TABLE assertion_evidence (
  assertion_id TEXT NOT NULL REFERENCES assertion(assertion_id),
  evidence_id  TEXT NOT NULL REFERENCES evidence(evidence_id),
  role         TEXT NOT NULL CHECK(role IN ('supports','challenges','context')),
  PRIMARY KEY(assertion_id, evidence_id)
) WITHOUT ROWID;

CREATE TABLE assertion_relation (
  subject_assertion_id TEXT NOT NULL REFERENCES assertion(assertion_id),
  relation_type        TEXT NOT NULL CHECK(relation_type IN
    ('supports','challenges','contradicts','supersedes','qualifies')),
  object_assertion_id  TEXT NOT NULL REFERENCES assertion(assertion_id),
  evidence_id          TEXT NOT NULL REFERENCES evidence(evidence_id),
  PRIMARY KEY(subject_assertion_id, relation_type, object_assertion_id),
  CHECK(subject_assertion_id <> object_assertion_id)
) WITHOUT ROWID;

CREATE TABLE relationship_type (
  relationship_type_id TEXT PRIMARY KEY,
  namespace            TEXT NOT NULL,
  local_name           TEXT NOT NULL,
  inverse_type_id      TEXT REFERENCES relationship_type(relationship_type_id),
  temporal_semantics   TEXT NOT NULL,
  description          TEXT NOT NULL,
  UNIQUE(namespace, local_name)
) WITHOUT ROWID;

CREATE TABLE relationship (
  relationship_id      TEXT PRIMARY KEY,
  subject_entity_id    TEXT NOT NULL REFERENCES entity(entity_id),
  relationship_type_id TEXT NOT NULL REFERENCES relationship_type(relationship_type_id),
  object_entity_id     TEXT NOT NULL REFERENCES entity(entity_id),
  valid_from           TEXT,
  valid_to             TEXT,
  observed_at          TEXT NOT NULL,
  confidence           REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  review_state         TEXT NOT NULL CHECK(review_state IN
    ('proposed','accepted','rejected','contested')),
  primary_evidence_id  TEXT NOT NULL REFERENCES evidence(evidence_id),
  source_observation_id TEXT REFERENCES source_observation(observation_id),
  extraction_method    TEXT NOT NULL,
  CHECK(subject_entity_id <> object_entity_id),
  CHECK(valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
) WITHOUT ROWID;
CREATE INDEX ix_relationship_subject_time
  ON relationship(subject_entity_id, relationship_type_id, valid_from, valid_to);
CREATE INDEX ix_relationship_object_time
  ON relationship(object_entity_id, relationship_type_id, valid_from, valid_to);

CREATE TABLE relationship_evidence (
  relationship_id TEXT NOT NULL REFERENCES relationship(relationship_id),
  evidence_id     TEXT NOT NULL REFERENCES evidence(evidence_id),
  role            TEXT NOT NULL CHECK(role IN ('supports','challenges','context')),
  PRIMARY KEY(relationship_id, evidence_id)
) WITHOUT ROWID;

