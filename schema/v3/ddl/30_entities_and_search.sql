-- ---------------------------------------------------------------------------
-- Canonical entities. IDs are opaque and independent of labels, handles and
-- source-native identifiers. Canonicalization never changes source rows.
-- ---------------------------------------------------------------------------
CREATE TABLE entity (
  entity_id             TEXT PRIMARY KEY,
  entity_kind           TEXT NOT NULL CHECK(entity_kind IN
    ('person','organisation','account','pseudonym','work','event','venue','place','concept','claim')),
  canonical_label       TEXT NOT NULL,
  label_observation_id  TEXT NOT NULL REFERENCES source_observation(observation_id),
  status                TEXT NOT NULL DEFAULT 'active' CHECK(status IN
    ('active','redirected','disputed','tombstoned')),
  created_at            TEXT NOT NULL,
  created_by            TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX ix_entity_kind ON entity(entity_kind);
CREATE INDEX ix_entity_label ON entity(canonical_label);

CREATE TABLE entity_alias (
  alias_id              TEXT PRIMARY KEY,
  entity_id             TEXT NOT NULL REFERENCES entity(entity_id),
  alias                 TEXT NOT NULL,
  alias_type            TEXT NOT NULL CHECK(alias_type IN
    ('name','handle','former_handle','pen_name','transliteration','abbreviation','source_label')),
  language_tag          TEXT,
  script_code           TEXT,
  valid_from            TEXT,
  valid_to              TEXT,
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  status                TEXT NOT NULL DEFAULT 'accepted' CHECK(status IN
    ('proposed','accepted','rejected','superseded')),
  UNIQUE(entity_id, alias, alias_type, valid_from)
) WITHOUT ROWID;

-- One row per searchable label/alias. unicode61 preserves non-Latin tokens and
-- remove_diacritics=2 permits accent-insensitive Latin lookup.
CREATE VIRTUAL TABLE entity_search USING fts5(
  entity_id UNINDEXED,
  text,
  source_kind UNINDEXED,
  source_row_id UNINDEXED,
  tokenize = 'unicode61 remove_diacritics 2'
);

CREATE TRIGGER entity_search_insert AFTER INSERT ON entity BEGIN
  INSERT INTO entity_search(entity_id, text, source_kind, source_row_id)
  VALUES(NEW.entity_id, NEW.canonical_label, 'entity', NEW.entity_id);
END;
CREATE TRIGGER entity_search_update AFTER UPDATE OF canonical_label ON entity BEGIN
  DELETE FROM entity_search WHERE source_kind = 'entity' AND source_row_id = OLD.entity_id;
  INSERT INTO entity_search(entity_id, text, source_kind, source_row_id)
  VALUES(NEW.entity_id, NEW.canonical_label, 'entity', NEW.entity_id);
END;
CREATE TRIGGER entity_search_delete AFTER DELETE ON entity BEGIN
  DELETE FROM entity_search WHERE source_kind = 'entity' AND source_row_id = OLD.entity_id;
END;
CREATE TRIGGER alias_search_insert AFTER INSERT ON entity_alias
WHEN NEW.status = 'accepted' BEGIN
  INSERT INTO entity_search(entity_id, text, source_kind, source_row_id)
  VALUES(NEW.entity_id, NEW.alias, 'alias', NEW.alias_id);
END;
CREATE TRIGGER alias_search_update AFTER UPDATE ON entity_alias BEGIN
  DELETE FROM entity_search WHERE source_kind = 'alias' AND source_row_id = OLD.alias_id;
  INSERT INTO entity_search(entity_id, text, source_kind, source_row_id)
  SELECT NEW.entity_id, NEW.alias, 'alias', NEW.alias_id WHERE NEW.status = 'accepted';
END;
CREATE TRIGGER alias_search_delete AFTER DELETE ON entity_alias BEGIN
  DELETE FROM entity_search WHERE source_kind = 'alias' AND source_row_id = OLD.alias_id;
END;

CREATE TABLE entity_identifier (
  entity_identifier_id  TEXT PRIMARY KEY,
  entity_id             TEXT NOT NULL REFERENCES entity(entity_id),
  scheme_id             TEXT NOT NULL REFERENCES identifier_scheme(scheme_id),
  value                 TEXT NOT NULL,
  normalized_value      TEXT NOT NULL,
  scope_type            TEXT NOT NULL CHECK(scope_type IN ('global','source','organisation')),
  scope_ref             TEXT NOT NULL DEFAULT '',
  stability             TEXT NOT NULL CHECK(stability IN ('stable','mutable','unknown')),
  uniqueness            TEXT NOT NULL CHECK(uniqueness IN ('unique','non_unique','unknown')),
  source_observation_id TEXT NOT NULL REFERENCES source_observation(observation_id),
  status                TEXT NOT NULL DEFAULT 'accepted' CHECK(status IN
    ('proposed','accepted','rejected','superseded')),
  valid_from            TEXT,
  valid_to              TEXT,
  CHECK(scope_type <> 'global' OR scope_ref = '')
) WITHOUT ROWID;

CREATE UNIQUE INDEX uq_entity_identifier_unique_scope
  ON entity_identifier(scheme_id, normalized_value, scope_type, scope_ref)
  WHERE uniqueness = 'unique' AND status = 'accepted' AND valid_to IS NULL;
CREATE INDEX ix_entity_identifier_entity ON entity_identifier(entity_id);

CREATE TRIGGER entity_identifier_semantics
BEFORE INSERT ON entity_identifier
WHEN (NEW.uniqueness = 'unique' AND
      (SELECT uniqueness_class FROM identifier_scheme WHERE scheme_id = NEW.scheme_id)
        NOT IN ('unique','conditional'))
   OR (NEW.stability = 'stable' AND
      (SELECT mutability_class FROM identifier_scheme WHERE scheme_id = NEW.scheme_id)
        NOT IN ('stable','unknown'))
BEGIN
  SELECT RAISE(ABORT, 'identifier assignment contradicts scheme definition');
END;

