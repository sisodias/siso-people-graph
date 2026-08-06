-- ---------------------------------------------------------------------------
-- Named/versioned derived projections. No column is a universal canonical rank.
-- ---------------------------------------------------------------------------
CREATE TABLE projection_definition (
  projection_definition_id TEXT PRIMARY KEY,
  name                     TEXT NOT NULL,
  version                  TEXT NOT NULL,
  purpose                  TEXT NOT NULL,
  output_semantics         TEXT NOT NULL,
  method_card_uri          TEXT NOT NULL,
  method_sha256            TEXT NOT NULL
    CHECK(length(method_sha256) = 64 AND method_sha256 NOT GLOB '*[^0-9a-f]*'),
  created_at               TEXT NOT NULL,
  UNIQUE(name, version)
) WITHOUT ROWID;

CREATE TABLE projection_run (
  projection_run_id        TEXT PRIMARY KEY,
  projection_definition_id TEXT NOT NULL REFERENCES projection_definition(projection_definition_id),
  as_of                    TEXT NOT NULL,
  source_scope_json        TEXT NOT NULL CHECK(json_valid(source_scope_json)),
  parameters_json          TEXT NOT NULL CHECK(json_valid(parameters_json)),
  input_digest             TEXT NOT NULL
    CHECK(length(input_digest) = 64 AND input_digest NOT GLOB '*[^0-9a-f]*'),
  uncertainty_method       TEXT NOT NULL,
  started_at               TEXT NOT NULL,
  completed_at             TEXT,
  status                   TEXT NOT NULL CHECK(status IN ('running','complete','failed','superseded')),
  rights_state             TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  publication_state        TEXT NOT NULL REFERENCES publication_state_definition(publication_state)
) WITHOUT ROWID;

CREATE TABLE projection_value (
  projection_value_id TEXT PRIMARY KEY,
  projection_run_id   TEXT NOT NULL REFERENCES projection_run(projection_run_id),
  subject_entity_id   TEXT NOT NULL REFERENCES entity(entity_id),
  object_entity_id    TEXT REFERENCES entity(entity_id),
  metric_name         TEXT NOT NULL,
  value_json          TEXT NOT NULL CHECK(json_valid(value_json)),
  uncertainty_json    TEXT NOT NULL CHECK(json_valid(uncertainty_json)),
  UNIQUE(projection_run_id, subject_entity_id, object_entity_id, metric_name)
) WITHOUT ROWID;

COMMIT;
