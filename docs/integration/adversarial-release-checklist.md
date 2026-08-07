# Adversarial release checklist

A release candidate is not accepted because its happy-path fixtures pass. It must survive the following hostile combinations. Any unchecked P0 item blocks a release; the integration lane itself does not authorize launch.

## P0 contract and identity blockers

- [ ] Every imported source record validates as `pg-observation-0.1` or through a versioned, reviewable adapter.
- [ ] No observation contains a canonical People Graph ID, cluster assignment, redirect, `merged_into`, or automatic merge directive.
- [ ] Accepted identity decisions are stored/exported separately from source observations and can be undone without deleting source facts.
- [ ] No exact-name, normalized-name, display-name, surname-initial, company, employer, location, biography, or topic match can merge or auto-accept identity.
- [ ] Handles/logins are source-scoped mutable aliases; numeric/authority identifiers have explicit scope, stability, uniqueness, and evidence.
- [ ] Duplicate weak attributes do not enter `shared_external_id` or equivalent high-confidence paths.
- [ ] Homonyms, aliases, pseudonyms, renamed handles, recycled handles, organisations, bots, teams, and ancient/modern same-name people remain distinct unless evidence supports a reviewed decision.
- [ ] A malicious source record cannot inject a canonical ID or merge command through nested attributes/evidence.

## P0 source, rights, and security blockers

- [ ] Every source record has an exact snapshot/query receipt, retrieval time, observed time, terms revision, rights state, and payload digest.
- [ ] Rights are not inferred from “publicly accessible.” Restricted and discovery-only payloads are excluded from Git, API, MCP, logs, fixtures, and release assets.
- [ ] Source deletion, correction, opt-out, retraction, embargo, and terms-change workflows are tested.
- [ ] No credentials, auth headers, cookies, tokens, private URLs, user-home paths, vault paths, or raw private payloads are committed.
- [ ] Fixtures are synthetic or tiny public-safe receipts and still exercise failure behavior.
- [ ] APIs/MCP enforce read-only connections and do not permit arbitrary SQL, path traversal, SSRF, or payload dereferencing.

## Schema and migration

- [ ] One additive schema authority exists; no PR silently replaces another lane’s DDL.
- [ ] Migration/rebuild starts from source observations, not mutable current-state rows when that would lose history.
- [ ] Fresh build, upgrade, downgrade/rollback, repeated migration, interrupted migration, and empty-database cases are tested.
- [ ] Foreign keys, uniqueness, redirects, tombstones, and deletion semantics are validated after migration.
- [ ] v2 and v3 adapters produce equivalent source facts for a shared fixture without asserting equivalent canonical identity.
- [ ] Missing optional tables/features produce explicit capability gaps rather than crashes or invented defaults.

## Works, contributions, and topics

- [ ] Author, editor, translator, illustrator, contributor, host, guest, owner, and other roles remain on the Work/event edge.
- [ ] One person can hold multiple roles on one Work without deduplication loss.
- [ ] Work identifiers, titles, provenance, rights, source snapshots, and literal metadata survive round-trip export.
- [ ] Topic vocabularies remain source/scheme namespaced; identical strings from different schemes are not silently fused.
- [ ] Organisations and collective authors are represented honestly and do not become humans through defaults.

## Claims and temporal relations

- [ ] Source claims, accepted/rejected identity decisions, canonical entities, and named projections are separate layers.
- [ ] Claim evidence, source, extraction method, confidence, status, reviewer, validity interval, and contradiction links survive export.
- [ ] Contradictions are retained; “latest” does not erase historical observations.
- [ ] Events and relationships support uncertain or open intervals and do not invent dates.
- [ ] Derived metrics/projections are versioned and reproducible from source claims.

## Reproducibility and release integrity

- [ ] A clean checkout builds the tiny fixture offline with one documented command.
- [ ] Repeated builds produce identical logical digests despite benign SQLite byte differences.
- [ ] Input manifests pin source snapshots, hashes, terms/rights metadata, adapter versions, and build configuration.
- [ ] Validation reports include row counts, referential integrity, orphan counts, role counts, identifier classifications, claim status counts, and capability gaps.
- [ ] Release packaging excludes SQLite journals, temporary files, local caches, secrets, raw restricted payloads, and private paths.
- [ ] Versioned artifacts have checksums, schema version, build manifest, and rollback notes.

## Query, API, MCP, and performance

- [ ] Empty, v2-only, v3-only, partially migrated, observation-only, and fully built fixtures are tested.
- [ ] Query responses expose provenance, rights/capability limits, canonical decision provenance, and redirects where available.
- [ ] Missing capabilities are explicit; a missing database is not reported as an empty domain.
- [ ] Pagination, deterministic ordering, cancellation/timeouts, malformed inputs, Unicode, BCE years, and very long labels are tested.
- [ ] Hot queries have query plans/index coverage and bounded response sizes; adversarial inputs cannot trigger unbounded joins or full payload dumps.
- [ ] APIs/MCP never write to the graph and never expose raw restricted evidence by default.

## Parallel merge hygiene

- [ ] `integration/lane_registry.json` validates with thirteen unique branches and no owned-path overlap.
- [ ] Every PR changes only its owned paths or carries an explicit reviewed handoff from the owner.
- [ ] Every PR includes commands, tests, assumptions, compatibility seams, risks, data/rights notes, and merge considerations.
- [ ] Open PR changed paths have been exported and analyzed by `python3 -m integration risk`.
- [ ] No P0 merge-risk finding remains.
- [ ] Root configuration and generated artifacts have one selected owner and are regenerated after conflict resolution.

## Final rerun

```bash
python3 tests/integration_parallel/run.py
python3 -m integration check --repo-root . --pr-snapshot open-pr-snapshot.json \
  --database path/to/candidate.sqlite \
  --observation path/to/source-export.ndjson
```
