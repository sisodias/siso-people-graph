# Handoff — Reproducible builds and source manifests

**Lane:** 5 (parallel-slam Prompt 5 — *Reproducible builds and source manifests*).

Numbering caveat, because three schemes exist across the estate and "Lane 5"
means different things in each: this work is **Prompt 5 of `parallel-slam.md`**,
the pack that was actually launched, and the same work appears as **Prompt 4 of
`dependency-ordered-superseded.md`**. Both live in
`sisodias/great-library-of-siso` on branch
`agent/people-graph-audit-record-20260806` under
`research/people-graph-program-record/prompts/`. Both were read; where they
differ, parallel-slam was followed. The one substantive addition taken from the
superseded pack is its stronger phrasing that *"any ranking belongs to named,
versioned projection code with method metadata"*.
**Branch:** `pg/reproducible-builds-parallel-20260806`
**Status:** draft PR, not merged.
**Closes:** PG-AUDIT-004 / PGRT-001 (clean-checkout build). Addresses PG-AUDIT-005
(rank_score conflation and non-idempotent reruns).

---

## What was broken

### 1. A clean checkout could not build the graph at all — P0

`loaders/build_people_graph_v2.py` resolved its schema as

```python
SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "people_schema_v2.sql")
```

which is `loaders/people_schema_v2.sql`. The tracked file is
`schema/people_schema_v2.sql`. The build therefore raised `FileNotFoundError`
before reading a single byte of input, and only ever worked on a machine where
an untracked copy happened to sit beside the loader.

Reproduced before fixing, from a fresh clone of `main` into a temp directory:

```
FileNotFoundError: [Errno 2] No such file or directory:
  '.../mainco/loaders/people_schema_v2.sql'
```

The published source was not the build recipe. Everything else in this lane
follows from that: a build nobody else can run is a build nobody can verify.

### 2. Reruns were not idempotent — the graph depended on execution count

`loaders/load_owner_topics.py` ran

```sql
UPDATE person SET rank_score = COALESCE(rank_score,0) + ?
```

A second run over an unchanged source **doubled** every owner's contribution; a
third tripled it. The ranking was a function of how many times the loader had
been executed, not of what the source said.

### 3. `rank_score` had no unit, because four loaders wrote four different things

| writer | quantity | unit |
|---|---|---|
| `build_people_graph_v2.py` | `float(work_count)` | books written |
| `build_people_graph_v2.py` | copied v1 `rank_score` | a legacy score |
| `load_owners_into_people_graph.py` | `sum(stars)` | GitHub stars |
| `load_owner_topics.py` | `+= mean(overall_value)` | a 0–100 model rating |

A value of `30910` meant "summed stars" for one row and something else entirely
for the next, so `ORDER BY rank_score` compared incommensurable measurements.

This is not a cosmetic issue. Measured in the Foundry enrichment log: **dtolnay
— 10 repos rated ≥90, 30,910 stars — ranks above facebook at 801,473 stars**
once rated value is used instead of popularity. A single blended column cannot
express that inversion, and the inversion is the interesting signal. It is a
concrete instance of the program's own diagnosed category collapse,
*popularity metric → universal value*.

### 4. Stale rows accumulated; changed rows were frozen

Loaders used `INSERT OR IGNORE` and never deleted. A repo that was removed,
dropped below the star threshold, or turned out to be a fork kept its edge
forever, so the graph was the union of every snapshot ever loaded. `OR IGNORE`
also meant a *changed* row was silently skipped — the first snapshot's star
count was kept and every later snapshot was inert.

---

## What changed

### `build_v3/paths.py` — path resolution, with overrides

Repo root is derived from `__file__`, never from cwd, so a loader invoked from
anywhere resolves identically. Every well-known artifact has a named accessor
and an environment override (`PG_SCHEMA_V2`, `PG_MANIFESTS_DIR`, `PG_BUILD_DIR`),
so an operator can point a build at a vault **without that topology appearing in
public source**. Missing artifacts fail with a message naming the resolved repo
root, not a bare `FileNotFoundError`.

### `build_v3/observations.sql` — observations and projections

Additive, beside the v2 schema. It alters no existing table and drops no column.

`person_observation` — a named, timestamped, sourced measurement, with a
**required `unit`**. Primary key `(person_id, metric, source)` means a rerun
*replaces* rather than accumulates: **the additive bug cannot be expressed in
this table.**

`person_projection` — a named, versioned ranking, with `method` and
`method_version` in the primary key so changing a rule creates a new projection
rather than silently rewriting the old one.

`build_run` — run metadata, deliberately excluded from the logical digest. A
build timestamp stored on a canonical row would make two identical builds differ
and leave reproducibility unmeasurable by construction.

### The three owned loaders

All three now accept `--observed-at` (pins the timestamp), `--snapshot` (ties
rows back to a manifest) and, where they write edges, `--no-prune` to disable
pruning. They no longer write `person.rank_score` at all — the quantities they
used to put there are recorded as observations with their units.

Pruning is **scoped by source**: `load_owners_into_people_graph.py` only removes
`person_content` rows whose `source='github_identity'`, and
`load_owner_topics.py` only removes `github_topic`/`github_lang` schemes from
`repo_card`. The books loader's `lcsh` edges and the v1 migration's rows are
never touched. There is a test asserting exactly that, because a pruning bug
that deleted another loader's rows would be far worse than the accumulation it
replaces.

### Determinism fixes beyond the timestamp

Topic selection sorted by `-count` alone, so the top-25 cut silently depended on
the order rows came back from the source. Ties now break by name. Projection
ranks tie-break by `person_id` and use dense ranking, so equal values share a
rank rather than being ordered arbitrarily.

---

## Reproducibility: what is proven, and what is not

**Logical equivalence is the invariant. Byte identity is not, and is not claimed.**

Measured, two clean builds in separate directories with distinct run ids:

```
logical digest A = 65a70a5a22b731a169e4b1626cb3e252598d488946248deac5704abfbfe6f192
logical digest B = 65a70a5a22b731a169e4b1626cb3e252598d488946248deac5704abfbfe6f192
counts_equal     = true          differing_tables = []
byte_identical   = FALSE         (size 180224 both; sha256 differs)
```

The byte result is reported rather than assumed, per the spec's "measure binary
SQLite reproducibility honestly". A SQLite file is not a deterministic function
of its logical content: page allocation depends on insertion order, the freelist
carries the ghosts of deleted rows, the header holds a change counter, and WAL
checkpoint timing affects layout. Chasing byte identity would mean constraining
all of that; asserting it without measuring would be false.

The logical digest covers every canonical table, rows sorted by full tuple,
values rendered through one explicit typed rule, with `build_run` and FTS shadow
tables excluded and each exclusion justified in `build_v3/digest.py`.

### Remaining non-reproducible inputs — stated explicitly

1. **Real source snapshots are not content-addressed yet.** Manifests record a
   sha256 for each source, but nothing *enforces* that a build used the digest it
   declares. `manifest.verify_digest()` exists and is tested; wiring it as a hard
   gate on a production build is not done.
2. **`enrich_owners.py` is out of this lane's scope** and calls the GitHub API.
   Any build including it is network-dependent and therefore not reproducible.
   It is not part of the fixture build.
3. **Only the fixture path is one-command.** `build_v3/build.py` accepts
   `--fixture` only. A full production build still needs the operator to supply
   four source databases and the documented command below; it was not run here
   because no production corpus was available offline, and claiming otherwise
   would be fabrication.
4. **`identity_claim` is empty in fixture builds.** `match_identities.py` is
   owned by the identity lane (PR #4), so claim generation is untested here.
5. **gzip packaging is deterministic (mtime=0), but compression level is the
   Python default** and could change across CPython versions. The receipt
   therefore pins the *logical* digest, not the `.gz` checksum, as the invariant.

---

## Commands

```bash
# One-command offline fixture build: no network, no vault, no real data.
python3 build_v3/build.py --fixture --out-dir ./build-out

# The acceptance test: two clean builds, compared.
python3 build_v3/verify_reproducible.py

# Validation and digest of an existing graph.
python3 build_v3/validate.py people_v2.sqlite --manifests manifests/
python3 build_v3/digest.py people_v2.sqlite --compare-to other.sqlite

# Named projections (replaces the universal rank_score).
python3 build_v3/project.py --graph people_v2.sqlite --apply

# Release packaging. Produces artifacts; uploads nothing.
python3 build_v3/package.py --graph people_v2.sqlite --out-dir ./release \
    --manifests manifests/

# Tests
python3 -m unittest discover -s tests/build_v3 -t . -v
```

**Documented full build** (requires operator-supplied snapshots; not run here):

```bash
python3 loaders/build_people_graph_v2.py \
    --v1 "$V1_DB" --people "$BOOKS_PEOPLE_DB" --books "$BOOKS_DB" \
    --out people_v2.sqlite \
    --observed-at "$SNAPSHOT_TIME" --books-snapshot "$BOOKS_SNAPSHOT" \
    --run-id "$RUN_ID"
python3 loaders/load_owners_into_people_graph.py \
    --identity "$IDENTITY_DB" --graph people_v2.sqlite --min-stars 100 --apply \
    --observed-at "$SNAPSHOT_TIME" --snapshot "$GH_SNAPSHOT"
python3 loaders/load_owner_topics.py \
    --identity "$IDENTITY_DB" --graph people_v2.sqlite --min-stars 100 --apply \
    --observed-at "$SNAPSHOT_TIME" --snapshot "$GH_SNAPSHOT"
python3 build_v3/project.py --graph people_v2.sqlite --apply
python3 build_v3/validate.py people_v2.sqlite --manifests manifests/
```

Passing the same `--observed-at` to every step is what makes the run
reproducible. Omitting it restores the old wall-clock behaviour, which is
convenient for ad-hoc runs and unsuitable for a release.

---

## Migration note for existing release assets

The published `graph-v2` asset (2026-08-04) was built by the old pipeline. It
therefore contains `person.rank_score` values that blend four incompatible
quantities, and it carries no `person_observation`, `person_projection` or
`build_run` tables.

- **It is not invalidated.** Its content edges, topics and life dates are
  unaffected by this lane; only the ranking column is untrustworthy.
- **Do not compare its digest to a new build.** There is no logical digest for
  it, and the schemas differ.
- **Consumers reading `rank_score` must migrate** to a named projection.
  `github_popularity` reproduces the old star-based intent; `rated_value` is the
  one that surfaces the dtolnay-over-facebook inversion. Neither is "the" rank,
  which is the point.
- `rank_score` is left in the schema deliberately. Dropping a column other lanes
  may still read is not this lane's decision; this lane's loaders simply stop
  writing it, and validation fails if any of them starts again.

---

## Verification performed

| check | result |
|---|---|
| P0 reproduced on unmodified `main` | `FileNotFoundError: .../loaders/people_schema_v2.sql` |
| P0 test fails on `main` for the *right reason* | asserts on `FileNotFoundError` in stderr, using only flags that exist on main |
| Build from a temp cwd on this branch | exit 0, database produced |
| Two clean builds, separate directories | identical logical digest, identical counts |
| Distinct run ids | digest unchanged (run metadata does not leak) |
| 1 vs 2 vs 3 vs 5 loader runs | identical digest — no drift |
| `rank_score` written by any loader | 0 rows |
| Removed repo / dropped topic | edge pruned; `lcsh` edges untouched |
| Changed star count | updates (no longer frozen by `OR IGNORE`) |
| Validator catches orphan edge / rank regression / duplicate identity | all fail as designed |
| Digest sensitivity | a changed value changes the digest |
| Tracked data assets | none |
| Test suite | 35 tests, all passing |

## What a reviewer should challenge first

1. **The exclusion list in `digest.py`.** Excluding a table is a claim that its
   contents may legitimately vary. `build_run` and the FTS shadows are argued in
   the source; if either argument is wrong, the digest overstates reproducibility.
2. **Pruning scope.** It is bounded by `source` and `scheme`. If another loader
   ever writes rows under `source='github_identity'`, pruning would delete them.
3. **The fixture is small.** 6 people, 56 rows. It exercises the failure modes
   deliberately, but it is not evidence about behaviour at 280,708 people —
   nothing here has been run against a production corpus.
