# Source instructions — People Graph v3 ontology lane

**Purpose:** preserve the exact user-supplied operating contract needed to
reconstruct this lane without relying on a chat transcript.  
**Source date:** 2026-08-06  
**Original uploaded source SHA-256:** `077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d`  
**Original uploaded source size:** 54,730 bytes  
**Shared-program excerpt SHA-256:** `81fd3c1bd722347d901eb04c03e669ea67183f57b31326e55be0fb5d3c9b9711`  
**Prompt 3 excerpt SHA-256:** `dd5dfe689c4b7f4e8617fcbd08d0355059ec98a2bfd7e222be952bda1932c57d`  
**Prompt 3 excerpt size:** 4,243 bytes

The source contained thirteen parallel-agent prompts. This lane owns only Prompt
3. The shared launch rules and observation envelope are reproduced because they
constrain every implementation choice in Prompt 3. The other twelve prompts are
not copied here: they are separate lanes with separate path ownership.

## Shared launch rules and `pg-observation-0.1` contract — verbatim

```text
SISO People Graph — Parallel-Slam GPT-5.6 Agent Prompts

Date: 2026-08-06

Repositories:

sisodias/siso-people-graph

sisodias/siso-book-library

sisodias/great-library-of-siso

oracle is unrelated and explicitly out of scope.

Launch mode

Launch every prompt at the same time. There is no required order and no prompt may wait for another prompt, branch, schema, ADR, or PR.

The dependency graph has been replaced with four coordination mechanisms that work in the ChatGPT/Codex web UI:

Current-main rule: every agent starts from the latest canonical main available when it begins.

One owner per hot path: every lane has exclusive paths and must not edit another lane's paths.

Additive compatibility rule: when an ideal interface does not exist, the agent builds a lane-local adapter, fixture, or compatibility shim and records the exact future seam. It does not stop and it does not ask the user to merge another PR first.

Draft-PR handoff: every agent pushes its own branch and opens a draft PR containing an explicit integration manifest.

Rules shared by every prompt

Each prompt below is self-contained, but these are the operating principles behind all of them:

Inspect repository instructions, latest main, and currently open PRs before editing.

Use the exact branch in the prompt. If it already exists, append -2, -3, and so on rather than reusing another agent's branch.

Never commit directly to main, merge your own PR, force-push, delete branches/releases, or rewrite accepted immutable registry history.

Do not commit production SQLite databases, compressed corpora, credentials, private paths, client data, personal notes, or rights-unclear payloads.

Do not wait for another agent. Do not declare yourself blocked because a proposed v3 schema or interface is not merged.

Preserve existing behavior by default. Prefer new versioned modules and compatibility adapters over destructive renames.

Do not edit README.md, shared root configuration, or generated surfaces unless the prompt explicitly assigns them to your lane.

Before the final push, update from main, resolve only conflicts inside your reserved paths, run tests, and inspect the complete diff.

Add a unique handoff file at the exact path assigned by the prompt. It must contain: scope, changed paths, commands, tests, assumptions, compatibility seams, known risks, data/rights notes, and suggested merge considerations.

Open a draft PR. The PR description must include:

Parallel lane:
Branch:
Owned paths:
Behavior changed:
Compatibility preserved:
Tests and measurements:
External sources and rights:
Integration seams:
Known risks:

Parallel observation exchange envelope v0.1

Source and ingestion lanes must emit replayable fixture records using this interim envelope. It is deliberately an observation contract, not a canonical ontology, so agents can work independently without silently resolving identities.

{
  "envelope_version": "pg-observation-0.1",
  "source": {
    "source_id": "openalex",
    "snapshot_id": "source-native revision or dated snapshot",
    "record_native_id": "source-native stable identifier",
    "observed_at": "ISO-8601",
    "retrieved_at": "ISO-8601",
    "terms_revision": "URL, revision, or documented unknown",
    "rights_state": "public_metadata|open_data|restricted|discovery_only|pending",
    "payload_sha256": "sha256 of the replayable raw fixture or record"
  },
  "subject": {
    "kind": "person|organisation|account|work|event|venue|place|concept|claim",
    "source_native_id": "source-local identifier",
    "label": "source-observed label",
    "attributes": {}
  },
  "identifiers": [
    {
      "scheme": "orcid",
      "value": "0000-0000-0000-0000",
      "scope": "global|source|organisation",
      "stability": "stable|mutable|unknown",
      "uniqueness": "unique|non_unique|unknown",
      "evidence": "literal source field or locator"
    }
  ],
  "contributions": [],
  "relationships": [],
  "evidence": [],
  "raw_pointer": "fixture path, source locator, or content-addressed receipt"
}

Rules:

Names, companies, locations, biographies, topics, and handles are never globally unique identifiers.

The envelope never assigns a canonical People Graph ID.

Model-generated classifications are explicitly marked in evidence; they are not source observations.

Popularity, followers, stars, downloads, and citations are timestamped observations, never a universal canonical person score.

Full raw payloads remain outside Git unless they are tiny, public-safe test fixtures.
```

## Prompt 3 — verbatim

```text
Prompt 3 — Additive People Graph v3 ontology and schema

You are the ontology and schema agent for sisodias/siso-people-graph. You are running in parallel and must produce a complete standalone proposal from current main. Do not wait for the red-team or identity agents.

REPOSITORIES
- Read/write: sisodias/siso-people-graph
- Read-only context: sisodias/siso-book-library, sisodias/great-library-of-siso
- Oracle is out of scope.

BRANCH
`pg/v3-ontology-schema-20260806`

EXCLUSIVE PATH OWNERSHIP
- `schema/v3/**`
- `docs/architecture/**`
- `tests/schema_v3/**`
- `docs/handoffs/schema-v3.md`
Do not modify existing v2 schema, loaders, `ask.py`, README, or shared root config.

PARALLEL RULE
Use current main as evidence. Independently audit existing code. If another lane later reaches a different conclusion, your handoff must make the disagreement easy to adjudicate. Do not create a dependency on another PR.

MISSION
Define an additive v3 model that can grow 10× in observations and 100× in research usefulness without confusing source observations, canonical entities, identity decisions, claims, or projections.

REQUIRED MODEL
Create versioned SQLite DDL, constraints, sample data, compatibility notes, and tests covering:
- `source` and `source_snapshot`: terms revision, rights state, snapshot/revision, digests, acquisition method, observation time, and deletion/tombstone obligations;
- append-oriented source observations retaining source-native identifiers and raw evidence pointers;
- canonical entity IDs independent of handles/names, with person, organisation, account, pseudonym, Work, event, venue, place, and concept types;
- identifier definitions declaring scope, uniqueness, mutability, trust class, and source authority;
- first-class Works, versions/editions/expressions, contribution roles/order/time, venues, citations, dependencies, and locators;
- identity candidate claims, positive/negative evidence, decisions, conflicts, canonical clusters/redirects, reversibility, and review lineage;
- generic evidence-backed assertions with subject, predicate, object/value, confidence, status, valid time, observed time, extraction method, and deciding authority;
- typed temporal relationships;
- aliases plus Unicode-safe search;
- rights/privacy/publication state at source, Work, evidence, and claim levels;
- named derived projections with method/version/scope metadata rather than one canonical rank/tier/influence number.

INTERIM EXCHANGE CONTRACT
Map the following standalone observation envelope into v3 tables and document the mapping. Do not change its fields in this lane:
- envelope version `pg-observation-0.1`
- source snapshot and record-native ID
- subject kind/source-native ID/label/attributes
- identifiers with scope, stability, uniqueness, and literal evidence
- contributions, relationships, evidence, and raw pointer
The envelope never assigns a canonical ID.

INVARIANTS
- No silent name merge.
- Handles are aliases; stable platform IDs are identifiers.
- Company, location, topic, biography, and real name are attributes, not unique IDs.
- Every accepted fact has provenance and observed time.
- Corrections and merges are reversible while source observations survive.
- Source vocabularies stay namespaced; crosswalks are explicit.
- A Work is not embedded only as a title string on a person edge.
- Model inference never masquerades as source observation.

DELIVERABLES
- `docs/architecture/people-graph-v3.md` with diagrams, invariants, example records/queries, rejected alternatives, scale strategy, and v2 compatibility limits.
- Versioned schema under `schema/v3/`.
- Import mapping for `pg-observation-0.1`.
- Synthetic tests for foreign keys, uniqueness scopes, conflicting stable IDs, reversible identity decisions, rights coverage, and Unicode search.
- A rebuild/migration strategy that prefers source reconstruction and never rewrites the current production asset in this PR.

ACCEPTANCE
- All lane-local schema tests pass offline.
- Existing v2 files are untouched.
- Commit, push, and open a draft PR titled `Architecture: add the People Graph v3 evidence ontology`.
- Final response: branch, commits, PR, tests, schema summary, disputed decisions, and compatibility seams.
```

## Integrity check

From a checkout containing the original source file, the excerpts can be checked
with:

```bash
python3 - <<'PY_CHECK'
from pathlib import Path
import hashlib
s = Path('Pasted text.txt').read_text(encoding='utf-8')
common = s[:s.index('\nPrompt 1 —')].rstrip() + '\n'
p3s = s.index('Prompt 3 — Additive People Graph v3 ontology and schema')
p3e = s.index('\nPrompt 4 — Safe identity resolution and canonical clusters', p3s)
p3 = s[p3s:p3e].rstrip() + '\n'
print(hashlib.sha256(s.encode()).hexdigest())
print(hashlib.sha256(common.encode()).hexdigest())
print(hashlib.sha256(p3.encode()).hexdigest())
PY_CHECK
```

Expected digests, in order:

```text
077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d
81fd3c1bd722347d901eb04c03e669ea67183f57b31326e55be0fb5d3c9b9711
dd5dfe689c4b7f4e8617fcbd08d0355059ec98a2bfd7e222be952bda1932c57d
```
