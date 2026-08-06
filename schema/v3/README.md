# People Graph v3 schema (additive draft)

This directory is a standalone SQLite proposal. It does not alter, rename, or
migrate a v2 table.

## Apply and inspect

From the repository root, the committed CLI manifests load ordered modules:

```bash
sqlite3 /tmp/people-v3.sqlite < schema/v3/people_graph_v3.sql
sqlite3 /tmp/people-v3.sqlite < schema/v3/sample_data.sql
sqlite3 /tmp/people-v3.sqlite 'PRAGMA foreign_key_check; PRAGMA integrity_check;'
```

For environments without the `sqlite3` executable, the offline tests concatenate
`ddl/*.sql` and `sample/*.sql` in lexical order through Python's standard
`sqlite3` module:

```bash
python3 tests/schema_v3/run.py
```

SQLite 3.38 or newer with JSON1 and FTS5 is required.

## Layout

- `people_graph_v3.sql` — SQLite CLI manifest for the versioned DDL modules.
- `ddl/*.sql` — ordered, reviewable schema modules; the first opens and the last
  commits the schema transaction.
- `sample_data.sql` — SQLite CLI manifest for the synthetic fixture.
- `sample/*.sql` — tiny public-safe observations, entities, Works, identity,
  claims, relationships, Unicode aliases, rights, and projections.
- `observation-envelope-mapping.md` — exact mapping for
  `pg-observation-0.1` without canonicalization.

## Compatibility posture

A production migration is intentionally absent. Rebuild v3 from declared source
snapshots and replayable observation envelopes, then validate parity through
explicit projections. Keep the current v2 asset read-only until consumers have
capability-detecting adapters and the v3 build is independently accepted.
