# Coordinated agent program — People Graph truth kernel and expansion

**Date:** 2026-08-06  
**Parent dossier:** [`README.md`](README.md)  
**Evidence ledger:** [`evidence-ledger.json`](evidence-ledger.json)

This document converts the first-principles audit into non-overlapping work lanes. It is designed for several agents operating concurrently without silently changing the same schema, inventing incompatible semantics, or pushing unsupported claims.

---

## 1. Program rules

Every agent must:

1. work from an explicitly named repository and branch;
2. read the parent dossier and evidence ledger before editing;
3. state the exact finding, question, or contract it owns;
4. reserve non-overlapping paths;
5. separate observations, reproduced behavior, inferences, and proposals;
6. pin all external source snapshots and repository revisions;
7. add negative fixtures, not only positive examples;
8. preserve source records and rejected hypotheses;
9. never auto-accept identity based on a name, employer, location, topic, or generic website;
10. never describe a derived relation as asserted fact;
11. never claim completeness without a declared source universe;
12. never replace immutable release bytes in place;
13. run the relevant verification and include the exact command and outcome in the PR;
14. push a branch and open a draft PR rather than leaving work only in a local checkout;
15. include a machine-readable handoff describing changed contracts, migrations, unresolved risks, and the next agent-safe action.

### Required branch convention

```text
agent/pg-<lane>-<short-description>
```

### Required commit convention

```text
PG-<lane>: <terse change>
```

### Required PR sections

```text
## Question or finding owned
## What changed
## Evidence and reproduction
## Negative cases
## Contract or migration impact
## Validation
## Known limits
## Next safe action
```

---

## 2. Dependency graph

```text
Lane 00 — Baseline verification and CI
  ├── Lane 01 — Identity safety hotfix
  │     └── Lane 02 — Canonical actor assignments
  │           ├── Lane 03 — Query truth contract
  │           ├── Lane 04 — Temporal semantics
  │           └── Lane 05 — Typed observations
  ├── Lane 06 — Work/version/artifact contract
  │     ├── Lane 07 — Book export boundary
  │     └── Lane 08 — Release protocol
  ├── Lane 09 — Evidence receipt contract
  │     └── Lane 10 — Statement/position pilot
  └── Lane 11 — Source-overlap economics
        └── Lane 12 — Event source pilot

Great Library integration begins only after the owning contracts have stable drafts
and validation receipts.
```

---

# Agent prompts

The following prompts are ready to paste into separate agents. Each prompt owns a bounded lane.

---

## Lane 00 — Baseline verification and CI

### Prompt

You own **Lane 00: Baseline verification and CI** for `sisodias/siso-people-graph`.

Start by reading:

- `docs/first-principles/README.md`
- `docs/first-principles/evidence-ledger.json`
- `tools/verify_audit_findings.py`
- `README.md`
- every file under `loaders/`
- `schema/people_schema_v2.sql`

Your job is to establish an executable baseline before architecture work proceeds.

Create branch:

```text
agent/pg-00-baseline-ci
```

Own only these paths unless a fixture requires a narrowly justified addition:

```text
.github/workflows/
tests/
tools/
docs/testing/
```

Deliver:

1. a standard-library-only or dependency-pinned test harness;
2. a clean-checkout schema-path test;
3. a minimal V1/books/people fixture capable of building a small V2 graph;
4. an FTS test that proves the FTS branch executes rather than falling back;
5. identity positive and negative fixture scaffolding;
6. idempotence checks for every loader that mutates the graph;
7. query JSON golden files;
8. a CI workflow that runs on PRs;
9. a machine-readable validation report artifact.

Do not redesign the schema in this lane. Record failures faithfully. A failing baseline test that exposes current behavior is a valid result.

Acceptance gates:

- tests run from a clean checkout;
- no production database or network access is required;
- each fixture states which current behavior it captures;
- current failures are not silently skipped;
- the PR explains which failures should turn green in later lanes.

Kill gate:

- do not create mock tests that merely search source strings when a bounded behavioral fixture can be executed.

Push the branch and open a draft PR.

---

## Lane 01 — Identity safety hotfix

### Prompt

You own **Lane 01: Identity safety hotfix** for `sisodias/siso-people-graph`.

Start from the baseline test branch or rebase after Lane 00 is available. Read findings `PG-P0-002` and related evidence in:

- `docs/first-principles/README.md`
- `docs/first-principles/evidence-ledger.json`
- `loaders/enrich_owners.py`
- `loaders/match_identities.py`
- `schema/people_schema_v2.sql`

Create branch:

```text
agent/pg-01-identity-safety
```

Own:

```text
loaders/match_identities.py
schema/people_schema_v2.sql
tests/identity/
docs/identity/
```

Deliver:

1. an explicit identifier semantics registry;
2. a strict allowlist for issuer-unique identifiers;
3. separate treatment for mutable account handles;
4. explicit exclusion of `real_name`, `company`, `location`, topics, follower counts, and generic websites from shared-identifier auto-acceptance;
5. CLI restrictions preventing arbitrary weak-method auto-acceptance;
6. a unique constraint or equivalent invariant for one active claim per source pair and policy version;
7. Unicode-safe candidate normalization that does not discard non-Latin names;
8. positive fixtures for stable identifiers;
9. negative fixtures for shared employer, city, common name, organization website, transliteration, reused handle, organization account, and pseudonym;
10. documentation stating that heuristic confidence is not a calibrated probability.

Do not merge source records in this lane. Do not change the canonical actor model yet.

Acceptance gates:

- 100 actors sharing a company or city produce zero near-certain identity claims;
- the same stable issuer ID can produce a deterministic candidate;
- a mutable login alone cannot auto-accept;
- every auto-accepted method has documented issuer and uniqueness semantics;
- tests include false-positive pressure, not only success cases.

Kill gate:

- if the method has not been benchmarked, do not label its number a probability.

Push the branch and open a draft PR.

---

## Lane 02 — Source actors and canonical actor assignments

### Prompt

You own **Lane 02: Source actors and canonical actor assignments** for `sisodias/siso-people-graph`.

This is the central ontology lane. It depends on Lane 01’s safety policy.

Read:

- the full first-principles dossier;
- findings `PG-P0-003`, `PG-P0-004`, and `PG-P1-010`;
- `schema/people_schema_v2.sql`;
- all loaders;
- the Great Library registry and release boundaries referenced by the dossier.

Create branch:

```text
agent/pg-02-canonical-actors
```

Reserve:

```text
schema/actor_*.sql
loaders/build_actor_graph*.py
loaders/migrate_v2_to_actor_model*.py
tests/actors/
docs/architecture/actor-model.md
```

Do not delete V2. Build a versioned successor or migration fixture.

Deliver:

1. `source_actor` records preserving source-local identity;
2. opaque canonical `actor` IDs independent of source login or catalog name;
3. actor kinds including human, organization, collective, pseudonym/persona, automated agent, and unknown;
4. `actor_resolution` assignments with status, policy version, method, evidence links, valid time, and decision provenance;
5. supporting and challenging evidence rows;
6. accepted canonical actor projection;
7. assignment withdrawal and split behavior;
8. migration fixtures for book, GitHub, YouTube, and registry actors;
9. explicit handling for one actor with several accounts and one account controlled by an organization or team;
10. an ADR-style design note listing rejected alternatives.

Acceptance gates:

- source records survive canonicalization;
- a bad assignment can be withdrawn without deleting source data;
- accepted assignments affect the canonical projection;
- rejected and disputed candidates remain inspectable;
- actor IDs survive source handle changes;
- no direct exact-name merge remains in the successor build path.

Kill gate:

- do not represent pairwise transitive closure as canonical truth unless all assignments resolve through an explicit actor node and policy.

Push the branch and open a draft PR.

---

## Lane 03 — Query truth contract

### Prompt

You own **Lane 03: Query truth contract** for `sisodias/siso-people-graph`.

Depend on Lane 02’s canonical actor projection. Read findings `PG-P0-003`, `PG-P1-006`, and `PG-P1-007`.

Create branch:

```text
agent/pg-03-query-truth
```

Own:

```text
loaders/ask.py
query/
schemas/query-*.json
tests/query/
docs/query-contract.md
```

Deliver a versioned JSON contract for:

- inventory;
- actor lookup;
- actor resolution evidence;
- attributed works;
- artifact routes;
- source classifications and derived profiles;
- possible lifespan overlap;
- evidence-backed public statements;
- changes between releases.

Every response must expose:

- `as_of`;
- source snapshots searched;
- expected but unavailable sources;
- identity status;
- participating source records;
- resolution evidence;
- asserted versus derived fields;
- total result count;
- returned result count;
- pagination or truncation;
- known coverage gaps;
- evidence locators where applicable.

Correct the FTS query and prove the FTS path executes.

Acceptance gates:

- no output uses “all” or “everything” without a declared source universe;
- a 250-work fixture reports 250 total, 200 returned, and `truncated=true` or paginates;
- ambiguous identity returns alternatives rather than choosing the fullest row silently;
- accepted assignments aggregate the correct source actors;
- missing domains are disclosed rather than silently omitted;
- every derived field names its method or projection.

Kill gate:

- do not introduce a natural-language agent layer before the JSON truth contract is stable and fixture-tested.

Push the branch and open a draft PR.

---

## Lane 04 — Temporal and uncertainty semantics

### Prompt

You own **Lane 04: Temporal and uncertainty semantics** for `sisodias/siso-people-graph`.

Read finding `PG-P1-009` and the first-principles time requirements.

Create branch:

```text
agent/pg-04-temporal-semantics
```

Own:

```text
schema/temporal_*.sql
tests/temporal/
docs/architecture/temporal-semantics.md
```

Deliver:

1. observation time, valid time, source publication time, and ingest time distinctions;
2. date precision such as exact, month, year, range, circa, before, after, and unknown;
3. BCE support without losing precision semantics;
4. conflicting date assertions with evidence;
5. explicit estimation records;
6. a renamed possible-lifetime-overlap projection;
7. output fields identifying estimated endpoints and assumptions;
8. fixtures for ancient dates, open-ended dates, uncertain years, living actors, and conflicting sources.

Acceptance gates:

- `birth + 80` can exist only as a named projection assumption;
- estimated endpoints never appear as source-observed dates;
- changing one source observation does not erase an earlier conflicting observation;
- temporal queries expose precision and evidence.

Kill gate:

- do not force every source into exact ISO dates when the source does not support that precision.

Push the branch and open a draft PR.

---

## Lane 05 — Typed observations and ranking projections

### Prompt

You own **Lane 05: Typed observations and ranking projections** for `sisodias/siso-people-graph`.

Read finding `PG-P0-005` and inspect every use of `rank_score`, `primary_tier`, and derived topic weight.

Create branch:

```text
agent/pg-05-typed-observations
```

Own:

```text
schema/observation_*.sql
loaders/*metric*.py
projections/
tests/metrics/
docs/metrics-and-ranking.md
```

Deliver:

1. typed metric observations with subject, metric type, value, unit, source, observation time, valid time, and method version;
2. migration mappings for work count, repository stars, followers, and model-rated repository value;
3. idempotent upsert semantics keyed by source snapshot and metric type;
4. named ranking projections rather than one universal score;
5. age, popularity, and source-coverage bias notes;
6. tests proving repeated loader runs do not inflate observations;
7. transparent multi-dimensional examples such as infrastructure influence, scholarly influence, maintenance, pedagogy, and attention disparity.

Acceptance gates:

- no field mixes stars, followers, work count, and model rating;
- every metric has units and provenance;
- reruns are idempotent;
- rankings can be recomputed from observations;
- no ranking is stored as unexplained canonical truth.

Kill gate:

- do not create a single global “importance” score.

Push the branch and open a draft PR.

---

## Lane 06 — Work, version, artifact, locator, and contribution contract

### Prompt

You own **Lane 06: Work/version/artifact contract**, spanning `sisodias/siso-people-graph` and a coordinated export proposal for `sisodias/siso-book-library`.

Do not modify the Book Library directly in this branch. Produce the People Graph side and an interface proposal that Lane 07 can implement.

Create branch:

```text
agent/pg-06-work-artifact-contract
```

Own:

```text
schema/work_*.sql
schema/contribution_*.sql
schemas/domain-export-*.json
tests/works/
docs/architecture/work-artifact-model.md
```

Deliver:

1. abstract Work;
2. expression or version;
3. artifact or edition;
4. locator;
5. contribution with actor, role, target level, source assertion, time, and evidence;
6. examples for books, translations, editions, repositories, releases, videos, and podcast episodes;
7. duplicate and compilation fixtures;
8. source-domain export contract;
9. migration strategy for current `person_content` rows;
10. explicit limits when a source cannot distinguish levels.

Acceptance gates:

- Plato is not attributed as the direct producer of every modern translation artifact;
- translator, editor, scanner, repository owner, maintainer, and contributor roles attach at appropriate levels;
- locators can change without changing Work identity;
- the model permits an honest unknown rather than fabricating a distinction.

Kill gate:

- reject ontology complexity that does not change a tested query or cannot be supported by source evidence.

Push the branch and open a draft PR.

---

## Lane 07 — Book Library versioned export and integration retirement

### Prompt

You own **Lane 07: Book Library versioned export boundary** in `sisodias/siso-book-library`.

Read:

- the People Graph first-principles dossier;
- the Book Library audit branch documentation;
- Lane 06’s domain export contract;
- `scripts/build_books_module.py`;
- `scripts/build_people_graph.py`;
- `scripts/load_into_people_graph.py`;
- `scripts/build_locator.py`.

Create branch:

```text
agent/book-07-versioned-export
```

Own:

```text
schemas/
exports/
scripts/build_export*.py
tests/export/
docs/integration-contract.md
```

Deliver:

1. a versioned source snapshot record;
2. lossless source actor export;
3. source Work/expression/artifact export where supported;
4. role-bearing source attribution export;
5. source classification export;
6. rights and artifact-route export;
7. stable source-local IDs;
8. checksums and validation report;
9. a deprecation plan for direct writes into a People Graph database;
10. fixtures proving the People Graph can consume the export without source-specific SQL.

Acceptance gates:

- the Book Library never needs a People Graph schema path to produce its export;
- source records remain lossless;
- no normalized-name canonical merge happens in the Book Library;
- rights and retrieval routes survive export;
- the export is pinned and independently verifiable.

Kill gate:

- do not make the Book Library the owner of cross-domain canonical identity.

Push the branch and open a draft PR.

---

## Lane 08 — Immutable dataset release protocol

### Prompt

You own **Lane 08: Immutable dataset release protocol** across the People Graph, Book Library, and Great Library contracts.

Create coordinated branches:

```text
agent/pg-08-release-protocol
agent/book-08-release-protocol
agent/library-08-register-data-products
```

Do not modify generated Great Library pages directly.

Deliver:

1. a manifest schema binding source snapshots, schema version, source commit, builder commit, policy versions, row counts, rights, known gaps, and predecessor release;
2. artifact checksums;
3. a pinned build clock or deterministic metadata policy;
4. a validation report;
5. immutable successor rules;
6. Book payload packaging receipts and actual locator digest semantics;
7. Great Library Work and Release records for the People Graph and Book Library, following repository validation contracts;
8. a Snapshot update only after exact release evidence exists;
9. a clean-machine download and query receipt;
10. documentation distinguishing replaceable operational assets from immutable evidentiary versions.

Acceptance gates:

- existing release bytes are not replaced beneath the same version;
- a clean agent can identify the exact source and builder for every released database;
- checksums cover every published artifact;
- README claims match the checked-in locator and packaging implementation;
- Great Library distribution states are evidence-backed, not inferred from repository visibility.

Kill gate:

- do not publish a release manifest that points to mutable `latest` URLs without a digest and immutable version identity.

Push all branches and open draft PRs with cross-links.

---

## Lane 09 — Shared evidence receipt contract

### Prompt

You own **Lane 09: Shared evidence receipt contract** across People Graph, Book Library, and Great Library interfaces.

Read the GQ-009 finding that question-addressable summaries lacked URLs, quotations, or citations.

Create branch:

```text
agent/pg-09-evidence-receipts
```

Own:

```text
schemas/evidence-*.json
schema/evidence_*.sql
tests/evidence/
docs/evidence-receipt-contract.md
```

Deliver a minimum receipt for:

- identity evidence;
- contribution attribution;
- event participation;
- public statement extraction;
- relationship assertion;
- support and contradiction;
- model-generated candidate interpretation.

The receipt must carry:

- source snapshot;
- artifact identity;
- artifact digest or immutable revision;
- exact locator or source span;
- observation time;
- event time when known;
- extraction/assertion method;
- method version;
- actor or system making the assertion;
- rights and quotation state;
- review status;
- support/challenge direction.

Acceptance gates:

- every accepted assertion can be reopened to its evidence owner;
- model summaries without source spans remain candidates, not accepted evidence;
- private evidence can be referenced through a safe owner-held receipt without leaking payloads;
- conflicting receipts coexist.

Kill gate:

- do not make a URL alone sufficient evidence; bind version or digest and exact relevance.

Push the branch and open a draft PR.

---

## Lane 10 — Public statement and position pilot

### Prompt

You own **Lane 10: Public statement and position pilot** for `sisodias/siso-people-graph`, dependent on Lane 09.

Create branch:

```text
agent/pg-10-statement-pilot
```

Own:

```text
schema/statement_*.sql
pipelines/statements/
tests/statements/
docs/statement-model.md
```

Select one bounded Frontier Question and a small set of public, rights-compatible sources. Do not attempt whole-corpus extraction.

Deliver:

1. proposition identity;
2. statement record;
3. stance such as expressed, endorsed, rejected, questioned, or predicted;
4. modality and uncertainty;
5. direct quote versus paraphrase versus model candidate;
6. exact evidence receipt;
7. context and speaker-role checks;
8. contradiction and supersession;
9. review queue;
10. evaluation fixtures for quotation, reporting another person’s view, hypothetical argument, satire, uncertainty, and changed position.

Acceptance gates:

- the system never reports a described third-party view as the speaker’s position;
- every accepted statement dereferences to an exact source span;
- model extraction remains a candidate until reviewed under the declared policy;
- time and context are preserved;
- no output claims direct access to inner belief.

Kill gate:

- no inferred “belief” may be published as a fact about the actor.

Push the branch and open a draft PR.

---

## Lane 11 — Source-overlap economics

### Prompt

You own **Lane 11: Source-overlap economics**. This is a research lane; do not ingest millions of rows.

Create branch:

```text
agent/pg-11-source-economics
```

Own:

```text
research/source-universe/
docs/source-acquisition-matrix.md
fixtures/source-samples/
```

Evaluate candidate public source families using:

- stable identifiers;
- actor and contribution semantics;
- event participation;
- time coverage;
- exact evidence addressability;
- rights and access;
- source independence;
- expected overlap with unresolved high-value actors;
- relevance to active Frontier Questions;
- update cadence;
- ingestion and maintenance cost;
- privacy and pseudonymity risk.

Candidate families should include authority sources, modern scholarly metadata, technical publishing, conference and event systems, podcast feeds, package registries, creator-controlled websites, reading lists, and bounded public forums.

Deliver:

1. a source universe inventory;
2. a scored but transparent acquisition matrix;
3. explicit assumptions and sensitivity analysis;
4. one small sample per top source family;
5. expected identity and answer-value yield;
6. rights and ethical boundaries;
7. recommended order and rejected high-volume/low-value sources.

Acceptance gates:

- raw record count is not the leading score;
- every score dimension is separately visible;
- uncertainty ranges are stated;
- no source is recommended without a lawful access and maintenance path;
- pseudonymous platforms retain pseudonymity by default.

Kill gate:

- do not start bulk ingestion in this lane.

Push the branch and open a draft PR.

---

## Lane 12 — Event and participation pilot

### Prompt

You own **Lane 12: Event and participation pilot**, dependent on Lane 11’s selected source and Lane 09’s evidence receipts.

Create branch:

```text
agent/pg-12-event-pilot
```

Own:

```text
schema/event_*.sql
pipelines/events/
tests/events/
docs/event-model.md
```

Deliver:

1. event series;
2. event occurrence;
3. session or episode;
4. participation role;
5. recording and transcript artifact locators;
6. evidence receipts;
7. source-specific IDs;
8. temporal precision;
9. one bounded pilot source;
10. cross-domain resolution candidates generated from explicit public identities.

Acceptance gates:

- host, guest, speaker, moderator, panelist, organizer, and contributor remain distinct roles;
- shared participation does not become a friendship, collaboration, or influence edge;
- every participant record points to source evidence;
- the pilot measures new canonical resolutions and useful question paths, not only rows loaded;
- failed resolution candidates remain inspectable.

Kill gate:

- do not infer social relationships from co-appearance alone.

Push the branch and open a draft PR.

---

## 3. Integration agent — Great Library registration and decision record

Run this only after the first stable contracts and exact releases exist.

### Prompt

You own the Great Library integration for the People Graph program in `sisodias/great-library-of-siso`.

Read `AGENTS.md`, `CURRENT_STATE.md`, the latest whole-Library Snapshot, `site/intelligence.json`, the registry model, release schema, question-driven research architecture, and all accepted People Graph/Book Library PRs.

Create branch:

```text
agent/library-people-graph-program
```

Follow the repository’s Event reservation and immutable history rules.

Deliver:

1. independently addressable Work records for SISO People Graph and SISO Book Library if they do not already exist;
2. immutable Releases pinned to exact source and data artifacts;
3. evidence-backed distribution states;
4. an ADR recording the boundary among Great Library, source-domain libraries, People Graph, and Evidence Engines;
5. a publication-safe research program or Frontier Question linkage;
6. a new Snapshot selecting releases only after validation;
7. authored documentation linking the first-principles dossier and evidence ledger;
8. closed Event threads with exact receipts;
9. generated site and catalog updates through the source-of-truth generator;
10. full `npm run verify` results.

Acceptance gates:

- the Great Library does not absorb the graph data plane;
- graph actors do not become hundreds of thousands of Library Works;
- catalog presence is not presented as downloadable or verified without release evidence;
- generated pages are not hand-edited;
- the active Snapshot changes only after all records validate.

Push the branch and open a draft PR.

---

## 4. Merge order

Recommended merge order:

1. Lane 00 — baseline tests and CI
2. Lane 01 — identity safety hotfix
3. Lane 02 — actor model
4. Lane 03 — query truth
5. Lane 04 and Lane 05 — time and metrics
6. Lane 06 — Work/artifact contract
7. Lane 07 — Book export boundary
8. Lane 09 — evidence receipts
9. Lane 08 — immutable release protocol
10. Lane 11 — source economics
11. Lane 12 — event pilot
12. Lane 10 — statement pilot
13. Great Library registration and selected releases

Where two lanes touch one file, the later lane must rebase and preserve the earlier lane’s tests. Do not resolve conflicts by dropping negative fixtures or evidence fields.

---

## 5. Program success criteria

The first program milestone is complete when:

- a clean checkout builds a tested small graph;
- descriptive attributes cannot trigger automatic identity acceptance;
- source actors and canonical actors are distinct;
- accepted assignments change query results and remain reversible;
- queries expose source coverage, identity status, total counts, truncation, and evidence;
- metrics are typed observations rather than a universal score;
- Work, artifact, locator, and contribution semantics are explicit;
- data releases are immutable, pinned, and checksummed;
- one event source creates measured cross-domain value without false social inference;
- one statement pilot produces source-span-grounded positions for a bounded question;
- the Great Library can cite exact graph and book releases without becoming their warehouse.

The milestone is **not** defined by a target row count.
