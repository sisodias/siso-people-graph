# Integration contract lane handoff

## Scope

Implemented the isolated parallel integration contract and merge-risk sweeper for all thirteen People Graph program lanes. The lane is additive, offline, standard-library-only, and does not launch or release the system.

## Changed paths

- `integration/**`
- `tests/integration_parallel/**`
- `docs/integration/**`
- `docs/handoffs/integration-contract.md`

No schema, loader, identity, query, claims, source-adapter, root configuration, or README path was changed.

## Commands

```bash
python3 tests/integration_parallel/run.py
python3 -m integration check --repo-root .
python3 -m integration validate tests/integration_parallel/fixtures/valid_observations.ndjson --payload-root .
python3 -m integration risk tests/integration_parallel/fixtures/open_pr_snapshot_conflict.json
```

After other lanes merge:

```bash
python3 -m integration check --repo-root . \
  --pr-snapshot open-pr-snapshot.json \
  --database path/to/candidate.sqlite \
  --observation path/to/source-export.ndjson
```

## Tests

The isolated suite contains 26 tests covering contract validation, payload hashes, canonical-ID/merge injection, identifier semantics, v2/Book/NDJSON/v3 adapters, separate identity decisions, Work roles/provenance/rights, partial capabilities, all thirteen lane owners, synthetic PR conflicts, and the end-to-end CLI gate.

## Assumptions

- `pg-observation-0.1` is the agreed cross-lane source-observation seam.
- Source observations are immutable evidence; canonical identity decisions and derived claims remain separate.
- Missing rights/snapshot information is represented honestly as pending/documented-unknown, never inferred.
- Open-PR changed paths can be exported to the documented offline snapshot format by a release/integration operator.
- Production databases remain outside Git and are supplied explicitly for runtime checks.

## Compatibility seams

- Current v2: read-only projection from `person`, `person_content`, `external_ids`, optional `person_topic`, and separate `identity_claim` decisions.
- Book Library and source pilots: deterministic NDJSON using `pg-observation-0.1`.
- Future v3: full-envelope JSON table detection without guessing canonical or claim joins.
- Query/build/claims lanes: capability report names what is present and missing after any subset merges.
- Identity lane: observations and decisions are separate, and attribute-like legacy external-ID rows are not treated as identifiers.

## Known risks

- Current-main identity matching can classify shared `real_name`, company, or location rows as high-confidence shared external IDs.
- Current-main v2 build reuses normalized names before reviewable identity claims.
- Current-main builder/schema path consistency is unproven in a clean checkout.
- v2 lacks exact source snapshots, terms, rights, deletion obligations, and stable metric semantics.
- Future normalized v3 tables require explicit versioned mappers; detection alone is not semantic compatibility.
- The merge-risk tool cannot analyze PRs omitted from its offline snapshot.

## Data/rights notes

Only tiny public-safe synthetic/example fixtures are committed. No production database, raw private payload, credential, token, user-home path, or vault path is included. Fixture records carry explicit terms references, rights state, retrieval/observation times, and SHA-256 payload receipts. SQLite fixtures are generated in temporary directories during tests.

## Suggested merge considerations

1. Merge this lane independently; it owns no hot production path.
2. Keep `pg-observation-0.1` stable. Other lanes should add adapters rather than fork field semantics.
3. Run the lane registry and open-PR risk analyzer before combining parallel branches.
4. Treat P0 identity and migration findings in the current-main baseline as release blockers, not as reasons to broaden this lane’s ownership.
5. After schema/identity/build/query/source lanes merge, rerun with their actual databases and NDJSON exports. Missing capabilities may remain acceptable only when the release claim explicitly excludes them.
6. Do not use this handoff as launch approval; complete the adversarial release checklist and owning-lane reviews.
