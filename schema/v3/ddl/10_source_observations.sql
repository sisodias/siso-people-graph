-- ---------------------------------------------------------------------------
-- Source control plane and immutable source observations.
-- ---------------------------------------------------------------------------
CREATE TABLE source (
  source_id           TEXT PRIMARY KEY,
  source_namespace    TEXT NOT NULL UNIQUE,
  name                TEXT NOT NULL,
  owner               TEXT,
  homepage_uri        TEXT,
  default_terms_uri   TEXT,
  default_terms_revision TEXT NOT NULL,
  default_rights_state TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  default_privacy_state TEXT NOT NULL REFERENCES privacy_state_definition(privacy_state),
  default_publication_state TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  acquisition_method  TEXT NOT NULL,
  created_at          TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE source_snapshot (
  snapshot_id             TEXT PRIMARY KEY,
  source_id               TEXT NOT NULL REFERENCES source(source_id),
  source_native_revision  TEXT NOT NULL,
  snapshot_at             TEXT,
  retrieved_at            TEXT NOT NULL,
  terms_revision          TEXT NOT NULL,
  rights_state            TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  privacy_state           TEXT NOT NULL REFERENCES privacy_state_definition(privacy_state),
  publication_state       TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  acquisition_method      TEXT NOT NULL,
  acquisition_locator_class TEXT NOT NULL,
  content_sha256          TEXT NOT NULL
    CHECK(length(content_sha256) = 64 AND content_sha256 NOT GLOB '*[^0-9a-f]*'),
  expected_record_count   INTEGER CHECK(expected_record_count IS NULL OR expected_record_count >= 0),
  parent_snapshot_id      TEXT REFERENCES source_snapshot(snapshot_id),
  deletion_policy         TEXT NOT NULL,
  tombstone_policy        TEXT NOT NULL,
  retention_until         TEXT,
  UNIQUE(source_id, source_native_revision)
) WITHOUT ROWID;

CREATE TABLE observation_envelope_receipt (
  envelope_receipt_id TEXT PRIMARY KEY,
  envelope_version    TEXT NOT NULL CHECK(envelope_version = 'pg-observation-0.1'),
  source_id           TEXT NOT NULL REFERENCES source(source_id),
  snapshot_id         TEXT NOT NULL REFERENCES source_snapshot(snapshot_id),
  record_native_id    TEXT NOT NULL,
  payload_json        TEXT NOT NULL CHECK(json_valid(payload_json)),
  payload_sha256      TEXT NOT NULL
    CHECK(length(payload_sha256) = 64 AND payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  received_at         TEXT NOT NULL,
  CHECK(json_extract(payload_json, '$.envelope_version') = 'pg-observation-0.1'),
  CHECK(json_extract(payload_json, '$.source.source_id') = source_id),
  CHECK(json_extract(payload_json, '$.source.record_native_id') = record_native_id),
  CHECK(json_type(payload_json, '$.canonical_id') IS NULL),
  CHECK(json_type(payload_json, '$.subject.canonical_id') IS NULL),
  CHECK(json_type(payload_json, '$.subject.person_id') IS NULL),
  UNIQUE(snapshot_id, record_native_id, payload_sha256)
) WITHOUT ROWID;

CREATE TABLE source_observation (
  observation_id      TEXT PRIMARY KEY,
  snapshot_id         TEXT NOT NULL REFERENCES source_snapshot(snapshot_id),
  envelope_receipt_id TEXT REFERENCES observation_envelope_receipt(envelope_receipt_id),
  record_native_id    TEXT NOT NULL,
  observed_at         TEXT NOT NULL,
  retrieved_at        TEXT NOT NULL,
  subject_kind        TEXT NOT NULL CHECK(subject_kind IN
    ('person','organisation','account','work','event','venue','place','concept','claim','pseudonym')),
  subject_native_id   TEXT NOT NULL,
  label               TEXT,
  attributes_json     TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(attributes_json)),
  raw_pointer         TEXT NOT NULL,
  payload_sha256      TEXT NOT NULL
    CHECK(length(payload_sha256) = 64 AND payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  rights_state        TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  privacy_state       TEXT NOT NULL REFERENCES privacy_state_definition(privacy_state),
  publication_state   TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  UNIQUE(snapshot_id, record_native_id, subject_kind, subject_native_id, payload_sha256)
) WITHOUT ROWID;

-- Source observations and envelope receipts are append-only. Removals are
-- represented by status events so the audit receipt survives.
CREATE TRIGGER observation_envelope_no_update
BEFORE UPDATE ON observation_envelope_receipt
BEGIN
  SELECT RAISE(ABORT, 'observation envelopes are append-only');
END;
CREATE TRIGGER observation_envelope_no_delete
BEFORE DELETE ON observation_envelope_receipt
BEGIN
  SELECT RAISE(ABORT, 'observation envelopes are append-only');
END;
CREATE TRIGGER source_observation_no_update
BEFORE UPDATE ON source_observation
BEGIN
  SELECT RAISE(ABORT, 'source observations are append-only');
END;
CREATE TRIGGER source_observation_no_delete
BEFORE DELETE ON source_observation
BEGIN
  SELECT RAISE(ABORT, 'source observations are append-only');
END;

CREATE TABLE observation_status_event (
  status_event_id TEXT PRIMARY KEY,
  observation_id  TEXT NOT NULL REFERENCES source_observation(observation_id),
  status          TEXT NOT NULL CHECK(status IN
    ('active','superseded','tombstoned','deletion_requested','raw_pointer_revoked')),
  effective_at    TEXT NOT NULL,
  reason          TEXT NOT NULL,
  authority       TEXT NOT NULL,
  request_locator TEXT
) WITHOUT ROWID;

