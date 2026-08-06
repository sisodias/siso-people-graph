INSERT INTO entity (entity_id, entity_kind, canonical_label, label_observation_id, status, created_at, created_by) VALUES
  ('pg:01H-PERSON-A', 'person', 'Zoë Tanaka', 'obs:fixture-a:author-1', 'active', '2026-08-06T01:00:00Z', 'fixture-review'),
  ('pg:01H-PERSON-B', 'person', '田中 ゾーイ', 'obs:fixture-b:author-9', 'redirected', '2026-08-06T01:00:00Z', 'fixture-review'),
  ('pg:01H-WORK-A', 'work', 'Evidence Graphs in Practice', 'obs:fixture-a:work-1', 'active', '2026-08-06T01:00:00Z', 'fixture-review'),
  ('pg:01H-WORK-B', 'work', 'Example Graph Toolkit', 'obs:fixture-a:work-2', 'active', '2026-08-06T01:00:00Z', 'fixture-review'),
  ('pg:01H-VENUE-A', 'venue', 'Example Systems Conference', 'obs:fixture-a:venue-1', 'active', '2026-08-06T01:00:00Z', 'fixture-review'),
  ('pg:01H-ORG-A', 'organisation', 'Example Research Lab', 'obs:fixture-a:org-1', 'active', '2026-08-06T01:00:00Z', 'fixture-review'),
  ('pg:01H-CONCEPT-A', 'concept', 'Knowledge graphs', 'obs:fixture-a:concept-1', 'active', '2026-08-06T01:00:00Z', 'fixture-review');

INSERT INTO entity_alias (alias_id, entity_id, alias, alias_type, language_tag, script_code, valid_from, valid_to, source_observation_id, status) VALUES
  ('alias:zoe-latin', 'pg:01H-PERSON-A', 'Dr. Zoë Tanaka', 'source_label', 'en', 'Latn', NULL, NULL, 'obs:fixture-a:author-1', 'accepted'),
  ('alias:zoe-japanese', 'pg:01H-PERSON-A', '田中 ゾーイ', 'transliteration', 'ja', 'Jpan', NULL, NULL, 'obs:fixture-b:author-9', 'accepted');

INSERT INTO entity_identifier (entity_identifier_id, entity_id, scheme_id, value, normalized_value, scope_type, scope_ref, stability, uniqueness, source_observation_id, status, valid_from, valid_to) VALUES
  ('eid:zoe-orcid', 'pg:01H-PERSON-A', 'orcid', '0000-0002-1825-0097', '0000-0002-1825-0097', 'global', '', 'stable', 'unique', 'obs:fixture-a:author-1', 'accepted', '2026-08-05', NULL);

INSERT INTO work (work_id, work_type, title, original_language, source_observation_id, rights_state, privacy_state, publication_state, created_at) VALUES
  ('pg:01H-WORK-A', 'article', 'Evidence Graphs in Practice', 'en', 'obs:fixture-a:work-1', 'open_data', 'public', 'public', '2026-08-06T01:00:00Z'),
  ('pg:01H-WORK-B', 'software', 'Example Graph Toolkit', 'en', 'obs:fixture-a:work-2', 'open_data', 'public', 'public', '2026-08-06T01:00:00Z');

INSERT INTO work_version (work_version_id, work_id, version_type, version_label, sequence_number, language_tag, issued_at, source_observation_id, rights_state, privacy_state, publication_state) VALUES
  ('wv:work-a:v1', 'pg:01H-WORK-A', 'edition', '1', 1, 'en', '2026-07-01', 'obs:fixture-a:work-1', 'open_data', 'public', 'public'),
  ('wv:work-b:v2', 'pg:01H-WORK-B', 'release', '2.0', 2, 'en', '2026-06-15', 'obs:fixture-a:work-2', 'open_data', 'public', 'public');

INSERT INTO venue (venue_id, venue_type, source_observation_id, rights_state, publication_state) VALUES
  ('pg:01H-VENUE-A', 'conference', 'obs:fixture-a:venue-1', 'open_data', 'public');

INSERT INTO work_venue (work_venue_id, work_id, work_version_id, venue_id, relation_type, valid_from, valid_to, source_observation_id) VALUES
  ('workvenue:a', 'pg:01H-WORK-A', 'wv:work-a:v1', 'pg:01H-VENUE-A', 'presented_at', '2026-07-01', NULL, 'obs:fixture-a:work-1');

INSERT INTO contribution (contribution_id, contributor_entity_id, work_id, work_version_id, role_namespace, role, ordinal, credited_as, valid_from, valid_to, observed_at, source_observation_id, status) VALUES
  ('contrib:zoe-work-a', 'pg:01H-PERSON-A', 'pg:01H-WORK-A', 'wv:work-a:v1', 'credit', 'author', 1, 'Zoë Tanaka', NULL, NULL, '2026-08-05T12:00:00Z', 'obs:fixture-a:author-1', 'accepted');

INSERT INTO citation (citation_id, citing_work_id, citing_version_id, cited_work_id, cited_version_id, locator, observed_at, confidence, source_observation_id, status) VALUES
  ('citation:a-to-b', 'pg:01H-WORK-A', 'wv:work-a:v1', 'pg:01H-WORK-B', 'wv:work-b:v2', 'references[3]', '2026-08-05T12:00:00Z', 1.0, 'obs:fixture-a:work-1', 'accepted');

INSERT INTO work_dependency (dependency_id, work_id, work_version_id, depends_on_work_id, depends_on_version_id, dependency_type, requirement, valid_from, valid_to, observed_at, source_observation_id, status) VALUES
  ('dependency:a-on-b', 'pg:01H-WORK-A', 'wv:work-a:v1', 'pg:01H-WORK-B', 'wv:work-b:v2', 'software_library', '>=2.0', '2026-07-01', NULL, '2026-08-05T12:00:00Z', 'obs:fixture-a:work-1', 'accepted');

INSERT INTO work_locator (locator_id, work_id, work_version_id, locator_type, locator_value, content_sha256, access_state, valid_from, valid_to, source_observation_id) VALUES
  ('locator:work-a', 'pg:01H-WORK-A', 'wv:work-a:v1', 'url', 'https://example.invalid/work-a', NULL, 'open', '2026-07-01', NULL, 'obs:fixture-a:work-1'),
  ('locator:work-b', 'pg:01H-WORK-B', 'wv:work-b:v2', 'repository', 'example/graph-toolkit', '37ae18944d74c8590d4b8499e25bbe20edfd6eae550fce82875f77a61ce311c3', 'open', '2026-06-15', NULL, 'obs:fixture-a:work-2');

