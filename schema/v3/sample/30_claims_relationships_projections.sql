INSERT INTO assertion (assertion_id, subject_entity_id, predicate_namespace, predicate, object_entity_id, value_json, topic_term_id, scope_json, confidence, status, valid_from, valid_to, observed_at, extraction_method, model_name, model_version, input_sha256, deciding_authority, primary_evidence_id, rights_state, privacy_state, publication_state) VALUES
  ('assertion:zoe-affiliation', 'pg:01H-PERSON-A', 'fixture', 'affiliated_with', 'pg:01H-ORG-A', NULL, 'term:fixture:kg', '{}', 1.0, 'accepted', '2024-01-01', NULL, '2026-08-05T12:00:00Z', 'literal_field', NULL, NULL, NULL, 'fixture-source', 'ev:source-affiliation', 'open_data', 'public', 'public'),
  ('assertion:zoe-topic-model', 'pg:01H-PERSON-A', 'fixture', 'has_research_topic', 'pg:01H-CONCEPT-A', NULL, 'term:fixture:kg', '{}', 0.72, 'proposed', NULL, NULL, '2026-08-06T01:20:00Z', 'model_classification', 'fixture-classifier', '0.1', 'e3fc46673d6079c086686557034bfd0316f85dda7e8325874cbc01f9a1878dd1', NULL, 'ev:model-topic', 'open_data', 'public', 'internal');

INSERT INTO assertion_evidence (assertion_id, evidence_id, role) VALUES
  ('assertion:zoe-affiliation', 'ev:source-affiliation', 'supports'),
  ('assertion:zoe-topic-model', 'ev:model-topic', 'supports');

INSERT INTO relationship_type (relationship_type_id, namespace, local_name, inverse_type_id, temporal_semantics, description) VALUES
  ('reltype:fixture:affiliated_with', 'fixture', 'affiliated_with', NULL, 'interval', 'Person or account affiliation');

INSERT INTO relationship (relationship_id, subject_entity_id, relationship_type_id, object_entity_id, valid_from, valid_to, observed_at, confidence, review_state, primary_evidence_id, source_observation_id, extraction_method) VALUES
  ('relationship:zoe-lab', 'pg:01H-PERSON-A', 'reltype:fixture:affiliated_with', 'pg:01H-ORG-A', '2024-01-01', NULL, '2026-08-05T12:00:00Z', 1.0, 'accepted', 'ev:source-affiliation', 'obs:fixture-a:author-1', 'literal_field');

INSERT INTO relationship_evidence (relationship_id, evidence_id, role) VALUES
  ('relationship:zoe-lab', 'ev:source-affiliation', 'supports');

INSERT INTO projection_definition (projection_definition_id, name, version, purpose, output_semantics, method_card_uri, method_sha256, created_at) VALUES
  ('projection:def:topic-affinity', 'fixture-topic-affinity', '0.1', 'Demonstrate a named projection', 'Per-entity affinity within fixture_topics only; not a universal expertise score', 'docs/architecture/people-graph-v3.md#named-projections', '31df8b57bc8822f5966695d69608feb6672f8f474d007fea76f4958f79745961', '2026-08-06T01:30:00Z');

INSERT INTO projection_run (projection_run_id, projection_definition_id, as_of, source_scope_json, parameters_json, input_digest, uncertainty_method, started_at, completed_at, status, rights_state, publication_state) VALUES
  ('projection:run:topic-affinity', 'projection:def:topic-affinity', '2026-08-06T00:00:00Z', '{"snapshots": ["fixture-a-2026-08-06"]}', '{"min_evidence": 1}', '7c6e28c960fa893c3baaddc7a30619f3d22c7ecf92a7e8def77af5f34ada0b01', 'fixture interval', '2026-08-06T01:30:00Z', '2026-08-06T01:30:01Z', 'complete', 'open_data', 'public');

INSERT INTO projection_value (projection_value_id, projection_run_id, subject_entity_id, object_entity_id, metric_name, value_json, uncertainty_json) VALUES
  ('projection:value:zoe-kg', 'projection:run:topic-affinity', 'pg:01H-PERSON-A', 'pg:01H-CONCEPT-A', 'topic_affinity', '{"value": 0.42}', '{"low": 0.2, "high": 0.7}');

COMMIT;
