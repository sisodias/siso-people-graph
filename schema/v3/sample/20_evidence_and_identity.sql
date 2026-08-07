INSERT INTO evidence (evidence_id, observation_id, evidence_kind, locator, excerpt, excerpt_sha256, observed_at, extraction_method, model_name, model_version, input_sha256, generated_by_model, rights_state, privacy_state, publication_state) VALUES
  ('ev:source-a-person', 'obs:fixture-a:author-1', 'source_record', 'fixture://fixture-a/author-1', NULL, NULL, '2026-08-05T12:00:00Z', 'literal_record', NULL, NULL, NULL, 0, 'open_data', 'public', 'public'),
  ('ev:source-b-person', 'obs:fixture-b:author-9', 'source_record', 'fixture://fixture-b/author-9', NULL, NULL, '2026-08-05T14:00:00Z', 'literal_record', NULL, NULL, NULL, 0, 'public_metadata', 'public', 'public'),
  ('ev:manual-identity', NULL, 'manual_review', 'fixture://review/identity-1', 'reviewed same ORCID and website', '7a06893061ef4b96a4c8a91600f0cb8f9187030e035025d5a68a2eb0e04a6ea4', '2026-08-06T01:10:00Z', 'manual_review', NULL, NULL, NULL, 0, 'public_metadata', 'public', 'internal'),
  ('ev:source-affiliation', 'obs:fixture-a:author-1', 'source_span', 'fixture://fixture-a/author-1#affiliation', 'Example Research Lab', 'b793ba8a07674d8d005d8e89a94594cda710969a8aefadd23b2073d6fd0696e0', '2026-08-05T12:00:00Z', 'literal_field', NULL, NULL, NULL, 0, 'open_data', 'public', 'public'),
  ('ev:model-topic', NULL, 'model_output', 'fixture://model/topic-1', NULL, NULL, '2026-08-06T01:20:00Z', 'classifier', 'fixture-classifier', '0.1', 'e3fc46673d6079c086686557034bfd0316f85dda7e8325874cbc01f9a1878dd1', 1, 'open_data', 'public', 'internal');

INSERT INTO vocabulary (vocabulary_id, namespace, version, source_id, label, rights_state, publication_state) VALUES
  ('vocab:fixture-topics', 'fixture_topics', '1', 'fixture-a', 'Fixture Topics', 'open_data', 'public'),
  ('vocab:curated-topics', 'siso_curated', '1', NULL, 'SISO Curated Topics', 'public_metadata', 'public');

INSERT INTO vocabulary_term (term_id, vocabulary_id, source_local_id, label, description, source_observation_id) VALUES
  ('term:fixture:kg', 'vocab:fixture-topics', 'concept-1', 'Knowledge graphs', 'Source-native concept', 'obs:fixture-a:concept-1'),
  ('term:curated:kg', 'vocab:curated-topics', 'knowledge-graphs', 'Knowledge graphs', 'Curated navigation term', 'obs:fixture-a:concept-1');

INSERT INTO term_crosswalk (crosswalk_id, from_term_id, to_term_id, mapping_type, confidence, evidence_id, method_version, status) VALUES
  ('crosswalk:fixture-curated', 'term:fixture:kg', 'term:curated:kg', 'exact', 0.95, 'ev:source-affiliation', 'manual-crosswalk-1', 'accepted');

INSERT INTO identity_candidate (candidate_id, entity_a, entity_b, method_name, method_version, confidence, review_state, conflict_summary, created_at, created_by, rights_state, publication_state) VALUES
  ('identity-candidate:zoe', 'pg:01H-PERSON-A', 'pg:01H-PERSON-B', 'shared_stable_identifier', '1.0', 0.999, 'decided', NULL, '2026-08-06T01:05:00Z', 'fixture-matcher', 'public_metadata', 'internal');

INSERT INTO identity_candidate_evidence (candidate_id, evidence_id, polarity, weight, note) VALUES
  ('identity-candidate:zoe', 'ev:source-a-person', 'positive', 1.0, 'ORCID literal in source A'),
  ('identity-candidate:zoe', 'ev:source-b-person', 'positive', 1.0, 'Same ORCID literal in source B');

INSERT INTO identity_decision (decision_id, candidate_id, decision, decision_evidence_id, decided_by, decided_at, rationale, supersedes_decision_id, rights_state, publication_state) VALUES
  ('identity-decision:zoe-accept', 'identity-candidate:zoe', 'accepted', 'ev:manual-identity', 'fixture-reviewer', '2026-08-06T01:10:00Z', 'Two literal ORCID observations and manual website check', NULL, 'public_metadata', 'internal');

INSERT INTO identity_cluster (cluster_id, canonical_entity_id, created_by_decision_id, created_at, status) VALUES
  ('cluster:zoe', 'pg:01H-PERSON-A', 'identity-decision:zoe-accept', '2026-08-06T01:10:00Z', 'active');

INSERT INTO identity_cluster_membership (membership_id, cluster_id, entity_id, decision_id, valid_from, valid_to) VALUES
  ('membership:zoe-a', 'cluster:zoe', 'pg:01H-PERSON-A', 'identity-decision:zoe-accept', '2026-08-06T01:10:00Z', NULL),
  ('membership:zoe-b', 'cluster:zoe', 'pg:01H-PERSON-B', 'identity-decision:zoe-accept', '2026-08-06T01:10:00Z', NULL);

INSERT INTO entity_redirect (redirect_id, from_entity_id, to_entity_id, decision_id, valid_from, valid_to) VALUES
  ('redirect:zoe-b-a', 'pg:01H-PERSON-B', 'pg:01H-PERSON-A', 'identity-decision:zoe-accept', '2026-08-06T01:10:00Z', NULL);

