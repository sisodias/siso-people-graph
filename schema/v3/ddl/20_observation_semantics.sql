-- Identifier registry declares semantics before an identifier can participate
-- in canonical identity. Names, employers, locations and biographies belong in
-- attributes/aliases and must not be registered as globally unique identifiers.
CREATE TABLE identifier_scheme (
  scheme_id                TEXT PRIMARY KEY,
  namespace                TEXT NOT NULL,
  label                    TEXT NOT NULL,
  scope_policy             TEXT NOT NULL CHECK(scope_policy IN
    ('global','source','organisation','mixed')),
  uniqueness_class         TEXT NOT NULL CHECK(uniqueness_class IN
    ('unique','non_unique','conditional','unknown')),
  mutability_class         TEXT NOT NULL CHECK(mutability_class IN
    ('stable','mutable','unknown')),
  trust_class              TEXT NOT NULL CHECK(trust_class IN
    ('authority','platform','publisher','self_asserted','derived','unknown')),
  source_authority         TEXT,
  auto_resolution_eligible INTEGER NOT NULL DEFAULT 0 CHECK(auto_resolution_eligible IN (0,1)),
  normalization_method     TEXT NOT NULL,
  definition_version       TEXT NOT NULL,
  effective_at             TEXT NOT NULL,
  retired_at               TEXT,
  CHECK(auto_resolution_eligible = 0 OR
        (uniqueness_class = 'unique' AND mutability_class = 'stable'))
) WITHOUT ROWID;

CREATE TABLE observation_identifier (
  observation_identifier_id TEXT PRIMARY KEY,
  observation_id             TEXT NOT NULL REFERENCES source_observation(observation_id),
  scheme_id                  TEXT NOT NULL REFERENCES identifier_scheme(scheme_id),
  value                      TEXT NOT NULL,
  normalized_value           TEXT NOT NULL,
  scope_type                 TEXT NOT NULL CHECK(scope_type IN ('global','source','organisation')),
  scope_ref                  TEXT NOT NULL DEFAULT '',
  stability                  TEXT NOT NULL CHECK(stability IN ('stable','mutable','unknown')),
  uniqueness                 TEXT NOT NULL CHECK(uniqueness IN ('unique','non_unique','unknown')),
  literal_evidence           TEXT NOT NULL,
  UNIQUE(observation_id, scheme_id, value, scope_type, scope_ref)
) WITHOUT ROWID;
CREATE INDEX ix_observed_identifier_lookup
  ON observation_identifier(scheme_id, normalized_value, scope_type, scope_ref);

CREATE TABLE observation_contribution (
  observation_contribution_id TEXT PRIMARY KEY,
  observation_id              TEXT NOT NULL REFERENCES source_observation(observation_id),
  work_native_id              TEXT NOT NULL,
  contributor_native_id       TEXT NOT NULL,
  role_namespace              TEXT NOT NULL,
  role                        TEXT NOT NULL,
  ordinal                     INTEGER CHECK(ordinal IS NULL OR ordinal >= 0),
  valid_from                  TEXT,
  valid_to                    TEXT,
  attributes_json             TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(attributes_json)),
  literal_evidence            TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE observation_relationship (
  observation_relationship_id TEXT PRIMARY KEY,
  observation_id              TEXT NOT NULL REFERENCES source_observation(observation_id),
  subject_native_id           TEXT NOT NULL,
  predicate_namespace         TEXT NOT NULL,
  predicate                   TEXT NOT NULL,
  object_native_id            TEXT NOT NULL,
  valid_from                  TEXT,
  valid_to                    TEXT,
  attributes_json             TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(attributes_json)),
  literal_evidence            TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE observation_evidence_item (
  observation_evidence_item_id TEXT PRIMARY KEY,
  observation_id               TEXT NOT NULL REFERENCES source_observation(observation_id),
  evidence_kind                TEXT NOT NULL CHECK(evidence_kind IN
    ('field','record','locator','source_span','model_output')),
  locator                      TEXT NOT NULL,
  evidence_json                TEXT NOT NULL CHECK(json_valid(evidence_json)),
  generated_by_model           INTEGER NOT NULL DEFAULT 0 CHECK(generated_by_model IN (0,1)),
  model_name                   TEXT,
  model_version                TEXT,
  input_sha256                 TEXT,
  CHECK(generated_by_model = 0 OR
        (evidence_kind = 'model_output' AND model_name IS NOT NULL
         AND model_version IS NOT NULL AND input_sha256 IS NOT NULL))
) WITHOUT ROWID;

