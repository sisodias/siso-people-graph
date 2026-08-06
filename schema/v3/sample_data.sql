-- Synthetic People Graph v3 SQLite CLI manifest.
-- Apply after people_graph_v3.sql from the repository root.
.bail on
.read schema/v3/sample/00_observations.sql
.read schema/v3/sample/10_entities_and_works.sql
.read schema/v3/sample/20_evidence_and_identity.sql
.read schema/v3/sample/30_claims_relationships_projections.sql
