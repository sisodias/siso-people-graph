# Parallel People Graph integration contract

This directory documents the isolated integration lane created on 2026-08-06. The lane does not launch the People Graph, rewrite current v2 production code, or make any other lane a prerequisite. It provides a reusable compatibility contract, offline adapters, capability detection, path-ownership checks, and a merge-risk gate that can run after any subset of the thirteen branches merges.

## What is executable

- `integration/contract.py` validates `pg-observation-0.1` records, source snapshots, rights state, payload hashes, identifier semantics, and the prohibition on canonical IDs or name-only merging.
- `integration/adapters.py` reads current v2 SQLite, Book/source NDJSON, and a future v3 full-envelope JSON seam without resolving identity.
- `integration/capabilities.py` distinguishes declared files from available runtime assets and names missing capabilities explicitly.
- `integration/lanes.py` validates all thirteen branch/path ownership contracts.
- `integration/merge_risk.py` analyzes an offline open-PR snapshot for overlaps, duplicated contracts, migration conflicts, rights gaps, and missing handoffs.
- `integration/cli.py` exposes the repeatable commands.

## Primary commands

```bash
python3 tests/integration_parallel/run.py
python3 -m integration check --repo-root .
python3 -m integration validate path/to/observations.ndjson --payload-root .
python3 -m integration capabilities --repo-root . --database path/to/people.sqlite
python3 -m integration risk path/to/open-pr-snapshot.json
```

The contract gate is intentionally standard-library-only and offline. Optional databases are opened with SQLite `mode=ro`; no adapter mutates source data.

## Documents

- [Observation contract](observation-contract.md)
- [Adapter interface](adapter-interface.md)
- [Capability matrix](capability-matrix.md)
- [Current-main baseline](current-main-baseline.md)
- [Launch-time merge-risk review](merge-risk-review-2026-08-06.md)
- [Reusable merge-risk template](merge-risk-review-template.md)
- [Parallel lane matrix](parallel-lane-matrix.md)
- [Adversarial release checklist](adversarial-release-checklist.md)
- [Rerun guide](rerun.md)
- [Integration report](integration-report.md)
