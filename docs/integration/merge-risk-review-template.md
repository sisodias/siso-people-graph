# Parallel People Graph merge-risk review template

## Snapshot

- Repository:
- Base branch and SHA:
- Captured at:
- Open PR count:
- Reviewer:
- Offline snapshot file:

## Per-PR inventory

| PR | Lane branch | Owned paths | Actual changed paths | Handoff present | Tests reported | Rights/source notes | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |

## Cross-PR checks

- [ ] No exact changed-file overlap.
- [ ] No directory-prefix ownership overlap.
- [ ] No unregistered branch or path outside its lane.
- [ ] No competing definitions of `pg-observation-0.1`.
- [ ] One schema/migration authority is selected; other lanes use adapters.
- [ ] Root configuration changes are consolidated intentionally rather than resolved wholesale.
- [ ] Generated files are regenerated from their single source of truth.
- [ ] Each lane includes its required handoff and reproducible validation command.

## Identity and data-model checks

- [ ] Source observations remain append-only and separate from accepted identity decisions.
- [ ] Names, companies, locations, biographies, and topics are not promoted into identifiers.
- [ ] Handles remain mutable source aliases.
- [ ] Name-only merges are impossible in import, build, migration, query, and review paths.
- [ ] Canonical clusters and redirects are reversible and decision-provenanced.
- [ ] Work contributor roles survive import, storage, export, and query.
- [ ] Time-varying metrics are timestamped observations with source units.

## Rights/security checks

- [ ] Every source change declares snapshot, terms revision, rights state, update/deletion behavior, and retained payload policy.
- [ ] Restricted or discovery-only content is not committed or exposed by fixtures, API, MCP, logs, or reports.
- [ ] No secrets, tokens, private absolute paths, user home paths, vault paths, or bulk personal payloads are committed.
- [ ] Source robots/rate limits and removal workflows are documented.

## Findings

| ID | Severity | Category | PRs | Paths | Finding | Resolution owner | Merge blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |

## Decision

- [ ] Safe to combine in stated order.
- [ ] Safe only with adapters/follow-up listed above.
- [ ] Blocked by P0 finding.

Rerun:

```bash
python3 -m integration risk open-pr-snapshot.json
python3 tests/integration_parallel/run.py
python3 -m integration check --repo-root . --pr-snapshot open-pr-snapshot.json
```
