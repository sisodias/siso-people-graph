# Schema divergence: four shipped tables that existed in no tracked source

**Written 2026-08-08. Evidence is the published `graph-v2` release asset,
sha256 `9938237a33277fe3a29a278d68c361a1f300d9060740cc2e917920157d9b919b`.**

This is not a build bug report. The build bug is downstream of the finding, and
the finding is the more important half: **the published graph contained four
tables, holding 1,287,159 rows, that appeared in no tracked file on any branch
of this repository.** Nobody noticed until a build tried to reproduce the graph
and quietly succeeded at producing a smaller one.

A table that exists in production and in no schema is exactly how a graph
becomes unrebuildable. Recording how it happened is the point of this document.

## 1. The four tables

Measured directly against the release asset:

```
sqlite3 people_graph_v2.sqlite \
  "SELECT 'person_person', COUNT(*) FROM person_person
   UNION ALL SELECT 'organisation_content', COUNT(*) FROM organisation_content
   UNION ALL SELECT 'organisation', COUNT(*) FROM organisation
   UNION ALL SELECT 'person_organisation', COUNT(*) FROM person_organisation;"
```

| Table | Rows in the shipped asset | In tracked schema before this PR |
|---|---:|---|
| `person_person` | 1,272,495 | no |
| `organisation_content` | 13,533 | no |
| `organisation` | 1,131 | no |
| `person_organisation` | 0 | no |
| **Total** | **1,287,159** | |

For scale: those four tables between them hold more rows than the entire
`person` table (339,217).

## 2. What the tracked schema actually declared

`schema/people_schema_v2.sql` before this PR created exactly five tables, one
virtual table and two views:

```
person, external_ids, person_content, identity_claim, person_topic
person_search (fts5)
v_person_layers, v_contemporaries   (views)
```

The four tables above are absent. Not commented out, not conditional — absent.

## 3. How they diverged: an entire loader was never committed

The obvious hypothesis is schema drift — someone `ALTER`ed production and
forgot the migration. That is not what happened, and the truth is worse.

Every loader that has ever existed in this repository, across all branches:

```
git log --all --diff-filter=A --name-only --format="" | sort -u | grep loaders/
  loaders/ask.py
  loaders/build_people_graph_books.py
  loaders/build_people_graph_v2.py
  loaders/enrich_owners.py
  loaders/load_owner_topics.py
  loaders/load_owners_into_people_graph.py
  loaders/match_identities.py
```

Seven loaders. **None of them writes crates.io data, and none of them
references `person_person`, `organisation`, `organisation_content` or
`person_organisation`.** Searching all of git history for those four names
returns only prose documents describing the anomaly — never a `CREATE TABLE`,
never an `INSERT`, never a migration.

Yet the shipped graph contains:

* 58,509 people with `origin='crates_io'`
* 1,272,495 `person_person` rows, every one `source='crates_io_dependencies'`
* 13,533 `organisation_content` rows, every one `source='crates_io_teams'`

**The conclusion is that a crates.io loader was written, run against the
production database, and never committed.** The divergence is not a missing
migration; it is a missing *pipeline stage*. The graph has a source whose code
does not exist in the repository that publishes it.

The recovered DDL supports this. It is not ad-hoc — it carries `CHECK`
constraints, `ON DELETE CASCADE` foreign keys and composite primary keys
consistent in style with the tracked schema. Someone designed these tables
properly and applied them to the live database. The design was never the
problem; the tracking was.

## 4. A second, previously unrecorded divergence: the matcher ran and was wiped

`identity_claim` reads 0 rows, and the GQ-010 baseline concluded the matcher had
never run ("zero proposed, zero accepted, zero rejected... it holds because the
matcher never ran"). The AUTOINCREMENT high-water mark says otherwise:

```
sqlite3 people_graph_v2.sqlite "SELECT * FROM sqlite_sequence;"
  → identity_claim|58509

sqlite3 people_graph_v2.sqlite "SELECT COUNT(*) FROM person WHERE origin='crates_io';"
  → 58509
```

SQLite retains the high-water mark after `DELETE`, so a sequence of 58,509 on an
empty table means **58,509 rows were inserted and subsequently deleted**. That
number is exactly the crates_io person count, and matches no other table in the
database (crates external_ids = 68,324; distinct `person_a` = 59,240), so the
correspondence is specific rather than coincidental.

The most likely reading: the same uncommitted crates load proposed one identity
claim per crates person, and those claims were later deleted wholesale.

**Confidence: ~85%.** The high-water mark is a trace, not a log — it proves rows
were inserted and removed, and the count correspondence is one-to-one, but no
record survives of *who* deleted them or why. Raising this above 85% needs the
production write-ahead history or the uncommitted loader itself, neither of
which is available here.

This matters because the baseline's framing ("nothing has ever been merged") is
reassuring in a way the evidence does not support. The safety was not that the
matcher never ran. It is that its output was discarded.

## 5. What the build was actually validating

`build_v3/validate.py` carried a hand-maintained `EXPECTED_TABLES` of eight
names. Four of the shipped tables were not in it, so:

* a build producing 8 of 12 tables satisfied `stage_schema` and reported `pass`;
* `verify_reproducible.py` compared two such builds, found equal digests and
  equal counts, and reported success;
* **both builds were equally incomplete, and matching each other proved nothing
  about matching the shipped graph.**

The digest itself was not at fault. `digest.covered_tables()` enumerates tables
dynamically and would have covered all four had they existed. The failure was
entirely in the static expectation: nothing ever asserted that the set of tables
the build produces equals the set of tables that ship.

## 6. What changed in this PR

1. **The four tables are now in `schema/people_schema_v2.sql`**, DDL recovered
   verbatim from the asset, with the `person_person` semantics documented
   inline so the next reader cannot inherit the old overclaim.
2. **`loaders/load_crates_into_people_graph.py` reconstructs the missing
   pipeline stage**, so the shipped shape is reproducible from tracked source.
3. **`EXPECTED_TABLES` covers all 12 shipped tables**, including `person_search`.
4. **`stage_shipped_coverage` cross-checks that list against the schema file in
   both directions**, so the list can no longer drift silently. It parses the
   schema rather than restating it — a generated check, not a second
   hand-maintained list.
5. **Drop-detection tests actually drop tables** and assert the guard notices
   (see §7).

## 7. Proof the new guard can fail

A test that cannot fail guards nothing. Each guard was verified by breaking it
and observing the failure, not by reading the code:

| Mutation | Result |
|---|---|
| Remove `person_person` from `EXPECTED_TABLES` | **4 test failures** |
| Skip the crates load (table present, 0 rows) | **1 test failure** |
| Remove `person_person` from the schema file | **22 test errors** |

All three were reverted and the suite returns 44/44 green.

The second row is the important one: it is the subtle case where the table
exists and validates structurally but carries no data — the shape most likely to
slip through — and it is caught by
`test_person_person_semantics_are_recorded_not_inherited`.

## 8. Honest limits

**`person_organisation` builds with 0 rows.** It shipped with 0 rows; nothing
has ever populated it. The fixture reproduces that faithfully rather than
inventing membership data. So "who works where" remains structurally
unanswerable, and coverage of this table is *structural only*. That is a real
gap and it is stated rather than papered over.

**The fixture is small.** Three of four tables now carry real rows
(`organisation` 1, `organisation_content` 2, `person_person` 1) against
production's 1,131 / 13,533 / 1,272,495. The fixture proves the pipeline runs,
the semantics are correct and the guards fire; it does not exercise scale.

**The reconstructed loader is inferred, not recovered.** It reproduces the
shipped *shape* and *semantics* — verified against the asset's own DDL and
`GROUP BY` measurements — but the original code is gone. Row-for-row identity
with production is not claimed and has not been tested at production scale.

**Confidence on §4 is ~85%**, as stated there. Everything in §1–§3 is directly
measured and is not a matter of confidence.

## 9. The generalisable lesson

The defect was not that someone forgot a table. It was that **the check for
completeness was a hand-written list, and nothing compared it to reality.** Two
builds agreeing with each other is a weaker claim than it appears: it proves
determinism, not completeness. Reproducibility means reproducing *the shipped
artifact*, and that requires an assertion tied to what shipped — not to what
someone remembered to type.
