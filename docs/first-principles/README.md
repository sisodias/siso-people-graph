# SISO People Graph — first-principles re-derivation

**Research date:** 2026-08-06  
**Scope:** `sisodias/siso-people-graph`, `sisodias/siso-book-library`, and the People/Books/Research interfaces in `sisodias/great-library-of-siso`  
**Status:** architecture and implementation audit; findings are separated into observations, reproduced checks, inferences, and proposals  
**Primary objective:** make the reasoning, evidence, uncertainty, and proposed execution order recoverable by a cold human or agent

---

## 1. Executive conclusion

The People Graph is not primarily a database of biographies and should not optimize for the largest possible row count.

Its highest-value role is:

> Preserve source-specific actor records, resolve them into canonical public actors only when evidence permits, and project their attributed works, appearances, and source-grounded public statements without losing provenance, time, uncertainty, or the ability to reverse a decision.

The surrounding system then has four independent jobs:

1. **The Great Library** holds durable Work and Frontier Question identity, accepted public answer lineage, immutable Releases, selected Snapshots, decisions, and safe evidence references.
2. **Source-domain libraries** such as the SISO Book Library preserve upstream records, source-specific semantics, rights, artifacts, and retrieval routes.
3. **The People Graph** resolves actors and attributes contributions, appearances, affiliations, and public statements across source domains.
4. **Evidence Engines** transform exact source spans into candidate claims, contradiction records, and question-specific syntheses.

The earlier growth thesis — add many sources, people, relationships, beliefs, and a viewer — had the right destination but the wrong order of operations. Before broad ingestion, the system needs a truth kernel:

1. reproducible builds;
2. source records separate from canonical actors;
3. safe and calibrated identity resolution;
4. operational accepted-claim semantics;
5. typed observations instead of one universal score;
6. exact evidence receipts;
7. truthful query coverage and truncation;
8. immutable, verifiable data releases.

The governing value function is not raw graph size. A useful approximation is:

```text
value ≈
  important questions answerable
  × identity precision
  × evidence coverage
  × artifact retrievability
  × freshness
  ÷ (correction cost + false-merge risk + unsupported inference)
```

Ten times more rows can reduce value if they introduce twenty times more ambiguity and unsupported inference.

---

## 2. Reasoning record policy

This dossier preserves the decision-complete reasoning needed to audit or reverse the conclusions:

- the objective being optimized;
- premises and constraints;
- exact repository evidence;
- reproduced checks;
- distinctions that prevent category errors;
- alternatives considered;
- findings and confidence;
- known uncertainty;
- proposed architecture;
- sequencing and kill conditions.

It deliberately does **not** treat a token-by-token private scratchpad as an authoritative artifact. Scratchpad narration is neither stable nor a substitute for evidence. Future agents should be able to reproduce the conclusions from the source files, checks, evidence ledger, and explicit argument below.

Machine-readable findings live in [`evidence-ledger.json`](evidence-ledger.json). Reproductions live in [`../../tools/verify_audit_findings.py`](../../tools/verify_audit_findings.py). The coordinated work program lives in [`agent-program.md`](agent-program.md).

---

## 3. What was inspected

### People Graph

The audit inspected the following files at or after the initial public graph commit `de048bb3b34bf931b56fd741cb46c1334acdfb98`:

- `README.md`
- `schema/people_schema_v2.sql`
- `loaders/ask.py`
- `loaders/build_people_graph_books.py`
- `loaders/build_people_graph_v2.py`
- `loaders/load_owners_into_people_graph.py`
- `loaders/load_owner_topics.py`
- `loaders/enrich_owners.py`
- `loaders/match_identities.py`
- `.gitignore`

### Book Library

The audit inspected the source introduced by commits `c2f12b1476a2889d125e409e1652c0eb99c75f56`, `3a5d1875b395342730205100e99443308d3263e3`, and `be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b`:

- `README.md`
- `scripts/build_books_module.py`
- `scripts/build_people_graph.py`
- `scripts/load_into_people_graph.py`
- `scripts/build_locator.py`
- `scripts/probe_text_layer.py`
- `index/tier_queries.sql`
- `.gitignore`

### Great Library

The audit inspected the current model and the latest research-program evidence, including:

- `README.md`
- `AGENTS.md`
- `CURRENT_STATE.md`
- `docs/registry-model.md`
- `docs/question-driven-research.html`
- `docs/research-question-model.html`
- `registry/source-inventories/gutenberg-corpus-2026-08-03.json`
- `registry/works/frontier-question-gq-009.json`
- `schemas/release.schema.json`
- commit `12f4cc249b2b5dc268d05d1698fe9c5e3079327d`

The GitHub connector exposed source and history but did not expose arbitrary SQL execution against the published 688 MB graph release asset. Published row counts are therefore treated as repository claims, not independently re-counted observations. Small SQLite checks were reproduced against synthetic databases where noted.

---

## 4. First principles

### 4.1 The product begins with a question, not a warehouse

The Great Library research model is correct that collection is supply and a consequential question is demand. The system creates value when evidence changes an assumption, decision, experiment, or accepted answer.

Therefore:

- source acquisition should be prioritized by expected information gain;
- enrichment should be driven by unresolved high-value questions;
- whole-corpus claim extraction is not the default;
- a graph metric is useful only when it improves a real query or decision.

GQ-009 records a measured extraction ceiling: indiscriminate claim extraction across the existing passage corpus exceeds the stated token budget by orders of magnitude. That is a structural reason for question-driven retrieval, not merely a preference.

### 4.2 Source observations are not canonical truth

A source can assert:

- a GitHub account owns a repository;
- a Gutenberg catalog row lists an author string;
- a podcast feed lists a guest;
- a conference page lists a speaker;
- a profile supplies a name, company, or location.

Those are source observations. They do not by themselves prove that two records represent the same human, that an account is a human, or that the observed attribution is globally canonical.

The system must preserve the source record even after canonical resolution. Otherwise a correction destroys the evidence needed to explain what changed.

### 4.3 Identity is a decision over evidence

Identity resolution is not string normalization. It is a decision that one or more source actors belong to the same canonical actor.

A correct identity system needs:

- positive evidence;
- negative or contradictory evidence;
- issuer semantics for identifiers;
- time bounds;
- a policy version;
- decision status;
- review provenance;
- reversible assignments;
- benchmarked error rates.

A confidence label such as `0.90` is not automatically a probability. It becomes calibrated only when tested against representative labelled examples.

### 4.4 Roles are local to contributions

A person can author one work, translate another, edit a third, maintain a repository, host an interview, and appear as a guest. These are contribution or participation roles, not permanent person types.

The existing decision to keep roles on edges is correct and must be expanded rather than weakened.

### 4.5 An artifact ID is not a Work

A Gutenberg ID, repository full name, video ID, DOI, edition, translation, release, and abstract intellectual Work are not interchangeable.

The minimum useful hierarchy is:

```text
Work
  └── Expression or Version
        └── Artifact or Edition
              └── Locator
```

This distinction prevents translations, editions, compilations, mirrors, and releases from being counted as if the original creator directly produced every artifact.

### 4.6 A topic is not a belief

A work being catalogued under an LCSH heading or a repository carrying a GitHub topic does not establish what the actor believes.

The source-grounded relation is:

```text
actor → contributed_to → work
work  → classified_as → source topic
```

An actor output-subject profile may be derived from those relations. A belief or position requires a dated statement with an exact source span, context, modality, and interpretation status.

### 4.7 A reference is valuable only when it dereferences

An ID without a route to the underlying artifact is a navigation hint, not evidence. A model summary without a URL, digest, quotation, citation, or source span is a lead, not an accepted claim.

The latest GQ-009 update demonstrates this directly: question-addressable exports existed, but their evidence records contained only extracted summaries and could not replace manual evidence links.

### 4.8 Time is part of the fact

Names, account control, affiliations, locations, roles, statements, metrics, and relationships change. The system needs at least:

- source observation time;
- event or valid time;
- artifact publication time;
- date precision;
- explicit estimation status.

An unknown death year filled with `birth + 80` may be a useful query assumption, but it is not an observed death date and must never be returned as one.

### 4.9 Derived projections must be disposable

Rankings, communities, topic profiles, influence paths, under-recognition analyses, and multi-domain counts are useful projections. They must carry method, inputs, version, date, assumptions, and known bias.

They should not overwrite source observations or become unexplained universal fields.

### 4.10 Public knowledge production is not a licence for surveillance

The graph should map public creative and intellectual output, not aggregate every discoverable personal attribute.

Important boundaries:

- do not deanonymize pseudonymous actors merely because clues can be combined;
- do not collect private contact details or unnecessary fine-grained location history;
- do not equate public availability with ethical necessity;
- retain rights and publication boundaries per source and assertion;
- keep private corpora and private operational evidence outside the public repository.

---

## 5. Ten distinctions the system must never collapse

| Distinction | Failure caused by collapse |
| --- | --- |
| source record ≠ human | Catalog strings, accounts, projects, organizations, and bots become false people. |
| account ≠ actor | Shared accounts, renamed accounts, multiple accounts, and changing control are misrepresented. |
| owner ≠ creator | Repository ownership becomes false authorship or maintenance attribution. |
| subject ≠ belief | Catalog metadata is misreported as a human position. |
| lifetime overlap ≠ relationship | Possible temporal coexistence becomes a fictitious conversation or influence edge. |
| shared attribute ≠ shared identity | Names, employers, locations, and websites create false merges. |
| confidence label ≠ calibrated probability | Heuristic numbers create unjustified certainty. |
| popularity ≠ value | Stars, followers, citations, age, and visibility biases collapse into one ranking. |
| reference ≠ retrievable evidence | IDs and model summaries cannot be independently checked. |
| indexed output ≠ complete output | Partial source coverage is narrated as “everything this person produced.” |

---

## 6. Findings

### Severity definitions

- **P0:** can corrupt identity, prevent a documented clean build, or make a core guarantee false.
- **P1:** materially misstates semantics, reproducibility, or query truth.
- **P2:** valuable design improvement after correctness is established.

### 6.1 P0 — The documented V2 clean-build schema path is wrong

`loaders/build_people_graph_v2.py` computes:

```python
SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "people_schema_v2.sql")
```

That resolves to `loaders/people_schema_v2.sql`. The repository stores the schema at `schema/people_schema_v2.sql`.

A clean checkout therefore cannot follow the documented build command without an unrecorded local file copy or path change.

**Why it matters:** every downstream guarantee depends on being able to recreate the database from source.

**Required correction:** resolve the schema from the repository root, add a clean-checkout smoke test, and make the builder fail with an explicit path error.

### 6.2 P0 — Shared attributes can enter the near-certain identity path

`loaders/enrich_owners.py` writes all of these values into `external_ids`:

- `real_name`
- `x_handle`
- `website`
- `github_login`
- `github_id`
- `company`
- `location`

`loaders/match_identities.py` then reads every `(platform, value)` pair and, when repeated, proposes `shared_external_id` at confidence `0.98`.

There is no issuer-unique allowlist.

This means that repeated values such as:

- the same common real name;
- the same employer;
- the same city;
- the same organization website;

can be treated as near-certain evidence that two records are the same actor.

For a shared attribute used by 100 accounts, the pairwise loop can propose:

```text
100 × 99 / 2 = 4,950
```

near-certain same-person pairs.

**Required correction:** separate identifiers from descriptive attributes. Restrict automatic identity evidence to documented issuer-unique identifiers. Treat mutable handles as candidates with time semantics. Names, employers, locations, topics, follower counts, and generic websites must never use the shared-identifier acceptance path.

### 6.3 P0 — Accepted identity claims do not change query results

`identity_claim` can record `proposed`, `accepted`, or `rejected`, but `loaders/ask.py` does not consume accepted claims.

`--works` instead:

1. performs a name search;
2. chooses whichever raw matching person row has the largest content count;
3. returns only that row’s content.

There is no implemented path from an accepted claim to:

- canonical membership;
- aggregated works;
- aliases;
- canonical dates;
- a query-visible resolved actor;
- a reversible split.

**Conclusion:** the current repository contains an identity review table, not yet an operating identity-resolution layer.

### 6.4 P0 — Silent name merging still occurs before identity claims

`build_people_graph_v2.py` matches book people into existing graph people by lowercased, whitespace-normalized name and directly assigns book edges to the existing ID.

That bypasses `identity_claim`, even though the schema and README state that name-only matching should be explicit, evidenced, and reversible.

The Book Library also retains `scripts/load_into_people_graph.py`, an older direct integration path that performs normalized-name matching against another graph schema.

**Required correction:** source-domain actor rows must remain distinct. The People Graph should ingest source actor records and then assign them to canonical actors through one resolution policy. Retire or clearly mark old direct-write integrations.

### 6.5 P0 — One universal `rank_score` contains incompatible quantities

The current graph uses `rank_score` for several different meanings:

- inherited V1 rank;
- book work count;
- summed repository stars;
- average model-rated repository value added to an existing value;
- GitHub follower count replacing an earlier value.

These values have different units, observation times, sources, biases, and meanings.

`load_owner_topics.py` can also add its derived value again on repeated runs, so that path is not idempotent.

**Required correction:** replace the universal field with typed metric observations:

```text
metric_observation
  subject
  metric_type
  value
  unit
  source
  observed_at
  valid_at
  method_version
```

Rankings become named, versioned projections over selected observations.

### 6.6 P1 — The FTS query is written in a form SQLite rejects

The FTS branch in `who()` uses:

```sql
WHERE people.person_search MATCH ?
```

A minimal SQLite reproduction returns:

```text
no such column: people.person_search
```

The unqualified FTS table name works:

```sql
WHERE person_search MATCH ?
```

The exception is silently caught, so the query falls back to `LIKE`, hiding the failure and bypassing the index.

**Required correction:** fix the query and test that the FTS path was actually used rather than merely returning a correct fallback result.

### 6.7 P1 — “Everything produced” is stronger than the query contract

`ask.py --works` describes its result as everything a person produced, but it:

- selects one heuristic name match;
- ignores accepted identity claims;
- limits rows to 200;
- reports `count` as returned rows rather than total matching rows;
- exposes no `truncated` flag;
- does not declare a complete source universe;
- does not distinguish abstract Works from editions or source artifacts.

A truthful response should say:

> Works attributed to this resolved actor in the currently indexed source snapshots.

It should disclose:

```json
{
  "as_of": "...",
  "sources_searched": [],
  "sources_missing": [],
  "identity_resolution": {
    "status": "accepted|ambiguous|unresolved",
    "source_records": [],
    "evidence": []
  },
  "total_matching_rows": 0,
  "returned_rows": 0,
  "truncated": false,
  "known_coverage_gaps": []
}
```

### 6.8 P1 — `person_topic` overstates what source metadata proves

LCSH headings describe works. GitHub topics and languages describe repositories. Rolling them directly onto a person can be useful as a derived output profile, but the table name and README examples encourage stronger interpretation.

It does not prove expertise, endorsement, belief, or centrality.

**Required correction:** preserve source-level classifications and derive actor output profiles with role and method visible. Programming language remains a repository characteristic unless a separate assertion supports an actor skill.

### 6.9 P1 — Lifetime overlap is presented too strongly

`v_contemporaries` finds possible lifespan overlap. When death year is missing, it assumes birth year plus 80.

The README describes an “actual conversation,” but the view establishes only possible temporal coexistence. It does not prove contact, correspondence, influence, shared location, language access, or awareness.

**Required correction:** rename the projection to `v_possible_lifetime_overlap`, expose date sources and precision, mark estimated endpoints, and keep relationship claims separate.

### 6.10 P1 — The core entity is broader than a person

The schema supports `human`, `organisation`, `pseudonym`, and `unknown`. GitHub loaders add organizations and unknown actors, while the V2 migration hardcodes inherited V1 rows as `human`.

A repository owner can also be a project, collective, bot, shared team account, or persona.

**Required correction:** use a canonical internal `actor` abstraction with types such as:

```text
human
organisation
collective
pseudonym
persona
automated_agent
unknown
```

Accounts become separate source entities linked through evidenced, potentially time-bounded control relations.

### 6.11 P1 — The release and reproducibility contract is incomplete

The repositories state that large database assets can be replaced. Replaceability is operationally useful but incompatible with immutable evidentiary versions unless every replacement receives a new version, manifest, and digest.

The Book source inventory says the index is rebuildable byte-for-byte, but the builder writes the wall clock into each record. Identical source input therefore produces different database content unless time is pinned.

The Book README says `locator.sqlite` records SHA-256 per book, while the checked-in locator schema has no hash column and the inspected repository contains no payload-packaging path that computes those per-book hashes.

**Required correction:** publish immutable data releases with pinned source snapshots, builder commit, policy version, row counts, validation report, and cryptographic digests. Corrections create successor releases rather than replacing bytes beneath an existing identity.

### 6.12 P1 — Book extraction profiles contain SQL and policy ambiguity

The Book Library’s tier views are useful research profiles, but:

- core selection checks one-letter values against `bookcase`, while the builder turns classifications such as `QA` into two-letter bookcases;
- the extraction queue uses `UNION` over rows that include different `reason` values, so a book can remain in several rows despite the “deduped” description;
- “tier” reads like universal value rather than a versioned purpose-specific query profile.

**Required correction:** filter section-level policy using `section`, retain all membership reasons in a separate relation or aggregate, and name the policy as a versioned extraction profile tied to a decision purpose.

### 6.13 P1 — Evidence transformation remains the decisive missing organ

The current graph can connect an actor to a work and a work to a topic. It cannot yet support a reliable answer about what the actor argued, rejected, predicted, or changed their mind about.

Every accepted statement needs at least:

```text
source artifact identity
artifact version or digest
exact source locator or span
observed date
statement time when known
assertion or extraction method
method version
support/challenge direction
rights and quotation state
review status
```

A generated summary without this receipt is a research lead.

### 6.14 P1 — Automated contracts are missing

The public People Graph commit contains schema, loaders, and a query script but no checked-in test suite or CI workflow. Before parallel source ingestion, the repository needs:

- clean-build smoke tests;
- parser fixtures;
- identity positive and negative fixtures;
- idempotence tests;
- query contract tests;
- schema invariants;
- source snapshot validation;
- release reproducibility checks;
- privacy and secret scanning.

---

## 7. The re-derived canonical model

The central separation is:

```text
observation → evidence → hypothesis → decision → projection
```

### 7.1 Immutable source observations

```text
source_snapshot
source_actor
source_account
source_work
source_artifact
source_event
source_identifier
source_attribution
source_classification
```

Examples:

- GitHub account ID 123 used login `example` when snapshot S was observed;
- Gutenberg catalog item 84 contained a particular author string and role;
- a podcast feed listed a guest;
- a conference page listed a speaker.

These rows preserve the upstream assertion without pretending it is globally canonical.

### 7.2 Evidence receipts

```text
evidence_receipt
  evidence_id
  source_snapshot_id
  artifact_id
  locator
  source_span
  observed_at
  content_digest
  extraction_method
  method_version
  rights_state
```

All identity, attribution, relationship, and statement decisions point to receipts.

### 7.3 Canonical actors

```text
actor
  actor_id              opaque SISO identifier
  kind
  public_label
  state
```

The canonical actor ID should not be `gh:login` or `bk:name`. Those are source identifiers and may change or be corrected.

### 7.4 Resolution assignments

```text
actor_resolution
  source_actor_id
  actor_id
  status                proposed | accepted | rejected | disputed
  method
  policy_version
  score_model
  score
  valid_from
  valid_to
  decided_by
```

Supporting and challenging evidence should be separate rows.

This is safer than treating pairwise claims as the canonical object. Several source records can map to one actor without destructive merging, and a bad assignment can be withdrawn independently.

#### Initial auto-resolution policy

Automatic acceptance should be restricted to:

- the same stable identifier from the same documented issuer;
- a verified reciprocal link whose uniqueness semantics are understood;
- an explicit authority crosswalk.

Names, dates, employers, topics, locations, coauthors, writing similarity, and mutable handles may rank candidates or provide negative evidence, but should not independently trigger automatic acceptance.

### 7.5 Works, versions, artifacts, and contributions

```text
work
expression_or_version
artifact
artifact_locator
contribution
```

A contribution carries:

- actor;
- target level;
- role;
- source assertion;
- valid time;
- evidence;
- resolution or review status.

Examples:

- author → Work;
- translator → Expression;
- editor → Edition;
- scanner/OCR contributor → Artifact;
- repository maintainer → Repository or Release;
- host/guest → Event occurrence.

### 7.6 Events and participation

```text
event_series
event_occurrence
session
participation
```

This covers conferences, lectures, podcast episodes, interviews, panels, courses, standards meetings, and public institutional events.

Many person-to-person relations should be derived from shared work or event structures rather than asserted directly.

### 7.7 Statements and positions

The primitive is not an inferred inner belief. It is a source-grounded public statement:

```text
actor
  → expressed | endorsed | rejected | questioned | predicted
  → proposition
  in exact source span
  at time
  with modality and context
```

A record distinguishes:

- direct quotation;
- faithful paraphrase;
- model-extracted candidate;
- accepted interpretation;
- description of another view;
- hypothetical argument;
- satire or quotation;
- later supersession.

A belief profile is, at most, an explicitly uncertain projection over repeated public statements.

### 7.8 Derived projections

Useful but disposable projections include:

- output-subject profiles;
- communities;
- influence paths;
- multi-domain actors;
- possible lifespan overlap;
- under-recognition analyses;
- rankings;
- recommendation graphs;
- topic crosswalks.

Every projection carries method, version, inputs, date, assumptions, and known bias.

---

## 8. Correct repository boundaries

### Great Library

Owns:

- durable system and Frontier Question identity;
- immutable software, dataset, and Answer Releases;
- selected Snapshots;
- public decisions and research contracts;
- publication-safe evidence references.

It should register the Book Library and People Graph as independently addressable Works and their meaningful dataset versions as Releases. It should not create hundreds of thousands of Work records for graph actors.

### Book Library

Owns:

- upstream Gutenberg snapshots;
- lossless catalog metadata;
- source-specific parsing;
- source actors and attributions;
- source works, editions, and artifact locators;
- rights;
- payload packaging and integrity;
- versioned normalized exports.

It should not write directly into a particular People Graph schema.

### People Graph

Owns:

- canonical actor identity;
- source-actor resolution;
- aliases and identifiers through time;
- canonical contribution projections;
- events and participation;
- organizations and affiliations;
- evidence-preserving corrections;
- truthful cross-domain query contracts;
- portable read snapshots.

### Evidence Engines

Owns:

- source-span extraction;
- candidate propositions;
- support and contradiction;
- statement interpretation;
- evidence grading;
- question-specific synthesis.

---

## 9. Data and release architecture

SQLite remains a strong portable read snapshot. It does not need to be replaced merely because the logical data is a graph.

A practical scale path is:

```text
immutable source exports     Parquet or NDJSON
build and analytical joins   DuckDB / SQL pipelines
portable agent snapshot      SQLite
optional traversal service   derived API or graph engine
public identity and lineage  Great Library manifests
```

A release bundle should contain:

```text
manifest.json
source_snapshots.parquet
source_actors.parquet
actors.parquet
actor_resolutions.parquet
works.parquet
artifacts.parquet
contributions.parquet
events.parquet
participations.parquet
evidence_receipts.parquet
metrics.parquet
people_graph.sqlite
validation.json
checksums.sha256
```

The manifest binds:

- schema version;
- upstream snapshot identifiers and digests;
- source repository commit;
- builder commit;
- policy versions;
- row counts;
- integrity digests;
- rights states;
- validation results;
- known coverage gaps;
- predecessor release.

A corrected binary becomes a successor release. Existing evidentiary bytes are not replaced beneath the same release identity.

---

## 10. Query truth contract

Every agent-facing query should answer not only “what was found?” but also:

- which source snapshots were searched;
- when they were observed;
- which expected sources were absent;
- whether identity is accepted, ambiguous, or unresolved;
- which source records participated;
- why the resolution is believed;
- total matches versus returned matches;
- truncation and pagination;
- asserted versus derived fields;
- evidence locators;
- known coverage gaps.

Canonical test questions:

1. Who is this actor?
2. Which source actors are assigned to them, and why?
3. What output is attributed in the indexed source universe?
4. Which artifacts can be fetched now?
5. Which topics classify the works, and which actor profiles are derived?
6. Which public statements are directly evidenced?
7. Which relationships are asserted, derived, or merely possible?
8. What evidence challenges the current resolution or interpretation?
9. What is missing from the source universe?
10. What changed since the previous release?

---

## 11. Re-ranked research portfolio

| Earlier direction | Re-derived decision |
| --- | --- |
| Complete public-output graph | Keep, but define completeness relative to declared source snapshots and distinguish Works, versions, artifacts, and roles. |
| Identity resolution | Make the absolute first priority. Build benchmarks, negative evidence, issuer semantics, and operational assignments. |
| Person-to-person relationships | Derive collaboration from contributions and events; reserve asserted relationships for exact evidence. |
| Influence graph | Start with citations, acknowledgements, dependencies, and explicit influence statements. Delay broad inference. |
| Belief graph | Replace with a dated, source-grounded statement and position graph. |
| Intellectual timelines | Promote to foundational infrastructure. Time belongs on identity, affiliation, contribution, metrics, and statements. |
| Communities and schools | Keep as versioned analytic projections unless formal membership is sourced. |
| Under-recognized people | Keep as transparent comparison families, never one universal importance score. |
| Topic ontology | Preserve raw vocabularies and add reversible mapping claims: equivalent, broader, narrower, related, implementation-of. |
| Knowledge supply chains | High value after Work/version/dependency semantics are stable. |
| Predictions and track records | Model as a statement subtype with condition, deadline, confidence, and resolution evidence. |
| Reading and recommendation graph | Store explicit recommendations, syllabi, citations, reviews, and endorsements with evidence. |
| Event graph | Promote near the top; events are a high-signal bridge across modern creators. |
| Institution graph | Promote to foundational actor and affiliation infrastructure. |
| Evidence quality | Move from a late research theme to the first cross-system contract. |
| Viewer | Delay until identity and evidence semantics are trustworthy; a polished viewer can amplify false certainty. |

---

## 12. Correct source expansion order

After the truth kernel is safe:

1. **Authority and stable-identity sources** — reduce ambiguity and provide identifiers, aliases, and dated biographical facts.
2. **Event-rich modern sources** — conferences, podcasts, talks, interviews, and courses create meaningful overlap among living authors, developers, researchers, and speakers.
3. **Modern scholarly and technical output** — papers, preprints, technical books, package registries, and public professional profiles connect authorship, code, institutions, and citations.
4. **Creator-controlled public surfaces** — personal sites, newsletters, blogs, and reading lists often provide reciprocal links and explicit statements.
5. **Broad social and forum sources** — ingest only for bounded questions; preserve pseudonymity unless the actor explicitly links identities.

Source selection should maximize expected answer value per unit of identity risk, rights cost, ingestion cost, and maintenance cost — not raw row count.

---

## 13. Immediate engineering order

### Phase 0 — Stop corruption and make the build executable

1. Fix the V2 schema path.
2. Add a clean-checkout fixture build.
3. Restrict shared-identifier matching to an explicit issuer-unique allowlist.
4. Block company, location, real name, and generic websites from near-certain identity matching.
5. Restrict or remove arbitrary method auto-acceptance.
6. Add positive and negative identity fixtures.
7. Fix the FTS query and prove the FTS path executes.

### Phase 1 — Make identity decisions operational

1. Introduce source actors and opaque canonical actors.
2. Replace silent name merging with assignments.
3. Add supporting and challenging evidence.
4. Build a canonical actor projection from accepted assignments.
5. Make `who`, `works`, and profile queries consume it.
6. Preserve unresolved alternatives.
7. Implement assignment withdrawal and actor split tests.

### Phase 2 — Correct semantics

1. Replace `rank_score` with typed observations.
2. Separate source classifications from actor output profiles.
3. Rename and qualify possible lifetime overlap.
4. Add Work/version/artifact/contribution semantics.
5. Add temporal precision and estimation fields.
6. Retire direct source-library writes into graph internals.

### Phase 3 — Reproducible releases and truthful queries

1. Pin inputs and builder commits.
2. Publish checksums and validation reports.
3. Expose source coverage, identity status, total counts, truncation, and evidence.
4. Register graph and dataset Releases in the Great Library.
5. Make corrected releases immutable successors.

### Phase 4 — High-information expansion

1. authority identifiers;
2. events and participation;
3. modern scholarly and technical works;
4. institutions and affiliations;
5. public statements and claims;
6. topic crosswalks;
7. derived relationships and communities;
8. viewer and API.

---

## 14. Ten deep research programs

### R1 — Identity-resolution safety benchmark

**Question:** What evidence is sufficient to assign heterogeneous source records to one public actor without unacceptable false merges?

**Deliverables:** labelled positive and negative pairs, multilingual fixtures, pseudonym cases, contradiction cases, calibrated methods, acceptance policy, review queue, and split tests.

**Kill condition:** no method auto-accepts until its error rate is measured on representative held-out cases.

### R2 — Shared evidence-receipt contract

**Question:** What minimum receipt allows an assertion to be independently reopened and checked?

**Deliverables:** cross-repository schema for artifact identity, source span, digest, observation time, method version, rights, support/challenge direction, and review status.

**Kill condition:** a record that cannot dereference to public evidence or an authorized evidence owner is not accepted evidence.

### R3 — Work, expression, artifact model

**Question:** What is the smallest model that distinguishes an intellectual Work from translations, editions, releases, source records, and bytes?

**Deliverables:** schema, role placement rules, Gutenberg fixtures, repository fixtures, duplicate-work tests, and migration plan.

**Kill condition:** reject complexity that does not improve real queries or cannot be supported by source metadata.

### R4 — Query truth contract

**Question:** What must every answer disclose about identity, coverage, truncation, evidence, and uncertainty?

**Deliverables:** golden questions, JSON schemas, fixtures, and compatibility policy.

**Kill condition:** no query may use “all” or “everything” without a declared source universe and completeness state.

### R5 — Source-overlap economics

**Question:** Which source family creates the most useful new answers per unit of ingestion, rights, identity, and maintenance cost?

**Deliverables:** ranked source matrix using stable IDs, contribution edges, event participation, time coverage, evidence addressability, rights, overlap with unresolved valuable actors, and Frontier Question demand.

**Kill condition:** raw record count cannot be the primary selection metric.

### R6 — Event and participation ontology

**Question:** Can podcasts, conferences, talks, interviews, and institutional events become the highest-signal bridge across modern creators?

**Deliverables:** event schema, participant roles, series/occurrence distinction, recording and transcript locators, evidence rules, and one pilot loader.

**Kill condition:** do not create social relationships when shared participation is the only evidence.

### R7 — Temporal and uncertainty semantics

**Question:** How should approximate, conflicting, and changing dates be represented?

**Deliverables:** valid time, observation time, publication time, date precision, circa/range support, conflict rules, and a revised lifetime-overlap projection.

**Kill condition:** estimated dates never appear without assumption and precision.

### R8 — Topic and concept crosswalk

**Question:** How can LCSH, GitHub topics, languages, conference tracks, and curated concepts be queried together without flattening meaning?

**Deliverables:** mapping-claim schema, relation types, evidence, versioning, and evaluation set.

**Kill condition:** raw source labels remain unchanged and every mapping is independently removable.

### R9 — Immutable data-release protocol

**Question:** Can every graph or corpus index be reconstructed or independently verified from pinned inputs?

**Deliverables:** manifest, checksums, builder receipt, deterministic-content rules, validation report, Great Library records, and successor policy.

**Kill condition:** never replace bytes beneath an immutable release identity.

### R10 — Statement and position extraction

**Question:** Can agents extract dated, attributable propositions without confusing quotation, reporting, argument, speculation, and endorsement?

**Deliverables:** proposition model, stance and modality taxonomy, source-span fixtures, contradiction model, human-review gates, and one question-driven pilot.

**Kill condition:** no inferred belief is published as a fact about a person.

---

## 15. Alternatives considered

### A. Keep the current person row as both source record and canonical identity

**Rejected.** It cannot safely represent several accounts, source conflicts, handle changes, shared accounts, split decisions, or one source actor assigned to an organization rather than a human.

### B. Improve name normalization and continue direct merging

**Rejected as a canonical strategy.** Better normalization improves candidate generation but does not make names unique. It also creates transliteration and multilingual failure modes and can increase false confidence.

### C. Put all graph entities into the Great Library registry

**Rejected.** The Great Library is durable identity and lineage for independently addressable Works, Releases, questions, and decisions. Hundreds of thousands of operational actor rows belong in the graph data plane.

### D. Replace SQLite immediately with a graph database

**Rejected for now.** The primary failures are semantic and evidentiary, not traversal-engine limits. SQLite is a strong portable read snapshot. A graph service can be derived later when measured query patterns justify it.

### E. Extract claims from the entire corpus before defining questions

**Rejected.** GQ-009’s measured token economics show that indiscriminate extraction is structurally uneconomic. Question-driven selection also produces more relevant and reviewable evidence.

### F. Build the visual graph first

**Rejected.** Visualization can make weak identity and inferred relationships appear more authoritative. Build trustworthy contracts first.

### G. Create one universal importance score

**Rejected.** Popularity, scholarly impact, infrastructure dependency, maintenance, pedagogy, translation, and attention disparity are different dimensions with different biases.

---

## 16. Confidence and uncertainty

### High-confidence findings

- schema path mismatch;
- FTS query form fails in SQLite and is silently bypassed;
- matcher treats every repeated external-id platform/value as near-certain identity evidence;
- enrichment stores descriptive attributes in the same table consumed by that path;
- accepted claims are not used by `ask.py`;
- V2 build performs silent exact-name merging;
- `rank_score` carries incompatible meanings;
- query limit and count semantics overstate completeness;
- locator schema does not contain the README-claimed per-book SHA-256 field;
- current public repositories lack a checked-in automated test contract.

### Medium-confidence architectural conclusions

- source actor and canonical actor separation is the safest long-term model;
- event-rich sources will create more meaningful modern overlap than indiscriminate social ingestion;
- Work/version/artifact semantics are necessary for trustworthy cross-edition output queries;
- typed observations will outperform universal scores for future projections.

These are strongly reasoned but should still be tested against representative queries and migration fixtures.

### Unverified in this audit

- the exact current contents of the published graph and book SQLite release assets;
- current release-asset checksums and whether remote bytes have ever been replaced;
- actual false-positive rate of current identity proposals;
- performance at full scale after the proposed model changes;
- exact overlap yield of candidate new source families;
- current GitHub Actions behavior, because no workflow was found in the inspected public source.

Future agents must not convert these unknowns into claims.

---

## 17. Agent operating rules

A cold agent continuing this work must:

1. read this dossier and `evidence-ledger.json`;
2. run `python3 tools/verify_audit_findings.py`;
3. distinguish observation, reproduction, inference, and proposal in every commit;
4. pin exact source commits or snapshots;
5. create negative identity fixtures before changing match thresholds;
6. never auto-accept an identifier without documenting issuer uniqueness and time semantics;
7. never publish a relationship stronger than its evidence;
8. never call indexed output complete without a declared source universe;
9. never store a derived score without units, source, date, and method version;
10. never replace an immutable release artifact in place;
11. keep public-data, rights, privacy, and pseudonymity boundaries explicit;
12. report failed hypotheses and null results, not only successful additions.

The detailed parallel work split is in [`agent-program.md`](agent-program.md).

---

## 18. Final decision

The People Graph should become the trustworthy actor-resolution and attribution layer for a question-driven research system.

The target flow is:

```text
Frontier Question
  → declared evidence universe
  → source snapshots
  → source actors, works, events, and artifacts
  → evidence-backed canonical resolution
  → contributions and dated public statements
  → supporting and contradicting source spans
  → graded answer
  → immutable Answer Release
  → watch trigger and successor
```

The first 100× improvement will not come from ten times more data.

It will come from making the first important query one hundred times more trustworthy.
