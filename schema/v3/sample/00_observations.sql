-- Synthetic, public-safe fixture for people_graph_v3.sql.
-- It demonstrates observation import, canonical entities, a reversible identity
-- decision, first-class Works, evidence-backed claims, temporal relationships,
-- Unicode aliases, namespaced topics and a named projection.

PRAGMA foreign_keys = ON;
BEGIN;

INSERT INTO source (source_id, source_namespace, name, owner, homepage_uri, default_terms_uri, default_terms_revision, default_rights_state, default_privacy_state, default_publication_state, acquisition_method, created_at) VALUES
  ('fixture-a', 'fixture_a', 'Fixture Source A', 'SISO test fixtures', 'fixture://a', 'fixture://a/terms', 'fixture-terms-1', 'open_data', 'public', 'public', 'offline_fixture', '2026-08-06T00:00:00Z'),
  ('fixture-b', 'fixture_b', 'Fixture Source B', 'SISO test fixtures', 'fixture://b', 'fixture://b/terms', 'fixture-terms-1', 'public_metadata', 'public', 'public', 'offline_fixture', '2026-08-06T00:00:00Z');

INSERT INTO source_snapshot (snapshot_id, source_id, source_native_revision, snapshot_at, retrieved_at, terms_revision, rights_state, privacy_state, publication_state, acquisition_method, acquisition_locator_class, content_sha256, expected_record_count, parent_snapshot_id, deletion_policy, tombstone_policy, retention_until) VALUES
  ('fixture-a-2026-08-06', 'fixture-a', 'revision-1', '2026-08-05T12:00:00Z', '2026-08-06T00:00:00Z', 'fixture-terms-1', 'open_data', 'public', 'public', 'offline_fixture', 'tracked_fixture', '1c744868dfe7d1c5585e99b11ac458a4bd4fae446ce3b30d170ae76ad4b9826d', 6, NULL, 'replace raw fixture on valid removal request', 'append tombstone event', NULL),
  ('fixture-b-2026-08-06', 'fixture-b', 'revision-9', '2026-08-05T14:00:00Z', '2026-08-06T00:10:00Z', 'fixture-terms-1', 'public_metadata', 'public', 'public', 'offline_fixture', 'tracked_fixture', 'd5558a01e179b69fe8a338fa181dcbb453000c098fbcc35a097a3bd53b461533', 1, NULL, 'replace raw fixture on valid removal request', 'append tombstone event', NULL);

INSERT INTO observation_envelope_receipt (envelope_receipt_id, envelope_version, source_id, snapshot_id, record_native_id, payload_json, payload_sha256, received_at) VALUES
  ('env:fixture-a:author-1', 'pg-observation-0.1', 'fixture-a', 'fixture-a-2026-08-06', 'author-1', '{"contributions":[{"order":1,"role":"author","work_native_id":"work-1"}],"envelope_version":"pg-observation-0.1","evidence":[{"field":"author.orcid","locator":"fixture://fixture-a/author-1"}],"identifiers":[{"evidence":"author.orcid","scheme":"orcid","scope":"global","stability":"stable","uniqueness":"unique","value":"0000-0002-1825-0097"}],"raw_pointer":"fixtures/fixture-a/author-1.json","relationships":[{"object_native_id":"org-1","predicate":"affiliated_with"}],"source":{"observed_at":"2026-08-05T12:00:00Z","payload_sha256":"4e2f1565da5563c3a010577c763901263c2999b5923cd421af9ffa767ec6662c","record_native_id":"author-1","retrieved_at":"2026-08-06T00:00:00Z","rights_state":"open_data","snapshot_id":"fixture-a-2026-08-06","source_id":"fixture-a","terms_revision":"fixture-terms-1"},"subject":{"attributes":{"affiliation_label":"Example Research Lab"},"kind":"person","label":"Dr. Zoë Tanaka","source_native_id":"author-1"}}', '16327553e309a625ab950f26282c822cc6dcc91fbe96e9fb8ecafe6ed9d5f818', '2026-08-06T00:00:01Z');

INSERT INTO source_observation (observation_id, snapshot_id, envelope_receipt_id, record_native_id, observed_at, retrieved_at, subject_kind, subject_native_id, label, attributes_json, raw_pointer, payload_sha256, rights_state, privacy_state, publication_state) VALUES
  ('obs:fixture-a:author-1', 'fixture-a-2026-08-06', 'env:fixture-a:author-1', 'author-1', '2026-08-05T12:00:00Z', '2026-08-06T00:00:00Z', 'person', 'author-1', 'Dr. Zoë Tanaka', '{"affiliation_label": "Example Research Lab"}', 'fixtures/fixture-a/author-1.json', '4e2f1565da5563c3a010577c763901263c2999b5923cd421af9ffa767ec6662c', 'open_data', 'public', 'public'),
  ('obs:fixture-b:author-9', 'fixture-b-2026-08-06', NULL, 'author-9', '2026-08-05T14:00:00Z', '2026-08-06T00:10:00Z', 'person', 'author-9', '田中 ゾーイ', '{"website": "https://example.invalid/zoe"}', 'fixtures/fixture-b/author-9.json', '1d1aa6476264a313478c8fd6370964dd19bb10088899705a2081809ec22ecf71', 'public_metadata', 'public', 'public'),
  ('obs:fixture-a:work-1', 'fixture-a-2026-08-06', NULL, 'work-1', '2026-08-05T12:00:00Z', '2026-08-06T00:00:00Z', 'work', 'work-1', 'Evidence Graphs in Practice', '{"type": "article"}', 'fixtures/fixture-a/work-1.json', '6681a48acac21248e6d5d98a3acda1ad67df349f56c23a5ace436cc3d3a5d0df', 'open_data', 'public', 'public'),
  ('obs:fixture-a:work-2', 'fixture-a-2026-08-06', NULL, 'work-2', '2026-08-05T12:00:00Z', '2026-08-06T00:00:00Z', 'work', 'work-2', 'Example Graph Toolkit', '{"type": "software"}', 'fixtures/fixture-a/work-2.json', 'c3be29a890c175a1ae8a5b756fac8f66405713943e00f4d7c995bd417ef3463f', 'open_data', 'public', 'public'),
  ('obs:fixture-a:venue-1', 'fixture-a-2026-08-06', NULL, 'venue-1', '2026-08-05T12:00:00Z', '2026-08-06T00:00:00Z', 'venue', 'venue-1', 'Example Systems Conference', '{"type": "conference"}', 'fixtures/fixture-a/venue-1.json', 'a227a1e2f8f839351af1a4b7ae7a7fc66c912da805a686ac356a4610a40dbaec', 'open_data', 'public', 'public'),
  ('obs:fixture-a:org-1', 'fixture-a-2026-08-06', NULL, 'org-1', '2026-08-05T12:00:00Z', '2026-08-06T00:00:00Z', 'organisation', 'org-1', 'Example Research Lab', '{"country": "JP"}', 'fixtures/fixture-a/org-1.json', '0429bc428eacea10ca356d9c67dad58c7d00a672d6740508f4b080cd0561b819', 'open_data', 'public', 'public'),
  ('obs:fixture-a:concept-1', 'fixture-a-2026-08-06', NULL, 'concept-1', '2026-08-05T12:00:00Z', '2026-08-06T00:00:00Z', 'concept', 'concept-1', 'Knowledge graphs', '{"vocabulary": "fixture-topics"}', 'fixtures/fixture-a/concept-1.json', '5c692b53f6a31ef88115d136c663aa055541f3558565400c7da82ea871a6b879', 'open_data', 'public', 'public');

INSERT INTO observation_status_event (status_event_id, observation_id, status, effective_at, reason, authority, request_locator) VALUES
  ('status:obs-a-author-1:active', 'obs:fixture-a:author-1', 'active', '2026-08-06T00:00:01Z', 'initial import', 'fixture-loader', NULL);

INSERT INTO identifier_scheme (scheme_id, namespace, label, scope_policy, uniqueness_class, mutability_class, trust_class, source_authority, auto_resolution_eligible, normalization_method, definition_version, effective_at, retired_at) VALUES
  ('orcid', 'orcid', 'ORCID', 'global', 'unique', 'stable', 'authority', 'ORCID', 1, 'lowercase-and-hyphenate', '1', '2026-08-06T00:00:00Z', NULL),
  ('github_numeric_account_id', 'github', 'GitHub numeric account ID', 'source', 'unique', 'stable', 'platform', 'GitHub', 1, 'decimal-string', '1', '2026-08-06T00:00:00Z', NULL),
  ('github_login', 'github', 'GitHub login', 'source', 'conditional', 'mutable', 'platform', 'GitHub', 0, 'unicode-casefold', '1', '2026-08-06T00:00:00Z', NULL);

INSERT INTO observation_identifier (observation_identifier_id, observation_id, scheme_id, value, normalized_value, scope_type, scope_ref, stability, uniqueness, literal_evidence) VALUES
  ('oid:fixture-a:orcid', 'obs:fixture-a:author-1', 'orcid', '0000-0002-1825-0097', '0000-0002-1825-0097', 'global', '', 'stable', 'unique', 'author.orcid'),
  ('oid:fixture-b:orcid', 'obs:fixture-b:author-9', 'orcid', '0000-0002-1825-0097', '0000-0002-1825-0097', 'global', '', 'stable', 'unique', 'profile.orcid');

INSERT INTO observation_contribution (observation_contribution_id, observation_id, work_native_id, contributor_native_id, role_namespace, role, ordinal, valid_from, valid_to, attributes_json, literal_evidence) VALUES
  ('oc:fixture-a:author-work', 'obs:fixture-a:author-1', 'work-1', 'author-1', 'fixture', 'author', 1, NULL, NULL, '{}', 'contributions[0]');

INSERT INTO observation_relationship (observation_relationship_id, observation_id, subject_native_id, predicate_namespace, predicate, object_native_id, valid_from, valid_to, attributes_json, literal_evidence) VALUES
  ('or:fixture-a:affiliation', 'obs:fixture-a:author-1', 'author-1', 'fixture', 'affiliated_with', 'org-1', '2024-01-01', NULL, '{}', 'relationships[0]');

INSERT INTO observation_evidence_item (observation_evidence_item_id, observation_id, evidence_kind, locator, evidence_json, generated_by_model, model_name, model_version, input_sha256) VALUES
  ('oe:fixture-a:orcid', 'obs:fixture-a:author-1', 'field', 'fixture://fixture-a/author-1#orcid', '{"field": "author.orcid"}', 0, NULL, NULL, NULL);

