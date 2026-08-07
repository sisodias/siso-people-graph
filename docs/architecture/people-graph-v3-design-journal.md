# People Graph v3 design journal and reasoning record

**Schema:** `3.0.0-draft.1`  
**Branch:** `pg/v3-ontology-schema-20260806`  
**Base:** `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Recorded:** 2026-08-06

## What this record is

This is the complete public reasoning record for the schema proposal: evidence
consulted, deductions, decisions, rejected alternatives, trade-offs, unknowns,
and validation steps. It is designed so another agent can reproduce or dispute
the result without access to the original chat.

It is not a token-by-token transcript of private model deliberation or transient
tool chatter. Such a transcript is neither a stable engineering artifact nor a
source of truth. The reconstructable content is committed instead: the original
brief, exact source ledger, requirement traceability, decision rationales,
fixtures, executable constraints, and tests.

## Working method

1. **Freeze the evidence boundary.** The branch was based on the exact current
   People Graph main commit visible at lane start. The prompt, source files, and
   Book/Great Library context were recorded by immutable commit or blob SHA where
   available.
2. **Separate observation from inference.** Literal source behavior was listed
   before proposing any v3 table. Design claims were accepted only when they
   followed from a prompt invariant, a demonstrated v2 coupling, or both.
3. **Convert failure classes into invariants.** Name-based identity, untyped
   external IDs, title-string Works, universal rank, and inert merge decisions
   became explicit negative requirements.
4. **Choose the least destructive integration posture.** Because parallel lanes
   own existing loaders/query code and because v2 is a shipped asset, v3 was made
   standalone and additive.
5. **Model provenance before convenience.** Source snapshots, immutable receipts,
   evidence, decisions, and policy states were defined before canonical entities,
   relationships, or projections.
6. **Make disputed policy visible.** Thresholds, source eligibility, sharding,
   canonical label policy, and Work-version subtype policy were deliberately not
   hidden in DDL.
7. **Prove invariants with a synthetic fixture.** A small Unicode, multi-source,
   multi-Work, reversible-identity fixture was built to exercise constraints
   without publishing production data.
8. **Test the contract offline.** Standard-library tests apply every DDL/sample
   module and probe the invariants directly.

## Chronological work log

### Step 1 — establish scope and non-negotiable constraints

The shared brief required an additive schema lane, strict path ownership,
parallel independence, an exact `pg-observation-0.1` import mapping, no canonical
ID in the exchange envelope, offline tests, and no production assets. Therefore
editing v2 tables or waiting for another PR was ruled out before design began.

### Step 2 — audit the v2 data model and query behavior

The audit identified six structural couplings:

1. source-native identity and canonical identity share `person_id`;
2. identifier values do not declare uniqueness/mutability/scope semantics;
3. name normalization participates in cross-domain matching;
4. Works remain mostly string references on person edges;
5. canonical rows carry score/tier fields whose units depend on source;
6. accepted identity claims do not themselves define temporal canonical
   membership, redirect lookup, or an executable undo record.

These are not claims that v2 is useless. V2 already contains valuable choices:
roles on edges, provenance fields, reversible intent, BCE years, namespaced topic
schemes, read-only querying, and rebuild-over-migration. V3 preserves those
strengths while separating layers more rigorously.

### Step 3 — derive the layer boundary

The minimum safe decomposition was:

`source -> snapshot -> envelope receipt -> source observation -> evidence ->`
`canonical entity -> identity decision/cluster -> Work/relationship/assertion ->`
`named projection`.

The key deduction was that an import receipt cannot also be a canonical entity.
If import assigns canonical identity, replaying a corrected source record can
silently alter truth. If a canonical entity erases source-native rows, a merge
cannot be reversed. Therefore source observations and canonical entities must be
independent, with explicit evidence-bearing transitions between them.

### Step 4 — design identity as reviewable state transition

A single confidence number is insufficient because two strong stable identifiers
can conflict. The schema therefore records:

- identifier definitions before assignments;
- candidates with method/version and review state;
- positive and negative evidence;
- explicit conflicts;
- append-only decisions;
- clusters, memberships, and redirects with validity intervals.

An open conflict blocks acceptance. Undo is an append-only revocation plus closing
membership/redirect intervals; it never deletes source observations or entities.

### Step 5 — promote Works and contributions to first-class records

A title string cannot represent an edition, translation, release, citation,
dependency, contributor order, venue, or fetch locator without overloading one
edge. The Work model was split into canonical Work, version, venue, contribution,
citation, dependency, and locator tables. Contributor role remains on the
contribution, not the person.

### Step 6 — distinguish claims, relationships, and projections

A source field, a reviewed assertion, a temporal relationship, and a computed
ranking have different truth conditions. The schema therefore uses:

- `evidence` for literal spans/records, manual review, derived evidence, or model
  output with explicit lineage;
- `assertion` for evidence-backed subject/predicate/object-or-value statements;
- `relationship` for typed temporal entity-to-entity edges;
- `projection_*` for named/versioned computed outputs with scope and uncertainty.

This prevents topic membership from becoming a claim about belief and prevents a
source-specific metric from becoming one universal person score.

### Step 7 — encode policy and deletion obligations

Rights, privacy, and publication are independent. Public metadata can point to a
restricted payload; a record may be internally usable but not publicly
publishable. Shared policy vocabularies were therefore referenced at source,
snapshot, observation, Work, evidence, assertion, and projection layers.
Append-only observations coexist with legal removal by recording status events
and revoking governed raw pointers rather than pretending retained payload is
immutable forever.

### Step 8 — construct adversarial synthetic data

The fixture includes:

- two source observations for one reviewed human;
- Latin diacritics and Japanese aliases;
- a stable global ORCID and colliding mutable GitHub-style handles;
- an unresolved conflicting-ORCID candidate;
- one reversible accepted cluster and redirect;
- first-class article/software Works, versions, roles, venue, citation,
  dependency, and locators;
- literal, manual, and model-generated evidence;
- accepted and proposed assertions;
- a temporal relationship;
- two namespaced vocabularies and an explicit crosswalk;
- a named uncertain projection.

### Step 9 — validate and publish

The initial branch ran 13 offline tests, Python compilation, foreign-key checks,
and SQLite integrity checks before the first commit and draft PR. This follow-up
adds machine-readable provenance tests and reruns the entire suite. The validation
record in `schema/v3/design_provenance.json` is updated only after the final run.

## Decision records

### D-001 — build v3 beside v2, not through in-place alteration

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-003, SRC-004.  
**Reasoning:** v2 lacks source evidence that no migration can reconstruct; the
existing asset is shipped; parallel path ownership forbids modifying v2 here.
A fresh build preserves rollback and makes comparison explicit.  
**Rejected:** ALTERing v2 in place; silently renaming v2 tables.  
**Cost:** dual capability adapters are required during coexistence.

### D-002 — make source receipts and observations append-oriented

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-003, SRC-004, SRC-007.  
**Reasoning:** canonical corrections must not erase what a source actually said.
Snapshot/revision, payload digest, observed/retrieved time, raw pointer, and
policy state are needed to replay and audit imports.  
**Rejected:** treating the latest canonical row as both source history and truth.

### D-003 — use opaque canonical entity IDs

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-003, SRC-004, SRC-005, SRC-007.  
**Reasoning:** names, handles, source IDs, and normalization rules change. A
canonical ID derived from them makes correction destructive.  
**Rejected:** `gh:<login>`, normalized-name IDs, and source-first IDs as the
cross-domain canonical key.  
**Deferred:** concrete ULID/UUID generator policy.

### D-004 — register identifier semantics before identity use

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-003, SRC-005.  
**Reasoning:** the same string has different identity value depending on scheme,
scope, uniqueness, mutability, authority, and version. Scoped partial uniqueness
should apply only to accepted active identifiers declared unique.  
**Rejected:** treating every `external_ids` row as near-certain evidence.

### D-005 — separate candidates, conflicts, decisions, clusters, and redirects

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-002, SRC-003, SRC-005.  
**Reasoning:** proposal confidence is not adjudication, and adjudication is not
materialized canonical lookup. Separate records make review, application, and
undo inspectable.  
**Rejected:** one mutable merge flag or destructive row deletion.  
**Deferred:** auto-accept policy and canonical winner algorithm.

### D-006 — model Works, versions, contributions, and locators explicitly

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-002, SRC-003, SRC-007, SRC-008.  
**Reasoning:** roles, editions, releases, translations, citations, dependencies,
venues, and locators have independent identity and time semantics.  
**Rejected:** title/ref JSON attached only to a person edge.  
**Deferred:** whether expression/edition/release become subtype tables.

### D-007 — separate evidence, assertions, and temporal relationships

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-003, SRC-006.  
**Reasoning:** a literal source field, a reviewed factual assertion, and an
entity-to-entity relation have different constraints and review states.  
**Rejected:** one polymorphic edge table with optional columns for every case.

### D-008 — keep source vocabularies namespaced and crosswalk explicitly

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-002, SRC-003.  
**Reasoning:** equal labels do not imply equal authority or meaning. Crosswalks
need their own evidence, method version, confidence, and status.  
**Rejected:** flattening all topic strings into one namespace.

### D-009 — preserve Unicode in labels, aliases, and search

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-004, SRC-005, SRC-007.  
**Reasoning:** ASCII deletion creates collisions and makes non-Latin names
unsearchable. FTS indexes canonical labels and accepted aliases without deriving
IDs from either.  
**Known limit:** FTS5 is not full locale-aware morphology or transliteration.

### D-010 — attach rights, privacy, and publication policy to evidence-bearing layers

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-009.  
**Reasoning:** access, retention, personal-data handling, and publication are not
one boolean. Policy must travel with data and derived outputs.  
**Rejected:** assuming public visibility means reusable/publicable.

### D-011 — replace universal score/tier with named projections

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-002, SRC-003, SRC-008.  
**Reasoning:** work count, stars, citations, followers, and curated tiers use
incompatible units. Any derived metric must expose method, version, source scope,
as-of time, input digest, parameters, and uncertainty.  
**Rejected:** copying v2 `rank_score` or `primary_tier` into canonical v3 entity.

### D-012 — import the exact observation envelope and stop before canonicalization

**Decision:** accepted.  
**Evidence:** SRC-001.  
**Reasoning:** parallel source lanes need replayable interoperability without
sharing a canonical ontology or silently resolving identity. The exact JSON is
retained as a receipt and child arrays map only to observation tables.  
**Rejected:** extending the envelope in this lane or allowing `canonical_id`.

### D-013 — rebuild canonical state from declared snapshots and decisions

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-004.  
**Reasoning:** deterministic source reconstruction exposes missing inputs and
allows the current asset to remain untouched.  
**Rejected:** treating the current v2 database as complete source truth.  
**Deferred:** physical build orchestration and release packaging.

### D-014 — define a logical contract and defer physical partitioning

**Decision:** accepted.  
**Evidence:** SRC-001, scale reported in SRC-002.  
**Reasoning:** schema invariants can be reviewed independently of whether
observations live in one SQLite file, attached shards, or an external columnar
plane. Premature physical layout would couple every parallel lane.  
**Deferred:** benchmark-backed shard boundaries and indexes.

### D-015 — preserve compatibility through capability-detecting adapters

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-003, SRC-006.  
**Reasoning:** v2 consumers must continue to function while v3 remains a draft.
Adapters should label compatibility data and never promote v2 name matches to
accepted v3 identity.  
**Rejected:** changing `ask.py` or existing loaders in this lane.

### D-016 — use only synthetic public-safe fixtures in Git

**Decision:** accepted.  
**Evidence:** SRC-001, SRC-002, SRC-009.  
**Reasoning:** the schema can prove integrity without publishing a database,
corpus, credentials, personal notes, or rights-unclear payloads.  
**Rejected:** checking in a production SQLite sample or raw source payload.

## Rejected alternatives summary

| Alternative | Rejection reason |
| --- | --- |
| In-place v2 migration | Cannot reconstruct missing provenance; mutates shipped asset. |
| Name- or handle-derived canonical IDs | Mutable, collision-prone, non-Unicode-safe. |
| Any shared external value as auto-merge evidence | Scheme semantics are missing and conflicts can exist. |
| Destructive merge | Prevents audit and reliable undo. |
| String-only Works | Cannot model versions, roles, venues, citations, dependencies, or locators. |
| One universal edge table | Hides incompatible invariants and review semantics. |
| One universal score | Mixes units and conceals method/scope/uncertainty. |
| Flattened vocabularies | Erases authority and meaning boundaries. |
| Model output as source fact | Conceals inference lineage and review state. |
| Production payload in Git | Violates rights, privacy, size, and rebuild boundaries. |

## Unresolved questions and required future evidence

1. **Identity auto-accept:** needs measured precision by identifier scheme and an
   explicit risk policy; the schema only records eligibility.
2. **Canonical label provenance:** one observation pointer may evolve into an
   accepted multi-evidence label assertion.
3. **Authority scopes:** textual `scope_ref` may become a first-class scope entity.
4. **Work abstractions:** real scholarly, software, media, and Book pilots must
   test whether one `work_version` table is sufficient.
5. **Physical scale:** attached SQLite shards versus columnar observations needs
   benchmark evidence, not intuition.
6. **Deletion implementation:** source-specific legal and contractual removal
   workflows must define what can remain as a tombstone receipt.
7. **Temporal semantics:** relation-type policies need source-specific interval
   rules and uncertainty representation.
8. **Query behavior:** the query lane must prove capability metadata, pagination,
   timeouts, and ambiguity disclosure.
9. **Production migration:** requires source manifests, logical digests, parity
   queries, rollback, and explicit consumer cutover.

## Reproduction checklist

```bash
python3 tests/schema_v3/run.py
python3 -m unittest discover -s tests/schema_v3 -p 'test_*.py' -v
python3 -m py_compile tests/schema_v3/*.py

sqlite3 /tmp/people-v3.sqlite < schema/v3/people_graph_v3.sql
sqlite3 /tmp/people-v3.sqlite < schema/v3/sample_data.sql
sqlite3 /tmp/people-v3.sqlite 'PRAGMA foreign_key_check; PRAGMA integrity_check;'
```

Read these in order to reproduce the design:

1. `docs/architecture/people-graph-v3-agent-brief.md`
2. `docs/architecture/people-graph-v3-source-ledger.md`
3. this journal
4. `docs/architecture/people-graph-v3-traceability.md`
5. `schema/v3/design_provenance.json`
6. ordered DDL and sample manifests
7. `tests/schema_v3/`
