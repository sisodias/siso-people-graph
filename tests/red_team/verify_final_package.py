#!/usr/bin/env python3
"""Verify the final Prompt 2 red-team package and optionally replay all cases.

This standard-library-only checker validates the final branch layout. It treats
the committed gzip prompt archive as authoritative while preserving the earlier
plain-path provenance projections as historical artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import run as runner
from support import Context

EXPECTED_COUNTS = {"PASS": 3, "XFAIL": 19, "FAIL": 0, "XPASS": 0, "ERROR": 0}
EXPECTED_SEVERITIES = {"P0": 8, "P1": 8}
EXPECTED_REQUIREMENTS = {f"PGRT-R{i:02d}" for i in range(1, 15)}
EXPECTED_FINDINGS = {f"PGRT-{i:03d}" for i in range(1, 17)}
EXPECTED_CONTROLS = {"PGRT-T007", "PGRT-T016", "PGRT-T022"}
EXPECTED_BLOCKERS = {
    "PGRT-001", "PGRT-002", "PGRT-003", "PGRT-004",
    "PGRT-006", "PGRT-009", "PGRT-011", "PGRT-016",
}
SOURCE_BLOBS = {
    "README.md": "3ae7738eed163cabb72ed5ea4d57d38453ec40f1",
    "schema/people_schema_v2.sql": "07b70a2eaf8db48d741010d2d5f31810a0c9d0d1",
    "loaders/ask.py": "37e19c92d242bc979eb2ab55b4f6f6a02872083d",
    "loaders/build_people_graph_books.py": "08b667b448c3acbc4bc0357f378270d46892e071",
    "loaders/build_people_graph_v2.py": "7983db530d242b386fcd3c8277718010b7a43034",
    "loaders/enrich_owners.py": "9ea6956f30a06115b8c5946be02ef2dfffb7208b",
    "loaders/load_owner_topics.py": "f33d0cfc459330fd97fb69865c7cb7da33468e57",
    "loaders/load_owners_into_people_graph.py": "726742a7e7dcfe8c0f76107daef0c147f9e42e34",
    "loaders/match_identities.py": "541c68e7083e54327141aaed37f004579b024c4c",
}
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: {type(exc).__name__}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return {}
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def normalize(value: Any, repo: Path) -> Any:
    if isinstance(value, dict):
        return {k: normalize(v, repo) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v, repo) for v in value]
    if isinstance(value, str):
        value = value.replace(str(repo.resolve()), "<clean-checkout>")
        return "<run-timestamp>" if ISO_UTC.fullmatch(value) else value
    return value


def projection(row: dict[str, Any], repo: Path) -> dict[str, Any]:
    return {
        "case_id": row.get("case_id"),
        "title": row.get("title"),
        "status": row.get("status"),
        "expectation": row.get("expectation"),
        "invariant": row.get("invariant"),
        "finding_ids": row.get("finding_ids", []),
        "evidence": normalize(row.get("evidence", {}), repo),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--run", action="store_true", help="rerun and compare all case evidence")
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    errors: list[str] = []
    checks: list[str] = []

    rel = {
        "final": "docs/audits/people-graph-v2-final-provenance.json",
        "archive": "docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt.gz",
        "locator": "docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt",
        "prompt2": "docs/audits/sources/prompt-02-people-graph-red-team.txt",
        "findings": "docs/audits/people-graph-v2-findings.json",
        "trace": "docs/audits/people-graph-v2-traceability.json",
        "ledger": "docs/audits/source-evidence-ledger.json",
        "contract": "tests/red_team/fixtures/prompt_2_contract.json",
        "receipt": "docs/audits/receipts/people-graph-v2-red-team-run-2026-08-06.json",
        "worklog": "docs/audits/people-graph-v2-forensic-worklog-2026-08-06.md",
        "audit": "docs/audits/people-graph-v2-red-team-2026-08-06.md",
        "book": "tests/red_team/fixtures/book_library_export_contract.json",
        "handoff": "docs/handoffs/red-team.md",
    }
    paths = {k: repo / v for k, v in rel.items()}
    for key, path in paths.items():
        require(path.is_file(), f"missing {key}: {rel[key]}", errors)
    if errors:
        payload = {"ok": False, "checks": checks, "errors": errors}
        print(json.dumps(payload, indent=2) if args.json else "\n".join(f"ERROR {e}" for e in errors))
        return 1

    final = load_json(paths["final"], errors)
    findings = load_json(paths["findings"], errors)
    trace = load_json(paths["trace"], errors)
    ledger = load_json(paths["ledger"], errors)
    contract = load_json(paths["contract"], errors)
    receipt = load_json(paths["receipt"], errors)
    book = load_json(paths["book"], errors)

    source = final.get("assignment_source", {})
    archive_bytes = paths["archive"].read_bytes()
    try:
        decoded = gzip.decompress(archive_bytes)
    except Exception as exc:
        errors.append(f"archive decompression failed: {type(exc).__name__}: {exc}")
        decoded = b""
    require(len(archive_bytes) == source.get("archive_bytes"), "archive byte count differs", errors)
    require(sha256_bytes(archive_bytes) == source.get("archive_sha256"), "archive SHA-256 differs", errors)
    require(git_blob_sha(paths["archive"]) == source.get("archive_git_blob_sha"), "archive Git blob differs", errors)
    require(len(decoded) == source.get("decoded_bytes"), "decoded prompt byte count differs", errors)
    require(sha256_bytes(decoded) == source.get("decoded_sha256"), "decoded prompt SHA-256 differs", errors)
    require(paths["prompt2"].stat().st_size == source.get("prompt_2_bytes"), "Prompt 2 byte count differs", errors)
    require(sha256(paths["prompt2"]) == source.get("prompt_2_sha256"), "Prompt 2 SHA-256 differs", errors)
    locator = paths["locator"].read_text(encoding="utf-8")
    require(rel["archive"] in locator, "locator does not name archive", errors)
    require(source.get("archive_sha256") in locator and source.get("decoded_sha256") in locator,
            "locator omits source digests", errors)
    checks.append("lossless assignment archive and exact Prompt 2 verified")

    cases = runner.cases()
    case_ids = {case.case_id for case in cases}
    require(len(cases) == 22 and len(case_ids) == 22, "runner does not expose 22 unique cases", errors)
    checks.append("runner exposes 22 unique executable cases")

    finding_rows = findings.get("findings", [])
    finding_ids = {row.get("id") for row in finding_rows}
    require(finding_ids == EXPECTED_FINDINGS, "finding ID set differs", errors)
    require(dict(Counter(row.get("severity") for row in finding_rows)) == EXPECTED_SEVERITIES,
            "finding severity counts differ", errors)
    require(set(findings.get("bulk_ingestion_blockers", [])) == EXPECTED_BLOCKERS,
            "bulk blocker set differs", errors)
    checks.append("16 findings, P0/P1 counts, and blocker set verified")

    requirements = trace.get("requirements", [])
    requirement_ids = {row.get("requirement_id") for row in requirements}
    mapped_cases = {cid for row in requirements for cid in row.get("test_cases", [])}
    mapped_findings = {fid for row in requirements for fid in row.get("finding_ids", [])}
    require(requirement_ids == EXPECTED_REQUIREMENTS, "traceability does not contain 14 requirements", errors)
    require(mapped_cases == case_ids, "requirements do not exactly cover runner cases", errors)
    require(mapped_findings == EXPECTED_FINDINGS, "requirements do not cover all findings", errors)
    checks.append("14 requirements map exactly to 22 cases and 16 findings")

    contract_requirements = {row.get("requirement_id") for row in contract.get("requirements", [])}
    require(contract_requirements == EXPECTED_REQUIREMENTS, "Prompt contract requirements differ", errors)
    require(contract.get("audited_result", {}).get("counts") == EXPECTED_COUNTS,
            "Prompt contract status counts differ", errors)
    checks.append("machine-readable Prompt 2 contract verified")

    ledger_ids = {row.get("finding_id") for row in ledger.get("entries", [])}
    require(ledger_ids == EXPECTED_FINDINGS, "evidence ledger finding IDs differ", errors)
    for row in ledger.get("entries", []):
        require(bool(row.get("source_observations")), f"{row.get('finding_id')} lacks source observations", errors)
        require(bool(row.get("test_cases")), f"{row.get('finding_id')} lacks test cases", errors)
        require(bool(row.get("decision")), f"{row.get('finding_id')} lacks decision record", errors)
    checks.append("source-to-decision ledger covers all findings")

    receipt_rows = receipt.get("results", [])
    receipt_by_id = {row.get("case_id"): row for row in receipt_rows}
    require(set(receipt_by_id) == case_ids, "receipt case IDs differ", errors)
    require(receipt.get("counts") == EXPECTED_COUNTS, "receipt counts differ", errors)
    controls = {cid for cid, row in receipt_by_id.items() if row.get("status") == "PASS"}
    require(controls == EXPECTED_CONTROLS, "positive control set differs", errors)
    checks.append("normalized receipt and three positive controls verified")

    matched = 0
    for relative, expected in SOURCE_BLOBS.items():
        path = repo / relative
        require(path.is_file(), f"missing baseline source: {relative}", errors)
        if path.is_file() and git_blob_sha(path) == expected:
            matched += 1
        elif path.is_file():
            errors.append(f"baseline source blob differs: {relative}")
    require(matched == 9, f"source blob matches={matched}, expected 9", errors)
    checks.append("all 9 local production sources match baseline Git blobs")

    book_source = book.get("source", {})
    require(book_source.get("commit") == "be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b", "Book commit differs", errors)
    require(book_source.get("blob_sha") == "de4e9fd91c076fd514887c82bd334dde43271d7b", "Book blob differs", errors)
    checks.append("cross-repository Book export seam is pinned")

    worklog = paths["worklog"].read_text(encoding="utf-8")
    audit = paths["audit"].read_text(encoding="utf-8")
    for fid in EXPECTED_FINDINGS:
        require(fid in worklog, f"worklog omits {fid}", errors)
        require(fid in audit, f"audit omits {fid}", errors)
    handoff = paths["handoff"].read_text(encoding="utf-8")
    for heading in ("## Scope", "## Changed paths", "## Commands", "## Tests and measurements",
                    "## Assumptions", "## Compatibility seams", "## Known risks",
                    "## Data and rights notes", "## Suggested merge considerations"):
        require(heading in handoff, f"handoff omits {heading}", errors)
    checks.append("narrative, worklog, and handoff coverage verified")

    if args.run:
        ctx = Context(repo)
        runner.verify_layout(ctx)
        live = [runner.execute(case, ctx) for case in cases]
        counts = {status: 0 for status in EXPECTED_COUNTS}
        for result in live:
            counts[result.status] += 1
            require(projection(result.__dict__, repo) == projection(receipt_by_id[result.case_id], repo),
                    f"{result.case_id} live evidence differs from receipt", errors)
        require(counts == EXPECTED_COUNTS, f"live counts differ: {counts}", errors)
        checks.append("live 22-case non-volatile evidence replay matches receipt")

    payload = {
        "ok": not errors,
        "checks": checks,
        "counts": {
            "prompt_requirements": len(requirement_ids),
            "cases": len(case_ids),
            "findings": len(finding_ids),
            "source_blob_matches": matched,
            "live_replay": bool(args.run),
        },
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for check in checks:
            print(f"PASS {check}")
        for error in errors:
            print(f"ERROR {error}")
        print(f"SUMMARY ok={str(not errors).lower()} checks={len(checks)} errors={len(errors)}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
