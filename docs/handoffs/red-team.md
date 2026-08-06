# Red-team lane handoff

## Scope

This lane adds an offline, standard-library-only failure-mode suite and two audit
artifacts for People Graph v2. It intentionally does not edit production schema,
loaders, query code, README, or root configuration.

Baseline:

- `sisodias/siso-people-graph` `main`
- `de048bb3b34bf931b56fd741cb46c1334acdfb98`
- no open pull requests at lane launch

Read-only context:

- `sisodias/siso-book-library` at
  `be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b`
- `sisodias/great-library-of-siso` at
  `12f4cc249b2b5dc268d05d1698fe9c5e3079327d`

## Changed paths

```text
tests/red_team/run.py
tests/red_team/README.md
tests/red_team/fixtures/adversarial_people.json
tests/red_team/fixtures/book_library_export_contract.json
docs/audits/people-graph-v2-red-team-2026-08-06.md
docs/audits/people-graph-v2-findings.json
docs/handoffs/red-team.md
```

Every changed path is inside the lane-owned directories from Prompt 2.

## Commands

```bash
python3 tests/red_team/run.py
python3 tests/red_team/run.py --json
python3 tests/red_team/run.py --list
python3 tests/red_team/run.py --case PGRT-T003 --case PGRT-T004
```

## Tests and measurements

Full offline run:

```text
PASS=3
XFAIL=19
FAIL=0
XPASS=0
ERROR=0
TOTAL=22
```

The runner exits zero only when every case is `PASS` or documented `XFAIL`.
`FAIL`, `XPASS`, and `ERROR` are non-zero. That makes current failure modes green
without allowing implementation fixes or fixture breakage to pass silently.

Severity register:

```text
P0=8
P1=8
```

Bulk-ingestion blockers:

```text
PGRT-001 PGRT-002 PGRT-003 PGRT-004
PGRT-006 PGRT-009 PGRT-011 PGRT-016
```

## Assumptions

- The suite targets the baseline commit named above and reads production modules
  from the current checkout at runtime.
- SQLite FTS5 is available in the Python SQLite build, matching the production
  schema's existing requirement.
- Tiny fixtures establish code-path behavior, not corpus-wide prevalence.
- Expected failures are deliberate audit state, not skipped tests.
- The Book Library contract fixture is pinned to a public commit, path, and blob
  SHA so this repository remains independently testable offline.

## Compatibility seams

- Implementation PRs should preserve finding IDs (`PGRT-001` … `PGRT-016`) in
  commit and PR descriptions.
- Fixes should convert the relevant `XFAIL` case to `PASS` and update both audit
  artifacts in the same lane; an unexplained `XPASS` is intentionally non-zero.
- `PGRT-T022` is a control proving that People Graph v2 preserves supplied Book
  roles. Do not solve PGRT-016 by removing role assertions from the v2 builder;
  the affected seam is the pinned Book export contract.
- `PGRT-T007` proves exact owner-source reruns are already duplicate-free. The
  required change for PGRT-006/011 is replacement, tombstone, and stable-ID
  behavior rather than indiscriminate deletion of idempotency safeguards.
- The tests import loaders by file path and monkeypatch only the network fetch
  function. Moving or renaming production entry points requires a coordinated
  fixture update.

## Known risks

- Several production fixes will need schema or loader changes outside this
  lane's ownership. This PR must remain tests/docs only.
- A fix can expose a second failure hidden behind the current first failure. The
  corresponding case should be split rather than weakening the invariant.
- The cross-repository Book fixture can become stale when the Book export
  contract changes. Update its source commit/blob SHA and replay evidence in the
  same PR that changes that contract.
- `rank_score` fixes may affect ordering consumers not present in this repository;
  migration and compatibility should be handled by the owning implementation
  lane.

## Data and rights notes

- Fixture data is synthetic and tiny.
- No production databases, release assets, book text, private profile data,
  credentials, or live API responses are included.
- The two non-Latin labels are used only to exercise Unicode key behavior.
- The Book fixture records public source-code behavior by commit/path/blob SHA;
  it does not copy third-party corpus content.

## Suggested merge considerations

- Merge this audit before or alongside the first implementation fix so finding
  IDs and expected-failure behavior remain stable across parallel lanes.
- Do not squash away the finding IDs from the PR narrative, even if the commits
  are squashed.
- Require the full offline command in every implementation PR touching a named
  seam.
- Keep production changes out of this branch; this lane is the shared evidence
  contract for subsequent fixes.
