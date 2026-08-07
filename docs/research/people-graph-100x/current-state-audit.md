# Current-state audit and repair gates

**Reviewed baseline:** `de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Executable defect authority:** draft PR #1, branch `pg/red-team-fixtures-20260806`, head `89dfec07acc38c6dadba69547a7ad4d60fbccf15`  
**Status at research cut:** 22 offline cases; 3 PASS, 19 expected failures, 0 unexpected failures; 8 P0 and 8 P1 findings  

## How to use this audit

This file is the program-level interpretation of the red-team evidence. The machine-readable finding IDs, fixture behavior and exact reproduction commands live in draft PR #1. Implementation PRs should repair the relevant code and convert its expected failures to passes rather than weakening assertions here.

No bulk source ingestion should be treated as production-safe while any P0 bulk-ingestion blocker remains open.

## P0 bulk-ingestion blockers

### PGRT-001 — Clean-checkout v2 build cannot locate the tracked schema

**Evidence**

- `loaders/build_people_graph_v2.py` resolves `people_schema_v2.sql` beside the loader.
- The repository tracks the schema under `schema/people_schema_v2.sql`.

**Failure mode:** a clean rebuild fails before reading inputs.

**Repair gate:** a fresh checkout can run the documented builder with only tracked files and supplied fixture databases.

**Owner:** reproducible-build lane.

### PGRT-002 — v2 silently fuses source people by normalized display name

**Evidence:** `build_people_graph_v2.py` maps lower-cased whitespace-normalized names to existing IDs before adding book people.

**Failure mode:** different people with the same label receive one actor identity and combined attribution.

**Repair gate:** source-native people remain separate observations until an accepted, evidenced identity decision produces a reversible cluster or redirect.

**Owner:** identity-resolution lane, with build compatibility support.

### PGRT-003 — Non-unique profile attributes can be treated as 0.98 identity evidence

**Evidence**

- `match_identities.py` treats every duplicated external `(platform, value)` pair as `shared_external_id` evidence.
- `enrich_owners.py` stores values such as real name, company and location in `external_ids`.

**Failure mode:** a shared employer, city or common name can be interpreted as near-certain same-person evidence.

**Repair gate:** every identifier scheme has declared scope, uniqueness, mutability and auto-accept policy; non-identifiers are ordinary observations, not identity keys.

**Owner:** identity-resolution lane.

### PGRT-004 — Accepted identity claims are inert in canonical reads

**Evidence:** `ask.py` does not consult accepted `identity_claim` rows or `merged_into` when returning identity and work results.

**Failure mode:** review work does not change what an agent sees; duplicates and partial work sets remain.

**Repair gate:** accepted decisions produce a non-destructive canonical cluster projection consumed consistently by `who`, `works`, relationships and source adapters.

**Owner:** identity and query lanes jointly, through a versioned interface.

### PGRT-006 — Loaders are additive rather than source-replaceable

**Evidence**

- topic/rating logic can accumulate on reruns;
- removed ownership or book records are not tombstoned;
- existing output databases can retain stale rows.

**Failure mode:** replay changes truth based on execution count, and deleted or transferred source records remain active.

**Repair gate:** every loader has an ingest-run identity, source snapshot/delta identity, idempotent replay behavior and explicit replacement/tombstone semantics.

**Owner:** reproducible-build and integration lanes.

### PGRT-009 — Book identity keys collapse distinct non-Latin names

**Evidence:** book identity normalization removes characters outside ASCII `a-z`, digits, comma and space before using the result as an identity key.

**Failure mode:** different contributors written in Chinese, Arabic, Cyrillic, Devanagari, Japanese, Korean and other scripts can collapse into identical keys.

**Repair gate:** source labels remain lossless Unicode assertions; lossy comparison forms are never canonical IDs; a multilingual benchmark covers collision and recall behavior.

**Owner:** identity-resolution lane.

### PGRT-011 — GitHub login changes and repository transfers split identity

**Evidence**

- numeric GitHub IDs are observed;
- loaders still resolve people and ownership by mutable login/full-name strings.

**Failure mode:** one account becomes multiple actors after rename, while transferred repositories can remain attached to the former owner.

**Repair gate:** stable platform IDs drive account continuity; handles and repository names are temporal observations; transfer and deletion events replace prior current-state assertions.

**Owner:** identity, software-source and reproducible-build lanes.

### PGRT-016 — Book export silently merges names and drops contributor roles

**Evidence:** the pinned Book Library export reuses canonical IDs by normalized display name and exports authorship only, although the upstream book graph preserves editor, translator and other roles.

**Failure mode:** identity corruption and attribution loss occur before People Graph ingest.

**Repair gate:** the Book Library emits source actors and every source role without canonicalizing them; People Graph resolves identity separately.

**Owner:** Book Library integrity/export lane, with an integration fixture in People Graph.

## P1 integrity and query defects

### PGRT-005 — Matcher reruns duplicate claims

Add a canonical-pair uniqueness invariant, explicit evidence identity and replay tests. Multiple independent receipts should attach to one claim or assertion rather than appear as duplicate decisions.

### PGRT-007 — Enrichment overwrites canonical fields and blocks partial refresh

External profile responses should append source-scoped observations. Each field refreshes independently; one observed field must not suppress missing fields or overwrite a canonical label, actor kind, ranking projection or build timestamp.

### PGRT-008 — GitHub enrichment assumes `gh:` canonical IDs

All adapters should resolve through external identifier assertions, not canonical ID prefixes, origin values or display-name-as-login assumptions.

### PGRT-010 — Preserved aliases disappear from search

Every source label, pseudonym, transliteration and historical name should be searchable while remaining attributable to its source and time interval.

### PGRT-012 — Candidate matching ignores actor-kind conflicts

Human, organisation, pseudonym and collective relationships require explicit semantics. A known kind conflict is negative evidence or a different relationship, not an ordinary same-person candidate.

### PGRT-013 — `rank_score` mixes incompatible units

Current loaders place work count, repository stars, ratings and follower count into one field. Replace this with source observations carrying named units and named projection definitions with pinned inputs.

### PGRT-014 — Contemporaries fabricates an unlabelled lifespan end

The `birth + 80` heuristic can remain as an optional projection, but results must expose that it is inferred, its model/version and the uncertainty interval. Documented and possible overlaps must not be presented identically.

### PGRT-015 — Missing databases look like evidence-backed empty results

Every query response should state capability state per domain: available, absent, unreadable, stale, unsupported or queried-with-zero-results. An unavailable source is not negative evidence.

## Additional architectural gaps not represented by a single v2 defect

These are not necessarily bugs in the intended v2 scope; they are missing prerequisites for the 100x system.

### A1 — No source-neutral canonical actor identity

Current IDs encode the first materializing source (`gh:`, `yt:`, `bk:` or registry slug). This is useful for source traceability but unsafe as permanent canonical ontology. Introduce opaque canonical IDs and preserve source IDs as assertions.

### A2 — No first-class canonical Work graph

`person_content(domain, content_ref)` cannot reconcile DOI/arXiv/conference versions, repository/package/release relationships, podcast audio/video mirrors, or book work/expression/manifestation distinctions.

### A3 — No many-receipt assertion model

A final edge has one `source` field. Independent confirmations, contradictions, source replacements and deletion provenance need separate assertion and evidence tables.

### A4 — No bitemporal observation model

`observed_at` alone does not distinguish when an affiliation, name, account, contribution or relationship was true from when the graph learned it.

### A5 — No evidence-span contract

Research-grade claims need exact text quotes/selectors, page/paragraph positions, timestamps, transcript cues, commit lines or dataset cells, plus content digests and transform versions.

### A6 — No first-class organisation, event and community graph

Organisations currently fit imperfectly into `person`. Conferences, podcast episodes, affiliations, funding, working groups, schools and communities need typed temporal entities and relationships.

### A7 — Topic schemes are separated but not reconciled

Keeping LCSH, GitHub topics, languages and curated tags separate is correct. A reversible mapping-claim layer is still needed for cross-domain concepts.

### A8 — Rights are not assertion- and artifact-specific end to end

The Book Library build default can stamp one rights state across a source run. Rights must attach to manifestations/items, identify jurisdiction and evidence, and carry review/withdrawal state.

### A9 — Living-person privacy and publication controls are not explicit enough

The system needs collection, retention and publication tiers, sensitive-attribute restrictions, correction/appeal paths and abuse threat models before social, location or discourse ingestion.

### A10 — Great Library research prose exceeds current machine contracts

The public research method describes Source Cards, Claims, Assumptions, Experiments, contradictions and Answer Releases. Durable IDs, exact evidence selectors and formal answer contents remain incomplete in schemas.

## Integration order

The safest repair sequence is:

1. merge and retain red-team fixtures;
2. fix clean builds and replay semantics;
3. agree the source-observation envelope and source-neutral ID boundary;
4. implement Unicode-safe identity assertions and contradiction evidence;
5. expose accepted identity clusters to reads;
6. introduce canonical Work and contribution contracts;
7. add assertion/evidence, temporal, rights and deletion semantics;
8. only then expand source ingestion materially;
9. build evidence-path queries and products;
10. publish reproducible Answer Releases against benchmark questions.

Schema work, identity work and source pilots can proceed in parallel through fixtures, but production promotion must respect these gates.

## Definition of fixed

A finding is not closed because a document says so. It is fixed only when:

- a deterministic fixture fails on the old behavior and passes on the new behavior;
- replay produces an identical logical result;
- source deletion or correction has a tested propagation path;
- no incompatible source data is silently collapsed;
- the query surface exposes evidence and capability state;
- the handoff names compatibility consequences and any migration required;
- the relevant expected failure in draft PR #1 becomes a normal passing invariant.
