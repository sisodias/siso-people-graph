# Schema inventory — People Graph v3

**Schema version:** `3.0.0-draft.1`  
**Logical tables:** 46 (including the `entity_search` virtual table)  
**FTS5 shadow tables:** 5  
**Explicit indexes:** 9  
**Triggers:** 15  
**Views:** 0 (the draft favors versioned query/projection layers over stored compatibility views).

## Module-to-object map

| Ordered module | Objects | Responsibility |
| --- | --- | --- |
| `00_metadata_policy.sql` | `schema_metadata`, `rights_state_definition`, `privacy_state_definition`, `publication_state_definition` | Schema identity and shared policy vocabularies. |
| `10_source_observations.sql` | `source`, `source_snapshot`, `observation_envelope_receipt`, `source_observation`, `observation_status_event` | Source control plane, immutable receipts/observations, and status events. |
| `20_observation_semantics.sql` | `identifier_scheme`, `observation_identifier`, `observation_contribution`, `observation_relationship`, `observation_evidence_item` | Source-native identifier, contribution, relationship, and evidence semantics. |
| `30_entities_and_search.sql` | `entity`, `entity_alias`, `entity_search`, `entity_identifier` | Opaque canonical entities, Unicode aliases/search, and accepted identifiers. |
| `40_works.sql` | `work`, `work_version`, `venue`, `work_venue`, `contribution`, `citation`, `work_dependency`, `work_locator` | First-class Work/version and production/citation/dependency/locator graph. |
| `50_vocabularies.sql` | `vocabulary`, `vocabulary_term`, `term_crosswalk` | Namespaced vocabularies and explicit evidence-backed mappings. |
| `60_evidence_and_identity.sql` | `evidence`, `identity_candidate`, `identity_candidate_evidence`, `identity_conflict`, `identity_decision`, `identity_cluster`, `identity_cluster_membership`, `entity_redirect` | Evidence and reversible identity review lineage. |
| `70_assertions_relationships.sql` | `assertion`, `assertion_evidence`, `assertion_relation`, `relationship_type`, `relationship`, `relationship_evidence` | Evidence-backed claims and typed temporal relations. |
| `80_projections.sql` | `projection_definition`, `projection_run`, `projection_value` | Named/versioned/scoped derived outputs and schema commit. |

## Explicit indexes

- `ix_entity_identifier_entity` on `entity_identifier`
- `ix_entity_kind` on `entity`
- `ix_entity_label` on `entity`
- `ix_observed_identifier_lookup` on `observation_identifier`
- `ix_relationship_object_time` on `relationship`
- `ix_relationship_subject_time` on `relationship`
- `uq_active_entity_redirect` on `entity_redirect`
- `uq_active_identity_membership` on `identity_cluster_membership`
- `uq_entity_identifier_unique_scope` on `entity_identifier`

## Triggers and enforced behavior

- `alias_search_delete` — Remove alias FTS row.
- `alias_search_insert` — Index an accepted alias.
- `alias_search_update` — Synchronize alias FTS row and review state.
- `entity_identifier_semantics` — Reject assignments that contradict registered uniqueness/mutability semantics.
- `entity_search_delete` — Remove canonical-label FTS row on entity delete.
- `entity_search_insert` — Index canonical label on entity insert.
- `entity_search_update` — Replace canonical-label FTS row on label update.
- `identity_accept_rejects_open_conflict` — Block acceptance while a candidate has an open conflict.
- `identity_decision_no_delete` — Identity decisions cannot be deleted.
- `identity_decision_no_update` — Identity decisions are append-only.
- `observation_envelope_no_delete` — Envelope receipts cannot be deleted.
- `observation_envelope_no_update` — Envelope receipts are append-only.
- `source_observation_no_delete` — Source observations cannot be deleted.
- `source_observation_no_update` — Source observations are append-only.
- `work_requires_work_entity` — Require Work specialization to reference an entity of kind work.

## Synthetic fixture row counts

Counts below are produced by applying all DDL and sample modules in lexical order. FTS shadow tables are omitted.

| Table | Rows |
| --- | ---: |
| `assertion` | 2 |
| `assertion_evidence` | 2 |
| `assertion_relation` | 0 |
| `citation` | 1 |
| `contribution` | 1 |
| `entity` | 7 |
| `entity_alias` | 2 |
| `entity_identifier` | 1 |
| `entity_redirect` | 1 |
| `entity_search` | 9 |
| `evidence` | 5 |
| `identifier_scheme` | 3 |
| `identity_candidate` | 1 |
| `identity_candidate_evidence` | 2 |
| `identity_cluster` | 1 |
| `identity_cluster_membership` | 2 |
| `identity_conflict` | 0 |
| `identity_decision` | 1 |
| `observation_contribution` | 1 |
| `observation_envelope_receipt` | 1 |
| `observation_evidence_item` | 1 |
| `observation_identifier` | 2 |
| `observation_relationship` | 1 |
| `observation_status_event` | 1 |
| `privacy_state_definition` | 5 |
| `projection_definition` | 1 |
| `projection_run` | 1 |
| `projection_value` | 1 |
| `publication_state_definition` | 5 |
| `relationship` | 1 |
| `relationship_evidence` | 1 |
| `relationship_type` | 1 |
| `rights_state_definition` | 8 |
| `schema_metadata` | 3 |
| `source` | 2 |
| `source_observation` | 7 |
| `source_snapshot` | 2 |
| `term_crosswalk` | 1 |
| `venue` | 1 |
| `vocabulary` | 2 |
| `vocabulary_term` | 2 |
| `work` | 2 |
| `work_dependency` | 1 |
| `work_locator` | 2 |
| `work_venue` | 1 |
| `work_version` | 2 |

## Requirement coverage

| Prompt requirement | Primary objects | Executable check |
| --- | --- | --- |
| Sources/snapshots, terms, rights, digests, removal | `source`, `source_snapshot`, observation/status tables | core policy and append-only tests |
| Opaque canonical entities and kinds | `entity`, `entity_alias`, `entity_identifier` | envelope canonical-ID rejection; Unicode search |
| Identifier semantics | `identifier_scheme`, observed/accepted identifier tables | scoped uniqueness and conflicting-ID tests |
| First-class Works and versions | Work module tables | Work/role/version/citation/dependency test |
| Reversible identity | candidate/evidence/conflict/decision/cluster/membership/redirect | conflict-block and undo tests |
| Evidence-backed assertions | `evidence`, assertion tables | model-output/source-evidence test |
| Typed temporal relationships | relationship type/edge/evidence | fixture foreign-key/integrity coverage |
| Namespaced vocabularies | vocabulary/term/crosswalk | vocabulary separation test |
| Named projections | projection definition/run/value | scoped/uncertain projection test |
| Audit reconstruction | provenance JSON, source/decision/worklog docs, SHA manifest | audit package tests |

## Deliberate absences

- No production migration script or automatic v2 mutation.
- No hard-coded identity threshold or canonical-selection algorithm.
- No arbitrary SQL/query API, write endpoint, or production source adapter.
- No raw corpus, SQLite asset, compressed payload, credential, or private topology.
- No physical partitioning commitment before scale measurements.
