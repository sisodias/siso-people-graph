# Handoff — read-only query surface (Lane 6)

- **Branch**: `pg/query-surface-parallel-20260806`, forked from `origin/main` @ `de048bb`
- **Spec**: parallel-slam Prompt 6, "Read-only query library, API/MCP, and explorer".
  Cross-read against the superseded v0 Prompt 5; where they differ, parallel-slam
  is canonical per `.docs/lane-numbering-map.html`. The material difference: v0
  Prompt 5 declared a hard dependency on merged v3 canonical resolution, which
  has not merged. Prompt 6's resolver-adapter rule is what made this lane
  executable now.
- **Status**: draft PR. Not merged. No production database was opened.

## What this closes

**PG-AUDIT-002 / PGRT-004 — accepted identity claims were inert.**

`loaders/ask.py` queried `person` rows directly and never read `identity_claim`
or `person.merged_into`. A reviewer could accept an identity merge, the review
queue would report success, and every read path kept returning the duplicate
rows. Reviewers did the work and the graph ignored them. The estate's other
identity work (Lane 4, `identity_v3/`) was invisible for the same reason: nothing
downstream consumed its decisions.

Two further defects in the same file, from the reasoning ledger, had the same
shape — a failure that presented as a success:

| defect | before | after |
|---|---|---|
| identity | `--who Kant` → `bk:kant` and `gh:kant`, split coverage `book:3` / `github:1` | one person, `{book:3, github:1}`, with the decision reported |
| FTS | `WHERE people.person_search MATCH ?` raised `no such column`, swallowed by a bare `except`, silently degraded to a LIKE scan | unaliased-table MATCH; `execution.search_path` declares which path ran |
| truncation | `--works` capped at 200, reported `count = len(rows)` | `returned: 200, total_matched: 250, truncated: true` |

## Necessary, and currently latent

PG-BASELINE measured the production database directly and found **`identity_claim`
holds zero rows** — no proposed, no accepted, no rejected. Two consequences,
stated plainly so nobody reads more into this PR than it delivers:

- This fix is **necessary but not yet sufficient**. On today's production data it
  changes nothing visible, because there are no accepted decisions to honour.
  What it removes is the reason not to produce any: until now, populating
  `identity_claim` would have been pointless work, since no read path consumed it.
  The matcher (`loaders/match_identities.py`) and Lane 4's `identity_v3/` now
  have a consumer.
- The `person.merged_into` half of the resolver is live regardless: it applies to
  any merge a build has already written, independent of the claim table.

The fix is demonstrated against fixtures that contain the decisions production
lacks. That is the correct order — a read path that cannot honour a decision is a
defect whether or not a decision currently exists — but it does mean the
production-visible payoff arrives with the first accepted claim, not with this
merge.

## Architecture

`query_v3/` is the single source of truth. The CLI (`loaders/ask.py`), HTTP API
(`api/`), MCP server (`mcp/`) and viewer (`viewer/`) are projections that hold no
SQL of their own — enforced by `test_no_surface_contains_sql`, which fails the
build if any surface starts talking to the database directly. Four surfaces each
carrying their own SQL is the original defect with four times the surface area.

```
query_v3/capability.py   probe what this database can answer; absence is reportable
query_v3/resolver.py     APPLY decisions already made; never make one
query_v3/evidence.py     the four provenance grades
query_v3/response.py     the truth-contract envelope
query_v3/engine.py       who / works / relationships / path / claims / inventory / source
```

### The resolver boundary — the thing not to break

`query_v3/resolver.py` contains **no matching logic**: no name comparison, no
confidence threshold, no heuristic. Deciding whether two rows are the same human
belongs to Lane 4 (`identity_v3/`, method card `identity-v3.1.0`), which owns the
thresholds, the registry, and the deny-by-default automatic policy. This module
reads decisions a reviewer or an audited policy already recorded and applies them
to reads. If it ever starts deciding, two systems will disagree about who is who
and neither will be authoritative.

Three adapters, chosen by capability detection:

- **v2** — `person.merged_into` plus `identity_claim` where `status='accepted'`.
- **v3** — additive decision/cluster tables when present. Written to the
  documented shape, **unexercised against a real v3 database**, and it says so in
  its own warnings rather than implying it was verified.
- **none** — no identity machinery: duplicates are returned and explicitly
  declared as possible duplicates.

Accepted claims are applied at **read time even when `merged_into` is not yet
written**. That gap — decided but not yet rebuilt — is precisely the window where
a reviewer's work disappears. Proposed claims are reported as unresolved
ambiguity and never applied; rejected claims are never applied.

## Truth contract

Every response carries `schema_version`, `page` (returned / total_matched /
truncated / counts_are_exact), `identity_resolution` (mode, applied decisions,
unresolved candidates), `sources` (resolved path, its origin, rights state),
`capabilities` (including `v3_tables_absent`), `coverage_gaps`, `warnings`, and
`execution` (which search path ran, elapsed ms).

`total_matched` is a real `COUNT` over the same predicate as the page query,
never `len(rows)`. No query says "all" without a declared source universe.

Two subtleties worth knowing before you extend this:

- **`who()` pages in source rows, not people.** Identity resolution legitimately
  reduces row count to people count; counting resolved people against a row total
  would make a successful merge look like truncation and advise paging for
  results that do not exist. Both numbers are reported (`page.total_matched` and
  `result.people_returned`).
- **An absent table is a capability gap, not an empty answer.** `claims()`
  against a database with no `claim` table reports a missing capability rather
  than "this person has no claims".

## Verification

Full offline suite, no network, no production data:

```bash
PYTHONPATH=. python3 -m unittest discover -s tests/query_v3 -t . -p 'test_*.py'
# Ran 64 tests — OK   (clean under -W error::ResourceWarning)
```

`tests/query_v3/test_regression_vs_main.py` is the before/after proof: it
extracts `loaders/ask.py` as it exists on `origin/main`, runs it against the same
fixture, asserts the old behaviour **is** the defect, then asserts the new
behaviour differs in the specific way that matters. A regression test that passes
both before and after proves nothing, so this one is written to fail loudly if
either half stops demonstrating the defect.

`tests/query_v3/test_search_path.py` proves **which execution path ran**, not
merely that a result came back. Both broken MATCH forms are pinned as raising:
the schema-qualified `people.person_search MATCH ?` (what shipped) and the
aliased `s MATCH ?` (a plausible fix that is also wrong — verified against
SQLite, not assumed). The correct operand is the unaliased table name.

Fixtures cover the lane's acceptance list: a multi-source person, a reviewer-
accepted merge with no `merged_into` yet, an ambiguous common name, an
organisation, a historical figure with BCE dates, a relationship path, a 250-work
truncation case, a rejected claim, and a missing database.

`tests/query_v3/test_adversarial.py` covers hostile database states: merge
cycles, self-merge, dangling claim targets, a 12-long merge chain, SQL
metacharacters in names, and a corrupt database file.

### A bug this suite caught

The 12-long merge chain test failed on first run. `_canonical()` preferred "a row
something merged into" ahead of "a row that is not itself merged", so a chain
`A→B→…→L` elected `bk:chain-1` — a row with `state='merged'` — while the only
live row was ignored. Liveness is now checked first. Recorded here because the
same trap is available to anyone extending canonical selection.

## Safety properties

Read-only throughout: every connection and every attach uses `?mode=ro`. All
values are bound; no user input is interpolated into SQL. Limits are capped at
500. The HTTP API serves GET/HEAD only and refuses every mutating verb with an
explicit 405 stating the API is read-only by design — the stdlib default of 501
would read as "not implemented yet" rather than a guarantee. There is no write
endpoint, no arbitrary-SQL endpoint, and no full-corpus payload proxy;
`test_no_write_or_sql_endpoints_exist` and `test_no_write_tool_is_exposed` hold
that line for the API and MCP respectively. The viewer escapes every value that
came from the database.

Machine-specific path guessing is gone. Configuration is explicit
(`PEOPLE_GRAPH_CONFIG`, `PEOPLE_GRAPH_<DOMAIN>`, `PEOPLE_GRAPH_ROOT`, or
`--root`/`--people`), with a local-fixture default, and every resolved path plus
its origin appears in the response — so "why did this machine answer differently"
is always answerable from the output.

## What is NOT done

- **`--about` and `--contemporaries` are degraded.** Both resolve as name queries
  and say so in `coverage_gaps`. Namespaced topic vocabularies with explicit
  crosswalks, and temporal overlap, need the v3 topic/temporal tables. The old
  `--about` topic/subject search was lost in the rewrite; it is reinstatable
  against v2 `person_topic` and `books.book_subject` and is the most obvious next
  task.
- **`compare` and `timeline` are unimplemented.** Both are in the spec's required
  capability list. Neither has a v2 substrate worth projecting.
- **The v3 resolver adapter is unverified.** It matches the documented shape; no
  v3 database existed to run it against.
- **Relationships are derived, not asserted.** Co-contribution on a shared
  `content_ref` is adjacency we computed, labelled `derived_relation`. Typed,
  temporal, evidenced relations need `person_relation`.
- **No performance benchmarks against a production-scale database.** The spec
  asks for them; fixtures are tiny by constraint. The FTS path is now genuinely
  used, which is the change that matters at 280k rows, but the measurement is
  owed.
- **Rights state is undeclared, not clean.** No `source_snapshot` table exists in
  v2; the response says `undeclared` rather than implying permissiveness.

## For the integrator

Exclusive paths owned by this lane: `query_v3/**`, `api/**`, `mcp/**`,
`viewer/**`, `loaders/ask.py`, `tests/query_v3/**`, this file. Nothing outside
them was touched — no schema, identity, build, or source-adapter path.

`loaders/ask.py` is the only pre-existing file modified. Its CLI flags are
backward compatible; **its output shape is not** — every response is now wrapped
in the truth-contract envelope, so `result.matches` replaces top-level `matches`.
Any caller parsing the old shape needs updating. That break is the point: the old
shape had nowhere to put identity resolution, truncation, or provenance.

When Lane 3/4 merge, the v3 adapter should be exercised against a real v3
database and its provisional warning removed.
