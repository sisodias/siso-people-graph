-- ---------------------------------------------------------------------------
-- Namespaced vocabularies and explicit crosswalks.
-- ---------------------------------------------------------------------------
CREATE TABLE vocabulary (
  vocabulary_id        TEXT PRIMARY KEY,
  namespace            TEXT NOT NULL,
  version               TEXT NOT NULL,
  source_id             TEXT REFERENCES source(source_id),
  label                 TEXT NOT NULL,
  rights_state          TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  publication_state     TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  UNIQUE(namespace, version)
) WITHOUT ROWID;

CREATE TABLE vocabulary_term (
  term_id               TEXT PRIMARY KEY,
  vocabulary_id         TEXT NOT NULL REFERENCES vocabulary(vocabulary_id),
  source_local_id       TEXT NOT NULL,
  label                 TEXT NOT NULL,
  description           TEXT,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  UNIQUE(vocabulary_id, source_local_id)
) WITHOUT ROWID;

CREATE TABLE term_crosswalk (
  crosswalk_id          TEXT PRIMARY KEY,
  from_term_id          TEXT NOT NULL REFERENCES vocabulary_term(term_id),
  to_term_id            TEXT NOT NULL REFERENCES vocabulary_term(term_id),
  mapping_type          TEXT NOT NULL CHECK(mapping_type IN
    ('exact','close','broader','narrower','related')),
  confidence            REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  evidence_id           TEXT NOT NULL REFERENCES evidence(evidence_id),
  method_version        TEXT NOT NULL,
  status                TEXT NOT NULL CHECK(status IN ('proposed','accepted','rejected')),
  CHECK(from_term_id <> to_term_id)
) WITHOUT ROWID;

