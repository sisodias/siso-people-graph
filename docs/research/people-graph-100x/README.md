# People Graph 100x research dossier

**Research cut:** 2026-08-06  
**Base reviewed:** `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Status:** public reasoning and coordination record; no production database mutation  
**Owner:** Shaan / SISO, with agent-authored evidence and proposals  

## Why this packet exists

The initial question was how to make the People Graph 100x more valuable and how to coordinate many agents without losing their work or the reasoning behind it. The first answer focused on adding people, media, relationships, topics and identity sources. Deeper inspection showed that this framing was still too small.

The durable opportunity is an **evidence-backed map of human knowledge production**:

```text
source observations
  -> reversible identity assertions
  -> canonical actors and organisations
  -> contributions to canonical works
  -> versions, editions, translations and parts
  -> relationships, events, institutions and communities
  -> atomic claims anchored to exact evidence spans
  -> support, contradiction, belief change and influence
  -> Frontier Questions, experiments and immutable Answer Releases
```

The project should not be optimized as a larger biography or profile database. It should be optimized as a trustworthy research substrate that can answer consequential questions and show how every answer was constructed.

A useful value model is:

```text
value = coverage x identity quality x relationship depth x evidence quality x query utility
```

Ten times more rows with weak identity, rights, provenance or query semantics can reduce value rather than increase it.

## What is preserved here

This directory contains the complete public reasoning record for the 100x thesis:

1. [`research-notebook.md`](research-notebook.md) — what was inspected, the hypotheses tested, evidence found, inferences made, uncertainties retained and alternatives rejected.
2. [`current-state-audit.md`](current-state-audit.md) — concrete integrity and architecture gaps found in the reviewed code, with exact paths and repair criteria.
3. [`architecture-and-100-tracks.md`](architecture-and-100-tracks.md) — the target system and one hundred missing research, data, governance and product tracks.
4. [`source-and-standards-ledger.md`](source-and-standards-ledger.md) — repository evidence, external standards, public data sources and the delegated 39-source matrix.
5. [`agent-missions.md`](agent-missions.md) — executable missions and copy-paste prompts, including the existing thirteen-lane program and the additional work not yet owned.
6. [`coordination-state.md`](coordination-state.md) — observed branches, draft pull requests, path reservations, integration seams and present gaps.
7. [`decision-log.md`](decision-log.md) — decisions, alternatives, assumptions, falsifiers and reversal conditions.
8. [`research-manifest.json`](research-manifest.json) — machine-readable scope, evidence, assertions, live branches and review gates.
9. [`handoff.md`](handoff.md) — verification, merge guidance and the precise boundary of this documentation-only lane.

This is a transparent decision record, not a claim to expose private hidden chain-of-thought. It records the useful reproducible material agents need: inputs, observations, tests, assumptions, alternatives, deductions, uncertainties, falsifiers and decisions.

## Read this in order

A cold agent should:

1. read this file;
2. read `research-notebook.md` and `current-state-audit.md`;
3. inspect the cited repository files at the pinned commit;
4. read `decision-log.md`;
5. use `architecture-and-100-tracks.md` as the opportunity map;
6. check `coordination-state.md` before selecting work;
7. take only an unowned mission from `agent-missions.md`;
8. emit a handoff that can be reviewed without access to a private conversation or local machine.

## Core architectural split

### SISO People Graph

Should own actor identity and participation semantics:

```text
actor
actor_name_assertion
actor_identifier_assertion
identity_claim
identity_evidence
identity_cluster_projection
organisation
membership_and_affiliation
relationship
 event
participation
contribution
```

It should not own entire books, papers, source archives, video payloads or final research answers.

### SISO Book Library

Should evolve from a Gutenberg source-record index into a bibliographic and textual evidence plane:

```text
source_record
work
expression
manifestation
item_location
work_relation
contribution
document_part
text_representation
text_anchor
rights_assertion
quality_observation
```

Gutenberg should remain one source adapter, not the definition of the library.

### Great Library of SISO

Should remain the durable public control and registry plane:

```text
Work
Release
Assembly
Snapshot
Source Inventory
Frontier Question
Source Card
Claim reference
Assumption
Experiment
Answer Release
Watch Trigger
Decision
Event
```

It should reference actor, work and evidence identities rather than copying their operational databases.

### Evidence transformation plane

A versioned contract is needed for:

```text
claim
claim_expression
source_span
evidence_link
claim_relation
stance
argument
prediction
resolution
extraction_run
```

The repository location of this plane remains an explicit decision for the Great Library, SISO Knowledge and Evidence Engines. The model should be designed before creating another product or warehouse.

## Findings that change the near-term order

The reviewed repository already has valuable principles: edge-level roles, explicit identity claims, reversible merges, namespaced external IDs, topic schemes, provenance columns and a read-only query router. However, code and stated policy currently disagree in several places.

The highest-priority blockers are:

- a clean v2 builder path defect;
- silent normalized-name identity reuse inside the v2 builder;
- identity-claim duplicate insertion on reruns;
- ASCII-only normalization that is unsafe for global names;
- accepted identity claims not affecting query-time identity closure;
- source evidence collapsing into single final edges;
- source-native content references standing in for canonical Works;
- derived ranking fields remaining in the schema despite the stated rule;
- false temporal precision and undocumented assumptions in outputs;
- blanket Book Library rights assignment;
- Gutenberg records being described as Works without edition/manifestation resolution;
- Great Library research concepts being richer in prose than in machine contracts.

These findings are expanded and linked in `current-state-audit.md`. The dedicated red-team draft PR should remain the executable defect authority; this packet supplies the system-level interpretation and integration order.

## Existing parallel work

This dossier does not compete with the live lanes. It intentionally owns only:

```text
docs/research/people-graph-100x/**
```

Known published draft work at this research cut:

- People Graph PR #1 — red-team failure fixtures;
- People Graph PR #2 — software and AI source observations;
- People Graph PR #3 — v3 evidence ontology;
- Great Library PR #1 — registry, ownership and GQ-010 program spine;
- Great Library PR #2 — 39-source research matrix and pilot portfolio.

Other reserved People Graph branches existed but were still identical to `main` when checked. Exact status and commit IDs are in `coordination-state.md` and `research-manifest.json`.

## Non-negotiable operating principles

1. **Source observations are not canonical truth.** Adapters emit literal evidence and never assign final actor IDs.
2. **Identity is reversible and contradiction-aware.** Negative evidence is first-class.
3. **Canonical IDs are source-neutral.** First-arriving source IDs must not become permanent ontology.
4. **A Work is not a file or source row.** Versions, expressions and manifestations remain distinct.
5. **Every assertion can carry multiple evidence receipts.** Repeated sources do not collapse into one provenance string.
6. **Time is uncertain and bitemporal.** Event time and observation time are different facts.
7. **Rights are asserted per artifact and jurisdiction.** Public addressability is not permission.
8. **Derived values are named, versioned projections.** They are never stored as unexplained truth.
9. **Living-person privacy limits collection and publication.** Public usefulness does not override safety.
10. **Answers must be reproducible.** A result should identify source snapshots, transforms, model versions, assumptions and unresolved contradictions.

## Program gates

Before large-scale ingestion, require:

- clean-build and replay tests;
- a versioned source-observation envelope;
- source-neutral IDs;
- a labelled identity benchmark with difficult negatives;
- contradiction and deletion handling;
- per-source terms, rights and retention review;
- Work-resolution fixtures;
- exact evidence-span selectors;
- documented privacy/publication policy;
- reproducible named projections;
- at least five decision-use benchmark questions.

## Success is not person count

Track at least:

- identity precision and recall by language, era and source pair;
- verified actors represented across two, three, four and five source families;
- percentage of contributions resolved to canonical Works;
- evidence receipts per assertion and their independence;
- temporal coverage and uncertainty quality;
- artifact-level rights coverage;
- correction and deletion propagation time;
- reproducible builds from pinned source snapshots;
- percentage of research answers returning complete provenance paths;
- Frontier Questions whose assumptions or decisions changed because of the graph.

## First milestone

A credible first milestone is:

```text
zero silent identity merges
zero blanket rights assumptions
100% of canonical assertions linked to ingest runs and evidence receipts
100% of extracted claims linked to exact source spans
one versioned multilingual identity benchmark
one canonical Work-resolution benchmark
first 10,000 verified multi-domain modern actors, subject to audited sampling
first reproducible Answer Release generated from graph evidence
```

## Relationship to the Great Library program

Great Library draft PR #1 proposes stable registry identities, ADR-0005, GQ-010, a thirteen-lane event and Whole Library V37. Great Library draft PR #2 supplies the current 39-source matrix, rights/deletion analysis, value theses and pilot portfolio. Those branches are cited as evidence but are not assumed merged or authoritative until reviewed and accepted.

Corrections to this dossier should preserve the same rule: do not silently rewrite why a decision was made. Add a dated successor entry, record the new evidence and state which conclusion changed.
