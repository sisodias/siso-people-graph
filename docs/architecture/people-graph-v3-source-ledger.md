# People Graph v3 source and evidence ledger

**Status:** complete public source ledger for `3.0.0-draft.1`  
**Base audited:** `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Recorded:** 2026-08-06

This ledger records every source that materially affected the schema proposal.
It separates direct observations from design inferences. A source appearing here
does not make every statement in that source true; it identifies the exact input
that was inspected and the narrow conclusions drawn from it.

## Evidence classes

- **Observed:** literal behavior, structure, or statement in a pinned file.
- **Inferred:** a design consequence derived from one or more observations.
- **Unproven:** a proposition intentionally left for pilots, benchmarks, policy,
  or another lane.

## Source ledger

### SRC-001 — user brief and shared exchange contract

- Kind: user-provided design brief.
- Original file: `Pasted text.txt`.
- SHA-256: `077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d`.
- Committed excerpt: `docs/architecture/people-graph-v3-agent-brief.md`.
- Observed requirements: additive v3; exclusive-path discipline; independent
  parallel execution; exact `pg-observation-0.1` envelope; source/canonical/
  identity/claim/projection separation; offline tests; no production assets.
- Not inferred from this source: physical sharding, identity thresholds, source
  eligibility, or production migration timing.

### SRC-002 — People Graph README

- Repository/ref: `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`.
- Path: `README.md`.
- Git blob SHA: `3ae7738eed163cabb72ed5ea4d57d38453ec40f1`.
- Observed: the graph reports 280,708 people, 564,486 works, 2,050,629 topic
  edges, and 253,815 platform identities; roles belong on edges; identity claims
  and reversible merges are explicit goals; topic vocabularies are kept
  separate; the documented cross-domain stitch is three people; the database is
  a release asset rather than a Git file.
- Design use: preserve roles, reversibility, namespaced vocabularies, and the
  external data-plane boundary while removing source-shaped canonical identity
  and universal score assumptions.

### SRC-003 — v2 schema

- Repository/ref: `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`.
- Path: `schema/people_schema_v2.sql`.
- Git blob SHA: `07b70a2eaf8db48d741010d2d5f31810a0c9d0d1`.
- Observed: `person_id` is source-shaped; `primary_tier` and `rank_score` live on
  the canonical person row; external identifiers lack a registry of scope,
  uniqueness, mutability, and authority semantics; Works are represented by
  `person_content` strings; identity claims do not themselves create temporal
  cluster membership or redirect history; contemporaries use an 80-year fallback.
- Design use: separate observations from canonical entities, replace universal
  scores with named projections, make Works first-class, and model identity
  application/undo explicitly.

### SRC-004 — v2 rebuild builder

- Repository/ref: `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`.
- Path: `loaders/build_people_graph_v2.py`.
- Git blob SHA: `7983db530d242b386fcd3c8277718010b7a43034`.
- Observed: the builder already prefers a rebuild to in-place migration; it
  matches book people to existing people by normalized name; it copies book
  titles onto `person_content`; it inserts empty aliases into FTS; source
  provenance is represented at edge level but not as immutable source receipts.
- Design use: retain rebuild discipline while moving name matching out of import,
  preserving raw observations, and providing first-class Work and alias models.

### SRC-005 — v2 identity matcher

- Repository/ref: `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`.
- Path: `loaders/match_identities.py`.
- Git blob SHA: `541c68e7083e54327141aaed37f004579b024c4c`.
- Observed: every shared `external_ids` value can currently become
  `shared_external_id` evidence at confidence 0.98; normalization removes
  non-ASCII characters; exact-name and surname-initial proposals are generated;
  proposed/accepted rows do not themselves materialize reversible canonical
  clusters.
- Design use: require identifier-scheme declarations before identity use,
  preserve Unicode, distinguish candidates from decisions, block conflicts, and
  model cluster/redirect application separately.

### SRC-006 — current read/query surface

- Repository/ref: `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`.
- Path: `loaders/ask.py`.
- Git blob SHA: `37e19c92d242bc979eb2ab55b4f6f6a02872083d`.
- Observed: the query surface is read-only, guesses machine-local paths, chooses
  the content-richest duplicate candidate for `works`, and exposes provenance
  primarily as domain/ref routes rather than source snapshot, identity decision,
  evidence, rights, and projection lineage.
- Design use: keep v3 additive and require capability-detecting query adapters;
  do not modify the query surface in this lane.

### SRC-007 — Book Library contributor graph builder

- Repository/ref: `sisodias/siso-book-library@be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b`.
- Path: `scripts/build_people_graph.py`.
- Git blob SHA: `08b667b448c3acbc4bc0357f378270d46892e071`.
- Observed: source author strings are parsed into name-derived keys; contributor
  roles and BCE years are retained; corporate classification uses heuristics;
  raw variants are stored; co-authorship is derived from person-work edges.
- Design use: preserve roles, dates, variants, and source-native records, but do
  not promote name-derived keys or corporate heuristics into canonical identity.

### SRC-008 — Book Library to People Graph loader

- Repository/ref: `sisodias/siso-book-library@be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b`.
- Path: `scripts/load_into_people_graph.py`.
- Git blob SHA: `de4e9fd91c076fd514887c82bd334dde43271d7b`.
- Observed: existing people are selected by normalized name; book Work count is
  written into `rank_score`; only the `author` role is loaded into the canonical
  graph; Gutenberg works remain referenced by string ID.
- Design use: import Book records as observations and contributions without
  assigning canonical identity or a cross-domain score.

### SRC-009 — Great Library/SISO Knowledge boundary

- Repository/ref: `sisodias/great-library-of-siso@12f4cc249b2b5dc268d05d1698fe9c5e3079327d`.
- Path: `docs/siso-knowledge-model.html`.
- Git blob SHA: `dc1f74cdf77eea64f54f56c828ae996d8345a1e6`.
- Observed: the public architecture distinguishes Great Library registry identity,
  SISO Knowledge graphs/indexes, Foundry source discovery, Evidence Engines, and
  an external governed data plane for databases and corpora.
- Design use: reinforce the no-production-payload-in-Git boundary. Ownership is
  not resolved by this schema lane and remains a program-level ADR question.

### SRC-010 — branch and draft PR state

- Repository: `sisodias/siso-people-graph`.
- Branch: `pg/v3-ontology-schema-20260806`.
- Original commit: `2f66fbe1f4523399463d9e1ff8971879a84f5b88`.
- Draft PR: `#3`, `Architecture: add the People Graph v3 evidence ontology`.
- Base: `main@de048bb3b34bf931b56fd741cb46c1334acdfb98`.
- Observed at follow-up: open, draft, mergeable, 24 files, 2,077 additions,
  no deletions before this provenance commit.

## Source-to-decision map

| Decision | Primary source IDs |
| --- | --- |
| Additive rebuild beside v2 | SRC-001, SRC-003, SRC-004 |
| Immutable source observations | SRC-001, SRC-003, SRC-004, SRC-007 |
| Opaque canonical entities | SRC-001, SRC-003, SRC-004, SRC-005, SRC-007 |
| Identifier registry and scoped uniqueness | SRC-001, SRC-003, SRC-005 |
| Reversible reviewed identity | SRC-001, SRC-002, SRC-003, SRC-005 |
| First-class Works and contribution roles | SRC-001, SRC-002, SRC-003, SRC-007, SRC-008 |
| Unicode-preserving aliases/search | SRC-001, SRC-004, SRC-005, SRC-007 |
| Named projections instead of universal score | SRC-001, SRC-002, SRC-003, SRC-008 |
| Rights/privacy/publication state | SRC-001, SRC-009 |
| External payload/data plane | SRC-001, SRC-002, SRC-009 |

## Explicit non-sources and unproven claims

No live production SQLite asset, release payload, private vault path, external
API, bulk source snapshot, user record, benchmark corpus, or network pilot was
used. No claim is made that v3 is production-ready, performant at full scale,
legally sufficient for any source, byte-reproducible, or already integrated with
identity/build/query/source/claims lanes. Those remain validation work.
