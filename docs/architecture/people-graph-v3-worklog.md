# Reproducible worklog — People Graph v3 ontology

**Lane:** ontology and schema  
**Branch:** `pg/v3-ontology-schema-20260806`  
**Base commit:** `de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Initial implementation commit:** `2f66fbe1f4523399463d9e1ff8971879a84f5b88`  
**Draft PR:** `sisodias/siso-people-graph#3`

## What “all reasoning” means in this repository

This package preserves the material an independent agent can inspect and rerun:
exact source instructions, pinned source files and blob hashes, observed facts,
bounded inferences, alternatives, decisions, consequences, unresolved questions,
schema modules, fixtures, tests, commands, outputs, and artifact hashes.

It does **not** publish private hidden chain-of-thought, credentials, authentication
material, ephemeral internal scratch text, or unrelated personal data. Those are
neither necessary nor appropriate for technical reproducibility. The shareable
reasoning is the evidence-to-decision record in
`people-graph-v3-evidence-ledger.md` and
`people-graph-v3-decision-record.md`.

## Phase 1 — Resolve the operating contract

1. Extracted the shared parallel rules and Prompt 3 from the user-supplied source.
2. Verified branch and exclusive ownership:
   - `schema/v3/**`
   - `docs/architecture/**`
   - `tests/schema_v3/**`
   - `docs/handoffs/schema-v3.md`
3. Pinned current `main` to
   `de048bb3b34bf931b56fd741cb46c1334acdfb98`.
4. At original lane start, no open PR was visible. During this audit-trail pass,
   PR #1 (red-team), PR #2 (software/AI pilot), and this PR #3 were visible.
   Their owned paths do not overlap this lane. Unmerged conclusions from #1/#2
   were not imported as schema authority.
5. Confirmed the requested posture: additive proposal, no v2 edits, no production
   database, no dependency on another branch.

## Phase 2 — Audit pinned current state

Inspected the exact People Graph README, v2 schema, builder, matcher, and query
surface; the Book Library person graph builder and graph loader; and the Great
Library Knowledge/question architecture. Every source is pinned by repository,
commit, path, and blob where available in the evidence ledger.

The audit separated direct observations from design inference. Examples:

- Direct observation: the v2 builder maps book people to existing rows by a
  normalized name. Bounded inference: import-time name collapse is unsafe as a
  canonical identity policy. Decision: source observations import separately and
  canonicalization requires a reviewed identity decision.
- Direct observation: `person_content` stores Work identity as domain/ref/title
  strings. Bounded inference: editions, roles, citations, dependencies, and
  locators need first-class semantics. Decision: Work and contribution tables.
- Direct observation: matcher normalization removes non-ASCII characters and
  treats any shared external-ID scheme as the strongest method. Bounded
  inference: identity strength belongs to registered identifier semantics, not a
  generic key/value table. Decision: identifier scheme registry plus Unicode
  aliases and conflict-gated decisions.

## Phase 3 — Convert requirements into invariants

The source prompt was converted into executable invariants before fixture design:

1. An observation envelope cannot assign a canonical ID.
2. Source observations and identity decisions are append-only.
3. Orphan observations fail foreign keys.
4. Unique identifiers are enforced only within declared scope.
5. Mutable/non-unique handles may collide without merging entities.
6. Conflicting stable identifiers block identity acceptance.
7. Undo closes redirects/memberships without deleting sources or entities.
8. Rights/publication state is present and valid on evidence-bearing layers.
9. Unicode labels and aliases remain searchable.
10. A Work must reference an entity of kind `work` and retains versions/roles.
11. Source vocabularies remain separate and crosswalks explicit.
12. Model output is marked and cannot masquerade as source evidence.
13. Projections are named, versioned, scoped, digest-backed, and uncertain.

## Phase 4 — Design the ordered schema

The DDL was split so reviewers can examine one responsibility at a time:

```text
00 metadata and policy vocabularies
10 sources, snapshots, receipts, observations, status events
20 observation identifiers, contributions, relationships, evidence items
30 canonical entities, Unicode aliases/search, accepted identifiers
40 Works, versions, venues, contributions, citations, dependencies, locators
50 namespaced vocabularies and explicit crosswalks
60 evidence and reversible identity decisions/clusters/redirects
70 assertions and typed temporal relationships
80 named projection definitions/runs/values and COMMIT
```

The first module opens the schema transaction and the last commits it. Therefore
modules must be concatenated in lexical order or loaded through the committed
SQLite CLI manifest. Executing each module as an independent `executescript`
causes the expected transaction-boundary failure:

```text
sqlite3.OperationalError: cannot commit - no transaction is active
```

The lane-local test helper deliberately bundles the files before execution.

## Phase 5 — Build the synthetic fixture

A tiny public-safe fixture was written to exercise all layers without production
payloads: two source snapshots; two representations of one person; Unicode Latin
and Japanese labels; stable and mutable identifiers; two Works and versions; a
venue; contribution role/order; citation; dependency; locator; namespaced topic
crosswalk; literal and model evidence; an accepted and reversible identity; an
accepted affiliation; a proposed model claim; and one named projection with an
uncertainty interval.

The fixture is intentionally not a production data sample and makes no claim
about real-source coverage or precision.

## Phase 6 — Write tests before claiming acceptance

The initial suite encoded thirteen invariants under `tests/schema_v3/` using only
Python standard library `sqlite3` and `unittest`. The audit pass adds 13 provenance/audit checks for source prompts, manifests, stable decision IDs, owned-path scope, SHA-256 receipts, relative links, and absence of database/corpus artifacts. The full suite now contains 26 tests (13 schema invariants plus 13 audit/provenance checks).

## Phase 7 — Validate

Canonical commands:

```bash
python3 tests/schema_v3/run.py
python3 -m unittest discover -s tests/schema_v3 -p 'test_*.py' -v
python3 -m py_compile tests/schema_v3/*.py
```

Schema/fixture validation uses one in-memory database with `PRAGMA foreign_keys =
ON`, then checks:

```sql
PRAGMA foreign_key_check;
PRAGMA integrity_check;
```

The exact latest transcript and runtime versions are committed in
`people-graph-v3-validation-record.md`.

## Phase 8 — Inspect and publish the complete diff

The initial implementation was published as commit
`2f66fbe1f4523399463d9e1ff8971879a84f5b88` and draft PR #3. It added only lane-
owned paths. The audit-trail follow-up adds only the same owned paths, recalculates
file hashes, reruns tests, compares the branch to `main`, and updates the existing
draft PR rather than opening a duplicate.

Publishing used authenticated GitHub repository APIs because `gh` was unavailable
and the isolated execution environment could not clone over external DNS. That
transport limitation did not change the Git objects: blobs, trees, commits, and
the branch ref are inspectable in normal Git history.

## Failed or deliberately unperformed work

- No production v3 database or release asset was built or uploaded.
- No network source acquisition was performed.
- No v2 runtime file was modified.
- No identity precision threshold was invented.
- No physical sharding choice was claimed without benchmarks.
- No GitHub Actions result was claimed when no workflow run existed.
- No hidden model scratchpad was committed; the complete shareable rationale is
  represented by source evidence, decisions, tests, and this worklog.

## Independent reconstruction path

1. Read `people-graph-v3-source-prompt.md`.
2. Verify pinned sources in `people-graph-v3-evidence-ledger.md`.
3. Review choices and reversal triggers in `people-graph-v3-decision-record.md`.
4. Apply `schema/v3/people_graph_v3.sql`, then
   `schema/v3/sample_data.sql`, or use the Python bundle loader.
5. Run `python3 tests/schema_v3/run.py`.
6. Verify `schema/v3/ARTIFACTS.sha256`.
7. Review unresolved choices in the handoff before integration.
