# Agent missions and copy-paste prompts

**Cut:** 2026-08-06  
**Rule:** check `coordination-state.md` and GitHub immediately before starting; branch state may have changed after this file was written.  

## Common operating contract for every agent

Copy this preamble above one mission block:

```text
You are one bounded lane in the SISO People Graph 100x program. Work publicly and leave enough evidence that a cold agent can reproduce your conclusions without private chat context.

Before changing anything:
1. Read the repository README and this dossier under docs/research/people-graph-100x/.
2. Read the Great Library program documents in draft PR #1 and source research in draft PR #2 when relevant.
3. Inspect open PRs, branches and path reservations. Do not overwrite another lane.
4. Start from the current main of the owning repository unless the mission explicitly tells you to continue an existing branch.
5. Stay inside the exclusive path zone. Cross-lane needs become fixtures, interface proposals or explicit blockers—not edits to another lane’s files.

Hard rules:
- Source observations are not canonical truth.
- Adapters must not assign final person/actor IDs.
- Never silently merge identities, Works, claims or source records.
- Preserve literal source evidence, source revision, observed time, rights/terms revision, deletion obligations and content digests where available.
- Keep humans, organisations, pseudonyms, accounts, Works and events distinct.
- Unknown rights or privacy state blocks publication or payload promotion.
- No credentials, private corpora, personal paths, raw production databases or machine-specific topology enter Git.
- Use synthetic or tiny public-safe fixtures by default.
- Derived scores or clusters must be named, versioned projections with pinned inputs.
- Open a draft PR early. Push all useful code, tests, findings, assumptions, rejected alternatives, sources and handoff notes.

Every draft PR body and handoff must state:
- mission and branch;
- exact owned paths;
- base commit;
- files changed;
- behavior changed and compatibility preserved;
- commands and exact test results;
- source revisions and rights/privacy boundaries;
- assumptions, falsifiers and known risks;
- integration seams and merge order;
- what was deliberately not claimed.

Do not report completion unless the branch is pushed and the draft PR exists.
```

# Mission 1 — Great Library registry and public program spine

**Status at cut:** published draft PR #1; continue that PR rather than starting a competing branch.  
**Repository:** `sisodias/great-library-of-siso`  
**Branch:** `gls/people-graph-parallel-spine-20260806`  
**Head at cut:** `215cf63a320523f9c6405b17ae64ddb5468fb2f1`  

```text
Continue the Great Library People Graph control-plane lane. Review draft PR #1, its validation state, comments and current main before editing.

Own only the paths declared by its program manifest: new People Graph/Book Library/GQ-010 Works and Releases, ADR-0005, program Events, successor Snapshot, CURRENT_STATE.md, docs/people-graph-program/**, and generated site output only through repository tooling.

Objectives:
- make the People Graph and Book Library independently addressable without absorbing their operational databases;
- preserve immutable Work/Release/Snapshot/Event/Decision history;
- keep the question program distinct from an accepted Answer Release;
- define ownership across Great Library, SISO Knowledge, Foundry, Evidence Engines and the external governed data plane;
- ensure all thirteen lane reservations and handoff rules remain machine-readable;
- reconcile this dossier as evidence without copying it into generated pages manually.

Run the full Node 20 verification gate. Do not merge source-repository implementation claims into registry truth before exact source commits and evidence exist.
```

# Mission 2 — People Graph red-team fixtures

**Status at cut:** published draft PR #1; executable defect authority.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/red-team-fixtures-20260806`  
**Head at cut:** `89dfec07acc38c6dadba69547a7ad4d60fbccf15`  
**Owned paths:** `tests/red_team/**`, `docs/audits/**`, `docs/handoffs/red-team.md`.

```text
Continue the deterministic red-team lane. Preserve stable finding IDs PGRT-001 through PGRT-016.

Objectives:
- keep every known defect encoded as PASS or intentional XFAIL;
- add new fixtures only when they expose a distinct invariant;
- separate production prevalence claims from code-path behavior;
- retain tiny synthetic data and standard-library-only execution where possible;
- provide implementation lanes with exact case names to convert from XFAIL to PASS.

Do not edit production loaders or schemas. Do not weaken a fixture because another lane has not fixed it. When a production PR repairs a finding, review its behavior and update the fixture/audit in a dedicated compatible change.
```

# Mission 3 — v3 evidence ontology and schema

**Status at cut:** published draft PR #3.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/v3-ontology-schema-20260806`  
**Head at cut:** `2f66fbe1f4523399463d9e1ff8971879a84f5b88`  
**Owned paths:** `schema/v3/**`, `docs/architecture/**`, `tests/schema_v3/**`, `docs/handoffs/schema-v3.md`.

```text
Continue the additive v3 ontology lane without modifying v2 runtime behavior.

Review whether the schema covers:
- immutable source observations and ingest runs;
- source-neutral actors and scoped identifiers;
- first-class Works, versions, manifestations and contributions;
- contradiction-aware reversible identity decisions;
- many-receipt assertions;
- temporal relationships and bitemporal observations;
- rights, privacy, publication and deletion state;
- Unicode names and aliases;
- exact evidence spans and named projections.

Use synthetic fixtures and invariant tests. Record disputed modeling choices rather than silently deciding integration policy owned by other lanes. Keep physical sharding and production migration out of scope unless separately authorized.
```

# Mission 4 — Identity resolution engine and benchmark

**Status at cut:** branch existed but was identical to `main`; verify before continuing.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/identity-resolution-parallel-20260806`  
**Owned paths:** `identity_v3/**`, `loaders/match_identities.py`, `loaders/enrich_owners.py`, `tests/identity_v3/**`, `docs/handoffs/identity-resolution.md`.

```text
Build the contradiction-aware, Unicode-first identity-resolution lane.

Required deliverables:
1. a source-identifier registry declaring scope, uniqueness, mutability, transfer risk and auto-accept eligibility;
2. lossless Unicode name assertions and separate comparison/transliteration features;
3. positive and negative identity evidence records;
4. actor-kind and pseudonym constraints;
5. a versioned labelled benchmark with difficult negatives across scripts, eras and source pairs;
6. candidate generation, scoring/calibration and review-queue interfaces;
7. a reversible canonical-cluster projection consumed through a documented seam;
8. tests for rename, account transfer, common names, organisations, pseudonyms, contradictory dates, duplicate reruns and reversal.

Do not use company, location, real-name text or website strings as unique IDs. Do not auto-accept name-only matches. Do not mutate source actor rows destructively. Report precision, recall and calibration by benchmark slice; a single aggregate score is insufficient.
```

# Mission 5 — Reproducible builds, replay and deletion

**Status at cut:** declared lane; branch was not observed. Create it from current main only if it still does not exist.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/reproducible-builds-parallel-20260806`  
**Owned paths:** `build_v3/**`, `manifests/**`, `loaders/build_people_graph_v2.py`, `loaders/load_owner_topics.py`, `loaders/load_owners_into_people_graph.py`, `tests/build_v3/**`, build-specific `.github/workflows/**`, `docs/handoffs/reproducible-builds.md`.

```text
Make builds clean-checkout reproducible and source-replaceable.

Required deliverables:
- repair the tracked schema path defect with a test;
- define an ingest-run manifest containing source revision, digest, loader commit, parameters, times, counts and failures;
- prove identical logical output on repeated replay;
- replace or tombstone source observations removed or transferred upstream;
- keep historical observations without presenting them as current;
- stop additive rank inflation and any execution-count-dependent truth;
- distinguish full snapshot, incremental delta and discovery receipt inputs;
- provide clean-build CI using only declared fixtures and tracked files;
- publish logical digests and database integrity checks.

Coordinate through interfaces, not edits, with identity and schema lanes. Preserve v2 compatibility only where it does not preserve corruption.
```

# Mission 6 — Query surface, API, MCP and explorer

**Status at cut:** declared lane; branch was not observed.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/query-surface-parallel-20260806`  
**Owned paths:** `query_v3/**`, `api/**`, `mcp/**`, `viewer/**`, `loaders/ask.py`, `tests/query_v3/**`, `docs/handoffs/query-surface.md`.

```text
Build an evidence-first read surface without inventing a second index.

Required queries and products:
- actor search with source labels, canonical cluster, disputes and capability state;
- complete contribution/Work views across accepted identities;
- relationship paths with asserted versus projected steps;
- temporal queries with documented versus inferred bounds;
- concept/topic intersections without flattening schemes;
- multi-domain and bridge-person queries;
- exact evidence receipts and source-span fetch routes;
- missing-domain, stale-domain, unsupported and zero-result states;
- pagination, deterministic ordering and machine-readable error contracts;
- API and MCP contracts plus a minimal explorer using the same query layer.

Use synthetic fixtures or read-only databases. Do not hide ambiguity by choosing the row with most content. Return evidence, projection version and unresolved contradictions.
```

# Mission 7 — Book Library integrity, Work model and export

**Status at cut:** no open Book Library PR observed; verify branch existence.  
**Repository:** `sisodias/siso-book-library`  
**Branch:** `books/integrity-export-parallel-20260806`  
**Owned paths:** `scripts/**`, `index/**`, new `tests/**`, `manifests/**`, `docs/**`, `.github/workflows/**`.

```text
Repair the Book Library export seam and design a lossless path from Gutenberg source records to canonical bibliographic evidence.

Required deliverables:
- preserve every source contributor and role; never export authors only;
- emit source actors without reusing People Graph canonical IDs by display name;
- make Unicode identity keys lossless and non-canonical;
- distinguish Gutenberg source record, abstract Work, expression/translation, manifestation and retrievable item;
- create versioned Work-resolution fixtures for editions, translations and duplicates;
- change blanket rights defaults to evidence-backed artifact assertions with safe unknown state;
- preserve jurisdiction, source header/receipt, observed date and withdrawal state;
- retain current byte-range addressing and verify it independently where possible;
- provide deterministic source/export manifests and integration fixtures for People Graph.

Do not copy payload text into Git. Do not claim 79,071 distinct abstract Works until resolution supports that statement.
```

# Mission 8 — External source universe and pilot economics

**Status at cut:** published Great Library draft PR #2.  
**Repository:** `sisodias/great-library-of-siso`  
**Branch:** `gls/people-graph-source-research-20260806`  
**Head at cut:** `20dc000451c28c707b0a97b943d1a4b178ea9bf0`  
**Owned paths:** `research/people-graph-sources/**`.

```text
Continue the source-research lane only inside its reserved research directory.

Maintain the 39-source matrix with official references, terms revision, identifiers, access, freshness, snapshot/delta behavior, rights, attribution, quota, deletion, privacy, reproducibility, overlap hypothesis, information gain, cost, kill condition and state.

Requirements:
- re-check time-sensitive policies at every pilot decision;
- keep do-not-ingest and discovery-only decisions explicit;
- separate metadata rights from linked payload rights;
- keep directional cost estimates labelled as estimates;
- add evidence when a source state changes rather than rewriting history silently;
- compare reusable open-source systems without creating a second control plane.

Do not download production corpora or mutate source repositories in this lane.
```

# Mission 9 — Scholarly authority pilot

**Status at cut:** declared lane; branch was not observed.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/scholarly-authority-pilot-20260806`  
**Owned paths:** `sources/scholarly/**`, `tests/sources_scholarly/**`, `docs/source-methods/scholarly/**`, `docs/handoffs/scholarly-pilot.md`.

```text
Build an offline-first, bounded scholarly/authority observation pilot for OpenAlex, Crossref, ORCID, DBLP, ROR and optionally Wikidata/LoC fixtures.

Required deliverables:
- one adapter contract emitting pg-observation-0.1 or a reviewed successor;
- source-native actors, organisations, Works, identifiers, contributions, affiliations, funding and relations;
- literal source receipts and per-source terms/rights/deletion metadata;
- fixtures with agreement and disagreement across sources;
- no canonical person IDs or silent Work merges;
- an overlap experiment against a frozen synthetic or public-safe cohort;
- metrics for identifier coverage, strong bridge yield, disagreement, missing roles, stale records and cost;
- kill criteria for each source and a scale recommendation.

Avoid linked full text by default. Public metadata does not grant rights to underlying papers, abstracts or files.
```

# Mission 10 — Software, package and AI creator pilot

**Status at cut:** published People Graph draft PR #2.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/software-ai-pilot-20260806`  
**Head at cut:** `b78ff6704783dff100774063c305011ce456d704`.

```text
Continue the software/AI observation pilot in its existing paths and draft PR.

Preserve the separation between accounts, organisations, repositories, packages, releases, model/dataset/Space repositories, revisions and contributions. Maintain source disagreement, temporal renames/transfers, dependency links, rights receipts and deterministic NDJSON manifests.

Do not treat package coordinates, repository owners, free-text maintainers or mutable handles as human identity. Keep model weights, source archives, gated datasets and private repositories out of fixtures. Coordinate with identity and v3 ontology through documented seams only.
```

# Mission 11 — Living creators, podcasts, talks and media

**Status at cut:** branch existed but was identical to `main`; verify before continuing.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/living-creators-media-pilot-20260806`  
**Owned paths:** `sources/creators/**`, `sources/media/**`, `tests/sources_creators_media/**`, `docs/source-methods/living-creators/**`, `docs/handoffs/living-creators-pilot.md`.

```text
Design the highest-overlap modern-creator pilot using public-safe feed and event fixtures.

Prioritize open RSS/Atom, Podcast Namespace person credits, event-owned conference exports, explicit personal-site links and bounded discovery receipts. Treat Podcast Index and YouTube as discovery-only unless their current terms and retention rules support the exact pilot.

Required deliverables:
- show/feed, episode, event, session, recording and transcript-representation objects;
- host, guest, speaker, moderator, organiser and producer roles;
- exact transcript/timestamp selectors without storing unauthorized full transcripts;
- stable IDs versus mutable feed URLs and channel handles;
- deletion/withdrawal behavior and living-person publication limits;
- overlap metrics connecting modern authors, researchers, developers and speakers;
- source-specific kill criteria.

Do not scrape bios, infer sensitive traits or publish precise private locations. An appearance is not endorsement or belief.
```

# Mission 12 — Claims, temporal relations and projections

**Status at cut:** branch existed but was identical to `main`; verify before continuing.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/claims-temporal-relations-20260806`  
**Owned paths:** `claims/**`, `projections/**`, `tests/claims/**`, `docs/reasoning/**`, `docs/handoffs/claims-relations.md`.

```text
Build the evidence and temporal reasoning contracts against synthetic fixtures.

Required deliverables:
- atomic claim, claim expression, source span and evidence link;
- supports, contradicts, qualifies, depends-on and supersedes relations;
- actor stance with direct/asserted/inferred distinction;
- prediction and resolution objects;
- valid-time and observed-time intervals with uncertainty/precision;
- documented versus possible contemporaries;
- named, versioned projections for communities, influence and topic trajectories;
- exact model/prompt/code/input provenance for extracted or inferred records;
- privacy-safe publication rules for living-person claims.

Do not create personality profiles or unsupported belief assignments. Short quotations and source selectors must respect rights and context.
```

# Mission 13 — Parallel integration contract

**Status at cut:** branch existed but was identical to `main`; verify before continuing.  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/parallel-integration-contract-20260806`  
**Owned paths:** `integration/**`, `tests/integration_parallel/**`, `docs/integration/**`, `docs/handoffs/integration-contract.md`.

```text
Define and test the seams between all parallel lanes without absorbing their implementation.

Required deliverables:
- one versioned observation envelope and compatibility policy;
- source actor/Work/organisation/event/contribution fixtures from each pilot;
- schema mapping tests without canonicalization;
- identity-cluster interface consumed by query fixtures;
- Work-resolution interface consumed by contributions and claims;
- rights/privacy/publication gates;
- deletion and replay drill across source, assertion, projection and query layers;
- integration ordering, compatibility shims and migration risks;
- a synthetic end-to-end question returning an evidence path and reproducible manifest.

Do not resolve disputed ontology by editing another lane. Record required decisions and proposed options with evidence.
```

# Mission 14 — Canonical Work-resolution benchmark

**Status at cut:** additional unowned mission; verify no new lane has claimed it.  
**Repository:** `sisodias/siso-people-graph`  
**Suggested branch:** `pg/work-resolution-benchmark-20260806`  
**Exclusive paths:** `work_resolution/**`, `tests/work_resolution/**`, `benchmarks/work_resolution/**`, `docs/handoffs/work-resolution.md`.

```text
Build the benchmark and reference resolver for canonical Works across books, papers, software and media without changing the v3 schema lane.

Create labelled fixtures for:
- DOI versus arXiv versus conference/journal versions;
- repository versus package versus release;
- abstract book Work versus translation, edition and Gutenberg manifestation;
- podcast episode versus mirrored video recording;
- corrected, retracted, forked and superseding versions;
- same title/different Work and different title/same Work negatives.

Required output:
- a source-neutral Work candidate/decision contract;
- benchmark labels and rationale;
- deterministic baseline methods;
- precision/recall by relation type;
- explicit unresolved cases and review interface proposal;
- mapping requirements for Book Library and source pilots.

Do not assign production Work IDs or duplicate ontology files.
```

# Mission 15 — Decision-use and evidence-path benchmark

**Status at cut:** additional unowned mission.  
**Repository:** `sisodias/siso-people-graph`  
**Suggested branch:** `pg/research-value-benchmark-20260806`  
**Exclusive paths:** `benchmarks/decision_use/**`, `docs/research-value/**`, `tests/research_value/**`, `docs/handoffs/research-value.md`.

```text
Define whether the graph creates real research value rather than merely more records.

Freeze at least five benchmark questions spanning:
- complete output attribution;
- identity ambiguity;
- influence/evidence path;
- temporal belief or affiliation change;
- under-recognised contribution;
- source contradiction or retraction.

For each question record:
- decision or user action it could change;
- required answer shape;
- evidence completeness rubric;
- unacceptable failure modes;
- baseline answer from v2 where possible;
- target answer using proposed contracts;
- time/cost and source requirements;
- falsifiers and stopping rule.

Build synthetic query fixtures and a scoring rubric for provenance completeness, correctness, uncertainty, reproducibility and usefulness. Do not invent production answers.
```

# Mission 16 — Privacy, correction and governance contract

**Status at cut:** additional unowned mission.  
**Repository:** `sisodias/siso-people-graph`  
**Suggested branch:** `pg/privacy-corrections-governance-20260806`  
**Exclusive paths:** `governance/**`, `tests/governance/**`, `docs/privacy/**`, `docs/handoffs/privacy-governance.md`.

```text
Design the living-person privacy, correction, deletion and abuse-safety contract before social or location-rich ingestion.

Required deliverables:
- actor/publication privacy tiers;
- allowed, restricted and prohibited attribute classes;
- source retention and deletion obligations;
- correction, dispute, appeal and verified-profile workflows;
- append-only decision history with public/private evidence separation;
- abuse threat model covering stalking, doxxing, harassment, reputation scoring, political targeting and quote decontextualization;
- publication-safe uncertainty UX requirements;
- synthetic tests for source deletion, identity reversal, suppressed evidence, correction propagation and cache/projection rebuild;
- governance review checklist for every new source adapter and user-facing product.

Do not collect real sensitive personal data for fixtures. Legal conclusions must be labelled and supported by current official sources or qualified counsel; unknown jurisdictional questions remain blockers.
```

# Merge and promotion guidance

A practical order is:

1. retain red-team fixtures;
2. accept or revise the observation envelope and control-plane split;
3. land clean-build/replay safety;
4. align v3 schema, identity, Work and governance contracts;
5. integrate source pilots only as observations;
6. expose identity and Work resolution to queries;
7. land claims/temporal projections and exact evidence paths;
8. pass deletion, rights, privacy and reproducibility drills;
9. evaluate against decision-use benchmarks;
10. publish a Great Library Answer Release only when the evidence universe and limitations are explicit.

Parallel development is encouraged. Parallel promotion of incompatible truth models is not.
