-- People Graph v3 SQLite CLI manifest.
-- Run from the repository root:
--   sqlite3 /tmp/people-v3.sqlite < schema/v3/people_graph_v3.sql
.bail on
.read schema/v3/ddl/00_metadata_policy.sql
.read schema/v3/ddl/10_source_observations.sql
.read schema/v3/ddl/20_observation_semantics.sql
.read schema/v3/ddl/30_entities_and_search.sql
.read schema/v3/ddl/40_works.sql
.read schema/v3/ddl/50_vocabularies.sql
.read schema/v3/ddl/60_evidence_and_identity.sql
.read schema/v3/ddl/70_assertions_relationships.sql
.read schema/v3/ddl/80_projections.sql
