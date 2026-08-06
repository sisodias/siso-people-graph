# Capability matrix

The executable matrix is produced by:

```bash
python3 -m integration capabilities --repo-root .
python3 -m integration capabilities --repo-root . --database path/to/people.sqlite
```

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `available` | An executable repository or runtime seam was detected and opened successfully. |
| `declared` | Code/schema is present, but no populated runtime asset or successful operation is implied. |
| `missing` | No supported path was detected. |
| `unsupported` | A supplied runtime artifact exists but does not expose a supported adapter seam. |
| `invalid` | A supplied observation export failed the shared contract. |

## Launch-time current-main baseline

Base commit: `de048bb3b34bf931b56fd741cb46c1334acdfb98`.

| Capability | Status on launch-time `main` | Evidence | Explicit gap |
| --- | --- | --- | --- |
| v2 schema | Declared | `schema/people_schema_v2.sql` | No committed database; identifier semantics, snapshots, rights, and deletion obligations are absent from row contracts. |
| v2 build | Declared | `loaders/build_people_graph_books.py`, `loaders/build_people_graph_v2.py`, owner/topic loaders | No clean-checkout or reproducibility proof. The v2 builder resolves its schema relative to `loaders/` while the schema is stored under `schema/`. |
| v2 identity proposals | Declared | `loaders/match_identities.py`, `identity_claim` table | Not a canonical-cluster interface. The legacy external-ID namespace mixes identifiers and attributes. |
| v2 query | Declared | `loaders/ask.py` | No runtime database in Git, no rights/snapshot/build digest/claims response, and no normalized accepted-decision surface. |
| v3 schema | Missing | No `schema/v3/**` on launch-time main | Future lane. |
| v3 identity engine | Missing | No `identity_v3/**` | Future lane. |
| reproducible build/manifests | Missing | No `build_v3/**` or `manifests/**` | Future lane. |
| query library/API/MCP | Missing | No `query_v3/**`, `api/**`, or `mcp/**` | Future lane. |
| generic claims/projections | Missing | No `claims/**` or `projections/**` | Future lane. |
| source pilots | Missing | No scholarly/software/AI/creator/media adapter paths | Future lanes. |
| executable red-team suite | Missing | No `tests/red_team/**` | Future lane. |
| shared observation contract | Missing on main; available in this branch | `integration/contract.py`, JSON schema | Integration lane only; not a launch dependency. |
| compatibility adapter spine | Missing on main; available in this branch | `integration/adapters.py` | Legacy rights/snapshots remain explicitly unknown unless supplied. |
| merge-risk/path ownership gate | Missing on main; available in this branch | lane registry and analyzer | Consumes an offline PR snapshot; it does not require GitHub credentials. |

## Partial-merge behavior

The detector independently probes each lane path. A checkout with only v3 schema and scholarly sources will report those paths while keeping identity, claims, API, MCP, and build capabilities missing. A v2 database is selected only when all current required tables are present. A v3-like database is selected only when a full-envelope JSON seam is detected. Missing capabilities stay visible in the report and must be handled by adapters or explicit degraded behavior.
