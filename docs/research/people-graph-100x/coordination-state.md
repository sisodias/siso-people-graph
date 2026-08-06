# Coordination state and integration map

**Observed:** 2026-08-06  
**This is a point-in-time receipt, not a live scheduler. Re-check GitHub before acting.**

## Status vocabulary

| State | Meaning |
| --- | --- |
| `published_pr` | branch has commits and an open draft pull request |
| `published_branch` | branch has commits but no observed PR |
| `reserved_empty` | branch exists but compares identical to `main` |
| `declared_not_observed` | Great Library program declared the lane, but the branch was not found during this check |
| `unowned_proposal` | mission proposed by this dossier; no ownership claim is made |

## Repository baselines

| Repository | Baseline used by program |
| --- | --- |
| `sisodias/siso-people-graph` | `main@de048bb3b34bf931b56fd741cb46c1334acdfb98` |
| `sisodias/siso-book-library` | `main@be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b` |
| `sisodias/great-library-of-siso` | program branches started from `main@12f4cc249b2b5dc268d05d1698fe9c5e3079327d` |

## Published People Graph draft PRs

| Lane | PR | Branch | Head at cut | Status | Exclusive paths |
| --- | ---: | --- | --- | --- | --- |
| Red-team fixtures | [#1](https://github.com/sisodias/siso-people-graph/pull/1) | `pg/red-team-fixtures-20260806` | `89dfec07acc38c6dadba69547a7ad4d60fbccf15` | `published_pr`, draft, mergeable when checked | `tests/red_team/**`, `docs/audits/**`, `docs/handoffs/red-team.md` |
| Software and AI pilot | [#2](https://github.com/sisodias/siso-people-graph/pull/2) | `pg/software-ai-pilot-20260806` | `b78ff6704783dff100774063c305011ce456d704` | `published_pr`, draft, mergeable when checked | `sources/software/**`, `sources/ai/**`, `tests/sources_software_ai/**`, `docs/source-methods/software-ai/**`, handoff |
| v3 ontology and schema | [#3](https://github.com/sisodias/siso-people-graph/pull/3) | `pg/v3-ontology-schema-20260806` | `2f66fbe1f4523399463d9e1ff8971879a84f5b88` | `published_pr`, draft, mergeable when checked | `schema/v3/**`, `docs/architecture/**`, `tests/schema_v3/**`, handoff |
| 100x reasoning dossier | pending PR from this branch | `agent/people-graph-100x-research-dossier-20260806` | update after final commit | `published_branch` while this record was authored | `docs/research/people-graph-100x/**` |

## Reserved People Graph branches that were still empty

Each branch below compared `identical` to `main`, with `ahead_by=0` and `behind_by=0`, when checked.

| Declared lane | Branch | State |
| --- | --- | --- |
| Identity resolution | `pg/identity-resolution-parallel-20260806` | `reserved_empty` |
| Living creators/media | `pg/living-creators-media-pilot-20260806` | `reserved_empty` |
| Claims/temporal/relations | `pg/claims-temporal-relations-20260806` | `reserved_empty` |
| Parallel integration | `pg/parallel-integration-contract-20260806` | `reserved_empty` |

Branch existence is not evidence that implementation or research has been published.

## Declared lanes not observed in the branch search

| Lane | Expected branch | State at check |
| --- | --- | --- |
| Reproducible builds | `pg/reproducible-builds-parallel-20260806` | `declared_not_observed` |
| Query/API/MCP/explorer | `pg/query-surface-parallel-20260806` | `declared_not_observed` |
| Scholarly authority pilot | `pg/scholarly-authority-pilot-20260806` | `declared_not_observed` |

An agent should search again before creating these branches because another worker may have started after this receipt.

## Book Library status

No open pull request was returned for `sisodias/siso-book-library` at the time checked.

The Great Library program declares:

- branch: `books/integrity-export-parallel-20260806`;
- mission: Book Library integrity and export;
- intended path zone: `scripts/**`, `index/**`, new `tests/**`, `manifests/**`, `docs/**`, `.github/workflows/**`.

Treat this as `declared_not_observed` until branch or PR evidence exists.

## Published Great Library draft PRs

| Lane | PR | Branch | Head at cut | Status |
| --- | ---: | --- | --- | --- |
| Registry/program spine | [#1](https://github.com/sisodias/great-library-of-siso/pull/1) | `gls/people-graph-parallel-spine-20260806` | `215cf63a320523f9c6405b17ae64ddb5468fb2f1` | `published_pr`, draft, mergeable when checked |
| Source universe research | [#2](https://github.com/sisodias/great-library-of-siso/pull/2) | `gls/people-graph-source-research-20260806` | `20dc000451c28c707b0a97b943d1a4b178ea9bf0` | `published_pr`, draft, mergeable when checked |

Great Library `site/intelligence.json` on the inspected main projection reported zero active initiatives. Draft PR #1 adds a successor People Graph program Event, but it must not be treated as canonical-main state until accepted.

## Thirteen declared lanes

The authoritative proposed reservation table is in Great Library draft PR #1 at:

`docs/people-graph-program/parallel-lanes.md`

| No. | Mission | Repository/branch | State at this cut |
| ---: | --- | --- | --- |
| 1 | Great Library registry and public program | GL / `gls/people-graph-parallel-spine-20260806` | `published_pr` |
| 2 | People Graph red-team fixtures | PG / `pg/red-team-fixtures-20260806` | `published_pr` |
| 3 | v3 ontology and schema | PG / `pg/v3-ontology-schema-20260806` | `published_pr` |
| 4 | Identity resolution | PG / `pg/identity-resolution-parallel-20260806` | `reserved_empty` |
| 5 | Reproducible builds | PG / `pg/reproducible-builds-parallel-20260806` | `declared_not_observed` |
| 6 | Query/API/MCP/explorer | PG / `pg/query-surface-parallel-20260806` | `declared_not_observed` |
| 7 | Book integrity/export | Books / `books/integrity-export-parallel-20260806` | `declared_not_observed` |
| 8 | Source research | GL / `gls/people-graph-source-research-20260806` | `published_pr` |
| 9 | Scholarly authority pilot | PG / `pg/scholarly-authority-pilot-20260806` | `declared_not_observed` |
| 10 | Software and AI pilot | PG / `pg/software-ai-pilot-20260806` | `published_pr` |
| 11 | Living creators/media | PG / `pg/living-creators-media-pilot-20260806` | `reserved_empty` |
| 12 | Claims/temporal/projections | PG / `pg/claims-temporal-relations-20260806` | `reserved_empty` |
| 13 | Parallel integration contract | PG / `pg/parallel-integration-contract-20260806` | `reserved_empty` |

## Additional unowned mission proposals

These do not override later reservations. They were introduced because the thirteen lanes do not clearly own the complete benchmark/governance work.

| Mission | Suggested branch | Proposed exclusive paths |
| --- | --- | --- |
| Canonical Work-resolution benchmark | `pg/work-resolution-benchmark-20260806` | `work_resolution/**`, `tests/work_resolution/**`, `benchmarks/work_resolution/**`, handoff |
| Decision-use/evidence-path benchmark | `pg/research-value-benchmark-20260806` | `benchmarks/decision_use/**`, `docs/research-value/**`, `tests/research_value/**`, handoff |
| Privacy/correction/governance | `pg/privacy-corrections-governance-20260806` | `governance/**`, `tests/governance/**`, `docs/privacy/**`, handoff |

## Cross-lane interface map

```text
source research
   -> source method cards and state decisions

source pilots
   -> pg-observation-0.1 envelopes only

Book Library export
   -> source actors + contributions + Work/manifestation observations

reproducible builds
   -> ingest manifests + replay/tombstone semantics

v3 ontology
   -> logical storage contract

identity resolution
   -> reviewed actor-cluster projection

Work resolution benchmark
   -> reviewed Work/version relation decisions

claims/temporal
   -> exact evidence spans + temporal assertions + named projections

query surface
   -> reads cluster/Work/assertion interfaces; returns capability and evidence state

integration lane
   -> synthetic end-to-end fixtures and compatibility gates

Great Library
   -> durable public identity, decisions, program/answer Releases and selected snapshots
```

## Merge dependencies

### Can merge early

- red-team fixtures, because they change no production behavior;
- documentation-only source research, subject to Great Library process;
- this reasoning dossier;
- additive schema proposals and offline source pilots when their boundaries remain explicit.

### Must coordinate before production promotion

- identity cluster interface and query behavior;
- Work identity/version interface and Book export;
- observation envelope and ingest manifests;
- rights/privacy/deletion fields and publication gates;
- claim selectors and representation digests;
- projection provenance and versioning.

### Must not be assumed

- an open draft PR is merged truth;
- a branch name means work exists;
- a schema proposal implies a production database;
- a fixture pilot implies source approval at scale;
- a program Release is an accepted Answer Release;
- GitHub mergeability means architecture is correct.

## Collision protocol

Before writing:

1. search open PRs in all three repositories;
2. search exact and prefix-matching branches;
3. compare the intended branch to current `main`;
4. inspect changed filenames in relevant PRs;
5. reserve a non-overlapping path zone;
6. add a public handoff early;
7. stop and record an interface proposal if another lane owns the needed file.

If two lanes have already modified the same contract, do not force-push or privately choose a winner. Open an integration decision containing:

- both exact heads;
- the conflicting semantics;
- compatibility options;
- test consequences;
- migration consequences;
- rights/privacy consequences;
- recommended owner and decision deadline.

## Refresh commands for a local maintainer

```bash
# Open work
gh pr list -R sisodias/siso-people-graph --state open
gh pr list -R sisodias/siso-book-library --state open
gh pr list -R sisodias/great-library-of-siso --state open

# Remote branches
git ls-remote --heads https://github.com/sisodias/siso-people-graph.git
git ls-remote --heads https://github.com/sisodias/siso-book-library.git
git ls-remote --heads https://github.com/sisodias/great-library-of-siso.git

# Scope of a PR
gh pr view <N> -R <owner/repo> --json headRefName,headRefOid,baseRefName,isDraft,mergeable,files,commits,statusCheckRollup
```

These commands are guidance; their output must be captured in a new dated receipt before updating this file’s status claims.
