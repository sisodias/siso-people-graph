# People Graph v3 schema inventory

**Schema version:** `3.0.0-draft.1`  
**DDL modules:** 9  
**Synthetic sample modules:** 4  
**Offline tests:** 26 (13 schema invariants + 13 provenance/audit checks)

This is a reviewer-oriented inventory. The machine-readable equivalent is
[`traceability.json`](traceability.json).

## Ordered DDL modules

### `00_metadata_policy.sql`

Tables: `schema_metadata`, `rights_state_definition`,
`privacy_state_definition`, `publication_state_definition`.

Purpose: schema/envelope version receipt and shared governed policy vocabularies.

### `10_source_observations.sql`

Tables: `source`, `source_snapshot`, `observation_envelope_receipt`,
`source_observation`, `observation_status_event`.

Triggers: no update/delete on envelope receipts and source observations.

Purpose: source control plane, replayable receipts, append-oriented observations,
and removal/tombstone events.

### `20_observation_semantics.sql`

Tables: `identifier_scheme`, `observation_identifier`,
`observation_contribution`, `observation_relationship`,
`observation_evidence_item`.

Index: observed identifier lookup.

Purpose: source-native semantics before canonicalization.

### `30_entities_and_search.sql`

Tables: `entity`, `entity_alias`, `entity_identifier`.

Virtual table: `entity_search` using FTS5 `unicode61 remove_diacritics 2`.

Triggers: entity/alias FTS synchronization; identifier-scheme semantics check.

Indexes: entity kind/label, entity identifier lookup, partial unique accepted
identifier within declared scope.

Purpose: opaque canonical entities, aliases, identifiers, and discovery search.

### `40_works.sql`

Tables: `work`, `work_version`, `venue`, `work_venue`, `contribution`,
`citation`, `work_dependency`, `work_locator`.

Trigger: a `work` row must specialize an entity whose kind is `work`.

Purpose: Works and their versioned attribution/evidence graph.

### `50_vocabularies.sql`

Tables: `vocabulary`, `vocabulary_term`, `term_crosswalk`.

Purpose: source namespaces and explicit evidenced crosswalks.

### `60_evidence_and_identity.sql`

Tables: `evidence`, `identity_candidate`, `identity_candidate_evidence`,
`identity_conflict`, `identity_decision`, `identity_cluster`,
`identity_cluster_membership`, `entity_redirect`.

Triggers: identity decisions append-only; acceptance blocked by open conflict.

Indexes: one active cluster membership per entity; one active redirect per source
entity.

Purpose: evidence, review lineage, reversible identity materialization.

### `70_assertions_relationships.sql`

Tables: `assertion`, `assertion_evidence`, `assertion_relation`,
`relationship_type`, `relationship`, `relationship_evidence`.

Indexes: temporal relationship lookups by subject and object.

Purpose: evidence-backed claims and typed valid-time/observed-time relations.

### `80_projections.sql`

Tables: `projection_definition`, `projection_run`, `projection_value`.

Purpose: named/versioned/scoped derived outputs with input digest and uncertainty.

## Synthetic fixture inventory

- 2 sources and 2 snapshots;
- 1 exact envelope receipt;
- 7 source observations and 2 observed identifiers;
- 7 canonical entities, 2 aliases, and 1 accepted entity identifier;
- 2 Works and 2 Work versions;
- 1 contribution, 1 citation, 1 dependency, 1 venue relation, and 2 locators;
- 5 evidence records spanning literal source, source span, manual review, and
  model output;
- 1 identity candidate, decision, cluster, redirect, and 2 memberships;
- 2 namespaced vocabularies, 2 terms, and 1 crosswalk;
- 2 assertions, 1 typed temporal relationship;
- 1 projection definition/run/value with uncertainty.

## Constraint map

| Invariant | Mechanism |
| --- | --- |
| Envelope version and source/native IDs match JSON | receipt `CHECK` constraints |
| No canonical ID in envelope | JSON-path `CHECK` constraints and test |
| Source observations/decisions append-only | `BEFORE UPDATE/DELETE` abort triggers |
| Hashes are lower-case SHA-256 shape | length and hex `CHECK` constraints |
| Accepted unique identifiers do not collide in scope | partial unique index |
| Scheme semantics match accepted identifier declaration | trigger |
| Open identity conflict blocks acceptance | trigger |
| One active membership/redirect | partial unique indexes |
| Work specialization uses Work entity | trigger |
| Assertion uses either entity object or JSON value | exclusive-or `CHECK` |
| Model output carries model/version/input digest | evidence/assertion checks |
| Temporal intervals are ordered | `valid_to >= valid_from` checks |
| Vocabularies remain namespaced | unique namespace/version and term IDs |
| Projections are named/versioned and input-addressed | uniqueness plus method/input hashes |

## Test files

- `test_schema_core.py` — application, FKs, envelope boundary, append-only,
  policy coverage, Unicode search.
- `test_schema_identity.py` — scoped identifiers, stable-ID conflict gate,
  reversible identity.
- `test_schema_works.py` — Works/contributions, vocabularies, model evidence,
  projections.
- `test_design_provenance.py` — source hashes, decision/requirement completeness, owned-path safety, runtime declarations, public audit packet, and cross-manifest consistency.
- `test_audit_package.py` — exact prompt receipt, stable decision IDs, full-file SHA-256 verification, payload/path safety, and relative Markdown-link integrity.

## Deliberately external responsibilities

ID generation, source acquisition, rights adjudication, candidate generation,
confidence calibration, canonical selection, cluster application/undo commands,
bulk build/sharding, query/API behavior, projection execution, and production
release packaging are interfaces for their owning lanes, not hidden schema logic.
