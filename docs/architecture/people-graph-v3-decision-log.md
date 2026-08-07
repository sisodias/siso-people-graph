# People Graph v3 decision log

All decisions are **proposed** until the draft PR is reviewed and merged. Each
record identifies evidence, alternatives, consequences, reversibility, and a
falsifier or open integration question.

## D-001 — build v3 beside v2; reconstruct from sources

- **Evidence:** E-101, E-102, E-103, assignment rebuild requirement.
- **Alternatives:** alter the current v2 asset in place; add columns gradually;
  reinterpret v2 rows as complete v3 provenance.
- **Decision:** ship standalone `3.0.0-draft.1` DDL and rebuild a fresh database
  from declared snapshots/observations.
- **Why:** v2 cannot recover evidence it never retained, and an in-place rewrite
  would risk the published asset and parallel consumers.
- **Consequence:** coexistence requires adapters and parity validation.
- **Reversible:** yes; v2 remains untouched.
- **Falsifier/open question:** a measured migration may later be safe for a
  constrained subset, but it must not fabricate missing provenance.

## D-002 — separate source observations from canonical entities

- **Evidence:** E-103 and E-202 show ingestion and identity reuse can occur in the
  same loading path.
- **Alternatives:** one row per source record; directly upsert canonical people;
  canonicalize inside envelope import.
- **Decision:** append source observations first; canonical entity creation and
  identity resolution are later reviewed operations.
- **Consequence:** one source record can survive rejected or reversed identity.
- **Reversible:** source rows are immutable; canonical decisions are temporal.
- **Falsifier/open question:** none for the logical separation; physical storage
  can change if the separation remains observable.

## D-003 — use opaque canonical IDs

- **Evidence:** E-102 uses domain-shaped IDs; E-104 normalizes names for matching;
  E-201 derives Book person keys from names/life dates.
- **Alternatives:** `gh:<login>`, `bk:<normalized-name>`, hash of display name,
  authority ID as primary key.
- **Decision:** canonical entity IDs are generated independently of attributes
  and source-native identifiers.
- **Consequence:** identifiers and aliases require joins, but renames and source
  changes do not rewrite identity.
- **Reversible:** identifier assignments can change without changing entity ID.
- **Falsifier/open question:** choose UUID/ULID generation policy outside DDL.

## D-004 — register identifier semantics before identity use

- **Evidence:** E-104's `shared_external_id` treats platform/value pairs as the
  strongest available method; the assignment forbids names, companies,
  locations, topics, biographies, and real names as unique IDs.
- **Alternatives:** hard-code a safe-scheme list in each matcher; accept every
  external ID as unique; store only scheme/value strings.
- **Decision:** `identifier_scheme` records scope, uniqueness, mutability, trust,
  authority, normalization version, and auto-resolution eligibility.
- **Consequence:** matchers can be policy-driven and auditable; accepted unique
  identifiers are scope-constrained.
- **Reversible:** scheme definitions are versioned and may retire.
- **Falsifier/open question:** exact schemes eligible for auto-accept are an
  identity-policy decision, not a schema default.

## D-005 — preserve envelope receipts and reject canonical IDs at import

- **Evidence:** assignment's exact `pg-observation-0.1` contract.
- **Alternatives:** transform and discard the JSON; add a canonical ID to the
  envelope; accept only child rows without a receipt.
- **Decision:** retain a hashed exact receipt, validate fixed fields, reject
  canonical/person IDs, and map child arrays to observation tables.
- **Consequence:** adapters are replayable and import cannot silently merge.
- **Reversible:** child observations can be rebuilt from receipts where rights
  permit; legal removal may revoke raw pointers while retaining a minimal event.
- **Falsifier/open question:** whether full receipt JSON may be retained depends
  on each source's rights/deletion policy.

## D-006 — make Works, versions, and contributions first-class

- **Evidence:** E-102 stores title/ref on `person_content`; E-201 retains
  person-Work-role edges; E-202 filters roles and writes Work count into rank.
- **Alternatives:** keep generic content edges; embed edition/version in JSON;
  make every source-native Work immediately canonical.
- **Decision:** source-native Work observations precede reviewed canonical Work
  entities; canonical Works have versions, contribution roles/order/time,
  venues, citations, dependencies, and locators.
- **Consequence:** richer queries and preservation of attribution semantics.
- **Reversible:** source observations survive Work dedup/split decisions.
- **Falsifier/open question:** unified `work_version` versus separate expression,
  edition, release, and manifestation subtypes needs pilot evidence.

## D-007 — represent identity as append-only decisions and temporal clusters

- **Evidence:** E-101 values reversible merges; E-102 has claims and
  `merged_into`; E-104 proposes but does not fully materialize canonical query
  state.
- **Alternatives:** overwrite losing entity; delete duplicates; store only a
  confidence score; mutate one accepted claim row.
- **Decision:** candidate + evidence + conflicts + append-only decision + cluster
  membership + temporal redirect.
- **Consequence:** acceptance affects canonical lookup while remaining undoable.
- **Reversible:** append `revoked`, close active intervals, reactivate entity.
- **Falsifier/open question:** deterministic canonical selection belongs to the
  identity implementation lane.

## D-008 — block accepted identity while a recorded conflict is open

- **Evidence:** assignment explicitly requires conflicting stable-ID handling.
- **Alternatives:** confidence score overrides conflict; permit acceptance with a
  warning; encode conflict only in free text.
- **Decision:** a trigger rejects an accepted decision when an open
  `identity_conflict` exists.
- **Consequence:** conflict detection must happen before acceptance; unresolved
  contradictions cannot be hidden by a high score.
- **Reversible:** conflicts can be resolved/waived with lineage before a new
  decision is appended.
- **Falsifier/open question:** conflict taxonomies and waiver authority need
  method cards and review policy.

## D-009 — distinguish evidence, assertions, and temporal relationships

- **Evidence:** assignment requires provenance, observed/valid time, confidence,
  extraction method, review authority, and model distinction.
- **Alternatives:** generic key/value attributes; one polymorphic edge table;
  store only extracted conclusions.
- **Decision:** evidence rows ground assertions and typed relationships;
  assertion-to-assertion relations express support/challenge/contradiction.
- **Consequence:** research answers can show what was observed versus inferred.
- **Reversible:** assertions can be rejected/withdrawn and superseding relations
  added without rewriting source evidence.
- **Falsifier/open question:** high-volume claim storage may require partitioning.

## D-010 — carry rights/privacy/publication state through evidence-bearing layers

- **Evidence:** assignment and E-301 distinguish metadata, payloads, publication,
  and governed external data.
- **Alternatives:** source-level rights only; free-text policy notes; assume public
  visibility permits reuse.
- **Decision:** normalized policy vocabularies plus required references on source
  snapshots, observations, Works, evidence, assertions, and projection runs.
- **Consequence:** public-safe projections can filter by explicit policy state.
- **Reversible:** policy state may be superseded by later governed records; raw
  pointers can be revoked.
- **Falsifier/open question:** actual rights adjudication remains source-specific
  and cannot be solved by schema enums alone.

## D-011 — keep source vocabularies namespaced and crosswalk explicitly

- **Evidence:** E-101 documents several distinct topic vocabularies; assignment
  forbids silent flattening.
- **Alternatives:** normalize identical labels into one term; copy all topics into
  free text; one global topic list.
- **Decision:** vocabulary/version/term identities remain namespaced; crosswalks
  carry mapping type, confidence, evidence, method version, and status.
- **Consequence:** same text may legitimately have different meanings/authority.
- **Reversible:** reject or supersede a crosswalk without deleting source terms.
- **Falsifier/open question:** vocabulary-specific hierarchy tables may be added.

## D-012 — use Unicode FTS for discovery, never for identity

- **Evidence:** E-104's ASCII-only normalization and assignment's Unicode-safe
  search requirement.
- **Alternatives:** ASCII canonical keys; case-folded name primary keys; external
  search service only.
- **Decision:** preserve original labels/aliases and index them through FTS5
  `unicode61 remove_diacritics 2`; IDs remain opaque.
- **Consequence:** non-Latin labels survive and Latin diacritic-insensitive lookup
  works in tested SQLite builds.
- **Reversible:** search implementation can be replaced without changing IDs.
- **Falsifier/open question:** FTS5 is not full locale morphology,
  transliteration, or culturally correct collation.

## D-013 — store rankings as named/versioned projections

- **Evidence:** E-101 warns against duplicated derived state; E-202 writes Work
  count into `rank_score`; assignment forbids one universal rank/tier/influence.
- **Alternatives:** one `rank_score`; one tier; per-domain columns on entity.
- **Decision:** projection definition + run + values, with method hash, source
  scope, as-of time, parameters, input digest, uncertainty, and policy state.
- **Consequence:** scores are reproducible and comparable only within declared
  semantics.
- **Reversible:** rerun or supersede a projection without mutating canonical rows.
- **Falsifier/open question:** physical storage and query caching need benchmarks.

## D-014 — use modular ordered DDL plus a stdlib offline test harness

- **Evidence:** parallel lane ownership, reviewability requirement, no root config
  ownership, and the need to run without database assets/network.
- **Alternatives:** one very large SQL file; introduce a migration framework;
  modify shared CI/config.
- **Decision:** lexical DDL/sample modules, SQLite CLI `.read` manifests, and
  Python stdlib application/tests.
- **Consequence:** modules are reviewable and work without third-party packages;
  CLI and Python paths are both documented.
- **Reversible:** modules can be consolidated after schema acceptance.
- **Falsifier/open question:** production build tooling belongs to the build lane.

## D-015 — do not claim production readiness from the synthetic fixture

- **Evidence:** no production asset or source pilot was in scope or loaded.
- **Alternatives:** extrapolate from schema tests; publish a production database;
  claim performance based on row-count design.
- **Decision:** label the schema draft, report only measured fixture behavior, and
  list scale/partitioning decisions as risks.
- **Consequence:** the PR is a logical contract and testable proposal, not a
  release migration.
- **Reversible:** status changes only after independent pilots and integration.
- **Falsifier/open question:** source pilots may reveal missing subtypes,
  constraints, or policy fields and should revise the draft before 3.0.0.
