# Current-main baseline at integration-lane launch

## Observation

- Repository: `sisodias/siso-people-graph`
- Default branch: `main`
- Launch-time base commit: `de048bb3b34bf931b56fd741cb46c1334acdfb98`
- Open pull requests returned by the launch-time repository query on 2026-08-06: **0**
- Open pull requests returned by a second pre-publish query on 2026-08-06: **0**
- Existing integration branch with the required name: **none**
- Created branch: `pg/parallel-integration-contract-20260806`

The repository connector did not return a server-side timestamp for the open-PR query, so this record intentionally gives the exact date and query result without inventing a time.

## Current implementation surface

The launch-time commit is the initial repository commit. It declares the v2 schema, a query script, deterministic-looking loaders, GitHub enrichment, an identity-claim proposer, and release-asset guidance. The database itself is excluded from Git.

## Findings that constrain integration

### P0 — Attribute rows can be promoted into high-confidence identity evidence

`loaders/enrich_owners.py` writes `real_name`, `company`, and `location` into `external_ids` alongside numeric GitHub IDs, handles, and websites. `loaders/match_identities.py` treats every duplicate `(platform, value)` pair in that table as `shared_external_id` at confidence `0.98`, and its CLI can auto-accept that method. Two people at the same company or location can therefore receive evidence semantics intended for a stable authority ID. The integration adapter partitions these attributes and the shared validator refuses to treat them as identifiers, but current v2 code remains unchanged.

### P0 — The v2 rebuild silently merges normalized names

`loaders/build_people_graph_v2.py` creates a normalized-name map and reuses an existing person key when a Book person has the same normalized name. That action occurs before `identity_claim` and does not create a reviewable claim. It conflicts with the stated no-silent-name-merge goal and must not be copied into v3 or source pilots.

### P1 — Clean-checkout schema path is inconsistent

The v2 builder resolves `people_schema_v2.sql` beside the loader, while the committed schema is under `schema/people_schema_v2.sql`. A clean-checkout build needs an explicit test or path fix in the owning build lane.

### P1 — Source snapshots, terms, rights, and deletion obligations are absent

The v2 `person`, `external_ids`, `person_content`, and `person_topic` records do not carry an exact source snapshot, terms revision, rights state, or source deletion/update obligation. `source` and `observed_at` are partial provenance, not a full replay contract.

### P1 — Mutable values overwrite source observations

GitHub enrichment updates `person.name`, `person.kind`, `person.rank_score`, and `built_at`. The same `rank_score` field can mean summed repository stars before enrichment and follower count afterward. Without an observation history, a rebuild cannot explain when or why the meaning changed.

### P1 — Accepted identity decisions do not form a queryable canonical layer

The v2 query surface searches `person` and content tables directly. `identity_claim` is not used to produce a reversible canonical cluster or redirect view, and the query surface does not expose decision provenance.

### P2 — Query availability and data availability are conflated

`loaders/ask.py` can exist while every candidate database is absent. It skips missing domains and returns only the domains it can attach. The new capability matrix distinguishes code declaration from runtime assets.

## Integration response

This lane does not change those owning files. It creates a strict observation contract, conservative v2 compatibility projection, separate identity-decision stream, capability detector, and release checklist so later lanes cannot silently inherit the risks.
