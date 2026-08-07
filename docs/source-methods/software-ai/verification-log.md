# Verification log

This log records the implementation verification completed before the audit-only
documentation commit. The audit does not modify adapter behavior, fixtures,
metrics, or the envelope contract.

## Repository state

- repository: `sisodias/siso-people-graph`
- branch: `pg/software-ai-pilot-20260806`
- base: `de048bb3b34bf931b56fd741cb46c1334acdfb98`
- verified implementation head: `b78ff6704783dff100774063c305011ce456d704`
- mode: offline replayable synthetic fixtures

## Commands

```bash
PYTHONPATH=. python -m unittest discover -s tests/sources_software_ai -v

PYTHONPATH=. python -m sources.software.pilot export \
  --fixtures tests/sources_software_ai/fixtures \
  --out /tmp/software-ai.ndjson \
  --metrics-out /tmp/software-ai-metrics.json

PYTHONPATH=. python -m sources.software.pilot validate /tmp/software-ai.ndjson
PYTHONPATH=. python -m sources.software.pilot metrics --path /tmp/software-ai.ndjson
python -m compileall -q sources tests
sha256sum /tmp/software-ai.ndjson
```

## Observed result

- 18 tests passed;
- 31 envelopes exported and validated;
- all fixture construction completed with network connection creation patched to
  fail;
- deterministic export was byte-identical when input order was reversed;
- committed fixture byte counts and SHA-256 values matched the manifest;
- recomputed metrics matched `pilot-metrics.json`;
- Python bytecode compilation succeeded;
- logical NDJSON SHA-256:
  `f1e5b923f22b6e94f9102bda2abc4c33f0bfd3bd8ed03b8fc903dee745b5780e`.

## Test coverage names

- reject canonical, merge, rank, and universal-score fields;
- reject name, real-name, company, location, and bio identifier schemes;
- preserve Unicode in canonical JSON;
- validate all records offline;
- deterministic export and replay;
- manifest, fixture-hash, and metrics replay;
- GitHub login rename continuity;
- repository transfer continuity through numeric repository ID;
- first-class organisations;
- package maintainers as contributions, not aliases;
- cross-registry dependency edges;
- intrinsic Software Heritage identifiers;
- distinct Hugging Face model/dataset/Space Works and links;
- timestamped metrics without rank mutation;
- literal cross-platform evidence without merge;
- preserved license disagreement;
- archived and abandoned Work cases;
- expected measured fixture summary.

## Interpretation

The result verifies the offline contract and synthetic edge cases. It does not
verify live API coverage, production precision/recall, freshness, deletion
compliance, throughput, or cost. Those remain explicit gates for an online
cohort.
