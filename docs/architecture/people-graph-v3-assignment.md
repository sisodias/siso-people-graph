# Prompt 3 assignment — additive People Graph v3 ontology and schema

**Source class:** operator-provided program brief  
**Received:** 2026-08-06  
**Extraction:** Prompt 3 only, reproduced verbatim below  
**SHA-256 of the extracted UTF-8 text including final newline:** `dd5dfe689c4b7f4e8617fcbd08d0355059ec98a2bfd7e222be952bda1932c57d`

This file preserves the exact task contract that governed the branch. It is an
input record, not a retrospective rewrite and not generated reasoning. The wider
brief also defined parallel path ownership and the `pg-observation-0.1` exchange
envelope; the relevant Prompt 3 text already repeats those constraints.

---

Prompt 3 — Additive People Graph v3 ontology and schema

You are the ontology and schema agent for sisodias/siso-people-graph. You are running in parallel and must produce a complete standalone proposal from current main. Do not wait for the red-team or identity agents.

REPOSITORIES
- Read/write: sisodias/siso-people-graph
- Read-only context: sisodias/siso-book-library, sisodias/great-library-of-siso
- Oracle is out of scope.

BRANCH
`pg/v3-ontology-schema-20260806`

EXCLUSIVE PATH OWNERSHIP
- `schema/v3/**`
- `docs/architecture/**`
- `tests/schema_v3/**`
- `docs/handoffs/schema-v3.md`
Do not modify existing v2 schema, loaders, `ask.py`, README, or shared root config.

PARALLEL RULE
Use current main as evidence. Independently audit existing code. If another lane later reaches a different conclusion, your handoff must make the disagreement easy to adjudicate. Do not create a dependency on another PR.

MISSION
Define an additive v3 model that can grow 10× in observations and 100× in research usefulness without confusing source observations, canonical entities, identity decisions, claims, or projections.

REQUIRED MODEL
Create versioned SQLite DDL, constraints, sample data, compatibility notes, and tests covering:
- `source` and `source_snapshot`: terms revision, rights state, snapshot/revision, digests, acquisition method, observation time, and deletion/tombstone obligations;
- append-oriented source observations retaining source-native identifiers and raw evidence pointers;
- canonical entity IDs independent of handles/names, with person, organisation, account, pseudonym, Work, event, venue, place, and concept types;
- identifier definitions declaring scope, uniqueness, mutability, trust class, and source authority;
- first-class Works, versions/editions/expressions, contribution roles/order/time, venues, citations, dependencies, and locators;
- identity candidate claims, positive/negative evidence, decisions, conflicts, canonical clusters/redirects, reversibility, and review lineage;
- generic evidence-backed assertions with subject, predicate, object/value, confidence, status, valid time, observed time, extraction method, and deciding authority;
- typed temporal relationships;
- aliases plus Unicode-safe search;
- rights/privacy/publication state at source, Work, evidence, and claim levels;
- named derived projections with method/version/scope metadata rather than one canonical rank/tier/influence number.

INTERIM EXCHANGE CONTRACT
Map the following standalone observation envelope into v3 tables and document the mapping. Do not change its fields in this lane:
- envelope version `pg-observation-0.1`
- source snapshot and record-native ID
- subject kind/source-native ID/label/attributes
- identifiers with scope, stability, uniqueness, and literal evidence
- contributions, relationships, evidence, and raw pointer
The envelope never assigns a canonical ID.

INVARIANTS
- No silent name merge.
- Handles are aliases; stable platform IDs are identifiers.
- Company, location, topic, biography, and real name are attributes, not unique IDs.
- Every accepted fact has provenance and observed time.
- Corrections and merges are reversible while source observations survive.
- Source vocabularies stay namespaced; crosswalks are explicit.
- A Work is not embedded only as a title string on a person edge.
- Model inference never masquerades as source observation.

DELIVERABLES
- `docs/architecture/people-graph-v3.md` with diagrams, invariants, example records/queries, rejected alternatives, scale strategy, and v2 compatibility limits.
- Versioned schema under `schema/v3/`.
- Import mapping for `pg-observation-0.1`.
- Synthetic tests for foreign keys, uniqueness scopes, conflicting stable IDs, reversible identity decisions, rights coverage, and Unicode search.
- A rebuild/migration strategy that prefers source reconstruction and never rewrites the current production asset in this PR.

ACCEPTANCE
- All lane-local schema tests pass offline.
- Existing v2 files are untouched.
- Commit, push, and open a draft PR titled `Architecture: add the People Graph v3 evidence ontology`.
- Final response: branch, commits, PR, tests, schema summary, disputed decisions, and compatibility seams.
