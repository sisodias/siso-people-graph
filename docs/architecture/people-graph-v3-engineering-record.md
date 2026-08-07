# People Graph v3 public engineering record

**Branch:** `pg/v3-ontology-schema-20260806`  
**Base audited:** `de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Original implementation commit:** `2f66fbe1f4523399463d9e1ff8971879a84f5b88`  
**Draft PR:** `sisodias/siso-people-graph#3`  
**Schema:** `3.0.0-draft.1`

This is a reproducible account of how the branch was produced. It records the
sequence, evidence, design transformations, commands, and limits. It intentionally
uses concise engineering rationale rather than private token-by-token chain-of-
thought.

## 1. Scope resolution

The assignment created a parallel lane with exclusive ownership of
`schema/v3/**`, `docs/architecture/**`, `tests/schema_v3/**`, and
`docs/handoffs/schema-v3.md`. Existing v2 schema, loaders, `ask.py`, root README,
shared configuration, production assets, and other lanes were out of bounds.

Resolved operating rules:

1. start from current main and treat it as evidence;
2. create a complete standalone proposal without waiting for another PR;
3. add new versioned files rather than rename or mutate v2;
4. use synthetic public-safe fixtures only;
5. make disagreements visible through handoff seams and explicit disputed
   decisions;
6. commit and open a draft PR rather than merge.

## 2. Source inspection

The exact sources and observations are in
[`people-graph-v3-evidence-ledger.md`](people-graph-v3-evidence-ledger.md).
Inspection focused on the smallest material set needed to answer the assignment:

- current People Graph README, v2 schema, rebuild loader, identity matcher, and
  query surface;
- Book Library contributor builder and graph loader;
- Great Library knowledge/data-plane boundary;
- official SQLite documentation for constraints, triggers, JSON, FTS5, partial
  indexes, and transactions.

The source review produced four concrete pressures:

- source-native and canonical identity are currently too close;
- normalized names are used as merge/key material;
- Works and some policy/provenance information are compressed into generic edges
  or JSON;
- identity claims, accepted facts, temporal relationships, and derived rankings
  do not share a complete evidence/decision lineage.

## 3. Requirement decomposition

The requested model was divided into independently reviewable layers before DDL
was written:

1. schema metadata and shared policy vocabularies;
2. source definitions, snapshots, receipts, observations, and status events;
3. observation-level identifiers, contributions, relationships, and evidence;
4. canonical entities, aliases, identifiers, and search;
5. Works, versions, venues, contributions, citations, dependencies, and locators;
6. namespaced vocabularies and explicit crosswalks;
7. evidence, identity candidates, conflicts, decisions, clusters, memberships,
   and redirects;
8. assertions and typed temporal relationships;
9. named projection definitions, runs, and values.

This decomposition became the ordered modules `00` through `80`. The order is
not cosmetic: later modules reference the policy and provenance layers created
before them.

## 4. Main design transformations

### 4.1 Source rows became immutable observations

Current loaders can materialize source-derived facts directly into canonical
rows. V3 instead preserves source snapshot/revision, source-native IDs, observed
and retrieval times, payload digest, rights/privacy/publication state, and a raw
pointer. Corrections append status events. This makes replay and legal removal
handling visible without rewriting history.

### 4.2 Canonical entities became independent decisions

A canonical entity receives an opaque ID that is not derived from a name, login,
platform, or source key. Source observations may exist without any entity. The
`pg-observation-0.1` receipt has checks that reject canonical IDs in the envelope.

### 4.3 Identifier semantics became registered data

The schema requires a scheme definition declaring scope, uniqueness, mutability,
trust class, authority, normalization version, and auto-resolution eligibility.
A trigger checks accepted entity identifiers against those semantics. A partial
unique index applies only to active, accepted identifiers declared unique in a
specific scope. Mutable aliases can collide without becoming merge evidence.

### 4.4 Works became first-class entities

A title string on `person_content` is insufficient for editions, releases,
translations, roles, venues, citations, dependencies, and locators. V3 therefore
specializes an entity of kind `work` and attaches versions and contributions.
The schema still preserves source-native Work observations before any canonical
Work decision.

### 4.5 Identity became candidate → evidence/conflict → decision → temporal cluster

The DDL does not encode a confidence threshold. It records method name/version,
positive or negative evidence, conflicts, review state, and append-only decisions.
An open conflict blocks acceptance. Applying an accepted decision creates
validity-bounded memberships and redirects; undo appends a revocation and closes
those intervals. Source observations and both entities survive.

### 4.6 Claims and relationships became evidence-bearing records

An accepted assertion must identify evidence, observed time, extraction method,
status, confidence, and deciding authority where applicable. Typed relationships
carry valid time and observed time separately. Model output records model/version
and input digest and remains distinguishable from literal source evidence.

### 4.7 Rankings became named projections

`rank_score`, tier, influence, expertise, centrality, and affinity depend on
method, source scope, time, and uncertainty. V3 stores projection definitions and
runs rather than a universal canonical person score.

## 5. Constraint strategy

The schema uses several enforcement layers:

- foreign keys for existence and provenance relationships;
- `CHECK` constraints for enums, valid JSON, hashes, confidence ranges, temporal
  ordering, and mutually exclusive assertion object/value shapes;
- append-only triggers for source receipts/observations and identity decisions;
- a conflict-blocking trigger before accepted identity decisions;
- a Work-kind trigger so `work` rows cannot specialize organisations/people;
- a semantics trigger for accepted identifiers;
- partial unique indexes for active unique identifiers, active memberships, and
  active redirects;
- FTS5 maintenance triggers for canonical labels and aliases.

Constraints were selected for invariants that are local and deterministic. The
schema deliberately does not attempt candidate generation, auto-accept policy,
canonical selection, sharding, or rights adjudication in SQL.

## 6. Synthetic fixture design

The fixture was designed to exercise interactions rather than maximize row count:

- two source snapshots and one exact observation-envelope receipt;
- two person observations representing a reviewed cross-source identity case;
- Unicode Latin and Japanese labels/aliases;
- one stable global ORCID and colliding mutable GitHub-style handles in tests;
- two Works, two versions, a venue, an author role, citation, dependency, and
  locators;
- literal source evidence, manual-review evidence, and explicit model evidence;
- an accepted identity decision, cluster, memberships, and redirect;
- an accepted affiliation assertion and a proposed model topic assertion;
- a temporal affiliation relationship;
- two vocabulary namespaces with an explicit crosswalk;
- one named projection run with uncertainty.

The fixture uses only fabricated people, organisations, Works, identifiers,
locators, and evidence.

## 7. Test derivation

Tests were written from invariants, not from implementation line coverage. The 13
checks prove:

1. ordered modules and fixture apply cleanly;
2. foreign keys reject orphan observations;
3. an observation envelope cannot assign a canonical ID;
4. observations and decisions are append-only;
5. rights/publication coverage exists on the required layers;
6. Unicode and accepted aliases are searchable;
7. unique identifiers are enforced only in their declared scope;
8. mutable/non-unique aliases may collide safely;
9. conflicting stable IDs block acceptance until resolved;
10. a merge can be reversed without deleting source rows or entities;
11. Works/versions/roles/citations/dependencies are first-class and typed;
12. vocabularies remain namespaced and model output remains explicit;
13. projections are named, versioned, scoped, reproducible, and uncertain.

## 8. Validation and publication sequence

The implementation sequence was:

1. create ordered DDL modules and CLI manifests;
2. create synthetic fixture modules;
3. create the Python stdlib test harness;
4. write architecture, mapping, compatibility, and handoff documentation;
5. run all tests and Python compilation;
6. apply the schema/fixture in-memory with foreign keys enabled and verify
   `foreign_key_check=[]` plus `integrity_check=ok`;
7. inspect changed paths and confirm no v2 or root file changed;
8. create one commit on the assigned branch;
9. push the branch and open draft PR #3;
10. re-fetch PR metadata, changed filenames, selected remote blobs, mergeability,
    and workflow status;
11. add this audit packet and rerun the complete offline validation.

Exact outputs, counts, hashes, and environment are recorded in
[`people-graph-v3-validation-record.md`](people-graph-v3-validation-record.md).

## 9. What was intentionally not done

- No production database was migrated, modified, downloaded, or committed.
- No source pilot or network ingestion was added.
- No v2 loader, matcher, query, README, or root configuration was changed.
- No stable identifier was declared automatically merge-safe by product policy.
- No universal score was calculated.
- No performance or production-scale claim was made from the tiny fixture.
- No parallel branch was cherry-picked or treated as a dependency.
- No rights decision was inferred from public visibility.

## 10. Independent reproducibility

A fresh reviewer can reconstruct the result by reading the assignment, replaying
the evidence ledger against the pinned commits, applying the ordered SQL modules,
running the 13 tests, and checking each decision against the traceability matrix.
The independent-review document lists attempts that should be made to falsify the
proposal before adoption.
