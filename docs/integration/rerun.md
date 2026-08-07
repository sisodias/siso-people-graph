# Rerun guide after any subset of lanes merges

The harness is capability-detecting. It does not require all thirteen branches, and a missing lane is reported as missing rather than treated as a failure unless the release candidate claims that capability.

## Repository-only gate

```bash
python3 tests/integration_parallel/run.py
python3 -m integration check --repo-root .
```

This validates the contract fixtures, all lane ownership records, the launch-time empty PR snapshot, and the repository capability matrix.

## Include merged runtime artifacts

```bash
python3 -m integration check --repo-root . \
  --database build/people.sqlite \
  --observation exports/books.ndjson \
  --observation exports/scholarly.ndjson
```

Each database is opened read-only. Each observation file must validate. Unsupported/invalid supplied artifacts fail the gate.

## Include current open PRs

Create a JSON file with:

```json
{
  "snapshot_version": "pg-open-pr-snapshot-0.1",
  "repository": "sisodias/siso-people-graph",
  "captured_at": "2026-08-06T00:00:00Z",
  "base_sha": "<current main SHA>",
  "pull_requests": [
    {
      "number": 123,
      "title": "Example",
      "head_branch": "pg/example-branch",
      "changed_paths": ["path/file.py", "docs/handoffs/example.md"]
    }
  ]
}
```

Then run:

```bash
python3 -m integration risk open-pr-snapshot.json
python3 -m integration check --repo-root . --pr-snapshot open-pr-snapshot.json
```

A `P0` merge-risk finding fails the command. P1/P2 findings remain visible for explicit review.

## Validate or round-trip one lane export

```bash
python3 -m integration validate export.ndjson --payload-root .
python3 -m integration roundtrip export.ndjson /tmp/export.roundtrip.ndjson
```

## Adapt current v2 or future v3

```bash
python3 -m integration adapt-sqlite people.sqlite /tmp/observations.ndjson \
  --source-policies source-policy.json \
  --decisions-output /tmp/identity-decisions.json
```

The two outputs intentionally remain separate.
