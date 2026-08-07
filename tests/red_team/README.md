# People Graph v2 red-team fixtures

This lane codifies the behavior of `sisodias/siso-people-graph` at baseline commit
`de048bb3b34bf931b56fd741cb46c1334acdfb98`. It does not change production
schema, loaders, queries, or repository configuration.

## Run

```bash
python3 tests/red_team/run.py
python3 tests/red_team/run.py --json
python3 tests/red_team/run.py --list
python3 tests/red_team/run.py --case PGRT-T003 --case PGRT-T004
```

The suite uses only Python's standard library. Every SQLite database is created
inside a temporary directory and deleted after its case. No network access,
release asset, production database, or environment-specific path is required.

## Status model

- `PASS`: a claimed invariant holds.
- `XFAIL`: a documented current failure reproduced. This is green by design.
- `FAIL`: a claimed invariant failed unexpectedly.
- `XPASS`: a documented failure no longer reproduces; update the audit and
  fixture before merging a fix.
- `ERROR`: the fixture could not execute.

The process exits zero only when every case is `PASS` or `XFAIL`. This keeps
known defects visible without turning the audit lane into a permanently failing
check, while still making stale expected-failure documentation actionable.

## Fixtures

- `fixtures/adversarial_people.json` contains common labels across human,
  organisation, and pseudonym kinds.
- `fixtures/book_library_export_contract.json` pins the observed legacy export
  behavior in `sisodias/siso-book-library` at commit
  `be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b`.

Stable finding IDs and severity are recorded in
`docs/audits/people-graph-v2-findings.json`. The narrative report is
`docs/audits/people-graph-v2-red-team-2026-08-06.md`.
