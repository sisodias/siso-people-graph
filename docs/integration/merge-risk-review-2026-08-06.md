# Launch-time open-PR merge-risk review — 2026-08-06

## Result

The launch-time query against open pull requests in `sisodias/siso-people-graph` returned **zero open PRs**. A second pre-publish query on the same date also returned **zero open PRs**. Therefore there were no PR diffs, migrations, root-configuration edits, contracts, source-rights changes, or handoffs to compare in either observation.

This is an observed empty set, not evidence that future merges are safe. The exact base was `de048bb3b34bf931b56fd741cb46c1334acdfb98`.

## Current-main risks carried forward

| Severity | Risk | Owning follow-up |
| --- | --- | --- |
| P0 | Legacy `external_ids` mixes stable IDs with `real_name`, `company`, and `location`; the matcher can label any shared pair `shared_external_id` at 0.98. | Identity lane; build/release gate must prevent bulk acceptance until identifier registry is enforced. |
| P0 | v2 Book integration reuses people by normalized name before reviewable claims. | Schema/build/identity lanes; do not copy into v3. |
| P1 | No exact source snapshot, terms revision, rights state, or deletion obligation in v2 rows. | Source pilots and reproducible-build lane. |
| P1 | v2 schema path used by the builder does not match the committed schema directory. | Reproducible-build lane. |
| P1 | Mutable GitHub enrichment overwrites name/kind/rank meaning instead of appending observations. | Schema/source/build lanes. |
| P1 | Accepted identity claims are not a canonical, reversible query layer. | Identity and query lanes. |
| P2 | Code presence does not prove runtime database/API/MCP capability. | Query and integration capability reporting. |

## Reusable review path

When PRs exist, export their number, title, head branch, and changed paths to `pg-open-pr-snapshot-0.1`, then run:

```bash
python3 -m integration risk open-pr-snapshot.json
python3 -m integration check --repo-root . --pr-snapshot open-pr-snapshot.json
```

`P0` findings fail the gate. The review template is in `merge-risk-review-template.md`.
