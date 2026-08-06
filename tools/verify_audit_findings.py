#!/usr/bin/env python3
"""Reproduce bounded findings from the 2026-08-06 first-principles audit.

This is an audit verifier, not a replacement for the product test suite. It
checks repository structure and source semantics, then runs a minimal SQLite FTS
fixture. The output is JSON so a cold agent can compare later revisions without
relying on prose.

Usage:
    python3 tools/verify_audit_findings.py
    python3 tools/verify_audit_findings.py --strict-current

`--strict-current` exits non-zero if a finding documented against the original
implementation is no longer reproduced. That mode is useful when verifying the
audit branch itself, but should not be used as a permanent CI gate: a repaired
implementation should make several findings disappear.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative: str) -> str:
    path = ROOT / relative
    return path.read_text(encoding="utf-8")


def result(
    check_id: str,
    title: str,
    reproduced: bool,
    evidence: dict[str, Any],
    *,
    finding_id: str | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "finding_id": finding_id,
        "title": title,
        "status": "finding_reproduced" if reproduced else "finding_not_reproduced",
        "evidence": evidence,
    }


def check_schema_path() -> dict[str, Any]:
    documented = ROOT / "loaders" / "people_schema_v2.sql"
    actual = ROOT / "schema" / "people_schema_v2.sql"
    builder = read_text("loaders/build_people_graph_v2.py")
    documented_expression_present = (
        'os.path.dirname(os.path.abspath(__file__))' in builder
        and '"people_schema_v2.sql"' in builder
    )
    reproduced = documented_expression_present and not documented.exists() and actual.exists()
    return result(
        "schema_path",
        "V2 builder resolves the schema from the loaders directory",
        reproduced,
        {
            "documented_expression_present": documented_expression_present,
            "documented_path": str(documented.relative_to(ROOT)),
            "documented_path_exists": documented.exists(),
            "actual_path": str(actual.relative_to(ROOT)),
            "actual_path_exists": actual.exists(),
        },
        finding_id="PG-P0-001",
    )


def check_matcher_allowlist() -> dict[str, Any]:
    matcher = read_text("loaders/match_identities.py")
    broad_select = "SELECT person_id, platform, value FROM external_ids" in matcher
    allowlist_markers = (
        "UNIQUE_EXTERNAL_ID_PLATFORMS",
        "AUTO_ACCEPT_ID_PLATFORMS",
        "STABLE_IDENTIFIER_PLATFORMS",
        "ISSUER_UNIQUE_PLATFORMS",
    )
    allowlist_present = any(marker in matcher for marker in allowlist_markers)
    enrichment = read_text("loaders/enrich_owners.py")
    descriptive_platforms = [
        platform
        for platform in ("real_name", "website", "company", "location")
        if f'"{platform}"' in enrichment
    ]
    reproduced = broad_select and not allowlist_present and bool(descriptive_platforms)
    return result(
        "matcher_allowlist",
        "Repeated descriptive attributes can enter shared_external_id matching",
        reproduced,
        {
            "broad_external_id_select": broad_select,
            "issuer_unique_allowlist_detected": allowlist_present,
            "descriptive_platforms_written_by_enrichment": descriptive_platforms,
        },
        finding_id="PG-P0-002",
    )


def check_shared_attribute_pair_explosion() -> dict[str, Any]:
    population = 100
    pairs = math.comb(population, 2)
    reproduced = pairs == 4950
    return result(
        "shared_attribute_pair_explosion",
        "A repeated attribute creates all pairwise identity candidates",
        reproduced,
        {
            "records_sharing_one_value": population,
            "candidate_pairs": pairs,
            "formula": "n * (n - 1) / 2",
        },
        finding_id="PG-P0-002",
    )


def check_claim_consumption() -> dict[str, Any]:
    ask = read_text("loaders/ask.py")
    schema = read_text("schema/people_schema_v2.sql")
    claim_table_exists = "CREATE TABLE IF NOT EXISTS identity_claim" in schema
    query_consumes_claims = "identity_claim" in ask
    reproduced = claim_table_exists and not query_consumes_claims
    return result(
        "accepted_claim_consumption",
        "The query surface does not consume identity_claim",
        reproduced,
        {
            "identity_claim_table_in_schema": claim_table_exists,
            "identity_claim_referenced_by_ask": query_consumes_claims,
        },
        finding_id="PG-P0-003",
    )


def check_silent_name_merge() -> dict[str, Any]:
    builder = read_text("loaders/build_people_graph_v2.py")
    normalized_existing_map = "existing.setdefault" in builder
    direct_reuse = "if nkey in existing" in builder and "id_for_key[pk] = existing[nkey]" in builder
    reproduced = normalized_existing_map and direct_reuse
    return result(
        "silent_name_merge",
        "The V2 build reuses an existing person ID on normalized-name equality",
        reproduced,
        {
            "normalized_existing_map_detected": normalized_existing_map,
            "direct_existing_id_reuse_detected": direct_reuse,
        },
        finding_id="PG-P0-004",
    )


def check_rank_score_semantics() -> dict[str, Any]:
    files = {
        "loaders/build_people_graph_v2.py": read_text("loaders/build_people_graph_v2.py"),
        "loaders/load_owners_into_people_graph.py": read_text(
            "loaders/load_owners_into_people_graph.py"
        ),
        "loaders/load_owner_topics.py": read_text("loaders/load_owner_topics.py"),
        "loaders/enrich_owners.py": read_text("loaders/enrich_owners.py"),
    }
    signals = {
        "book_work_count_or_v1_score": "rank_score" in files["loaders/build_people_graph_v2.py"],
        "summed_repo_stars": "float(o[\"stars\"])" in files[
            "loaders/load_owners_into_people_graph.py"
        ],
        "additive_model_value": "COALESCE(rank_score,0) + ?" in files[
            "loaders/load_owner_topics.py"
        ],
        "followers_replace_score": "float(data.get(\"followers\") or 0)" in files[
            "loaders/enrich_owners.py"
        ],
    }
    reproduced = all(signals.values())
    return result(
        "rank_score_semantics",
        "rank_score receives incompatible quantities and an additive rerun path",
        reproduced,
        signals,
        finding_id="PG-P0-005",
    )


def _run_fts_fixture() -> dict[str, Any]:
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        writer = sqlite3.connect(path)
        writer.execute("CREATE TABLE person(person_id TEXT PRIMARY KEY, name TEXT)")
        writer.execute(
            "CREATE VIRTUAL TABLE person_search USING fts5("
            "person_id UNINDEXED, name, aliases)"
        )
        writer.execute("INSERT INTO person VALUES('p1', 'Baruch Spinoza')")
        writer.execute(
            "INSERT INTO person_search VALUES('p1', 'Baruch Spinoza', 'Spinoza')"
        )
        writer.commit()
        writer.close()

        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        con.execute(f"ATTACH DATABASE 'file:{path}?mode=ro' AS people")
        current_sql = """
            SELECT p.person_id, p.name
            FROM people.person_search s
            JOIN people.person p ON p.person_id = s.person_id
            WHERE people.person_search MATCH ?
        """
        corrected_sql = """
            SELECT p.person_id, p.name
            FROM people.person_search s
            JOIN people.person p ON p.person_id = s.person_id
            WHERE person_search MATCH ?
        """
        current_error = None
        current_rows: list[tuple[str, str]] = []
        try:
            current_rows = con.execute(current_sql, ("Spinoza",)).fetchall()
        except sqlite3.Error as exc:
            current_error = str(exc)
        corrected_rows = con.execute(corrected_sql, ("Spinoza",)).fetchall()
        con.close()
        return {
            "current_query_error": current_error,
            "current_query_rows": current_rows,
            "corrected_query_rows": corrected_rows,
        }
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def check_fts_match() -> dict[str, Any]:
    fixture = _run_fts_fixture()
    reproduced = (
        fixture["current_query_error"] == "no such column: people.person_search"
        and fixture["corrected_query_rows"] == [("p1", "Baruch Spinoza")]
    )
    return result(
        "fts_match",
        "Qualified FTS MATCH fails while the unqualified table name succeeds",
        reproduced,
        fixture,
        finding_id="PG-P1-006",
    )


def check_works_contract() -> dict[str, Any]:
    ask = read_text("loaders/ask.py")
    evidence = {
        "limit_200_detected": "LIMIT 200" in ask,
        "count_uses_returned_length": '"count": len(rows)' in ask,
        "truncated_field_detected": '"truncated"' in ask,
        "identity_claim_reference_detected": "identity_claim" in ask,
    }
    reproduced = (
        evidence["limit_200_detected"]
        and evidence["count_uses_returned_length"]
        and not evidence["truncated_field_detected"]
        and not evidence["identity_claim_reference_detected"]
    )
    return result(
        "works_query_contract",
        "works() limits and counts returned rows without truncation disclosure",
        reproduced,
        evidence,
        finding_id="PG-P1-007",
    )


def check_person_topic_derivation() -> dict[str, Any]:
    builder = read_text("loaders/build_people_graph_v2.py")
    owner_topics = read_text("loaders/load_owner_topics.py")
    evidence = {
        "lcsh_rolled_to_person_topic": (
            "INSERT OR IGNORE INTO person_topic" in builder and "'lcsh'" in builder
        ),
        "github_topics_rolled_to_person_topic": (
            "INSERT OR IGNORE INTO person_topic" in owner_topics
            and '"github_topic"' in owner_topics
        ),
        "github_languages_rolled_to_person_topic": '"github_lang"' in owner_topics,
    }
    reproduced = all(evidence.values())
    return result(
        "person_topic_derivation",
        "Work classifications are rolled directly into person_topic",
        reproduced,
        evidence,
        finding_id="PG-P1-008",
    )


def check_lifetime_overlap_assumption() -> dict[str, Any]:
    schema = read_text("schema/people_schema_v2.sql")
    readme = read_text("README.md")
    evidence = {
        "birth_plus_80_assumption": "birth_year + 80" in schema,
        "view_named_contemporaries": "CREATE VIEW v_contemporaries" in schema,
        "actual_conversation_language": "actual 17th-century conversation" in readme,
    }
    reproduced = all(evidence.values())
    return result(
        "lifetime_overlap_semantics",
        "Possible lifespan overlap is presented as contemporaneity/conversation",
        reproduced,
        evidence,
        finding_id="PG-P1-009",
    )


def check_claim_pair_uniqueness() -> dict[str, Any]:
    schema = read_text("schema/people_schema_v2.sql")
    unique_markers = (
        "UNIQUE (person_a, person_b)",
        "UNIQUE(person_a, person_b)",
    )
    unique_present = any(marker in schema for marker in unique_markers)
    comment_claim = "one claim per pair" in schema
    reproduced = comment_claim and not unique_present
    return result(
        "claim_pair_uniqueness",
        "The schema comment promises one claim per pair without a UNIQUE constraint",
        reproduced,
        {
            "one_claim_per_pair_comment": comment_claim,
            "pair_unique_constraint_detected": unique_present,
        },
        finding_id=None,
    )


def run_checks() -> list[dict[str, Any]]:
    checks: list[Callable[[], dict[str, Any]]] = [
        check_schema_path,
        check_matcher_allowlist,
        check_shared_attribute_pair_explosion,
        check_claim_consumption,
        check_silent_name_merge,
        check_rank_score_semantics,
        check_fts_match,
        check_works_contract,
        check_person_topic_derivation,
        check_lifetime_overlap_assumption,
        check_claim_pair_uniqueness,
    ]
    results: list[dict[str, Any]] = []
    for check in checks:
        try:
            results.append(check())
        except Exception as exc:  # audit output must show failures, not hide them
            results.append(
                {
                    "check_id": check.__name__,
                    "finding_id": None,
                    "title": "Audit check raised an exception",
                    "status": "error",
                    "evidence": {
                        "exception_type": type(exc).__name__,
                        "message": str(exc),
                    },
                }
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-current",
        action="store_true",
        help="Fail when a documented current finding is not reproduced.",
    )
    args = parser.parse_args()

    checks = run_checks()
    summary = {
        "finding_reproduced": sum(c["status"] == "finding_reproduced" for c in checks),
        "finding_not_reproduced": sum(
            c["status"] == "finding_not_reproduced" for c in checks
        ),
        "errors": sum(c["status"] == "error" for c in checks),
    }
    report = {
        "audit_id": "siso-people-graph-first-principles-2026-08-06",
        "repository_root": str(ROOT),
        "summary": summary,
        "checks": checks,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if summary["errors"]:
        return 2
    if args.strict_current and summary["finding_not_reproduced"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
