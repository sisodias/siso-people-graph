# People Graph v2 red-team audit — 2026-08-06

## Executive summary

This audit ran a deterministic, offline fixture suite against
`sisodias/siso-people-graph` `main` at
`de048bb3b34bf931b56fd741cb46c1334acdfb98`. No production database, release
asset, network call, or non-standard Python dependency was used.

The suite contains **22 executable cases**:

- **3 PASS** — confirmed current invariants.
- **19 XFAIL** — documented current failures reproduced as expected.
- **0 FAIL, 0 XPASS, 0 ERROR** — no unexplained result and no stale expected
  failure at the audited baseline.

The findings register contains **8 P0** and **8 P1** issues. The P0 set should be
resolved before bulk ingestion or bulk identity acceptance because the fixtures
show build failure, silent identity fusion, unsafe auto-acceptance, inert
accepted claims, stale/additive reruns, Unicode identity collapse, GitHub
rename/transfer splits, and a cross-repository Book export contract that drops
roles and merges by display name.

This lane does **not** change production behavior. It codifies failure modes and
stable IDs so implementation lanes can fix one invariant at a time without
losing evidence.

## Baseline and scope

| Item | Value |
| --- | --- |
| Primary repository | `sisodias/siso-people-graph` |
| Baseline branch | `main` |
| Baseline commit | `de048bb3b34bf931b56fd741cb46c1334acdfb98` |
| Open PRs at launch | none |
| Read-only Book context | `sisodias/siso-book-library` at `be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b` |
| Read-only Great Library context | `sisodias/great-library-of-siso` at `12f4cc249b2b5dc268d05d1698fe9c5e3079327d` |
| Production files changed | none |
| Test dependencies | Python standard library only |

The tests target the tracked schema, builders, identity matcher, GitHub owner and
topic loaders, GitHub enrichment, query surface, and the pinned Book Library
export seam. Oracle and any private production topology are outside this audit.

## Reproduce

```bash
python3 tests/red_team/run.py
python3 tests/red_team/run.py --json
python3 tests/red_team/run.py --list
python3 tests/red_team/run.py --case PGRT-T003 --case PGRT-T004
```

The runner creates all SQLite files under temporary directories and deletes them
after each case. `XFAIL` means a known defect reproduced and is green by design.
`XPASS` is non-zero because a production fix requires the expected-failure audit
to be updated rather than silently going stale.

## Result inventory

| Finding | Severity | Cases | Result | Bulk-ingestion blocker | Suggested owning lane |
| --- | --- | --- | --- | --- | --- |
| PGRT-001 | P0 | T001 | XFAIL | yes | reproducible build and repository topology |
| PGRT-002 | P0 | T002 | XFAIL | yes | identity resolution and canonicalization |
| PGRT-003 | P0 | T003 | XFAIL | yes | identity evidence policy and identifier registry |
| PGRT-004 | P0 | T004 | XFAIL | yes | identity resolution plus query canonicalization |
| PGRT-005 | P1 | T005 | XFAIL | no | identity claim persistence and idempotency |
| PGRT-006 | P0 | T006, T008, T009 | XFAIL | yes | loader run provenance, replacement semantics, and idempotency |
| PGRT-007 | P1 | T010, T011 | XFAIL | no | GitHub enrichment observations and refresh policy |
| PGRT-008 | P1 | T012 | XFAIL | no | canonical ID adapters for GitHub loaders |
| PGRT-009 | P0 | T013 | XFAIL | yes | Unicode-safe source identity and normalization |
| PGRT-010 | P1 | T014 | XFAIL | no | FTS alias projection and search behavior |
| PGRT-011 | P0 | T008, T015 | XFAIL | yes | GitHub stable-ID ingest and ownership history |
| PGRT-012 | P1 | T017 | XFAIL | no | identity candidate constraints and pseudonym modelling |
| PGRT-013 | P1 | T006, T010, T018 | XFAIL | no | evidence metrics and derived ranking projections |
| PGRT-014 | P1 | T019 | XFAIL | no | temporal evidence and uncertainty-aware queries |
| PGRT-015 | P1 | T020 | XFAIL | no | query capability diagnostics and inventory contract |
| PGRT-016 | P0 | T021, T022 | XFAIL + PASS control | yes | Book export contract plus People Graph ingest seam |

Machine-readable details, exact source symbols, reproduction commands, blast
radius, and stable IDs are in
`docs/audits/people-graph-v2-findings.json`.

## P0 findings

### PGRT-001 — clean-checkout build cannot locate the schema

**Source evidence:** `loaders/build_people_graph_v2.py` defines `SCHEMA` as
`loaders/people_schema_v2.sql`, while the tracked file is
`schema/people_schema_v2.sql`.

**Fixture:** T001 launches the real builder with three empty SQLite inputs from a
temporary directory. It exits before reading those inputs with
`FileNotFoundError` for the loader-adjacent path.

**Violated invariant:** a deterministic builder must run from a clean checkout
using only tracked paths and supplied inputs.

**Blast radius:** every clean v2 rebuild through the documented builder entry
point is blocked.

### PGRT-002 — normalized names silently fuse source-native people

**Source evidence:** `build_people_graph_v2.build()` constructs an `existing`
map from whitespace-normalized, lower-case display names. A matching Book person
reuses that person ID without creating an `identity_claim`.

**Fixture:** T002 supplies a registry `Alex Lee` and a distinct Book source record
labelled `  Alex   Lee `. The output contains one person, the Book edge is
attached to `reg:alex`, and no claim records the decision.

**Violated invariant:** source observations remain separate until an explicit,
evidenced identity decision is accepted.

**Blast radius:** a common name collision can permanently attach works, dates,
and topics to the wrong canonical person.

### PGRT-003 — non-unique attributes can auto-accept identity

**Source evidence:** `match_identities.propose()` indexes every row in
`external_ids` by `(platform, value)` and emits `shared_external_id` at 0.98.
`enrich_owners.enrich()` stores `real_name`, `company`, and `location` in that
same table.

**Fixture:** T003 independently gives two unrelated people the same company,
location, and real name. Each attribute creates an accepted 0.98 claim when
`--accept shared_external_id` is used.

**Violated invariant:** only schemes with documented identifier uniqueness can
resolve identity automatically.

**Blast radius:** shared employers, cities, and common real names can merge
unrelated people during a bulk acceptance run.

### PGRT-004 — accepted claims do not affect canonical queries

**Source evidence:** `ask.who()` and `ask.works()` query person/content/topic
rows but never read `identity_claim` or `merged_into`.

**Fixture:** T004 creates two duplicate records with one accepted manual claim
and complementary GitHub/Book works. `who` still returns both IDs and `works`
returns one work instead of the two-work canonical set.

**Violated invariant:** an accepted identity decision must produce a canonical
cluster, redirect, or equivalent query behavior.

**Blast radius:** review and acceptance can report success while user-facing
answers remain duplicated and incomplete.

### PGRT-006 — reruns are additive rather than source-replaceable

**Source evidence:**

- `load_owner_topics.load()` adds the same mean rating to `rank_score` on every
  applied run.
- `load_owners_into_people_graph.load()` inserts current rows but never removes
  or tombstones source rows that disappear.
- `build_people_graph_books.build()` reuses an output database without clearing
  people or edges no longer present in the source.

**Fixtures:** T006 changes rank from 100 → 108 → 116 across identical runs. T008
replaces `oldorg/project` with `neworg/project` and both owners/edges remain.
T009 replaces the source Book row and both old and new people/works remain.

**Violated invariant:** identical reruns are idempotent, and a source replacement
cannot leave stale observations asserted as current.

**Blast radius:** periodic bulk jobs inflate values and accumulate deleted or
transferred assertions indefinitely.

### PGRT-009 — non-Latin names collapse into one identity key

**Source evidence:** `build_people_graph_books.person_key()` strips every
character outside ASCII `a-z`, digits, comma, and space, then uses the result as
the stored key.

**Fixture:** T013 maps both `李, 白` and `王, 維` to `,`. The output contains one
person, one edge, and a combined `raw_variants` list.

**Violated invariant:** Unicode source labels remain lossless, and a lossy
comparison key never becomes a canonical identity key.

**Blast radius:** distinct non-Latin contributors can be irreversibly fused and
their attribution combined during Book ingestion.

### PGRT-011 — GitHub rename/transfer handling ignores stable numeric IDs

**Source evidence:** enrichment records `github_id`, but the owner loader matches
only `github_login` or `gh:<login>`. Repository edges are keyed by current
`full_name` and stale rows are not reconciled.

**Fixtures:** T015 starts with `gh:oldlogin` plus `github_id=42`, then loads a
repository under `newlogin`; it creates `gh:newlogin`. T008 demonstrates that a
repository transfer leaves both old and new ownership edges.

**Violated invariant:** a stable platform ID preserves one account across a
login change, and source replacement reconciles transfers.

**Blast radius:** one account can split into multiple people, while contradictory
ownership assertions remain simultaneously active.

### PGRT-016 — Book export merges by name and drops contributor roles

**Source evidence:** the pinned
`sisodias/siso-book-library/scripts/load_into_people_graph.py` blob
`de4e9fd91c076fd514887c82bd334dde43271d7b` indexes canonical people by
normalized display name and filters contributions through
`AUTHORSHIP = {"author"}`.

**Fixture:** T021 replays that pinned contract. A distinct Book `Alex Kim` is
mapped to `gh:alex-kim`, while translator and editor contributions disappear.
T022 is the control: the People Graph v2 builder preserves both `author` and
`translator` when upstream supplies those rows.

**Violated invariant:** cross-repository exports preserve source identity
boundaries and every contributor role until explicit resolution.

**Blast radius:** same-named people can be fused and non-author attribution can
be lost before the v2 builder receives the data.

## P1 findings

### PGRT-005 — duplicate identity claims on rerun

The schema lacks a unique pair key and `INSERT OR IGNORE` therefore has no
conflict to ignore. T005 grows one exact-name claim to two identical rows on the
second run. This inflates review queues and makes change detection noisy.

### PGRT-007 — enrichment mutates canonical state and skips partial profiles

T010 shows a profile fetch changing `name`, `rank_score`, and `built_at`. T011
shows that an existing `real_name` prevents collection of missing `github_id`,
`x_handle`, and `website`. Enrichment should append source-scoped observations
and refresh fields independently.

### PGRT-008 — non-`gh:*` canonical people miss GitHub adapters

T012 gives `reg:alice` a valid `github_login=alice`. Topic loading and enrichment
both skip it because one requires a `gh:*` ID and the other requires
`origin='github'`. Domain loaders should resolve through external identifiers.

### PGRT-010 — aliases retained upstream never reach FTS

The Book people builder stores raw variants, but the v2 builder inserts an empty
FTS alias for every person. T014 shows `Mark Twain` retained upstream while an
FTS query for `Twain` returns no match for canonical `Clemens, Samuel`.

### PGRT-012 — kind and pseudonym conflicts are not candidate constraints

T017 creates human/organisation and human/pseudonym pairs with identical labels.
The matcher proposes ordinary exact-name claims for both because `kind` is not
part of candidate metadata or gating. Known incompatible kinds should be
negative evidence or a separately modelled relationship.

### PGRT-013 — `rank_score` has no stable unit

T018 executes the production sequence: 100 summed stars becomes 108 after adding
a repository rating, then becomes 7 after enrichment overwrites it with
followers. The same column also receives Book work counts. These are distinct
observations, not one comparable quantity.

### PGRT-014 — unknown death becomes a certain 80-year lifespan

`v_contemporaries` uses `COALESCE(death_year, birth_year + 80)` in both its join
condition and returned interval. T019 creates a contemporary edge from 1979 to
1980 solely through that substitution. The assumption is visible in SQL, but
the returned edge carries no uncertainty marker.

### PGRT-015 — missing capability is indistinguishable from no evidence

T020 attaches only a Book database. `who("Alice")` returns an ordinary empty
match list, and inventory reports only the present domain. An agent cannot tell
whether there is no person evidence or the required people domain is absent.

## Confirmed invariants

These PASS controls prevent the audit from describing the implementation as
more broken than the fixtures establish:

1. **T007:** two identical owner-loader runs do not duplicate people,
   `github_login` identifiers, or repository edges. The defect is replacement
   and mutation handling, not exact duplicate insertion.
2. **T016:** an ambiguous exact common name remains a 0.55 `proposed` claim when
   no auto-accept method is requested.
3. **T022:** the v2 builder preserves distinct Book roles when those roles are
   supplied in `bkp.person_work`. The observed role-loss seam is upstream in the
   pinned legacy Book export contract.

## Bulk-ingestion gate

The following findings are explicit blockers to bulk ingestion or bulk identity
acceptance:

`PGRT-001`, `PGRT-002`, `PGRT-003`, `PGRT-004`, `PGRT-006`, `PGRT-009`,
`PGRT-011`, and `PGRT-016`.

A safe reopening sequence is:

1. Restore clean deterministic builds and source-replacement semantics.
2. Preserve source-native entity boundaries and Unicode labels.
3. Define an allowlist of identifier schemes eligible for automatic identity
   acceptance.
4. Connect accepted claims to canonical reads with a reversible projection.
5. Make GitHub account/repository observations stable-ID aware.
6. Correct the Book export contract before replaying Book data.

Each implementation lane should convert the corresponding XFAIL to PASS and
update the findings JSON in the same change. An unexplained XPASS is a failing
suite result so that the audit cannot silently drift.

## Assumptions and limitations

- Fixtures are intentionally tiny and adversarial. They prove concrete behavior
  on the observed code path; they do not estimate prevalence in the production
  corpus.
- No production SQLite assets were opened. Dataset-wide counts and collision
  rates are therefore not claimed.
- The Book seam uses a pinned JSON contract derived from the exact public source
  blob named above, so the suite stays runnable from a clean People Graph
  checkout without cloning a sibling repository.
- No external API is called. Enrichment fixtures monkeypatch the production
  fetch function with deterministic response objects.
- Great Library was read-only context; no test depends on its local data.

## Data and rights

All fixture people, repositories, books, names, URLs, and identifiers are
synthetic except for the two Chinese historical-name labels used solely to
demonstrate Unicode key behavior. The fixtures contain no book text, private
profile data, credentials, API responses from real users, or release assets.
The pinned cross-repository source metadata identifies public repository code;
no third-party content is copied into the audit.
