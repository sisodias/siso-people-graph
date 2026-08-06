# Identity v3: safe, reversible resolution

`identity_v3` is an additive identity-resolution layer for the SISO People Graph.
It can run inside the current v2 SQLite database, against a lane-local fixture,
or against `pg-observation-0.1` records. It does not require a future v3 schema and
does not rewrite source people, aliases, or observations.

## Safety invariants

- Only identifier schemes explicitly marked `auto_resolution_eligible` can create
  an automatic candidate.
- Names, display names, companies, locations, topics, biographies, websites,
  popularity metrics, and mutable handles never auto-resolve identity.
- Name normalization is Unicode-preserving, comparison-only, and never used to
  mint an entity ID.
- Every candidate carries a method version, positive evidence, negative evidence,
  conflict reasons, confidence, and review state.
- An accepted decision creates a derived cluster generation. Source entities and
  aliases survive unchanged.
- A prospective decision is rejected when it would create conflicting stable
  identifiers. A manual conflict override is explicit and audit-visible.
- Repeating the same active decision is idempotent. One `undo` restores the prior
  cluster generation deterministically.

## Storage model

The lane-local DDL lives in `identity_v3/fixtures/schema.sql`. It creates only
versioned `identity_v3_*` tables:

- `identity_v3_entity`: source/canonical-row adapters without destructive merge;
- `identity_v3_identifier`: registry-classified stable identifiers;
- `identity_v3_alias`: mutable, time-bounded aliases linked to stable IDs;
- `identity_v3_attribute`: timestamped source observations and metrics;
- `identity_v3_candidate`: evidence-calibrated pair proposals;
- `identity_v3_decision`: append-oriented accept/reject decisions and reversals;
- `identity_v3_generation` and `identity_v3_cluster_member`: reproducible cluster
  projections and canonical redirects;
- enrichment receipts and audit events.

## CLI

Run from the repository root:

```bash
python3 -m identity_v3 registry
python3 -m identity_v3 sync-v2 --db people_v2.sqlite
python3 -m identity_v3 propose --db people_v2.sqlite
python3 -m identity_v3 review --db people_v2.sqlite --state proposed
python3 -m identity_v3 inspect --db people_v2.sqlite --entity 'gh:example'
python3 -m identity_v3 accept --db people_v2.sqlite \
  --candidate cand:... --decided-by reviewer@example --rationale 'literal evidence checked'
python3 -m identity_v3 reject --db people_v2.sqlite \
  --candidate cand:... --decided-by reviewer@example --rationale 'different people'
python3 -m identity_v3 resolve --db people_v2.sqlite --entity 'gh:example'
python3 -m identity_v3 undo --db people_v2.sqlite --decision decision:...
python3 -m identity_v3 audit --db people_v2.sqlite
python3 -m identity_v3 import-envelope --db fixture.sqlite --input observations.ndjson
```

Use `--automatic` on `accept` only for candidates already marked auto-eligible.
The engine still runs pair-level and transitive cluster conflict checks.
`--allow-conflicts` is a manual, audit-visible escape hatch for adjudication—not
a bulk-ingestion mode.

## Current loader compatibility

The existing commands remain available:

```bash
python3 loaders/match_identities.py --graph people_v2.sqlite
python3 loaders/match_identities.py --graph people_v2.sqlite --apply
python3 loaders/match_identities.py --graph people_v2.sqlite \
  --apply --accept shared_external_id
python3 loaders/enrich_owners.py --graph people_v2.sqlite --limit 500
python3 loaders/enrich_owners.py --graph fixture.sqlite \
  --fixture tests/identity_v3/fixtures/github_profiles.json
```

`shared_external_id` now means an exact match in a registry-eligible scheme.
The enricher records GitHub fields as observations, handles each missing field
independently, records null receipts, and never overwrites canonical `name`,
`rank_score`, or `built_at`.

## Validation

```bash
PYTHONPATH=. python3 -m unittest discover \
  -s tests/identity_v3 -p 'test_*.py' -v
PYTHONPATH=. python3 tests/identity_v3/measure_precision.py
```

All fixtures are tiny, synthetic, offline, and safe to commit.
