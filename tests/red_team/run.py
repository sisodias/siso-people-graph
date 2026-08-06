#!/usr/bin/env python3
"""Offline red-team fixtures for the current People Graph v2 implementation.

Run from a clean checkout with no databases or network:

    python3 tests/red_team/run.py

PASS and documented XFAIL are green. FAIL, XPASS, or ERROR are non-zero.
Use --json for machine-readable evidence and --list for the case inventory.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
import traceback

from support import BASELINE_COMMIT, BOOK_BASELINE_COMMIT, Case, Context, Result
from cases_build import (
    case_aliases_absent_from_fts, case_book_builder_stale_source,
    case_schema_lookup, case_silent_name_merge, case_unicode_collision,
    case_v2_preserves_book_roles,
)
from cases_identity import (
    case_accepted_claims_inert, case_book_export_contract,
    case_common_name_review_only, case_github_rename_stable_id,
    case_kind_and_pseudonym_conflicts, case_matcher_rerun,
    case_missing_domain_diagnostics, case_nonunique_external_ids,
    case_unknown_death_contemporaries,
)
from cases_loaders import (
    case_enrichment_mutates_canonical, case_enrichment_partial_field_block,
    case_non_gh_canonical_gap, case_owner_loader_exact_rerun,
    case_owner_loader_stale_source, case_rank_score_unit_mix,
    case_topic_loader_rerun,
)

def cases() -> list[Case]:
    return [
        Case(
            "PGRT-T001",
            "v2 builder resolves its schema from a clean checkout",
            "EXPECTED_FAILURE",
            "The tracked schema path must be resolvable without a database asset or local topology.",
            ("PGRT-001",),
            case_schema_lookup,
        ),
        Case(
            "PGRT-T002",
            "v2 builder does not silently merge normalized names",
            "EXPECTED_FAILURE",
            "A source-native person remains separate until an explicit identity decision is accepted.",
            ("PGRT-002",),
            case_silent_name_merge,
        ),
        Case(
            "PGRT-T003",
            "non-unique profile attributes cannot auto-resolve identity",
            "EXPECTED_FAILURE",
            "Company, location, and real-name attributes are never eligible stable identifiers.",
            ("PGRT-003",),
            case_nonunique_external_ids,
        ),
        Case(
            "PGRT-T004",
            "accepted identity claims affect canonical reads",
            "EXPECTED_FAILURE",
            "An accepted identity decision must create a queryable canonical cluster or redirect.",
            ("PGRT-004",),
            case_accepted_claims_inert,
        ),
        Case(
            "PGRT-T005",
            "identity matcher is idempotent across two runs",
            "EXPECTED_FAILURE",
            "Re-running a source-equivalent matcher must not duplicate claims.",
            ("PGRT-005",),
            case_matcher_rerun,
        ),
        Case(
            "PGRT-T006",
            "topic loader is idempotent across two runs",
            "EXPECTED_FAILURE",
            "Re-running a source-equivalent topic load must not add rank repeatedly.",
            ("PGRT-006", "PGRT-013"),
            case_topic_loader_rerun,
        ),
        Case(
            "PGRT-T007",
            "owner loader exact rerun remains duplicate-free",
            "PASS",
            "An identical owner-source rerun must not duplicate people, identifiers, or edges.",
            (),
            case_owner_loader_exact_rerun,
        ),
        Case(
            "PGRT-T008",
            "owner loader removes or tombstones stale source rows",
            "EXPECTED_FAILURE",
            "Source replacement must not retain stale owners or repository edges.",
            ("PGRT-006", "PGRT-011"),
            case_owner_loader_stale_source,
        ),
        Case(
            "PGRT-T009",
            "book-person builder removes stale source rows",
            "EXPECTED_FAILURE",
            "Rebuilding against a replaced source must not retain deleted people or works.",
            ("PGRT-006",),
            case_book_builder_stale_source,
        ),
        Case(
            "PGRT-T010",
            "GitHub enrichment preserves unrelated canonical fields",
            "EXPECTED_FAILURE",
            "Enrichment observations must not overwrite canonical name, build time, or unrelated rank.",
            ("PGRT-007", "PGRT-013"),
            case_enrichment_mutates_canonical,
        ),
        Case(
            "PGRT-T011",
            "GitHub enrichment fills each missing field independently",
            "EXPECTED_FAILURE",
            "One existing enrichment field must not block collection of other missing observations.",
            ("PGRT-007",),
            case_enrichment_partial_field_block,
        ),
        Case(
            "PGRT-T012",
            "topics and enrichment follow non-gh canonical IDs",
            "EXPECTED_FAILURE",
            "A canonical entity linked by github_login must work regardless of ID prefix or origin.",
            ("PGRT-008",),
            case_non_gh_canonical_gap,
        ),
        Case(
            "PGRT-T013",
            "Unicode names survive identity-key construction",
            "EXPECTED_FAILURE",
            "Comparison keys must preserve non-Latin distinctions and never become canonical IDs.",
            ("PGRT-009",),
            case_unicode_collision,
        ),
        Case(
            "PGRT-T014",
            "raw aliases reach FTS search",
            "EXPECTED_FAILURE",
            "Every retained raw name variant must be searchable without replacing the canonical label.",
            ("PGRT-010",),
            case_aliases_absent_from_fts,
        ),
        Case(
            "PGRT-T015",
            "GitHub rename resolves through stable numeric account ID",
            "EXPECTED_FAILURE",
            "A login change must not split one numeric GitHub account into two people.",
            ("PGRT-011",),
            case_github_rename_stable_id,
        ),
        Case(
            "PGRT-T016",
            "ambiguous common names remain review-only",
            "PASS",
            "Exact-name evidence alone stays proposed at low confidence.",
            (),
            case_common_name_review_only,
        ),
        Case(
            "PGRT-T017",
            "kind and pseudonym conflicts gate name candidates",
            "EXPECTED_FAILURE",
            "Human, organisation, and pseudonym kind conflicts must be explicit negative evidence.",
            ("PGRT-012",),
            case_kind_and_pseudonym_conflicts,
        ),
        Case(
            "PGRT-T018",
            "rank_score has one stable semantic unit",
            "EXPECTED_FAILURE",
            "Stars, ratings, followers, and work counts remain named observations or projections.",
            ("PGRT-013",),
            case_rank_score_unit_mix,
        ),
        Case(
            "PGRT-T019",
            "unknown death years do not create certain contemporaries",
            "EXPECTED_FAILURE",
            "Missing death years must remain uncertain rather than silently becoming birth+80.",
            ("PGRT-014",),
            case_unknown_death_contemporaries,
        ),
        Case(
            "PGRT-T020",
            "missing domains are explicit in query output",
            "EXPECTED_FAILURE",
            "An empty result caused by a missing domain must not look like an evidence-backed absence.",
            ("PGRT-015",),
            case_missing_domain_diagnostics,
        ),
        Case(
            "PGRT-T021",
            "Book Library export preserves identity boundaries and roles",
            "EXPECTED_FAILURE",
            "Book contributors remain source-native observations with all roles and no name-only merge.",
            ("PGRT-016",),
            case_book_export_contract,
        ),
        Case(
            "PGRT-T022",
            "v2 builder preserves supplied Book contributor roles",
            "PASS",
            "The v2 builder must retain distinct author and translator edges when supplied upstream.",
            (),
            case_v2_preserves_book_roles,
        ),
    ]

def execute(case: Case, ctx: Context) -> Result:
    start = time.perf_counter()
    evidence: dict[str, Any]
    try:
        holds, evidence = case.run(ctx)
        if case.expectation == "PASS":
            status = "PASS" if holds else "FAIL"
        elif case.expectation == "EXPECTED_FAILURE":
            status = "XPASS" if holds else "XFAIL"
        else:
            raise ValueError(f"unknown expectation: {case.expectation}")
    except Exception as exc:  # fixture failures must be visible, not swallowed
        status = "ERROR"
        evidence = {
            "exception": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc().splitlines()[-12:],
        }
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return Result(
        case_id=case.case_id,
        title=case.title,
        status=status,
        expectation=case.expectation,
        invariant=case.invariant,
        finding_ids=list(case.finding_ids),
        evidence=evidence,
        elapsed_ms=elapsed_ms,
    )

def verify_layout(ctx: Context) -> None:
    required = [
        "loaders/build_people_graph_v2.py",
        "loaders/build_people_graph_books.py",
        "loaders/match_identities.py",
        "loaders/load_owner_topics.py",
        "loaders/load_owners_into_people_graph.py",
        "loaders/enrich_owners.py",
        "loaders/ask.py",
        "schema/people_schema_v2.sql",
    ]
    for relative in required:
        ctx.production(relative)
    for fixture in ("adversarial_people.json", "book_library_export_contract.json"):
        ctx.fixture(fixture)

def main(argv: list[str] | None = None) -> int:
    default_repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=default_repo, help="People Graph checkout root")
    parser.add_argument("--json", action="store_true", help="emit one JSON document")
    parser.add_argument("--list", action="store_true", help="list cases without running")
    parser.add_argument("--case", action="append", default=[], help="run one case ID; repeatable")
    args = parser.parse_args(argv)

    ctx = Context(args.repo)
    verify_layout(ctx)
    selected = cases()
    if args.case:
        wanted = set(args.case)
        selected = [case for case in selected if case.case_id in wanted]
        missing = wanted - {case.case_id for case in selected}
        if missing:
            parser.error(f"unknown case IDs: {', '.join(sorted(missing))}")

    if args.list:
        for case in selected:
            print(f"{case.case_id}\t{case.expectation}\t{case.title}")
        return 0

    results = [execute(case, ctx) for case in selected]
    counts: dict[str, int] = {status: 0 for status in ("PASS", "XFAIL", "FAIL", "XPASS", "ERROR")}
    for result in results:
        counts[result.status] += 1

    payload = {
        "suite": "people-graph-v2-red-team",
        "suite_version": "1.0",
        "baseline": {
            "repository": "sisodias/siso-people-graph",
            "commit": BASELINE_COMMIT,
            "book_library_commit": BOOK_BASELINE_COMMIT,
        },
        "repo": str(ctx.repo),
        "offline": True,
        "counts": counts,
        "results": [asdict(result) for result in results],
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        for result in results:
            finding = ",".join(result.finding_ids) if result.finding_ids else "invariant"
            print(
                f"[{result.status:<6}] [{result.expectation:<16}] "
                f"[{finding}] {result.case_id} {result.title} ({result.elapsed_ms} ms)"
            )
            print(f"         INVARIANT: {result.invariant}")
            print(
                "         EVIDENCE: "
                + json.dumps(result.evidence, ensure_ascii=False, sort_keys=True, default=str)
            )
        print(
            "SUMMARY "
            + " ".join(f"{key}={counts[key]}" for key in ("PASS", "XFAIL", "FAIL", "XPASS", "ERROR"))
        )

    unexpected = counts["FAIL"] + counts["XPASS"] + counts["ERROR"]
    return 1 if unexpected else 0

if __name__ == "__main__":
    raise SystemExit(main())
