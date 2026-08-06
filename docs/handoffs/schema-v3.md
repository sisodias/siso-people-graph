# Handoff — additive People Graph v3 ontology and schema

## Scope

Parallel lane: ontology and schema  
Branch: `pg/v3-ontology-schema-20260806`  
Base: `sisodias/siso-people-graph@de048bb3b34bf931b56fd741cb46c1334acdfb98`  
Open PRs visible at lane start: none

This lane defines a standalone SQLite v3 contract separating immutable source
observations, opaque canonical entities, first-class Works, reversible identity
decisions, evidence-backed assertions, temporal relationships, policy state,
namespaced vocabularies, Unicode aliases, and named projections. It does not
alter v2 behavior or ship a production database.

## Changed paths

- `schema/v3/people_graph_v3.sql`, `schema/v3/ddl/*.sql`
- `schema/v3/sample_data.sql`, `schema/v3/sample/*.sql`
- `schema/v3/README.md`
- `schema/v3/observation-envelope-mapping.md`
- `docs/architecture/people-graph-v3.md`
- `tests/schema_v3/run.py`, `support.py`, and `test_schema_*.py`
- `docs/handoffs/schema-v3.md`

No existing v2 schema, loader, query surface, root README/configuration, database,
or release asset is changed.

## Commands

```bash
python3 tests/schema_v3/run.py
python3 -m unittest discover -s tests/schema_v3 -p 'test_*.py' -v
python3 -m py_compile tests/schema_v3/*.py

sqlite3 /tmp/people-v3.sqlite < schema/v3/people_graph_v3.sql
sqlite3 /tmp/people-v3.sqlite < schema/v3/sample_data.sql
sqlite3 /tmp/people-v3.sqlite 'PRAGMA foreign_key_check; PRAGMA integrity_check;'
```

## Tests

Latest lane-local result: **13 tests passed** using Python standard library only.
The tests also verify that the CLI manifests enumerate every ordered SQL module.
Coverage includes clean DDL/sample application; foreign keys; envelope rejection
of canonical IDs; append-only observations/decisions; scoped identifier
uniqueness; safe collision of mutable IDs; conflict-blocked identity acceptance;
reversible redirects while sources survive; policy coverage; Unicode search;
first-class Work/version/role/citation/dependency semantics; explicit vocabulary
crosswalks; model provenance; and named/versioned/scoped uncertain projections.

## Assumptions

- SQLite 3.38+ includes JSON1 and FTS5.
- Opaque ULID/UUID-like entity IDs are generated outside DDL and never derived
  from names or handles.
- Source adapters supply reviewed manifests with snapshot/revision, terms,
  rights, acquisition method, digest, and removal policy.
- Large raw payloads and production databases remain in a governed external data
  plane; Git contains only schema, docs, tests, and synthetic fixtures.
- Identity/query lanes implement deterministic policy and capability adapters
  rather than importing v2 acceptance as ground truth.

## Compatibility seams

- **Observation adapters:** write exact `pg-observation-0.1` receipts, map child
  arrays using `observation-envelope-mapping.md`, and stop before canonicalization.
- **Identity lane:** consume identifier definitions, observed identifiers,
  candidates/evidence/conflicts, append-only decisions, memberships, and temporal
  redirects. The DDL does not prescribe thresholds.
- **Build lane:** concatenate ordered DDL/sample modules, verify snapshot digests,
  bulk-load deterministically, and publish counts/logical digests. No in-place v2
  mutation is expected.
- **Query lane:** capability-detect v2/v3, resolve only active redirects, and label
  observation, decision, assertion, relationship, and projection outputs.
- **Claims lane:** use evidence/assertion/relation/relationship tables and method
  cards; model output remains proposed until reviewed.
- **Book/source lanes:** map source-native Works and contributor roles into
  observation rows. Canonical Work/version creation is later and reviewed.
- **Integration lane:** run `python3 tests/schema_v3/run.py` independently and
  verify the diff is confined to owned paths.

## Known risks

- Real pilots may move JSON attributes into typed subtype tables.
- High-volume observations may require attached SQLite shards or a columnar data
  plane; this PR defines the logical contract, not final partitioning.
- FTS5 Unicode tokenization is not full locale-aware collation, transliteration,
  or morphology.
- Unified `work_version` may split into expression/edition/release subtypes.
- `(scope_type, scope_ref)` may evolve into first-class authority scopes.
- Canonical-label provenance may evolve from one observation to an accepted
  multi-evidence assertion.
- The DDL blocks acceptance when a recorded conflict is open, but candidate
  generation must detect and insert conflicts.
- Append-only receipts must still honor legal deletion by minimizing retained
  data and revoking external raw pointers when required.

## Data/rights notes

No production data, SQLite asset, corpus, credential, private path, client data,
personal note, or rights-unclear payload is included. The fixture is synthetic.
Rights/privacy/publication, terms, digests, and deletion/tombstone obligations are
explicit. Public visibility is never treated as reuse permission. Model evidence
is marked and internal by default in the fixture.

## Suggested merge considerations

1. Confirm no overlapping schema lane owns these paths.
2. Keep this merge additive; do not wire v2 loaders or `ask.py` into v3 here.
3. Keep version `3.0.0-draft.1` until scholarly, software, media, and Book
   envelopes are contract-tested.
4. Require identity policy for canonical selection and any auto-accept scheme.
5. Require build decisions for sharding, import order, digest verification, and
   release packaging.
6. Require query capability metadata before exposing v3 results.
7. Add an integration test that imports an envelope without creating an entity
   and reverses one accepted identity without changing source rows.

## Disputed decisions

- one SQLite file versus attached observation shards;
- direct observation provenance for canonical labels versus multi-evidence label
  assertions;
- text scope references versus first-class authority-scope entities;
- unified `work_version` versus expression/edition/release subtype tables;
- which stable unique identifier schemes, if any, may auto-accept.

These are explicit future seams, not dependencies on another branch.
