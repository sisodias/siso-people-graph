# People Graph v3 requirements traceability

This matrix maps the Prompt 3 contract to concrete files, schema objects, and
executable checks. “Covered” means the draft contains a logical model and/or a
fixture test; it does not imply production-scale validation.

## Required model

| Requirement | Implementation | Executable evidence | Status/limit |
| --- | --- | --- | --- |
| Source and snapshot terms, rights, revisions, digests, acquisition, observation time, removal obligations | `source`, `source_snapshot`; `ddl/10_source_observations.sql` | core schema/sample apply; rights coverage | Covered logically; no real source manifest tested. |
| Append-oriented source observations with native IDs and raw pointers | `observation_envelope_receipt`, `source_observation`, `observation_status_event` | append-only test; orphan FK test | Covered; retention policy remains source-specific. |
| Opaque canonical entities for person, organisation, account, pseudonym, Work, event, venue, place, concept | `entity`; `ddl/30_entities_and_search.sql` | sample contains person, organisation, Work, venue, concept | Covered; ID generator is outside DDL. |
| Identifier scope, uniqueness, mutability, trust, authority | `identifier_scheme`, `observation_identifier`, `entity_identifier` | scoped-unique and mutable-collision tests | Covered; safe scheme policy is not chosen. |
| First-class Works, versions, roles/order/time, venues, citations, dependencies, locators | `work*`, `venue`, `contribution`, `citation`, `work_dependency`, `work_locator` | Work semantics test | Covered with synthetic article/software examples. |
| Identity candidates, evidence, decisions, conflicts, clusters, redirects, reversibility | `identity_*`, `entity_redirect` | conflict-block and reversal tests | Covered logically; clustering algorithm is external. |
| Evidence-backed assertions with entity/value objects, confidence, status, valid/observed time, method, authority | `evidence`, `assertion`, `assertion_evidence`, `assertion_relation` | model provenance test; fixture accepted/proposed assertions | Covered; extraction/review UI is external. |
| Typed temporal relationships | `relationship_type`, `relationship`, `relationship_evidence` | fixture relationship and FK/integrity checks | Covered; domain type catalog is not populated. |
| Aliases and Unicode-safe search | `entity_alias`, `entity_search`, FTS maintenance triggers | Unicode/alias search test | Covered for tested FTS5 runtime; not locale morphology. |
| Rights/privacy/publication at source, Work, evidence, claim layers | policy definition tables and required FKs | rights/privacy/publication coverage test | Covered as state fields; adjudication is external. |
| Named projections with method/version/scope instead of universal score | `projection_definition`, `projection_run`, `projection_value` | projection semantics test | Covered; no production projection implemented. |

## Interim exchange contract

| Envelope requirement | Mapping | Guard/test |
| --- | --- | --- |
| `pg-observation-0.1` exact version | receipt `envelope_version`; schema metadata | `CHECK` and canonical-ID rejection test |
| source snapshot/native record ID/times/terms/rights/hash | receipt + snapshot + observation columns | JSON checks, FKs, hash checks |
| subject kind/native ID/label/attributes | `source_observation` | allowed kind and `json_valid` checks |
| identifiers with scope/stability/uniqueness/literal evidence | `observation_identifier` | identifier-scheme FK and enum checks |
| contributions | `observation_contribution` | source observation FKs |
| relationships | `observation_relationship` | source observation FKs |
| evidence | `observation_evidence_item` then `evidence` after reviewed materialization | evidence-kind/model constraints |
| raw pointer | `source_observation.raw_pointer` | required value; status event can revoke pointer |
| envelope never assigns canonical ID | no entity FK in receipt/observation; JSON path checks | `test_envelope_import_cannot_assign_a_canonical_id` |

## Invariants

| Invariant | Enforcement | Test/documentation |
| --- | --- | --- |
| No silent name merge | import layer has no canonical ID; entities separate; identity requires candidate/decision | canonical-ID rejection; decision log D-002/D-003 |
| Handles are aliases; stable platform IDs are identifiers | alias table plus registered scheme semantics | mutable collision test; D-004 |
| Company/location/topic/biography/real name are attributes, not unique IDs | identifier registry requires explicit semantics; docs forbid registration as global unique | D-004; schema comments; independent review IR-04 |
| Every accepted fact has provenance and observed time | assertion/relationship/evidence FKs and required time/method fields | fixture integrity and model provenance tests |
| Corrections/merges reversible; source survives | status events; append-only decisions; temporal memberships/redirects | reversal test |
| Source vocabularies namespaced; crosswalks explicit | vocabulary IDs/versions/term uniqueness/crosswalk rows | vocabulary test |
| Work not only a title string on person edge | canonical Work/version/contribution tables | Work semantics test |
| Model inference never masquerades as source observation | evidence kind/model fields and checks | model-output test |

## Deliverables and acceptance

| Contract item | Artifact/evidence |
| --- | --- |
| Architecture with diagrams, invariants, records/queries, alternatives, scale, compatibility | `docs/architecture/people-graph-v3.md` plus this audit packet |
| Versioned schema | `schema/v3/ddl/*.sql`, manifest, metadata `3.0.0-draft.1` |
| Envelope mapping | `schema/v3/observation-envelope-mapping.md` |
| Synthetic schema tests | `tests/schema_v3/test_schema_*.py` — 13 tests |
| Provenance/audit tests | `test_design_provenance.py`, `test_audit_package.py` — 13 tests |
| Rebuild strategy; no production rewrite | architecture “Rebuild and migration”; D-001 |
| Tests pass offline | validation record: 13/13 under Python stdlib, SQLite 3.46.1 |
| Existing v2 untouched | original PR diff confined to 24 new owned-path files; audit additions remain owned-path only |
| Draft PR with exact title | `sisodias/siso-people-graph#3` |
| Handoff | `docs/handoffs/schema-v3.md` |

## Coverage gaps that remain honest

- production-scale performance, sharding, and query plans;
- source-specific rights adjudication and deletion execution;
- candidate generation, automatic acceptance policy, cluster canonical selection;
- real Book/scholarly/software/media envelope imports;
- query/API adapters and v2/v3 consumer parity;
- release packaging and deterministic full-build digest;
- locale-aware search/transliteration;
- production Work subtype boundaries.

Those gaps are assigned to integration seams rather than disguised as completed
features.
