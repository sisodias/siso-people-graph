# People Graph v3 requirement and verification traceability

**Contract:** `3.0.0-draft.1`  
**Brief:** `docs/architecture/people-graph-v3-agent-brief.md`  
**Machine-readable twin:** `schema/v3/design_provenance.json`

Status meanings:

- **implemented:** represented in DDL/sample/docs and covered by an executable test.
- **documented:** deliberately a policy or physical-design seam, not silently
  encoded as a default.
- **out of lane:** belongs to another exclusive path owner and is exposed through
  a compatibility seam.

## Requirement-to-artifact matrix

| ID | Requirement/invariant | Primary DDL or document | Fixture/test evidence | Status |
| --- | --- | --- | --- | --- |
| R-001 | Source and snapshot terms, rights, revision, digests, acquisition, observed time, removal duties | `ddl/10_source_observations.sql` | `sample/00_observations.sql`; `test_schema_core.py::test_rights_privacy_and_publication_coverage` | implemented |
| R-002 | Append-oriented source observations with native IDs and raw pointers | `ddl/10_source_observations.sql` | `test_schema_core.py::test_source_observations_and_identity_decisions_are_append_only` | implemented |
| R-003 | Canonical IDs independent of labels/handles; required entity kinds | `ddl/30_entities_and_search.sql` | synthetic person/org/work/venue/concept rows; `test_schema_core.py` | implemented |
| R-004 | Identifier scope, uniqueness, mutability, trust, authority, normalization, eligibility | `ddl/20_observation_semantics.sql`, `ddl/30_entities_and_search.sql` | `test_schema_identity.py::test_unique_identifiers_are_enforced_within_scope` | implemented |
| R-005 | First-class Works, versions, roles/order/time, venues, citations, dependencies, locators | `ddl/40_works.sql` | `test_schema_works.py::test_work_subtypes_roles_versions_citations_and_dependencies` | implemented |
| R-006 | Identity candidates, positive/negative evidence, decisions, conflicts, clusters, redirects, undo | `ddl/60_evidence_and_identity.sql` | conflict and reversal tests in `test_schema_identity.py` | implemented |
| R-007 | Generic evidence-backed assertions with value/object, confidence, status, time, method, authority | `ddl/60_evidence_and_identity.sql`, `ddl/70_assertions_relationships.sql` | assertion fixtures; model-provenance test | implemented |
| R-008 | Typed temporal relationships | `ddl/70_assertions_relationships.sql` | `relationship:zoe-lab`; foreign-key/integrity tests | implemented |
| R-009 | Aliases and Unicode-safe search | `ddl/30_entities_and_search.sql` | `test_schema_core.py::test_unicode_and_alias_search_preserve_non_latin_text` | implemented |
| R-010 | Rights/privacy/publication at source, Work, evidence, and claim layers | `ddl/00_metadata_policy.sql` plus affected modules | `test_schema_core.py::test_rights_privacy_and_publication_coverage` | implemented |
| R-011 | Named projections with method/version/scope/as-of/input/uncertainty | `ddl/80_projections.sql` | `test_schema_works.py::test_projections_are_named_versioned_scoped_and_uncertain` | implemented |
| R-012 | Exact `pg-observation-0.1` receipt and mapping, no canonical ID | `ddl/10_source_observations.sql`; `observation-envelope-mapping.md` | `test_schema_core.py::test_envelope_import_cannot_assign_a_canonical_id` | implemented |
| R-013 | No silent name merge | entity and identity separation across `ddl/30*` and `ddl/60*` | envelope rejection, explicit candidate/decision fixture | implemented |
| R-014 | Handles are aliases; stable platform IDs are identifiers | `identifier_scheme`, `entity_alias`, `entity_identifier` | colliding mutable handle test | implemented |
| R-015 | Company, location, topic, biography, real name are not unique IDs | `ddl/20_observation_semantics.sql`; architecture invariant | provenance manifest and identifier semantics test | implemented |
| R-016 | Every accepted fact has provenance and observed time | evidence/assertion/relationship/contribution tables | foreign keys, fixture joins, model-provenance test | implemented |
| R-017 | Corrections and merges reversible while observations survive | status events; append-only decisions; temporal memberships/redirects | `test_identity_merge_can_be_reversed_without_losing_sources` | implemented |
| R-018 | Source vocabularies namespaced; crosswalks explicit | `ddl/50_vocabularies.sql` | `test_vocabularies_remain_namespaced_and_crosswalks_explicit` | implemented |
| R-019 | A Work is not only a title on a person edge | `ddl/40_works.sql` | Work/version/contribution test | implemented |
| R-020 | Model inference never masquerades as source observation | `evidence` constraints and assertion model lineage | `test_model_output_is_explicit_and_not_source_evidence` | implemented |
| R-021 | Rebuild from source; never rewrite current production asset | architecture rebuild section; handoff | manifest/journal consistency tests | documented |
| R-022 | Existing v2 files untouched; additive owned paths only | branch diff and handoff | PR changed-file inspection | implemented |
| R-023 | Offline synthetic tests | `tests/schema_v3/**` | `python3 tests/schema_v3/run.py` | implemented |
| R-024 | Diagrams, examples, rejected alternatives, scale, compatibility limits | `docs/architecture/people-graph-v3.md` | documentation/provenance tests | implemented |
| R-025 | Exact public reasoning and source record | agent brief, source ledger, design journal, this matrix | `test_design_provenance.py` | implemented |

## Decision-to-test matrix

| Decision | Executable checks |
| --- | --- |
| D-001 additive rebuild | manifest enumerates only new v3 modules; no v2 path in owned artifact set |
| D-002 immutable observations | update/delete triggers tested |
| D-003 opaque IDs | envelope cannot carry canonical ID; entity IDs are fixture-assigned, not label-derived |
| D-004 identifier semantics | scoped uniqueness and mutable collision tests |
| D-005 reversible identity | open-conflict rejection and undo-preserves-source tests |
| D-006 first-class Works | Work kind trigger plus role/version/citation/dependency test |
| D-007 evidence/assertion/relationship split | foreign keys and model-evidence test |
| D-008 namespaced vocabularies | duplicate-local-ID and explicit-crosswalk test |
| D-009 Unicode preservation | diacritic, Japanese, and non-Latin search test |
| D-010 policy state | policy coverage and invalid-rights rejection test |
| D-011 named projections | unique method version, scope, value, uncertainty test |
| D-012 envelope stops before canonicalization | canonical-field rejection test |
| D-013 source reconstruction | ordered manifests and fresh in-memory build test |
| D-014 physical layout deferred | documented seam; no sharding assumption in DDL |
| D-015 capability adapters | documented out-of-lane seam; no `ask.py` modification |
| D-016 synthetic-only fixtures | sample paths and provenance manifest exclude production assets |

## Validation environment

The recorded follow-up validation environment is Python 3.13.5 with SQLite
3.46.1, JSON functions available, and FTS5 enabled. The DDL target remains
SQLite 3.38+; this run does not prove behavior on every supported patch version.

## Honest coverage limits

The tests prove relational and contract invariants on synthetic data. They do
not prove full-scale performance, identity precision, legal sufficiency,
production source coverage, source-specific deletion compliance, or migration
parity. Those require source pilots and integration/build/query lanes.
