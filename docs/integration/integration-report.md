# Parallel integration report

## Scope

This lane provides integration contracts and adversarial gates only. It does not modify current schema, loaders, identity code, query code, claims code, source adapters, root configuration, or README. It does not launch or release the People Graph.

## Baseline

The work began from `main` at `de048bb3b34bf931b56fd741cb46c1334acdfb98`. The launch-time open-PR query returned zero open PRs. The required branch did not previously exist.

## Delivered

1. Executable `pg-observation-0.1` validator with source snapshot, terms/rights, payload hash, raw-pointer, identifier, and identity-safety rules.
2. Deterministic NDJSON import/export and repository payload verification.
3. Read-only adapters for current v2 SQLite, Book/source NDJSON, and a future v3 full-envelope JSON seam.
4. Separate identity-decision stream; accepted legacy claims never mutate source observations.
5. Conservative partitioning that prevents `real_name`, company, location, biography, and topics from becoming identifiers.
6. Work/contribution projection preserving roles, rights policy, source, observed time, score observation, title, and metadata.
7. Repository/runtime capability matrix with explicit missing/declared/unsupported states.
8. Machine-readable thirteen-lane ownership registry and validator.
9. Offline open-PR merge-risk analyzer with ownership, overlap, root config, contract, migration, rights, and handoff checks.
10. Launch-time current-main risk review, reusable review template, adversarial release checklist, rerun guide, and handoff.

## Tests

The isolated standard-library suite covers:

- exact payload digest verification and mismatch failure;
- missing rights and malformed contract failure;
- canonical-ID and merge-directive injection;
- attribute-as-identifier and unsafe handle semantics;
- review-only identity relationships and name-only evidence rejection;
- deterministic NDJSON round-trip;
- v2 person/content/topic/external-ID mapping;
- accepted identity decisions as a separate stream;
- Work role/provenance/rights preservation;
- Book/source NDJSON summary;
- future v3 JSON seam detection;
- partial capability detection;
- all thirteen lane owners;
- synthetic PR path overlap, schema conflict, and ownership escape;
- end-to-end CLI gate.

Commands:

```bash
python3 tests/integration_parallel/run.py
python3 -m integration check --repo-root .
```

## Known limits

- No production databases or private source payloads were available or committed.
- Legacy v2 rights and snapshot metadata cannot be reconstructed from rows; the adapter reports explicit pending/documented-unknown values unless supplied through `SourcePolicy`.
- Normalized future v3 canonical/claim tables are detected but not mapped without a versioned schema-specific adapter.
- The offline PR analyzer requires a caller to export current changed paths; it intentionally does not embed GitHub credentials or network behavior.
- Current-main P0/P1 findings are documented but not fixed because those files belong to other lanes.
