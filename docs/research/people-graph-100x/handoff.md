# Handoff: People Graph 100x research dossier

**Repository:** `sisodias/siso-people-graph`  
**Branch:** `agent/people-graph-100x-research-dossier-20260806`  
**Base:** `main@de048bb3b34bf931b56fd741cb46c1334acdfb98`  
**Lane:** documentation-only public reasoning and coordination  

## Scope completed

This lane publishes the evidence, sources, assumptions, alternatives, decisions, opportunity map and agent-coordination state behind the People Graph 100x proposal.

It owns only:

```text
docs/research/people-graph-100x/**
```

It does not modify:

- v2 or v3 schemas;
- loaders or query behavior;
- tests owned by other lanes;
- database or release assets;
- root configuration or README;
- Book Library or Great Library source files;
- generated site content.

## Files added

| File | Purpose |
| --- | --- |
| `README.md` | cold-start map, architectural split, principles, gates and first milestone |
| `research-notebook.md` | evidence hierarchy, inspection sequence, observation-to-conclusion ledger, alternatives and falsifiers |
| `current-state-audit.md` | P0/P1 interpretation, architectural gaps, repair criteria and integration order |
| `architecture-and-100-tracks.md` | target planes, logical objects and one hundred missing tracks |
| `source-and-standards-ledger.md` | exact repository evidence, draft heads, 39 source families, official references and standards |
| `agent-missions.md` | common operating contract and sixteen copy-paste missions |
| `coordination-state.md` | point-in-time PR, branch, reservation and dependency receipt |
| `decision-log.md` | sixteen decisions, rejected alternatives, consequences, assumptions and reversal triggers |
| `research-manifest.json` | machine-readable scope, evidence, draft work, findings and promotion gates |
| `handoff.md` | this review and integration receipt |

## Behavior changed

No runtime behavior changed.

A cold agent now has one repository-native location that explains:

- why the project is being reframed as an evidence-backed knowledge-production graph;
- which conclusions come from exact code versus inference;
- which code defects block production-scale ingestion;
- how the People Graph, Book Library, Great Library and evidence plane should divide responsibility;
- where all one hundred opportunity tracks fit;
- which agents and branches already own work;
- which branches were empty or absent at the observation cut;
- how to start, test, push and hand off the remaining missions;
- which official sources and standards support the design;
- what would falsify or reverse each major decision.

## Compatibility preserved

- Existing v2 behavior is untouched.
- Existing draft PR path reservations are untouched.
- No statement treats an unmerged PR as canonical truth.
- No source adapter, schema or production database is promoted by this documentation.
- The Great Library remains the proposed public control plane; this repository remains the operational actor-graph owner.
- Book payloads, papers, transcripts, archives, model weights and private data remain outside Git.

## GitHub-side validation performed

A GitHub compare against `main` was run before this handoff was added.

Result at that point:

```text
status: ahead
base: de048bb3b34bf931b56fd741cb46c1334acdfb98
ahead_by: 9
behind_by: 0
changed files: 9
all changed paths: docs/research/people-graph-100x/**
additions: documentation and one JSON manifest only
deletions: 0
```

This handoff adds the tenth file in the same exclusive directory. A final comparison should be attached to the draft PR.

Manual consistency checks performed while authoring:

- all relative links from `README.md` target files created in this directory;
- the manifest uses strict JSON syntax with quoted keys/strings and no comments;
- exact repository commits, blob IDs and draft PR heads were copied from GitHub connector receipts;
- branch states marked `identical_to_main_at_cut` were confirmed through commit comparison;
- no credentials, private keys, client identifiers, raw databases or machine-specific private paths were included;
- external URLs are official entry points or exact GitHub repository/PR locators;
- claims not independently verified are listed under evidence gaps or claims deliberately not made.

## Validation limitation

A fresh local clone was attempted for parser and link checks, but the execution runtime could not resolve `github.com` over DNS. No local test or clone result is therefore claimed.

A maintainer with network access should run:

```bash
git clone https://github.com/sisodias/siso-people-graph.git
cd siso-people-graph
git checkout agent/people-graph-100x-research-dossier-20260806

python3 -m json.tool docs/research/people-graph-100x/research-manifest.json >/dev/null

python3 - <<'PY'
from pathlib import Path
import re
root = Path('docs/research/people-graph-100x')
missing = []
for path in root.glob('*.md'):
    text = path.read_text(encoding='utf-8')
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        clean = target.split('#', 1)[0]
        if clean and not (path.parent / clean).exists():
            missing.append((str(path), target))
if missing:
    raise SystemExit('\n'.join(f'{a}: {b}' for a, b in missing))
print('relative links: PASS')
PY

git diff --check main...HEAD

git diff --name-only main...HEAD | grep -v '^docs/research/people-graph-100x/' && exit 1 || true
```

A publication-safety scan may also search for common secret patterns and absolute user paths. Raw URLs in the source ledger are intentional public evidence.

## External sources and rights boundary

This lane imports no external dataset or copyrighted payload. It records public metadata about sources, official documentation links and exact repository evidence.

The detailed 39-source access/rights/deletion decisions remain in Great Library draft PR #2. The principal rule is preserved throughout this dossier:

> public addressability is a locator, not proof of truth, ownership, licence or redistribution permission.

Unknown rights, retention or privacy state remains a blocker, not a value to guess.

## Claims made

- the pinned source files contain the code/schema behavior described;
- the listed PRs, branches, heads and comparison states existed at the observation cut;
- the red-team and source-matrix counts are the reported results of their exact draft heads;
- the architectural decisions and one hundred tracks are proposals supported by the stated evidence;
- this branch is documentation-only and non-overlapping at the time checked.

## Claims deliberately not made

- no production database was queried or rebuilt;
- no README row count was independently validated;
- no draft PR is considered accepted or merged;
- no external source is approved beyond the exact research state and terms revision in its source record;
- no v3 schema is declared final;
- no source pilot proves production scale, accuracy, cost or rights compliance;
- the 10,000 verified multi-domain milestone is not claimed achieved;
- private chain-of-thought is not claimed exposed—reproducible evidence, assumptions, alternatives and decisions are provided instead.

## Integration seams

This dossier should be linked, not copied, by other lanes.

- Red-team lane remains executable defect authority.
- v3 schema lane remains logical ontology authority for its draft.
- identity lane owns candidate/decision/cluster implementation.
- build lane owns replay, manifests and tombstones.
- Book Library lane owns its source/export repair.
- source pilots own adapters and source-specific fixtures.
- claims lane owns source-span and temporal reasoning contracts.
- query lane owns evidence-first reads.
- integration lane owns cross-lane synthetic proofs.
- Great Library owns public registry, decisions, program/answer releases and selected snapshots.

Conflicts should cite exact branches and tests. This dossier does not grant one draft automatic precedence over another.

## Suggested review order

1. Confirm the branch diff remains inside the exclusive directory.
2. Parse `research-manifest.json` and run relative-link validation.
3. Verify the exact PR heads and branch statuses have not changed materially.
4. Review `current-state-audit.md` against red-team PR #1.
5. Review `source-and-standards-ledger.md` against Great Library PR #2.
6. Check that `agent-missions.md` does not assign a path now owned by a newer lane.
7. Review decisions D-001 through D-016 for assumptions that require amendment.
8. Merge or request corrections without coupling this documentation to production schema acceptance.

## Recommended next actions

- merge the red-team fixtures early;
- assign or resume the empty integrity/identity/integration lanes;
- start the Book Library repair and scholarly authority pilot if still unclaimed;
- add the Work-resolution, decision-use and privacy/governance benchmark lanes unless another agent already owns them;
- use this dossier as evidence in the Great Library People Graph program, preserving the exact PR/commit locator;
- update coordination status through a new dated receipt rather than silently treating this snapshot as live forever.
