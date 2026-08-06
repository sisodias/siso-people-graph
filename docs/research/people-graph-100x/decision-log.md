# Decision log: People Graph 100x program

**Cut:** 2026-08-06  
**Status:** research decisions and proposals; implementation authority remains with owning repositories and reviewed pull requests  

## How decisions are recorded

Each entry contains:

- context;
- direct evidence;
- decision;
- alternatives considered;
- consequences;
- confidence;
- reversal trigger.

These entries preserve why the recommendation exists. A later correction should add a successor entry or dated amendment rather than silently editing history until the original rationale disappears.

# D-001 — Define the project as an evidence graph for knowledge production

**Context**

The original repository describes one canonical graph of people who produced books, code and video. The initial expansion idea was to add more source families and person edges.

**Evidence**

- current high-value questions require identity, Works, relationships, time and source evidence together;
- Great Library research architecture already connects questions, claims, assumptions, decisions and Answer Releases;
- the current `person_content` string edge cannot represent versions, evidence spans or source disagreement.

**Decision**

Optimize the program as an evidence-backed map of human knowledge production, not a larger profile database.

**Rejected alternatives**

- “Wikipedia with more rows” — insufficient provenance and research semantics;
- “social graph of notable people” — invites attention bias and privacy risk;
- “universal influence leaderboard” — hides purpose, units and assumptions.

**Consequences**

The center of the architecture shifts from a person table to interoperable actor, Work, evidence, temporal and research-control planes.

**Confidence:** High.

**Reversal trigger:** five consequential benchmark questions are answered accurately, reproducibly and safely by the existing person/content/topic model without the proposed planes.

# D-002 — Source observations must remain separate from canonical truth

**Context**

Current builders and exports can reuse canonical IDs by normalized name before explicit identity review.

**Evidence**

- PGRT-002 and PGRT-016;
- loader replay and source deletion defects;
- source disagreement is expected across modern datasets.

**Decision**

Every adapter emits source-native observations and literal evidence. Canonicalization is a separate decision/projection stage.

**Rejected alternatives**

- canonicalize inside each loader for convenience;
- trust a “best” source as universal authority;
- merge identical labels and repair mistakes later.

**Consequences**

More storage and explicit interfaces are required, but identity and Work decisions become reversible and auditable.

**Confidence:** High.

**Reversal trigger:** a source can prove globally unique, permanent identity semantics across the relevant entity class and can carry all correction/deletion history without cross-source conflict. Even then, its record remains evidence rather than the internal ID.

# D-003 — Canonical IDs must be source-neutral

**Context**

Current IDs encode source prefixes such as `gh:`, `yt:` and `bk:`.

**Evidence**

- mutable logins and repository transfers already break identity continuity;
- first-arriving sources should not control permanent ontology;
- one actor can exist across many systems and can lose or transfer an account.

**Decision**

Use opaque internal actor and Work IDs. Preserve provider IDs as scoped identifier assertions.

**Rejected alternatives**

- continue source-prefixed canonical IDs forever;
- choose ORCID, Wikidata or another authority as global canonical identity;
- use normalized names as stable IDs.

**Consequences**

Existing v2 IDs need compatibility aliases or migration projections. No destructive rewrite should be attempted before fixtures and query compatibility exist.

**Confidence:** High.

**Reversal trigger:** none currently known; even globally strong authority IDs are external assertions and can merge, split, deprecate or be absent.

# D-004 — Identity resolution should produce reversible clusters, not destructive merges

**Context**

The schema values reversibility, but current query behavior does not consume accepted claims and builders can silently reuse IDs.

**Evidence**

- PGRT-002, PGRT-004, PGRT-005, PGRT-009, PGRT-011 and PGRT-012;
- difficult identity cases include pseudonyms, organisations, transferred accounts and contradictory dates.

**Decision**

Preserve source actors and calculate versioned canonical clusters from accepted evidence-backed decisions. Record contradiction and reversal explicitly.

**Rejected alternatives**

- destructive row merge;
- one winning record with discarded aliases;
- automated acceptance from exact names or profile text.

**Consequences**

Queries must resolve cluster membership and display disputes. Cluster versions become part of reproducibility manifests.

**Confidence:** High.

**Reversal trigger:** a simpler model demonstrates equal reversibility, source lineage and benchmark accuracy with materially lower cost.

# D-005 — Build a first-class canonical Work graph

**Context**

People currently connect to source-native content references. Book records, papers, repositories, packages and media each have version/manifestation ambiguity.

**Evidence**

- `person_content` has no source-neutral Work identity;
- Gutenberg IDs represent source records/ebook manifestations, not reliably abstract Works;
- scholarly, software and media sources expose overlapping identifiers and versions.

**Decision**

Introduce Work, expression/version, manifestation/item, part, identifier assertion, Work relation and contribution objects.

**Rejected alternatives**

- use `domain + content_ref` as the permanent Work key;
- flatten every version into one Work;
- count every source record as a distinct Work.

**Consequences**

A labelled Work-resolution benchmark is required. Book Library, scholarly and software pilots must emit source records and relations without deciding final Work identity.

**Confidence:** High.

**Reversal trigger:** benchmark questions show no material ambiguity across source records, versions, translations, editions and mirrors—which is considered unlikely.

# D-006 — Separate assertions from evidence receipts

**Context**

Current final edges carry one source string, while multiple sources may support, contradict or replace the same assertion.

**Evidence**

- `person_content` and `person_topic` primary keys collapse source evidence;
- source deletion and independent corroboration require receipt-level provenance;
- Great Library research prose expects source-grounded Claims and contradictions.

**Decision**

Represent assertions independently from one-or-many evidence receipts and ingest runs.

**Rejected alternatives**

- concatenate provenance into JSON on the edge;
- duplicate the final edge for every source;
- keep only the latest source.

**Consequences**

Evidence independence, conflict, replacement and deletion become queryable. Projections can count evidence without confusing copies with independent sources.

**Confidence:** High.

**Reversal trigger:** a simpler representation passes correction, deletion, conflict and independence drills with equal clarity and reproducibility.

# D-007 — Make time uncertain and bitemporal

**Context**

The current graph stores integer life years and uses an unlabelled birth-plus-80 fallback for unknown death.

**Evidence**

- PGRT-014;
- affiliations, account ownership, relationships, names and beliefs change over time;
- source observation time is not the same as the time a fact held.

**Decision**

Represent valid-time intervals, observation/transaction time, precision, uncertainty and source evidence. Derived temporal assumptions must be labelled and versioned.

**Rejected alternatives**

- retain one current-state row only;
- fill unknown bounds with hidden defaults;
- store dates as unstructured prose.

**Consequences**

Queries become more complex but can distinguish documented, possible and inferred histories.

**Confidence:** High.

**Reversal trigger:** none for bitemporality; physical implementation may change if a simpler storage form preserves the same semantics.

# D-008 — Rights belong to artifacts and assertions, not source membership

**Context**

Book Library prose is careful about jurisdiction and unknown rights, but the builder can stamp one run-wide `public_domain_us` value.

**Evidence**

- Book Library code and README conflict;
- external metadata rights do not grant rights to linked papers, media, package archives, model weights or transcripts;
- source policies and individual artifacts change.

**Decision**

Attach rights assertions, jurisdiction, scope, evidence, observed date and review/withdrawal state to each relevant manifestation/item or extracted evidence object. Unknown blocks payload/publication promotion.

**Rejected alternatives**

- infer rights from hosting platform;
- assign one licence to an entire source family;
- treat public visibility as reuse permission.

**Consequences**

Source adapters need rights receipts and publication gates. Metadata and payload pipelines remain separate.

**Confidence:** High.

**Reversal trigger:** an upstream source provides an authoritative, complete, per-record, jurisdiction-appropriate rights assertion that can be replayed and corrected; SISO would still preserve that assertion rather than replacing its model.

# D-009 — Keep the Great Library as control plane, not operational graph warehouse

**Context**

The Great Library already owns durable Works, Releases, Snapshots, Decisions, Events and Frontier Questions. The People Graph and Book Library own operational source/index semantics.

**Evidence**

- Great Library README, AGENTS, CONTRIBUTING and question-driven research model;
- draft ADR-0005 in Great Library PR #1;
- generated-site and immutable-history constraints.

**Decision**

The Great Library should register, select and explain the program and its Answer Releases while referencing stable actor, Work and evidence identities. It should not absorb mutable graph databases or raw corpora.

**Rejected alternatives**

- move the People Graph database into the Great Library repository;
- make every person a Great Library Work;
- create a second parallel research registry.

**Consequences**

Cross-repository identifiers and exact source Releases are required. Operational data remains outside Git and outside generated site artifacts.

**Confidence:** High, pending acceptance or revision of ADR-0005.

**Reversal trigger:** the owning teams demonstrate that the separation creates greater inconsistency than it prevents and propose a reviewed replacement preserving identity, lineage, rights and release semantics.

# D-010 — Fix integrity before material ingestion scale

**Context**

The source universe contains high-value modern populations, but current P0 defects can corrupt identity, roles, replay and current-state truth.

**Evidence**

- eight P0 findings in red-team PR #1;
- source matrix identifies many candidate pilots;
- source pilots can proceed safely as observations and fixtures without production promotion.

**Decision**

Run research and fixture pilots in parallel, but block production-scale promotion until clean-build, replay, identity, deletion, rights and integration gates pass.

**Rejected alternatives**

- stop all source research until schema is final;
- ingest first and clean later;
- merge each pilot’s private ontology independently.

**Consequences**

Parallel velocity is retained without allowing incompatible truth models into production.

**Confidence:** High.

**Reversal trigger:** a proposed pilot is fully isolated, disposable, rights-safe and incapable of influencing canonical outputs; it may run earlier but remains explicitly non-production.

# D-011 — Start the durable modern spine with scholarly authority sources

**Context**

Gutenberg-era authors and GitHub users have little temporal overlap. Living technical authors and researchers are the natural bridge population.

**Evidence**

- repository README’s measured cross-domain limitation;
- Great Library source matrix ranks OpenAlex, Crossref, ORCID, DBLP and ROR highly;
- these sources provide durable identifiers, Works, affiliations and contributor roles.

**Decision**

Pilot OpenAlex, Crossref, ORCID, DBLP and ROR as the first durable modern identity/Work spine, with Wikidata and LoC as supporting authority evidence.

**Rejected alternatives**

- social-media-first ingestion;
- use GitHub profile real names as the main bridge;
- prioritize popularity-rich sources over strong identifiers and replayability.

**Consequences**

The first overlap experiment focuses on researchers, technical authors and software creators rather than historical book authors alone.

**Confidence:** Medium-high; measured pilot yield is still required.

**Reversal trigger:** a bounded pilot produces low strong-identifier coverage, poor overlap, unacceptable rights/deletion cost or lower decision value than another source family.

# D-012 — Treat podcasts, talks and video as an overlap accelerator, not immediate durable corpus

**Context**

Modern authors, developers and researchers often appear in podcasts and conferences. Platform terms and transcript rights vary.

**Evidence**

- current video layer is tiny;
- open feed and Podcast Namespace metadata can encode people and roles;
- source matrix marks several platform APIs discovery-only or research-more.

**Decision**

Use open feeds, event-owned exports and explicit credits for bounded observation pilots. Keep platform-specific discovery data and unauthorized transcripts out of persistent canonical storage unless terms support it.

**Rejected alternatives**

- bulk scrape YouTube or podcast platforms;
- infer guest identity from title strings alone;
- store full transcripts by default.

**Consequences**

Media can increase verified cross-domain candidates without creating a rights-heavy shadow corpus.

**Confidence:** Medium-high.

**Reversal trigger:** current official terms and publisher permissions support a broader reproducible metadata/transcript corpus with deletion and attribution controls.

# D-013 — Keep derived metrics as named versioned projections

**Context**

The current `rank_score` mixes work count, stars, ratings and followers and can change based on loader order.

**Evidence**

- PGRT-006 and PGRT-013;
- repository documentation explicitly warns against stored derived verdicts.

**Decision**

Store source observations with named units. Compute importance, bridge, community, topic and influence results through named projection versions with pinned inputs and parameters.

**Rejected alternatives**

- one universal rank field;
- separate unexplained per-domain ranks on the person row;
- silently overwrite old projection values.

**Consequences**

Products must state which projection they display. Old results can be reproduced and compared.

**Confidence:** High.

**Reversal trigger:** a value is demonstrated to be a stable source fact rather than a computation; it then belongs as a sourced observation, not a projection.

# D-014 — Make privacy, correction and abuse safety a source gate

**Context**

A richer graph about living people can be used for research or for surveillance, harassment and reputational harm.

**Evidence**

- proposed sources include profiles, affiliations, events and discourse;
- deletion obligations vary;
- claim and belief extraction can remove context or infer sensitive attributes.

**Decision**

Define privacy tiers, prohibited attributes, correction/appeal workflow, source deletion propagation, publication controls and abuse threat models before social/location-rich scale or public actor profiles.

**Rejected alternatives**

- rely only on “publicly available” status;
- publish everything and provide removal later;
- infer sensitive attributes with confidence labels.

**Consequences**

Some potentially valuable sources remain discovery-only or do-not-ingest. Public products show uncertainty and disputes.

**Confidence:** High.

**Reversal trigger:** none for governance need; exact rules should change with law, source policy and measured abuse risk.

# D-015 — Measure success by decision-changing evidence, not row count

**Context**

The user asked for 10x data and 100x value. Raw count is easy to inflate and can reward low-quality ingestion.

**Evidence**

- identity and rights errors compound with scale;
- Great Library Frontier Questions define decision, success criteria, falsifiers and evidence gaps;
- the graph’s stated purpose is to answer questions across domains.

**Decision**

Use a scorecard covering identity accuracy, multi-source verification, Work resolution, evidence completeness, temporal/rights coverage, correction latency, reproducibility and benchmark decision usefulness.

**Rejected alternatives**

- person count as primary KPI;
- edge count as primary KPI;
- a single “graph quality” score.

**Consequences**

Every source pilot needs information-gain and kill criteria. Product work is evaluated against frozen benchmark questions.

**Confidence:** High.

**Reversal trigger:** a simpler metric is empirically shown to predict downstream answer quality and safety across multiple releases.

# D-016 — Publish the reasoning in a non-overlapping documentation lane

**Context**

Multiple agents were already working on red-team, schema, source and registry lanes. The user requested that all reasoning and sources be pushed to Git.

**Evidence**

- open PR and branch collision review;
- existing path reservations do not include `docs/research/people-graph-100x/**`;
- Great Library draft PR #1 requires public handoffs and non-overlapping lanes.

**Decision**

Publish one coordination dossier in the People Graph repository on `agent/people-graph-100x-research-dossier-20260806`, touching only `docs/research/people-graph-100x/**`, and open a draft PR.

**Rejected alternatives**

- duplicate the same packet in all three repositories;
- append large comments only to existing PRs;
- modify architecture, audit or source-research paths owned by other agents;
- commit directly to `main` without review.

**Consequences**

All public reasoning is durable and reviewable while implementation authority stays with existing lanes. Great Library and Book Library can link to the accepted dossier through their own processes.

**Confidence:** High.

**Reversal trigger:** maintainers select a different canonical home; move via a traceable successor change and preserve the original commit/PR history.

# Assumption register

| ID | Assumption | Status | Confidence | Falsifier |
| --- | --- | --- | --- | --- |
| A-001 | Modern scholarly/technical sources will materially increase verified cross-domain actors. | active | medium-high | bounded pilot yields low strong-link overlap or high false-match cost |
| A-002 | Canonical Work resolution changes important answers. | active | high | five benchmark questions show no material ambiguity without it |
| A-003 | Many-receipt assertions materially improve correction and contradiction handling. | active | high | simpler edge provenance passes deletion/conflict drills equally well |
| A-004 | Users and agents will value exact evidence paths enough to justify authoring/query cost. | active | medium-high | decision-use benchmark shows negligible utility improvement |
| A-005 | Great Library, People Graph and Book Library should remain independent repositories. | active | high | reviewed operating evidence shows the split creates unsustainable drift without compensating boundaries |
| A-006 | A relational/SQLite implementation can remain useful through early v3 scale. | active | medium | measured workloads exceed acceptable latency/rebuild cost despite indexing and partitioning |
| A-007 | The proposed 10,000 verified multi-domain milestone is feasible. | active | medium | source pilots and audited samples demonstrate a much lower attainable population under quality constraints |
| A-008 | First-class claim modeling can be privacy-safe with strict sourcing and publication controls. | challenged | medium | abuse review or error studies show unacceptable harm even under proposed controls |

# Research update rule

A future agent changing a decision should add:

```text
Decision amended: D-XXX
Date:
New evidence:
Old conclusion:
New conclusion:
Why the evidence changes it:
Affected schemas/loaders/queries/PRs:
Migration or compatibility action:
Tests or benchmarks rerun:
Remaining uncertainty:
```

The goal is not to freeze this plan. The goal is to make learning visible and reversible.
