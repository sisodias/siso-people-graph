# People Graph v3 schema (additive draft)

This directory is a standalone SQLite proposal. It does not alter, rename, or
migrate a v2 table.

## Apply and inspect

From the repository root, the committed SQLite CLI manifests load ordered
modules:

```bash
sqlite3 /tmp/people-v3.sqlite < schema/v3/people_graph_v3.sql
sqlite3 /tmp/people-v3.sqlite < schema/v3/sample_data.sql
sqlite3 /tmp/people-v3.sqlite 'PRAGMA foreign_key_check; PRAGMA integrity_check;'
```

When the `sqlite3` executable is unavailable, the offline Python harness applies
all modules in lexical order through the standard-library `sqlite3` module:

```bash
python3 tests/schema_v3/run.py
```

SQLite 3.38 or newer with JSON functions and FTS5 is required.

## Layout

- `people_graph_v3.sql` — ordered SQLite CLI DDL manifest.
- `ddl/*.sql` — versioned, reviewable schema modules; the first opens and the
  last commits the schema transaction.
- `sample_data.sql` and `sample/*.sql` — tiny public-safe observations, entities,
  Works, identity, claims, relationships, Unicode aliases, rights, and projections.
- `observation-envelope-mapping.md` — exact `pg-observation-0.1` mapping that
  stops before canonicalization.
- `SCHEMA_INVENTORY.md` — modules, tables, triggers, indexes, fixture counts,
  constraints, tests, and external responsibilities.

## Provenance and reconstruction

The proposal is reconstructable without chat history:

- `../../docs/architecture/people-graph-v3-audit-index.md` indexes the exact
  assignment, source ledgers, engineering journals, decision records, worklog,
  traceability, validation transcript, and independent review checks.
- `PROVENANCE.json` records prompt digests, pinned source commits/blobs, stable
  decision IDs, compatibility assertions, validation contract, and artifact
  metadata.
- `design_provenance.json` maps source evidence to 16 compact design decisions
  and 25 requirements.
- `traceability.json` records the compact requirement/test matrix, official
  SQLite references, validation result, and known gaps.
- `ARTIFACTS.sha256` hashes every lane file except the manifest itself.
- `tests/schema_v3/test_audit_package.py` and
  `tests/schema_v3/test_design_provenance.py` make the public record executable.

These artifacts expose all reproducible evidence, bounded inferences, decisions,
commands, outputs, and unresolved questions. Private token-by-token model
chain-of-thought and secrets are not part of the engineering artifact.

## Compatibility posture

A production migration is intentionally absent. Rebuild v3 from declared source
snapshots and replayable observation envelopes, validate parity through explicit
projections, and keep the current v2 asset read-only until consumers have
capability-detecting adapters and the v3 build is independently accepted.
