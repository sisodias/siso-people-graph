# Research notebook: how the 100x thesis was reached

**Observation window:** 2026-08-06  
**People Graph baseline:** `de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Book Library baseline:** `be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b`  
**Great Library program baseline:** `main@12f4cc249b2b5dc268d05d1698fe9c5e3079327d`, plus unmerged draft branches listed below  

## Purpose and transparency boundary

This notebook preserves the reproducible reasoning behind the proposed program. It is written so another agent can challenge or reconstruct the conclusions without access to the originating conversation, tool session or local checkout.

It records:

- the question and working hypotheses;
- the repository files and branches inspected;
- direct observations;
- interpretations and confidence;
- rejected alternatives;
- unresolved uncertainty;
- tests that would falsify the recommendations.

It does not claim to reproduce private hidden token-by-token chain-of-thought. The useful engineering substitute is stronger: explicit evidence, assumptions, intermediate conclusions, alternatives, decision rules and reversal conditions.

## Initial question

The task began as:

> Find much more that the People Graph project is missing, identify deep research programs that could create 100x value, and organize agents so their work is safe and reusable.

The early working model was that value would come primarily from adding more source families and more person-to-content edges.

## Initial hypotheses

| ID | Hypothesis | Initial confidence |
| --- | --- | --- |
| H1 | More modern source families will create substantially more cross-domain people. | High |
| H2 | Identity resolution is the main graph bottleneck. | High |
| H3 | Person-to-person relationships create a major new product layer. | High |
| H4 | A richer claim and belief model creates more depth than generic topics. | Medium-high |
| H5 | The existing three repositories already provide enough structural primitives for the expansion. | Medium |
| H6 | Ten times more rows will roughly create ten times more value. | Medium-low |
| H7 | Existing documentation and implementation are aligned closely enough to scale ingestion. | Medium |

H1 through H4 survived, with qualifications. H5 through H7 did not survive inspection.

## Evidence hierarchy used

Evidence was weighted in this order:

1. executable source code and schema at exact commits;
2. deterministic tests and fixtures;
3. immutable registry records and exact branch commits;
4. repository documentation describing intended behavior;
5. official external standards, source documentation and terms;
6. agent or maintainer summaries;
7. inference.

When source code and README language conflicted, code was treated as the current behavior and the contradiction was recorded explicitly.

## Repository inspection sequence

### 1. People Graph root model

Read:

- `README.md`
- `schema/people_schema_v2.sql`
- `loaders/build_people_graph_v2.py`
- `loaders/match_identities.py`
- `loaders/ask.py`

The root model correctly emphasizes:

- one canonical graph of people who produced something;
- roles on contribution edges;
- explicit identity claims;
- reversible merges;
- separate topic vocabularies;
- life dates including BCE;
- a read-only query surface across attached databases;
- the honest limitation that current book and GitHub populations have little temporal overlap.

### 2. Book Library source and identity model

Read:

- `README.md`
- `scripts/build_books_module.py`
- `scripts/build_people_graph.py`

The Book Library correctly treats classification membership as relations, preserves raw catalog columns, distinguishes contribution roles, supports byte-addressable payload retrieval and notes jurisdiction-specific rights limitations in prose.

### 3. Great Library public research model

Read:

- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `CURRENT_STATE.md`
- `docs/question-driven-research.html`
- `schemas/common.schema.json`
- `schemas/work.schema.json`
- `schemas/release.schema.json`
- `schemas/god-question-program.schema.json`
- `site/intelligence.json`

The authored research method already describes Frontier Questions, Source Cards, atomic Claims, Assumptions, Decisions, Experiments, Answer Releases and Watch Triggers. The machine schemas implement only part of that model.

### 4. Parallel work and collision review

Inspected open draft PRs and branch comparisons.

Published draft PRs at the cut:

| Repository | PR | Head | Scope |
| --- | ---: | --- | --- |
| People Graph | #1 | `89dfec07acc38c6dadba69547a7ad4d60fbccf15` | deterministic red-team fixtures and findings |
| People Graph | #2 | `b78ff6704783dff100774063c305011ce456d704` | software and AI source-observation pilot |
| People Graph | #3 | `2f66fbe1f4523399463d9e1ff8971879a84f5b88` | v3 evidence ontology and schema |
| Great Library | #1 | `215cf63a320523f9c6405b17ae64ddb5468fb2f1` | registry spine, ADR-0005, GQ-010 and thirteen lanes |
| Great Library | #2 | `20dc000451c28c707b0a97b943d1a4b178ea9bf0` | 39-source matrix, rights and pilot portfolio |

Observed People Graph branches with zero commits ahead of `main` at the time checked:

- `pg/claims-temporal-relations-20260806`
- `pg/identity-resolution-parallel-20260806`
- `pg/living-creators-media-pilot-20260806`
- `pg/parallel-integration-contract-20260806`

The Great Library generated `site/intelligence.json` reported zero active initiatives on its then-current `main`; draft PR #1 proposes the successor program event but was not assumed merged.

## Observation-to-conclusion ledger

### O1 — The v2 builder appears unable to find its schema in a clean checkout

**Evidence**

- `loaders/build_people_graph_v2.py` sets `SCHEMA` to a file beside the loader.
- The tracked schema is `schema/people_schema_v2.sql`.

**Interpretation**

A fresh build can fail before data logic runs unless an untracked duplicate schema exists beside the loader.

**Consequence**

Clean-build reproducibility must precede ingestion scale.

**Confidence:** High.

### O2 — Stated identity policy and builder behavior conflict

**Evidence**

- README and schema commentary say name matching should create claims, not silent merges.
- `build_people_graph_v2.py` normalizes a book name and directly reuses an existing person ID when the strings match.

**Interpretation**

Identity corruption can occur before `identity_claim` review.

**Consequence**

Adapters and builders must emit source observations; identity closure should happen in a separate, reviewed projection.

**Confidence:** High.

### O3 — Claim reruns are not guaranteed idempotent

**Evidence**

- Schema commentary says one identity claim per pair.
- The table lacks a uniqueness constraint on `(person_a, person_b)`.
- The matcher uses `INSERT OR IGNORE`.

**Interpretation**

`OR IGNORE` cannot prevent duplicate pairs without a matching uniqueness constraint.

**Consequence**

Add schema invariants and replay tests before using claim volume as a quality signal.

**Confidence:** High.

### O4 — Current normalization is unsafe outside ASCII-centric naming

**Evidence**

- `match_identities.py` removes all characters outside `a-z`, spaces and commas.
- `scripts/build_people_graph.py` in the Book Library reduces keys to `a-z0-9`.
- Undated names without commas are often treated as corporate.

**Interpretation**

Accented names lose information; many names written in non-Latin scripts can collapse to empty or near-empty keys; mononyms and non-Western ordering can be misclassified.

**Consequence**

A multilingual benchmark and Unicode-first assertion model are mandatory before global expansion.

**Confidence:** High for the code behavior; corpus prevalence remains to be measured.

### O5 — Accepted claims are not used as query-time identity closure

**Evidence**

- `ask.py` searches person rows and chooses the match with the greatest content count for `--works`.
- It does not resolve accepted claim clusters.

**Interpretation**

The query surface hides duplicates heuristically instead of presenting a reviewed canonical cluster with evidence and conflicts.

**Consequence**

Identity resolution needs a materialized or computed cluster projection that query code can consume without destructive merges.

**Confidence:** High.

### O6 — A content edge is not a canonical Work

**Evidence**

- `person_content` stores `domain`, `content_ref`, `role`, title and metadata.
- There is no source-neutral Work identity or version/manifestation model.

**Interpretation**

DOI, arXiv, repository, package, video and archival records cannot be reconciled reliably as the same or related intellectual output.

**Consequence**

A Work graph becomes the central missing layer between people and evidence.

**Confidence:** High.

### O7 — Evidence from multiple sources collapses into one final edge

**Evidence**

- `person_content` has one source column and a primary key that excludes source.
- `person_topic` similarly collapses by person/topic/scheme.

**Interpretation**

Independent support, source disagreement and loader-specific deletion cannot be represented fully on one row.

**Consequence**

Separate assertion identity from assertion-evidence receipts and source ingest runs.

**Confidence:** High.

### O8 — The “nothing derived is stored” rule is violated

**Evidence**

- `person` includes `primary_tier`, `rank_score` and `topics_json`.
- The v2 builder sets a book person’s rank score from work count.

**Interpretation**

The schema retains mutable projections as if they were entity facts.

**Consequence**

Derived scores, communities, topic weights and rankings should be versioned named projections with pinned inputs.

**Confidence:** High.

### O9 — Temporal data contains visible but misleading precision

**Evidence**

- Birth and death are integer years.
- `v_contemporaries` substitutes `birth_year + 80` for missing death.
- Output does not classify the overlap as documented versus inferred.

**Interpretation**

A useful fallback becomes a factual-looking date range.

**Consequence**

Store interval, precision, uncertainty, source and bitemporal observation semantics; label inferred results.

**Confidence:** High.

### O10 — Book rights prose and build defaults conflict

**Evidence**

- Book documentation correctly warns that public-domain status is jurisdiction-specific and unknown rights should block promotion.
- `build_books_module.py` defaults every loaded record to `public_domain_us` unless overridden for the entire run.

**Interpretation**

Source membership is being used as a blanket rights assertion.

**Consequence**

Rights must be artifact-specific, evidence-backed and replaceable; unknown is the safe default.

**Confidence:** High for code behavior. Per-record correction prevalence requires a corpus audit.

### O11 — Gutenberg record count is not resolved Work count

**Evidence**

- One Book Library row is keyed by Gutenberg ID.
- No abstract Work/expression/manifestation distinction exists.

**Interpretation**

Translations, editions and ebook manifestations can be counted as separate Works or conflated unpredictably.

**Consequence**

Preserve source records but resolve them into a canonical bibliographic graph.

**Confidence:** High.

### O12 — Great Library prose is ahead of machine contracts

**Evidence**

- `docs/question-driven-research.html` describes Source Cards, Claims, Arguments, Experiments and Answer Releases in detail.
- `work.schema.json` and `release.schema.json` expose only a subset, often as nested strings or generic evidence.

**Interpretation**

The project has the right research concepts but cannot yet address, query or version all of them independently.

**Consequence**

Promote research objects to durable IDs and schemas only after measuring authoring overhead and query value.

**Confidence:** High.

## How the strategic conclusion changed

### Before inspection

The expected route to 100x value was:

```text
more sources -> more people -> more edges -> better graph
```

### After inspection

The evidence supports:

```text
reproducible source observations
  x safe identity closure
  x canonical Works
  x evidence receipts
  x temporal and rights semantics
  x decision-changing query products
```

The most important change was recognizing that **the missing center of the system is larger than the person table**. The system needs actor, Work, evidence and research-control planes with explicit boundaries.

## Alternatives considered and rejected

### A. Load many public datasets immediately

Rejected because current identity, deletion, rights, Work identity and reproducibility gaps would amplify hard-to-repair assertions.

### B. Turn every external person into a Great Library Work

Rejected because registry Work identity is for durable public works and research objects, not a replacement for the People Graph’s actor identity plane.

### C. Flatten all source vocabularies into one topic list

Rejected because source taxonomies have different semantics. Use reversible mapping claims to a concept layer instead.

### D. Keep source-native IDs as canonical IDs

Rejected because accounts, handles, package names, URLs and provider IDs can be renamed, transferred, split or retired.

### E. Destructively merge accepted identities

Rejected because identity conclusions change and source rows must remain auditable.

### F. Store one universal importance or influence score

Rejected because importance is purpose-dependent and a scalar conceals assumptions. Publish named, versioned projections instead.

### G. Infer living-person beliefs and sensitive attributes broadly

Rejected because the error, context and abuse risks are high. Claims must be source-anchored, scoped, temporally bounded and publication-controlled.

### H. Create a new monolithic repository immediately

Rejected because the Great Library already defines a split test: create a new Work/service only when code, operators, release cadence or corpus lifecycle demand independent ownership.

## What remains uncertain

- Actual production database contents were not queried in this research lane.
- Repository README counts were not independently rebuilt.
- The prevalence of each defect in production data is not established by code inspection alone.
- External source terms, quotas, prices and deletion requirements can change and require re-verification at pilot start.
- The optimal physical storage engine is intentionally undecided; logical contracts should precede sharding or graph-database selection.
- The exact boundary between SISO Knowledge and Evidence Engines remains a governance decision.
- A 10,000-person multi-domain target is a proposed milestone, not a proven attainable count; source pilots and audited overlap samples must validate it.

## Falsifiers and reversal conditions

The program should change if evidence shows any of the following:

1. A clean checkout already builds deterministically without hidden files; the clean-build finding would be corrected.
2. Production builders do not execute the silent name-reuse path; its severity would be downgraded, though the invariant should remain.
3. A labelled identity benchmark shows source-native IDs and simple rules already meet required precision across languages and difficult negatives.
4. Five benchmark research questions can be answered accurately without canonical Work resolution.
5. Per-edge single-source provenance is sufficient for correction, conflict and deletion workflows in real pilots.
6. A smaller source family yields greater verified decision value at lower rights and maintenance cost than the proposed scholarly spine.
7. Authoring first-class Claims, Source Cards or Experiments costs more than their measured retrieval and decision benefit.

## Reproduction checklist

A reviewer can reproduce this notebook by:

1. checking out the pinned People Graph and Book Library commits;
2. opening the exact files listed above;
3. confirming schema paths and primary keys;
4. tracing the normalized-name reuse branch in the v2 builder;
5. replaying the matcher twice against a tiny fixture;
6. testing normalization on accented and non-Latin names;
7. following `ask.py --works` to verify its match-selection heuristic;
8. comparing the Great Library research prose with its schemas;
9. inspecting the five draft PR heads listed above;
10. comparing reserved branches to `main` before assuming work exists.

Executable defect fixtures are delegated to People Graph draft PR #1. The v3 logical proposal is delegated to People Graph draft PR #3. Current source and rights research is delegated to Great Library draft PR #2. This notebook records why those pieces belong in one program and where their assumptions intersect.
