-- ---------------------------------------------------------------------------
-- First-class Works, versions/expressions/editions, venues, contributions,
-- citations, dependencies and locators.
-- ---------------------------------------------------------------------------
CREATE TABLE work (
  work_id               TEXT PRIMARY KEY REFERENCES entity(entity_id),
  work_type             TEXT NOT NULL,
  title                 TEXT NOT NULL,
  original_language     TEXT,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  rights_state          TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  privacy_state         TEXT NOT NULL REFERENCES privacy_state_definition(privacy_state),
  publication_state     TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  created_at            TEXT NOT NULL
) WITHOUT ROWID;

CREATE TRIGGER work_requires_work_entity
BEFORE INSERT ON work
WHEN (SELECT entity_kind FROM entity WHERE entity_id = NEW.work_id) <> 'work'
BEGIN
  SELECT RAISE(ABORT, 'work_id must reference an entity of kind work');
END;

CREATE TABLE work_version (
  work_version_id       TEXT PRIMARY KEY,
  work_id               TEXT NOT NULL REFERENCES work(work_id),
  version_type          TEXT NOT NULL CHECK(version_type IN
    ('expression','edition','release','revision','translation','manifestation')),
  version_label         TEXT NOT NULL,
  sequence_number       INTEGER CHECK(sequence_number IS NULL OR sequence_number >= 0),
  language_tag          TEXT,
  issued_at             TEXT,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  rights_state          TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  privacy_state         TEXT NOT NULL REFERENCES privacy_state_definition(privacy_state),
  publication_state     TEXT NOT NULL REFERENCES publication_state_definition(publication_state),
  UNIQUE(work_id, version_type, version_label)
) WITHOUT ROWID;

CREATE TABLE venue (
  venue_id              TEXT PRIMARY KEY REFERENCES entity(entity_id),
  venue_type            TEXT NOT NULL,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  rights_state          TEXT NOT NULL REFERENCES rights_state_definition(rights_state),
  publication_state     TEXT NOT NULL REFERENCES publication_state_definition(publication_state)
) WITHOUT ROWID;

CREATE TABLE work_venue (
  work_venue_id         TEXT PRIMARY KEY,
  work_id               TEXT NOT NULL REFERENCES work(work_id),
  work_version_id       TEXT REFERENCES work_version(work_version_id),
  venue_id              TEXT NOT NULL REFERENCES venue(venue_id),
  relation_type         TEXT NOT NULL CHECK(relation_type IN
    ('published_in','presented_at','released_on','hosted_by')),
  valid_from            TEXT,
  valid_to              TEXT,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id)
) WITHOUT ROWID;

CREATE TABLE contribution (
  contribution_id       TEXT PRIMARY KEY,
  contributor_entity_id TEXT NOT NULL REFERENCES entity(entity_id),
  work_id               TEXT NOT NULL REFERENCES work(work_id),
  work_version_id       TEXT REFERENCES work_version(work_version_id),
  role_namespace        TEXT NOT NULL,
  role                  TEXT NOT NULL,
  ordinal               INTEGER CHECK(ordinal IS NULL OR ordinal >= 0),
  credited_as           TEXT,
  valid_from            TEXT,
  valid_to              TEXT,
  observed_at           TEXT NOT NULL,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  status                TEXT NOT NULL DEFAULT 'accepted' CHECK(status IN
    ('proposed','accepted','rejected','superseded')),
  UNIQUE(contributor_entity_id, work_id, work_version_id, role_namespace, role, ordinal,
         source_observation_id)
) WITHOUT ROWID;

CREATE TABLE citation (
  citation_id           TEXT PRIMARY KEY,
  citing_work_id        TEXT NOT NULL REFERENCES work(work_id),
  citing_version_id     TEXT REFERENCES work_version(work_version_id),
  cited_work_id         TEXT NOT NULL REFERENCES work(work_id),
  cited_version_id      TEXT REFERENCES work_version(work_version_id),
  locator               TEXT,
  observed_at           TEXT NOT NULL,
  confidence            REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  status                TEXT NOT NULL CHECK(status IN ('proposed','accepted','rejected','contested')),
  CHECK(citing_work_id <> cited_work_id OR
        COALESCE(citing_version_id, '') <> COALESCE(cited_version_id, ''))
) WITHOUT ROWID;

CREATE TABLE work_dependency (
  dependency_id          TEXT PRIMARY KEY,
  work_id                TEXT NOT NULL REFERENCES work(work_id),
  work_version_id        TEXT REFERENCES work_version(work_version_id),
  depends_on_work_id     TEXT NOT NULL REFERENCES work(work_id),
  depends_on_version_id  TEXT REFERENCES work_version(work_version_id),
  dependency_type        TEXT NOT NULL,
  requirement            TEXT,
  valid_from             TEXT,
  valid_to               TEXT,
  observed_at            TEXT NOT NULL,
  source_observation_id  TEXT NOT NULL REFERENCES source_observation(observation_id),
  status                 TEXT NOT NULL CHECK(status IN ('proposed','accepted','rejected','superseded')),
  CHECK(work_id <> depends_on_work_id OR
        COALESCE(work_version_id, '') <> COALESCE(depends_on_version_id, ''))
) WITHOUT ROWID;

CREATE TABLE work_locator (
  locator_id            TEXT PRIMARY KEY,
  work_id               TEXT NOT NULL REFERENCES work(work_id),
  work_version_id       TEXT REFERENCES work_version(work_version_id),
  locator_type          TEXT NOT NULL CHECK(locator_type IN
    ('doi','url','swhid','isbn','repository','archive_member','source_native')),
  locator_value         TEXT NOT NULL,
  content_sha256        TEXT CHECK(content_sha256 IS NULL OR
    (length(content_sha256) = 64 AND content_sha256 NOT GLOB '*[^0-9a-f]*')),
  access_state          TEXT NOT NULL CHECK(access_state IN
    ('open','authenticated','restricted','removed','unknown')),
  valid_from            TEXT,
  valid_to              TEXT,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  UNIQUE(locator_type, locator_value, valid_from)
) WITHOUT ROWID;

