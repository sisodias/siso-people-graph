# Verbatim source brief: Prompt 10

> Extracted verbatim from `SISO People Graph — Parallel-Slam GPT-5.6 Agent Prompts`, dated 2026-08-06.
> The surrounding prompts are not reproduced because this lane owns Prompt 10 only.

Prompt 10 — Software, packages, and AI-creator pilot

You are the software/AI ecosystem adapter agent for sisodias/siso-people-graph. Work immediately from current main and use the shared observation envelope; do not wait for another schema.

REPOSITORIES
- Read/write: sisodias/siso-people-graph
- Read-only context: sisodias/siso-book-library, sisodias/great-library-of-siso
- Oracle is out of scope.

BRANCH
`pg/software-ai-pilot-20260806`

EXCLUSIVE PATH OWNERSHIP
- `sources/software/**`
- `sources/ai/**`
- `tests/sources_software_ai/**`
- `docs/source-methods/software-ai/**`
- `docs/handoffs/software-ai-pilot.md`
Do not edit core schema, identity, build, query, claims, README, or root config.

PARALLEL RULE
Emit `pg-observation-0.1` records. Never assign canonical IDs. A missing v3 table is not a blocker.

MISSION
Move beyond “repository owner plus stars” to a source-native graph of accounts, repositories, packages, releases, models, datasets, Spaces/apps, maintainers, contributors, dependencies, organisations, transfers, and history.

SOURCES
Use a bounded, current, bulk-friendly subset of GitHub REST/GraphQL, GH Archive, Software Heritage, ecosyste.ms, PyPI, npm, crates.io, and Hugging Face Hub. Prefer public snapshots/indexes to expensive per-item calls when available. Evaluate relevant public GitHub projects before reinventing ingestion or entity-resolution components.

IDENTITY/WORK RULES
- GitHub numeric account/repository/node IDs are source-scoped stable identifiers; logins/full names are mutable aliases.
- Software Heritage IDs identify archived source artifacts/history.
- Package coordinates are Work identifiers; registry maintainers are contribution relationships, not person aliases.
- Hugging Face models, datasets, and Spaces are distinct Work types with versions, licenses, organisations, and relationships.
- Organisations remain first-class observations.
- Stars, downloads, followers, dependent counts, likes, and citations are timestamped metrics only.

OBSERVATION ENVELOPE
Every fixture/pilot record must include source snapshot/native ID/times/terms/rights/hash; subject kind/native ID/label/attributes; identifiers with scope/stability/uniqueness/evidence; contributions, relationships, evidence, and raw pointer; no canonical People Graph ID.

COHORT
Sample high-signal current GitHub labels plus multi-registry maintainers and AI creators. Include account rename, repository transfer, organisation account, co-maintainers, package dependency, archived repository, model-dataset-Space relationship, and abandoned Work cases.

MEASURE
New stable IDs, Work types, contribution/maintainership edges, dependencies, archived-history links, cross-platform identity evidence, temporal events, source conflicts, API cost, rights/license coverage, and projected scale. Compare API-heavy methods with snapshots/ecosyste.ms/registry dumps.

DELIVERABLES
Adapters, replayable fixtures, envelope exporter, pilot metrics, source method cards, and at least five evidence-first example questions whose answers are impossible from star rankings alone.

ACCEPTANCE
Offline tests pass; no canonical rank mutation or silent identity merge; no bulk repository cloning or large dataset commit. Commit, push, and open a draft PR titled `Pilot: add software and AI creator observations`. Final response: branch, commits, PR, metrics, stable-ID strategy, source costs, and recommended scale subset.

