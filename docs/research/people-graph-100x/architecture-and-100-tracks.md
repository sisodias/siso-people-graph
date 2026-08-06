# Target architecture and one hundred missing tracks

## The target system

The project should evolve from a person-to-source-reference graph into a set of interoperable evidence planes:

```text
UPSTREAM SOURCES
  APIs, dumps, feeds, repositories, archives, catalogs
        |
        v
SOURCE OBSERVATION PLANE
  source, source_snapshot, ingest_run, raw_record, observation,
  terms_revision, rights_receipt, deletion_obligation, content_digest
        |
        v
CANONICAL KNOWLEDGE PLANES
  actor + identity evidence
  organisation + affiliation
  work + version + manifestation
  event + participation
  relationship + contribution
  concept + mapping claim
  claim + exact source span + argument
        |
        v
VERSIONED PROJECTIONS
  canonical identity clusters, communities, influence paths,
  topic trajectories, overlap estimates, rankings, anomaly queues
        |
        v
QUERY AND RESEARCH PLANE
  evidence paths, actor/work/claim profiles, graph API, MCP,
  Frontier Questions, assumptions, experiments, Answer Releases
        |
        v
PUBLIC CONTROL PLANE
  Great Library Works, Releases, Snapshots, Decisions, Events,
  rights-safe reading surfaces and correction history
```

## Core logical objects

### Source and provenance

```text
source
source_terms_revision
source_snapshot
source_delta
source_record
raw_pointer
ingest_run
transform_run
model_run
tombstone
provenance_receipt
```

### Actors and identity

```text
actor
actor_type
name_assertion
identifier_assertion
attribute_observation
identity_claim
identity_evidence
identity_contradiction
identity_decision
identity_cluster_projection
```

### Works and artifacts

```text
work
expression
version
manifestation
item
part
identifier_assertion
work_relation
contribution
artifact_location
rights_assertion
quality_observation
```

### Context

```text
organisation
affiliation
event
participation
place
community
membership
funding_award
relationship
```

### Evidence and reasoning

```text
concept
concept_mapping_claim
claim
claim_expression
source_span
evidence_link
claim_relation
stance
argument_node
prediction
resolution
assumption
experiment
answer_release
```

## The one hundred tracks

The tracks below are deliberately wider than an implementation backlog. They define the complete opportunity universe so that agents can choose bounded work without losing the larger system.

# I. Actor and identity architecture

## 1. Source-neutral actor IDs

Create opaque canonical actor IDs that do not encode GitHub, Gutenberg, YouTube, ORCID or the first source to materialize the entity. Preserve all provider IDs as scoped assertions.

## 2. Full actor taxonomy

Distinguish humans, organisations, collectives, families, projects, pseudonyms, fictional entities, automated accounts and unresolved source entities. Do not overload `person` with mutually incompatible semantics.

## 3. Name assertions

Store each name with source, language, script, ordering, type, confidence, validity period and preferred context. A canonical display label should be a projection, not the destruction of source names.

## 4. Global Unicode matching

Use Unicode normalization, case folding, script-aware comparison and optional transliteration while retaining original text. Benchmark accented, non-Latin, mononym, patronymic and reordered names.

## 5. External-ID lifecycle

Record when an account, identifier, domain or profile was observed, verified, renamed, transferred, deprecated or retired. Stable IDs and mutable handles must have different semantics.

## 6. Atomic identity evidence

Represent shared authority IDs, verified links, affiliation overlap, coauthor networks, commit metadata and biographical agreement as separate evidence receipts rather than a single method string.

## 7. Negative identity evidence

Capture incompatible lifetimes, simultaneous distinct activity, conflicting verified sites, mutually exclusive affiliations and explicit “different person” statements.

## 8. Identity clusters instead of forced merges

Preserve source actor records and compute reviewed canonical clusters. A rejected or reversed decision should not require reconstructing deleted rows.

## 9. Pseudonym and persona relationships

Model `pen_name_of`, `stage_identity_of`, `legal_identity_of`, `collective_pseudonym_of`, `former_name_of` and unresolved identity relationships without equating every alias.

## 10. Identity benchmark

Publish versioned positive, negative and difficult pairs across languages, eras, name frequencies, source combinations, organisations and pseudonyms. Report precision, recall and calibration by slice.

# II. Canonical Work and artifact graph

## 11. Canonical Work IDs

Introduce source-neutral identities for intellectual outputs so one Work can be described by multiple source systems.

## 12. Work–Expression–Manifestation–Item

Distinguish the conceptual Work, language/version expression, published or rendered manifestation and retrievable item. Adapt the model to books, papers, software and media rather than copying a library standard blindly.

## 13. Identifier graph

Connect DOI, ISBN, PMID, PMCID, arXiv, OpenAlex, Gutenberg, repository URLs, package coordinates, SWHIDs and platform IDs as scoped assertions with evidence.

## 14. Part hierarchy

Address chapters, sections, paragraphs, figures, tables, files, commits, notebooks, podcast chapters, transcript cues and timed media segments.

## 15. Version lineage

Model predecessor, revision, release, fork, branch, correction, retraction, superseding version and backport relationships.

## 16. Translation and adaptation graph

Represent translations, abridgements, dramatizations, commentaries, critical editions, compilations and software implementations of earlier ideas.

## 17. Contribution model

Use a controlled contribution vocabulary for writing, editing, translation, illustration, review, maintenance, data curation, supervision, funding acquisition, hosting and production.

## 18. Contribution ordering and extent

Preserve credited order, corresponding-author status, credited name, source statement, temporal bounds and contribution extent where the source supplies them.

## 19. Work identity resolution

Build labelled fixtures for title similarity, creator overlap, identifiers, dates, venue, citation context and version relations. Keep “same Work,” “version of,” and “related” distinct.

## 20. Manifestation-level rights and preservation

Attach rights, jurisdiction, availability, format, checksum, location, preservation state and takedown history to the retrievable artifact rather than only the abstract Work.

# III. Relationships, organisations and events

## 21. Person-to-person relationship graph

Add typed, directed, temporal and evidenced relationships such as collaborator, mentor, student, interviewer, correspondent, cofounder and critic.

## 22. Affiliation history

Connect actors to companies, universities, laboratories, foundations, publishers, working groups and open-source organisations with start/end uncertainty and source receipts.

## 23. Education and mentorship

Capture degree, adviser, teacher, laboratory, apprenticeship and intellectual mentorship while distinguishing formal records from inferred influence.

## 24. Collaboration graph

Derive coauthor, co-maintainer, contributor, project-team and repeated-event relationships from contribution evidence without storing unexplained permanent labels.

## 25. First-class events

Represent conferences, panels, lectures, courses, podcast episodes, interviews, workshops, standards meetings and historical events.

## 26. Appearance roles

Distinguish host, guest, interviewer, interviewee, speaker, moderator, organiser, performer and attendee where publication-safe evidence exists.

## 27. Community membership

Represent formal organisations, schools of thought, online communities and inferred “invisible colleges.” Inferred communities must name the projection and inputs.

## 28. Funding graph

Connect grants, funders, sponsors, investors, patrons and procurement awards to people, organisations, projects and outputs.

## 29. Standards governance

Link people to working groups, proposals, drafts, reviews, ballots, implementations and final standards.

## 30. Place graph

Add birthplaces, residences, institutional locations, event venues and migration histories with privacy-sensitive precision and source confidence.

# IV. Concepts, claims and arguments

## 31. Canonical Concept layer

Keep LCSH, GitHub topics, languages and curated vocabularies separate while linking them to source-neutral concepts.

## 32. Vocabulary-mapping claims

Represent exact, broader, narrower, related, translated, acronym, historical-predecessor and commonly-confused mappings as sourced reversible assertions.

## 33. Atomic Claim entity

Turn propositions into first-class addressable objects rather than burying them in summaries or topic tags.

## 34. Exact evidence anchors

Target page, paragraph, text quote, byte range, timestamp, transcript cue, commit line, issue comment or dataset cell with a digest of the referenced representation.

## 35. Claim relationships

Add supports, contradicts, qualifies, narrows, depends-on, exemplifies, repeats and supersedes relationships.

## 36. Stance model

Record whether an actor asserted, endorsed, rejected, questioned, predicted, reported or merely discussed a proposition.

## 37. Belief evolution

Track adoption, modification, qualification, abandonment and later correction of positions, preserving source and date.

## 38. Prediction graph

Capture prediction text, scope, issue date, horizon, confidence, resolution criteria, outcome and adjudication evidence.

## 39. Argument graph

Connect premises, intermediate conclusions, objections, rebuttals, assumptions and scope conditions.

## 40. Evidence independence

Trace copied reporting and common upstream sources so ten derivative articles are not counted as ten independent confirmations.

# V. Time and historical reasoning

## 41. Uncertain date representation

Support approximate, unknown, open, disputed and ranged dates using a documented standard such as EDTF-compatible values plus source assertions.

## 42. Bitemporal data

Separate valid time—when a fact held—from transaction or observation time—when the graph learned it.

## 43. Career timelines

Reconstruct roles, employers, institutions and projects over time from sourced observations.

## 44. Output timelines

Show what an actor produced during each period rather than only a lifetime aggregate.

## 45. Topic trajectories

Calculate when interests emerged, peaked, converged, diverged or disappeared through versioned projections.

## 46. Relationship intervals

Store beginning, end, uncertainty and evidence for collaborations, affiliations and memberships.

## 47. Historical-context graph

Connect works and claims to wars, discoveries, institutions, movements, policy changes and technological transitions.

## 48. Uncertainty-aware contemporaries

Return documented, possible and model-inferred overlap separately, exposing the assumption used for unknown bounds.

## 49. Source time travel

Preserve enough source snapshot and transform history to reproduce what the graph knew at an earlier release.

## 50. Temporal query language

Support questions such as “what did this person believe before 2018?” and “who collaborated during the first version of this project?”

# VI. High-leverage source acquisition

## 51. ORCID–ROR bridge

Resolve researchers and institutions through public ORCID records and canonical research-organisation identifiers, retaining visibility and replacement semantics.

## 52. Global authority bridge

Integrate Wikidata, Library of Congress, VIAF and ISNI as evidence sources with source-specific freshness, scope and licensing.

## 53. Scholarly metadata stack

Combine OpenAlex, Crossref and DataCite for works, contributors, affiliations, funders, licences and datasets while preserving disagreement.

## 54. Domain scholarly sources

Add DBLP, OpenReview, arXiv, PubMed and field repositories where they supply stronger identity, venue, review or version evidence.

## 55. Citation infrastructure

Load OpenCitations and source-native reference lists as evidenced citation assertions with provenance and correction history.

## 56. Open podcast graph

Index open feeds, episode identifiers, person credits, chapters, transcripts, locations and recommendations under feed and platform terms.

## 57. Talk and video graph

Add channels, videos, playlists, captions, conference schedules and speaker-event relationships without assuming media reuse rights.

## 58. Software-production graph

Combine GitHub events, package registries, ecosyste.ms, deps.dev and Software Heritage to distinguish owner, contributor, maintainer and downstream dependency.

## 59. Patent, grant and standards graph

Connect inventors, principal investigators, funders, organisations, working groups, drafts, standards and resulting outputs.

## 60. Public-discussion graph

Evaluate Stack Exchange, Hacker News, newsletters, blogs, mailing lists, AT Protocol sources and permissioned community sources separately rather than treating “social data” as one licence class.

# VII. Additional high-depth baskets

## 61. Course and syllabus graph

Connect instructors, institutions, courses, readings, lectures, assignments and learning outcomes.

## 62. Reading and recommendation graph

Capture bibliographies, syllabi, public reading lists, podcast recommendations, endorsements and curated collections.

## 63. Review and criticism graph

Represent who reviewed, criticised, endorsed or responded to a Work and anchor the stance to exact evidence.

## 64. Mention and quotation graph

Extract sourced mentions and quotations while explicitly avoiding the inference that every mention is influence or endorsement.

## 65. Correspondence and mailing-list graph

Model dated exchanges, thread membership and referenced Works where lawful and publication-safe.

## 66. Dataset and model graph

Add creators, maintainers, versions, licences, training relationships, evaluations, benchmarks and dependent Works.

## 67. Knowledge supply chains

Trace the software, datasets, standards, papers, institutions and people necessary for an output to exist.

## 68. Grant-to-output attribution

Connect funding periods to publications, datasets, patents, software and reported outcomes without claiming causality beyond evidence.

## 69. Patent–paper–code pathways

Find concepts moving between academic research, patents, standards and implementation.

## 70. Retraction, correction and replication

Track retractions, errata, failed and successful replications and the downstream claims or decisions affected.

# VIII. User-facing intelligence products

## 71. Evidence-first actor profile

Show names, identities, Works, affiliations, claims and disputes with provenance and temporal qualification on every section.

## 72. Universal entity search

Search actors, organisations, Works, versions, concepts, claims, events and Frontier Questions through one typed result surface.

## 73. Interactive graph explorer

Traverse typed relationships with filters for evidence, date, source family, confidence and projection version.

## 74. Evidence-path finder

Explain exactly how two actors, Works, concepts or claims are connected and distinguish asserted from inferred steps.

## 75. Bridge-person finder

Surface actors who connect otherwise separate disciplines, source families, eras or communities.

## 76. Influence-lineage explorer

Display explicit citation, dependency, acknowledged influence, reuse and model-inferred influence separately.

## 77. Disagreement map

Identify genuine proposition-level disagreement, definition differences, scope differences and apparent disagreement caused by time or context.

## 78. Belief-change timeline

Show the evidence for a position changing, including contradictory sources and uncertainty.

## 79. Under-recognised contributor explorer

Surface translators, editors, maintainers, reviewers, dataset creators, archivists and infrastructure builders overlooked by audience metrics.

## 80. Research API, copilot and MCP

Return typed results with exact evidence receipts, capability state, query plan, uncertainty and source snapshot lineage.

# IX. Trust, rights, privacy and governance

## 81. Rights-evidence registry

Never assign rights solely from source membership. Record exact evidence, jurisdiction, scope, review state and withdrawal history.

## 82. Privacy tiers

Separate historical public figures, public professionals, ordinary living people, private individuals and sensitive cases; define collection and publication limits for each.

## 83. Sensitive-attribute boundary

Prohibit unsupported inference of health, sexuality, religion, ethnicity, political alignment, home location and comparable sensitive attributes.

## 84. Correction and appeal workflow

Allow actors, maintainers and source owners to dispute identities, relationships, quotations and publication decisions with append-only resolution history.

## 85. Verified-profile claims

Permit an actor or organisation to verify identifiers without letting self-assertion erase independent evidence or disagreement.

## 86. Deletion and retention compliance

Propagate source deletions, policy requirements, privacy requests and rights changes into future snapshots, projections and public surfaces.

## 87. Abuse threat model

Design against stalking, harassment, doxxing, reputation scoring, political targeting, impersonation and decontextualized quotation.

## 88. Coverage-bias dashboards

Measure representation by era, language, script, geography, field, gender where lawfully and appropriately sourced, source family and media type.

## 89. Uncertainty UX

Prevent confidence values, inferred relationships and source disagreement from rendering as settled facts.

## 90. Public audit trail

Record which source, loader, model, reviewer or decision introduced, accepted, rejected or revised an assertion.

# X. Data operations and research operating system

## 91. Immutable source-record layer

Preserve upstream records and pointers separately from canonical entities so parsing and resolution can be replayed.

## 92. First-class ingest runs

Record loader version, source revision, checksum, parameters, start/end time, counts, failures and rights/terms revision.

## 93. Assertion store

Represent canonical edges as assertions with multiple evidence receipts rather than mutable facts with one provenance string.

## 94. Versioned projections

Compute identity clusters, rankings, communities, topic weights, similarity and anomaly queues through named reproducible projections.

## 95. Schema invariants and tests

Test clean builds, replay, duplicate claims, identity reversibility, source replacement, tombstones, foreign keys, rights gating and capability-state output.

## 96. Quality benchmark releases

Publish labelled identity, Work-resolution, role, rights, claim-extraction and temporal evaluation sets with immutable versions.

## 97. First-class Great Library research objects

Give Source Cards, Claims, Assumptions, Experiments and other repeatedly reused objects durable IDs when measured use justifies the schema cost.

## 98. Formal Answer Release

Store conclusions, claim set, evidence universe, contradictions, uncertainty, predictions, changes from prior answers and decision implications.

## 99. Executable watch triggers

Turn “review when X changes” into a machine-readable source, condition, threshold, cadence and reopening action.

## 100. Agent coordination contract

Give each agent a question, branch, exclusive paths, source boundary, artifact shape, acceptance tests, rights/privacy rules, commit protocol and public handoff.

# Priority waves

## Wave 0 — Prevent corruption

- tracks 1, 4, 5, 7, 8, 10;
- tracks 41, 42;
- tracks 81–87;
- tracks 91–96;
- all P0 red-team repairs.

## Wave 1 — Establish the missing center

- canonical Work graph: 11–20;
- actor/organisation/event contracts: 21–30;
- concepts and claim evidence: 31–40.

## Wave 2 — Load overlap-rich modern populations

- scholarly authority: 51–55;
- podcasts/talks: 56–57;
- software/AI: 58;
- grants/patents/standards: 59;
- carefully selected discourse: 60.

## Wave 3 — Turn evidence into user value

- products 71–80;
- formal research outputs 97–99;
- decision-use benchmarks and feedback into source priorities.

# Dependency rules

1. A source adapter may be piloted before final ontology only if it emits the agreed observation envelope and does not canonicalize identity.
2. A projection may be developed before production data only against synthetic and labelled fixtures with a declared version.
3. An inferred edge may never replace or masquerade as a source assertion.
4. No living-person publication surface should launch before privacy, correction and abuse reviews.
5. No source should scale before terms revision, deletion behavior, attribution and cost are recorded.
6. No Answer Release should claim reproducibility without pinned source snapshots, transforms and model versions.
7. Agent lanes may proceed in parallel, but promotion must pass the integration gates in `current-state-audit.md`.

# Why this creates 100x value

The multiplication does not come from one feature. It comes from compounding:

```text
more relevant modern actors
x safer cross-source identity
x canonical intellectual outputs
x richer temporal relationships
x proposition-level evidence
x reproducible answer paths
x rights- and privacy-aware publication
```

A graph that can merely list a person’s source rows is useful. A graph that can show who produced a Work, which version was cited, what claim it supports, who disputed it, when the position changed, which evidence is independent, what rights permit inspection and which decision changed as a result is a qualitatively different system.
