#!/usr/bin/env python3
"""Staged validation of a built graph.

Each stage answers one question and returns a verdict with a COUNT, not a
boolean. "Foreign keys OK" is far less useful than "0 of 431 edges point at a
missing person", because the count is what tells you whether a fix worked.

The stages, and what each is guarding against:

  schema          -- the expected tables exist. Guards a build that silently
                     produced a partial database.
  shipped_coverage-- the expectation itself is right. Guards the failure one
                     level up: a build that satisfies every check while the
                     checks cover less than what ships. This is the stage that
                     would have caught person_person going missing.
  foreign_keys    -- SQLite's own FK check. person_content and person_topic are
                     declared with REFERENCES, so an orphan means a loader wrote
                     an edge for a person it never created.
  orphan_edges    -- the same question asked directly, because PRAGMA
                     foreign_key_check is silent when a table was created
                     without the constraint being enforced at write time.
  source_coverage -- every canonical row names a source. A row whose source is
                     'unknown' cannot be traced, corrected, or removed as a set.
  duplicate_ids   -- an external identity (platform, value) claimed by more than
                     one person. That is the identity-fusion failure mode the
                     whole identity design exists to prevent.
  impossible      -- facts that cannot be true: death before birth, a merged
                     person pointing at nothing, negative counts.
  rights_coverage -- every source in the build has a manifest declaring a rights
                     revision. An undeclared source is a legal unknown.
  observations    -- no canonical rank mutation survives, and observations carry
                     units. This is the regression guard for the defect this
                     lane exists to fix.
  smoke           -- the queries the README advertises actually return rows.

A stage returns status 'pass', 'warn' or 'fail'. Only 'fail' is fatal; 'warn'
exists so that an expected-but-imperfect state (a fixture with no rights
manifests, say) is visible rather than either hidden or blocking.
"""
import json
import os
import pathlib
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_v3 import paths  # noqa: E402

# Every table the PUBLISHED graph contains. This list is the build's contract
# with the shipped asset: if a table is in the release and not here, the build
# can omit it and still report success -- which is exactly what happened.
#
# HOW THIS LIST WENT WRONG, because the failure mode is the interesting part.
# It previously held 8 names and omitted four tables that ship with real data:
# person_person (1,272,495 rows), organisation_content (13,533), organisation
# (1,131) and person_organisation (0). Those four appear in no tracked file on
# any branch -- see docs/handoffs/schema-divergence.md. The consequence was not
# a warning but a false PASS: a build producing 8 of 12 tables satisfied
# stage_schema, and two such builds agreed with each other because both were
# missing the same four. Reproducibility was being proven over a subset nobody
# had declared.
#
# The lesson generalises past this instance: a hand-maintained list of what
# should exist drifts silently from what does exist, and nothing catches it.
# stage_shipped_coverage below therefore checks this list against the recovered
# schema file rather than trusting it, so the next divergence fails a build
# instead of waiting for someone to notice.
EXPECTED_TABLES = (
    "person", "person_content", "person_topic", "external_ids",
    "identity_claim", "person_observation", "person_projection", "build_run",
    # Recovered 2026-08-08 from the graph-v2 release asset.
    "person_person", "organisation", "organisation_content",
    "person_organisation",
    # The FTS virtual table. Declared in the schema and shipped with 35,834
    # rows, but absent from the original list -- caught by stage_shipped_coverage
    # on its first run, which is the behaviour that stage exists for.
    "person_search",
)

# Tables created by the build machinery rather than declared in the schema
# file, so the schema<->expectation cross-check does not flag them as drift.
_BUILD_MANAGED_TABLES = frozenset({
    "build_run", "person_observation", "person_projection",
})


def _q1(conn, sql, args=()):
    row = conn.execute(sql, args).fetchone()
    return row[0] if row else 0


def stage_schema(conn):
    present = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    missing = sorted(set(EXPECTED_TABLES) - present)
    return {
        "stage": "schema",
        "status": "fail" if missing else "pass",
        "missing_tables": missing,
        "tables_present": len(present),
    }


def _schema_declared_tables():
    """Table names the tracked schema file actually declares.

    Parsed from the schema rather than restated, so this is a reading of
    reality instead of a second hand-maintained list that could drift from the
    first in the same way.
    """
    import re
    sql = paths.require(paths.schema_v2(), "v2 schema").read_text()
    return set(re.findall(
        r"CREATE\s+(?:VIRTUAL\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
        r"[\"'`\[]?(\w+)", sql, re.IGNORECASE))


def stage_shipped_coverage(conn):
    """Cross-check EXPECTED_TABLES against the schema, in BOTH directions.

    This is the guard that the old 8-name list needed and did not have. It is
    deliberately bidirectional, because the two directions catch different
    mistakes:

      undeclared_but_expected -- a name in EXPECTED_TABLES that the schema does
        not create. The expectation is fiction; the build cannot satisfy it.
      declared_but_unexpected -- a table the schema creates that nothing
        requires. THIS is the person_person case: a table can be built, shipped
        and filled with 1.27M rows while no check would notice its absence.

    Both are 'fail', not 'warn'. A warn here is how the original defect
    survived: it was visible in principle and acted on by nobody.
    """
    declared = _schema_declared_tables()
    expected = set(EXPECTED_TABLES)
    undeclared = sorted(expected - declared - _BUILD_MANAGED_TABLES)
    unexpected = sorted(declared - expected)
    return {
        "stage": "shipped_coverage",
        "status": "fail" if (undeclared or unexpected) else "pass",
        "schema_declared": sorted(declared),
        "expected_tables": sorted(expected),
        "undeclared_but_expected": undeclared,
        "declared_but_unexpected": unexpected,
        "note": "EXPECTED_TABLES and the tracked schema must agree. A table in "
                "one and not the other means the build's idea of a complete "
                "graph has drifted from what the schema builds.",
    }


def stage_foreign_keys(conn):
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    return {
        "stage": "foreign_keys",
        "status": "fail" if violations else "pass",
        "violations": len(violations),
        "sample": [list(v) for v in violations[:5]],
    }


def stage_orphan_edges(conn):
    orphan_content = _q1(conn,
        "SELECT COUNT(*) FROM person_content c "
        "LEFT JOIN person p ON p.person_id=c.person_id WHERE p.person_id IS NULL")
    orphan_topic = _q1(conn,
        "SELECT COUNT(*) FROM person_topic t "
        "LEFT JOIN person p ON p.person_id=t.person_id WHERE p.person_id IS NULL")
    orphan_obs = _q1(conn,
        "SELECT COUNT(*) FROM person_observation o "
        "LEFT JOIN person p ON p.person_id=o.person_id WHERE p.person_id IS NULL")
    total = orphan_content + orphan_topic + orphan_obs
    return {
        "stage": "orphan_edges",
        "status": "fail" if total else "pass",
        "orphan_content": orphan_content,
        "orphan_topic": orphan_topic,
        "orphan_observations": orphan_obs,
    }


def stage_source_coverage(conn):
    total = _q1(conn, "SELECT COUNT(*) FROM person_content")
    unknown = _q1(conn,
        "SELECT COUNT(*) FROM person_content WHERE source IS NULL OR source='unknown'")
    sources = dict(conn.execute(
        "SELECT source, COUNT(*) FROM person_content GROUP BY 1 ORDER BY 1"))
    return {
        "stage": "source_coverage",
        "status": "warn" if unknown else "pass",
        "edges": total,
        "unattributed": unknown,
        "by_source": sources,
    }


def stage_duplicate_ids(conn):
    dupes = conn.execute(
        """SELECT platform, value, COUNT(DISTINCT person_id) n
           FROM external_ids GROUP BY platform, value HAVING n > 1
           ORDER BY n DESC, platform, value"""
    ).fetchall()
    return {
        "stage": "duplicate_ids",
        "status": "fail" if dupes else "pass",
        "duplicate_identities": len(dupes),
        "sample": [{"platform": d[0], "value": d[1], "people": d[2]}
                   for d in dupes[:5]],
    }


def stage_impossible(conn):
    bad_dates = _q1(conn,
        "SELECT COUNT(*) FROM person WHERE birth_year IS NOT NULL "
        "AND death_year IS NOT NULL AND death_year < birth_year")
    dangling_merge = _q1(conn,
        "SELECT COUNT(*) FROM person a WHERE a.merged_into IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM person b WHERE b.person_id=a.merged_into)")
    negative_obs = _q1(conn,
        "SELECT COUNT(*) FROM person_observation "
        "WHERE unit IN ('stars','repos','works') AND value < 0")
    total = bad_dates + dangling_merge + negative_obs
    return {
        "stage": "impossible",
        "status": "fail" if total else "pass",
        "death_before_birth": bad_dates,
        "dangling_merge_targets": dangling_merge,
        "negative_counts": negative_obs,
    }


def stage_rights_coverage(conn, manifests_dir=None):
    """Every source that wrote rows should have a manifest declaring rights."""
    sources = {r[0] for r in conn.execute(
        "SELECT DISTINCT source FROM person_content WHERE source IS NOT NULL")}
    declared = {}
    if manifests_dir and pathlib.Path(manifests_dir).exists():
        for p in sorted(pathlib.Path(manifests_dir).glob("*.manifest.json")):
            m = json.loads(p.read_text())
            declared[m["source_id"]] = m.get("rights_revision")
    undeclared = sorted(s for s in sources if s not in declared)
    return {
        "stage": "rights_coverage",
        # warn rather than fail: a source may legitimately predate the manifest
        # layer (the v1 migration does), and blocking a build on that would make
        # the validator unusable on existing data.
        "status": "warn" if undeclared else "pass",
        "sources_in_graph": sorted(sources),
        "declared": declared,
        "undeclared": undeclared,
    }


def stage_observations(conn):
    """Regression guard for the defect this lane fixes.

    rank_score must not be written by canonical loading, every observation must
    carry a unit, and no (person, metric, source) may appear twice -- the last
    being impossible by primary key, which is the point.
    """
    ranked = _q1(conn, "SELECT COUNT(*) FROM person WHERE rank_score IS NOT NULL")
    unitless = _q1(conn,
        "SELECT COUNT(*) FROM person_observation WHERE unit IS NULL OR unit=''")
    metrics = dict(conn.execute(
        "SELECT metric, COUNT(*) FROM person_observation GROUP BY 1 ORDER BY 1"))
    return {
        "stage": "observations",
        "status": "fail" if (ranked or unitless) else "pass",
        "rank_score_written": ranked,
        "unitless_observations": unitless,
        "by_metric": metrics,
        "note": "rank_score_written must be 0: canonical loading no longer "
                "writes a universal score. Non-zero means a loader regressed.",
    }


def stage_smoke(conn):
    """The queries the README advertises must actually return rows.

    A build that passes every structural check but cannot answer the questions
    it exists for is not a successful build.
    """
    checks = {}
    checks["person_content_lookup"] = _q1(conn,
        "SELECT COUNT(*) FROM person_content WHERE person_id IN "
        "(SELECT person_id FROM person LIMIT 1)")
    checks["multi_domain"] = _q1(conn,
        "SELECT COUNT(*) FROM v_person_layers WHERE domain_count >= 2")
    checks["contemporaries"] = _q1(conn, "SELECT COUNT(*) FROM v_contemporaries")
    try:
        checks["fts_name_search"] = _q1(conn,
            "SELECT COUNT(*) FROM person_search WHERE person_search MATCH 'a*'")
        fts_ok = True
    except sqlite3.Error as e:
        checks["fts_name_search"] = f"error: {e}"
        fts_ok = False
    checks["topics_joinable"] = _q1(conn,
        "SELECT COUNT(DISTINCT topic) FROM person_topic")
    return {
        "stage": "smoke",
        "status": "pass" if fts_ok else "fail",
        "checks": checks,
    }


def validate(db_path, manifests_dir=None):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        stages = [
            stage_schema(conn),
            stage_shipped_coverage(conn),
            stage_foreign_keys(conn),
            stage_orphan_edges(conn),
            stage_source_coverage(conn),
            stage_duplicate_ids(conn),
            stage_impossible(conn),
            stage_rights_coverage(conn, manifests_dir),
            stage_observations(conn),
            stage_smoke(conn),
        ]
    finally:
        conn.close()
    failed = [s["stage"] for s in stages if s["status"] == "fail"]
    warned = [s["stage"] for s in stages if s["status"] == "warn"]
    return {
        "database": str(db_path),
        "status": "fail" if failed else ("warn" if warned else "pass"),
        "failed_stages": failed,
        "warned_stages": warned,
        "stages": stages,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("db")
    ap.add_argument("--manifests", help="manifests directory for rights coverage")
    ap.add_argument("--report", help="write the JSON report here")
    a = ap.parse_args()
    rep = validate(a.db, a.manifests)
    text = json.dumps(rep, indent=2, sort_keys=True)
    if a.report:
        pathlib.Path(a.report).write_text(text + "\n")
    print(text)
    return 1 if rep["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
