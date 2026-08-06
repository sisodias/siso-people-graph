# Decision log: software, packages, and AI-creator pilot

**Lane:** Prompt 10  
**Repository:** `sisodias/siso-people-graph`  
**Branch:** `pg/software-ai-pilot-20260806`  
**Base inspected:** `de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Implementation head before this audit:** `b78ff6704783dff100774063c305011ce456d704`

Each entry records the decision, competing alternatives, evidence, consequences,
and the condition that should reopen it.

## D-001 — Emit observations, never canonical entities

**Decision.** Every adapter emits `pg-observation-0.1`; it cannot assign a
canonical People Graph ID, merge target, cluster membership, or universal score.

**Alternatives considered.** Write directly into v2; invent a lane-local v3
schema; merge exact names immediately.

**Why rejected.** The prompt explicitly makes the envelope an observation
contract. Current-main identity policy already warns against silent name merges,
and concurrent schema/identity lanes own canonical persistence and adjudication.

**Consequence.** Integration must map observations later. This is deliberate
separation of acquisition evidence from identity decisions.

**Reopen when.** A reviewed canonical schema and reversible identity policy are
merged, with an explicit adapter contract for source receipts and conflicts.

## D-002 — One strict envelope constructor and validator

**Decision.** All adapters pass through `sources/software/envelope.py`.

**Alternatives considered.** Let each source define its own JSON shape; validate
only in tests; normalize after collection.

**Why rejected.** Source-specific shapes would drift and make downstream logic
source-aware. Late validation would allow unsafe identifiers or rank fields to
enter artifacts before failure.

**Consequence.** Required timestamps, rights, identifiers, evidence, and raw
pointers are enforced at creation time. Canonical/rank fields and name/company/
location/bio identifier schemes are rejected recursively.

**Reopen when.** Only through a versioned envelope migration with backward
compatibility tests and a documented consumer transition.

## D-003 — Stable source IDs are continuity evidence, not human identity

**Decision.** GitHub numeric account/repository IDs, node IDs, release IDs,
checksums, Git revision SHAs, PURLs, and SWHIDs receive explicit scope,
stability, and uniqueness declarations. Handles and repository paths are
mutable.

**Alternatives considered.** Use logins/full names as IDs; treat any stable
account ID as a canonical human; infer identity from names/company/location.

**Why rejected.** Handles and paths can change. A stable account ID proves
continuity of a source account, not enduring human control. Free-text attributes
are not unique.

**Consequence.** Rename and transfer history can be preserved without silently
merging people. Cross-platform matches remain literal evidence receipts.

**Reopen when.** Scheme semantics change upstream or production evidence shows a
supposedly stable identifier is reused or insufficiently scoped.

## D-004 — Roles live on contribution edges

**Decision.** Repository owner, contributor, release publisher, package owner,
maintainer, publisher, model creator, and related roles are typed contributions.

**Alternatives considered.** Store maintainers as aliases; copy one owner field
onto a Work; reduce all activity to “creator.”

**Why rejected.** Roles are Work-specific, ordered, temporal, and can involve
organisations. Flattening would destroy provenance and create false identities.

**Consequence.** The graph can ask who maintained, published, owned, or
contributed to a specific Work at a specific observation time.

**Reopen when.** A future ontology provides a richer contribution model; the
semantic requirement remains.

## D-005 — Works remain distinct by source-native type

**Decision.** Repositories, releases, packages, models, datasets, Spaces, and
Software Heritage archive objects remain distinct Works linked by typed edges.

**Alternatives considered.** Collapse everything under a repository; treat a
model namespace as its creator; embed release/version data only as attributes.

**Why rejected.** These objects have different identifiers, versions, licenses,
lifecycles, dependencies, and rights.

**Consequence.** Model–dataset–Space, package–release, repository–release, source
repository, dependency, and archive relationships remain queryable.

**Reopen when.** The ontology lane introduces Work/Expression/Version classes;
map types explicitly rather than flattening.

## D-006 — Metrics are timestamped observations

**Decision.** Stars, followers, downloads, forks, dependent counts, likes, and
runs carry `observed_at`; no universal person rank is produced.

**Alternatives considered.** Sum metrics across platforms; convert them to a
single “influence” score; copy current values into canonical person rows.

**Why rejected.** Units, windows, sources, and susceptibility to gaming differ.
A sum would be mathematically easy and semantically false.

**Consequence.** Consumers can build named/versioned projections later while
retaining the original observations.

**Reopen when.** A projection owner publishes a method card, source scope,
normalization, timestamp, uncertainty, and sensitivity analysis.

## D-007 — Preserve source disagreement

**Decision.** Conflicting non-empty observations are retained and measured. The
fixture includes a deliberate PyPI/ecosyste.ms license disagreement.

**Alternatives considered.** Prefer the normalized source; prefer the registry;
select the newest value; overwrite one observation.

**Why rejected.** Authority, freshness, and field semantics differ. Silent
resolution would remove the evidence needed for later adjudication.

**Consequence.** Downstream storage needs conflict and provenance support.

**Reopen when.** A field-specific adjudication policy names an authority,
version, evidence threshold, and reversible review lineage.

## D-008 — Offline synthetic fixtures before online collection

**Decision.** Tests and pilot export use tiny invented fixtures and explicitly
block network connection creation.

**Alternatives considered.** Live integration tests; commit production API
responses; run a broad crawl first.

**Why rejected.** Live tests are nondeterministic and costly. Production payloads
raise privacy, retention, rights, and reproducibility problems.

**Consequence.** The pilot validates contracts and edge cases, not production
coverage, accuracy, lag, or API cost.

**Reopen when.** A bounded online cohort has approved terms receipts, cache and
removal policy, cost budget, and public-safe recording rules.

## D-009 — Deterministic logical export

**Decision.** Records are validated, sorted by stable source fields, serialized
with sorted keys and fixed separators, preserve Unicode, reject NaN, and end in
one newline. The manifest records the logical NDJSON SHA-256.

**Alternatives considered.** Preserve adapter iteration order; pretty-print
JSON; claim binary database reproducibility.

**Why rejected.** Iteration order is fragile. Pretty printing enlarges fixtures.
No SQLite database is built in this lane, so binary database claims would be
unsupported.

**Consequence.** Reversing record order produces identical bytes and the digest
makes contract changes visible.

**Reopen when.** The envelope version changes or consumers require a different
canonical serialization; introduce a new manifest version.

## D-010 — Prefer bulk-friendly sources and bounded enrichment

**Decision.** Recommended scale order is normalized package discovery,
bounded GitHub/Hugging Face enrichment, registry-native deltas, bounded GH
Archive windows, then Software Heritage point verification.

**Alternatives considered.** Per-login GitHub crawling; full GH Archive replay;
direct npm collection immediately; bulk Software Heritage API discovery;
default download of model weights/datasets.

**Why rejected.** Those approaches are expensive, duplicate broader sources,
or cross rights/retention boundaries before an information-gain gap is measured.

**Consequence.** Direct npm remains deferred and production cost remains an
explicit unknown, not a fabricated number.

**Reopen when.** A measured field/freshness gap shows the normalized source is
insufficient and a terms/rate-limit review approves direct collection.

## D-011 — Evaluate public projects without vendoring them

**Decision.** Record reuse decisions for official OpenAPI/client/model/package-
URL/linkage projects, but keep the fixture pilot standard-library only.

**Alternatives considered.** Vendor broad clients; build an entity resolver in
this lane; copy service implementations.

**Why rejected.** The pilot does not need network clients, and identity policy
belongs elsewhere. Vendoring increases license and maintenance surface.

**Consequence.** Production acquisition can adopt maintained clients after
license/operational review without coupling fixture tests to them.

**Reopen when.** An online collector is approved and the dependency reduces
measured maintenance or correctness risk.

## D-012 — Publish reproducible rationale, not private chain-of-thought

**Decision.** The repository contains decisions, alternatives, evidence,
commands, tests, outputs, assumptions, and limitations rather than claiming a
private scratchpad is authoritative.

**Why.** Engineering work must be reviewable and falsifiable. Internal hidden
reasoning cannot be rerun or reliably distinguished from abandoned hypotheses.

**Consequence.** Agents can reconstruct the implementation from durable
artifacts while reviewers retain a clear trust boundary.
