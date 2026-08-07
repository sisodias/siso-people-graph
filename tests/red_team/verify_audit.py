#!/usr/bin/env python3
"""Verify the Prompt 2 red-team evidence package is complete and consistent.

This checker is standard-library-only and offline. ``run.py`` executes the
pinned production paths; this script verifies that the surrounding prompt
archive, source pins, prompt contract, traceability map, findings registry,
evidence ledger, normalized receipts, narrative/worklog, and handoff do not
drift apart.

Usage:
    python3 tests/red_team/verify_audit.py
    python3 tests/red_team/verify_audit.py --json
    python3 tests/red_team/verify_audit.py --run
"""
from __future__ import annotations

import argparse
from collections import Counter
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
EXPECTED_CONTROLS = {"PGRT-T007", "PGRT-T016", "PGRT-T022"}
EXPECTED_HANDOFF_SECTIONS = {
    "Scope",
    "Changed paths",
    "Commands",
    "Tests and measurements",
    "Evidence and reasoning package",
    "Assumptions",
    "Compatibility seams",
    "Known risks",
    "Data and rights notes",
    "Suggested merge considerations",
}
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FORBIDDEN_LOCAL_PREFIXES = ("/mnt/data/", "/home/", "/Users/", "/Volumes/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha(path: Path) -> str:
    """Compute Git's blob object ID without requiring the git executable."""
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: cannot parse JSON: {type(exc).__name__}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: expected a JSON object")
        return {}
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def headings(markdown: str) -> set[str]:
    return {
        line[3:].strip()
        for line in markdown.splitlines()
        if line.startswith("## ")
    }


def normalize_runtime(value: Any, repo: Path) -> Any:
    """Remove only volatile checkout/timestamp diagnostics before replay compare."""
    if isinstance(value, dict):
        return {key: normalize_runtime(item, repo) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_runtime(item, repo) for item in value]
    if isinstance(value, str):
        normalized = value.replace(str(repo.resolve()), "<clean-checkout>")
        if ISO_UTC.fullmatch(normalized):
            return "<run-timestamp>"
        return normalized
    return value


def result_projection(row: dict[str, Any], repo: Path) -> dict[str, Any]:
    """Comparable case result; elapsed time is diagnostic, never evidence."""
    return {
        "case_id": row.get("case_id"),
        "title": row.get("title"),
        "status": row.get("status"),
        "expectation": row.get("expectation"),
        "invariant": row.get("invariant"),
        "finding_ids": row.get("finding_ids", []),
        "evidence": normalize_runtime(row.get("evidence", {}), repo),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit a JSON result")
    parser.add_argument(
        "--run",
        action="store_true",
        help="rerun all 22 fixtures and compare their non-volatile evidence to the receipt",
    )
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parents[2]
    errors: list[str] = []
    checks: list[str] = []

    paths = {
        "findings": repo / "docs/audits/people-graph-v2-findings.json",
        "traceability": repo / "docs/audits/people-graph-v2-traceability.json",
        "manifest": repo / "docs/audits/people-graph-v2-source-manifest.json",
        "ledger": repo / "docs/audits/source-evidence-ledger.json",
        "contract": repo / "tests/red_team/fixtures/prompt_2_contract.json",
        "receipt_json": repo / "docs/audits/receipts/people-graph-v2-red-team-run-2026-08-06.json",
        "receipt_text": repo / "docs/audits/receipts/people-graph-v2-red-team-run-2026-08-06.txt",
        "audit": repo / "docs/audits/people-graph-v2-red-team-2026-08-06.md",
        "worklog": repo / "docs/audits/people-graph-v2-forensic-worklog-2026-08-06.md",
        "audit_index": repo / "docs/audits/README.md",
        "source_index": repo / "docs/audits/sources/README.md",
        "prompt_bundle": repo / "docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt",
        "prompt_2": repo / "docs/audits/sources/prompt-02-people-graph-red-team.txt",
        "book_fixture": repo / "tests/red_team/fixtures/book_library_export_contract.json",
        "handoff": repo / "docs/handoffs/red-team.md",
    }
    for name, path in paths.items():
        require(path.is_file(), f"missing {name}: {path.relative_to(repo)}", errors)
    if errors:
        payload = {"ok": False, "checks": checks, "errors": errors}
        print(json.dumps(payload, indent=2) if args.json else "\n".join(f"ERROR {e}" for e in errors))
        return 1

    findings = load_json(paths["findings"], errors)
    traceability = load_json(paths["traceability"], errors)
    manifest = load_json(paths["manifest"], errors)
    ledger = load_json(paths["ledger"], errors)
    contract = load_json(paths["contract"], errors)
    receipt = load_json(paths["receipt_json"], errors)
    book_fixture = load_json(paths["book_fixture"], errors)

    case_list = runner.cases()
    case_ids = [case.case_id for case in case_list]
    case_id_set = set(case_ids)
    require(len(case_ids) == 22, f"runner case count is {len(case_ids)}, expected 22", errors)
    require(len(case_id_set) == len(case_ids), "runner contains duplicate case IDs", errors)
    checks.append(f"runner cases={len(case_ids)} unique={len(case_id_set)}")

    requirements = traceability.get("requirements", [])
    requirement_ids = {row.get("requirement_id") for row in requirements}
    require(requirement_ids == EXPECTED_REQUIREMENTS,
            f"requirements differ: got {sorted(requirement_ids)}, expected {sorted(EXPECTED_REQUIREMENTS)}",
            errors)
    mapped_cases = {case for row in requirements for case in row.get("test_cases", [])}
    require(mapped_cases == case_id_set,
            f"requirements do not exactly cover cases; missing={sorted(case_id_set-mapped_cases)} extra={sorted(mapped_cases-case_id_set)}",
            errors)
    checks.append("14 supplied requirements map exactly to all 22 cases")

    contract_requirements = contract.get("requirements", [])
    require(
        {row.get("requirement_id") for row in contract_requirements} == EXPECTED_REQUIREMENTS,
        "Prompt 2 contract requirement IDs differ from traceability",
        errors,
    )
    require(contract.get("lane", {}).get("branch") == "pg/red-team-fixtures-20260806",
            "Prompt 2 contract branch differs", errors)
    require(contract.get("audited_result", {}).get("counts") == EXPECTED_COUNTS,
            "Prompt 2 contract counts differ", errors)
    checks.append("machine-readable Prompt 2 contract preserves lane, requirements, and result")

    trace_cases = traceability.get("cases", [])
    trace_case_ids = [row.get("case_id") for row in trace_cases]
    require(set(trace_case_ids) == case_id_set, "traceability case inventory differs from runner", errors)
    require(len(trace_case_ids) == len(set(trace_case_ids)), "traceability has duplicate case IDs", errors)
    trace_by_id = {row["case_id"]: row for row in trace_cases if row.get("case_id")}
    for case in case_list:
        row = trace_by_id.get(case.case_id, {})
        require(row.get("expectation") == case.expectation,
                f"{case.case_id} expectation differs between runner and traceability", errors)
        require(set(row.get("finding_ids", [])) == set(case.finding_ids),
                f"{case.case_id} findings differ between runner and traceability", errors)
        require(row.get("invariant") == case.invariant,
                f"{case.case_id} invariant differs between runner and traceability", errors)
    controls = set(traceability.get("controls", {}).keys())
    require(controls == EXPECTED_CONTROLS,
            f"control set is {sorted(controls)}, expected {sorted(EXPECTED_CONTROLS)}", errors)
    checks.append("traceability mirrors runner expectations, invariants, findings, and controls")

    finding_rows = findings.get("findings", [])
    finding_ids = [row.get("id") for row in finding_rows]
    finding_id_set = set(finding_ids)
    require(len(finding_rows) == 16, f"finding count is {len(finding_rows)}, expected 16", errors)
    require(len(finding_ids) == len(finding_id_set), "findings register has duplicate IDs", errors)
    severity_counts = Counter(row.get("severity") for row in finding_rows)
    require(dict(severity_counts) == EXPECTED_SEVERITIES,
            f"severity counts are {dict(severity_counts)}, expected {EXPECTED_SEVERITIES}", errors)
    require(findings.get("severity_counts") == EXPECTED_SEVERITIES,
            "top-level severity counts disagree with finding rows", errors)
    checks.append("16 unique findings with P0=8 and P1=8")

    runner_finding_ids = {fid for case in case_list for fid in case.finding_ids}
    requirement_finding_ids = {fid for row in requirements for fid in row.get("finding_ids", [])}
    require(runner_finding_ids == finding_id_set, "runner and findings registry use different finding IDs", errors)
    require(requirement_finding_ids == finding_id_set, "requirements and findings registry use different finding IDs", errors)
    for finding in finding_rows:
        tests = set(finding.get("test_cases", []))
        require(bool(tests), f"{finding.get('id')} has no test case", errors)
        require(tests <= case_id_set,
                f"{finding.get('id')} references unknown tests {sorted(tests-case_id_set)}", errors)
        require(finding.get("status") == "open_expected_failure",
                f"{finding.get('id')} has unexpected status {finding.get('status')}", errors)
    checks.append("prompt, runner, traceability, and findings use the same stable IDs")

    ledger_entries = ledger.get("entries", [])
    ledger_by_id = {row.get("finding_id"): row for row in ledger_entries}
    require(set(ledger_by_id) == finding_id_set, "source-evidence ledger differs from findings registry", errors)
    require(len(ledger_entries) == len(ledger_by_id), "source-evidence ledger has duplicate IDs", errors)
    for finding in finding_rows:
        row = ledger_by_id.get(finding["id"], {})
        require(row.get("severity") == finding.get("severity"),
                f"{finding['id']} severity differs in evidence ledger", errors)
        require({test.get("case_id") for test in row.get("test_cases", [])} == set(finding.get("test_cases", [])),
                f"{finding['id']} tests differ in evidence ledger", errors)
        require(row.get("source_observations") == finding.get("source_evidence"),
                f"{finding['id']} source observations differ in evidence ledger", errors)
    checks.append("source-evidence ledger reconstructs all 16 finding chains")

    receipt_results = receipt.get("results", [])
    receipt_by_id = {row.get("case_id"): row for row in receipt_results}
    require(set(receipt_by_id) == case_id_set, "receipt result inventory differs from runner", errors)
    require(receipt.get("counts") == EXPECTED_COUNTS,
            f"receipt counts are {receipt.get('counts')}, expected {EXPECTED_COUNTS}", errors)
    require(receipt.get("offline") is True, "receipt is not marked offline", errors)
    require(receipt.get("repo") == "<clean-checkout>", "receipt checkout root is not sanitized", errors)
    for case_id, trace_row in trace_by_id.items():
        result = receipt_by_id.get(case_id, {})
        require(result.get("status") == trace_row.get("actual_status"),
                f"{case_id} receipt status differs from traceability", errors)
    require(traceability.get("status_summary") == EXPECTED_COUNTS,
            "traceability status summary differs from expected counts", errors)
    checks.append("normalized receipt is 3 PASS / 19 XFAIL / no unexpected result")

    prompt_bundle_sha = sha256(paths["prompt_bundle"])
    prompt_2_sha = sha256(paths["prompt_2"])
    request_source = manifest.get("request_source", {})
    require(SHA256.fullmatch(prompt_bundle_sha) is not None, "computed prompt bundle SHA is malformed", errors)
    require(prompt_bundle_sha == request_source.get("original_sha256"), "prompt bundle SHA differs from source manifest", errors)
    require(prompt_bundle_sha == request_source.get("committed_copy_sha256"), "committed prompt copy SHA differs from source manifest", errors)
    require(prompt_2_sha == request_source.get("prompt_2_sha256"), "Prompt 2 SHA differs from source manifest", errors)
    require(paths["prompt_bundle"].stat().st_size == request_source.get("original_bytes"), "prompt bundle byte count differs", errors)
    require(paths["prompt_2"].stat().st_size == request_source.get("prompt_2_bytes"), "Prompt 2 byte count differs", errors)
    require(traceability.get("request_source", {}).get("sha256") == prompt_bundle_sha,
            "traceability prompt bundle SHA differs", errors)
    require(traceability.get("request_source", {}).get("prompt_2_sha256") == prompt_2_sha,
            "traceability Prompt 2 SHA differs", errors)
    require(contract.get("source", {}).get("full_bundle_sha256") == prompt_bundle_sha,
            "Prompt 2 contract full-bundle SHA differs", errors)
    require(contract.get("source", {}).get("prompt_2_sha256") == prompt_2_sha,
            "Prompt 2 contract slice SHA differs", errors)
    checks.append("full supplied prompt and Prompt 2 slice match recorded SHA-256/byte counts")

    source_file_keys = {
        (row.get("repository"), row.get("commit"), row.get("path"))
        for row in manifest.get("source_files", [])
    }
    local_blob_matches = 0
    for row in manifest.get("source_files", []):
        require(SHA1.fullmatch(str(row.get("git_blob_sha", ""))) is not None,
                f"source manifest has malformed blob SHA for {row.get('path')}", errors)
        if row.get("repository") == "sisodias/siso-people-graph":
            path = repo / str(row.get("path", ""))
            require(path.is_file(), f"pinned local source file missing: {row.get('path')}", errors)
            if path.is_file():
                actual = git_blob_sha(path)
                require(actual == row.get("git_blob_sha"),
                        f"local source blob differs from baseline: {row.get('path')} got {actual}", errors)
                if actual == row.get("git_blob_sha"):
                    local_blob_matches += 1
    require(local_blob_matches == 9,
            f"local baseline blob matches={local_blob_matches}, expected 9", errors)
    for finding in finding_rows:
        for source in finding.get("source_evidence", []):
            key = (source.get("repository"), source.get("commit"), source.get("path"))
            require(key in source_file_keys,
                    f"{finding.get('id')} source is absent from manifest: {key}", errors)
    checks.append("all 9 local production sources match pinned baseline Git blobs")

    book_source = book_fixture.get("source", {})
    book_manifest = next(
        (row for row in manifest.get("source_files", [])
         if row.get("repository") == "sisodias/siso-book-library"),
        {},
    )
    require(book_source.get("commit") == book_manifest.get("commit"), "Book commit differs between fixture and manifest", errors)
    require(book_source.get("path") == book_manifest.get("path"), "Book path differs between fixture and manifest", errors)
    require(book_source.get("blob_sha") == book_manifest.get("git_blob_sha"), "Book blob differs between fixture and manifest", errors)
    checks.append("cross-repository Book export contract is pinned consistently")

    for row in manifest.get("execution_receipts", []):
        path = repo / row.get("path", "")
        require(path.is_file(), f"manifest receipt missing: {row.get('path')}", errors)
        if path.is_file():
            require(sha256(path) == row.get("sha256"), f"receipt digest drifted: {row.get('path')}", errors)
    for row in manifest.get("derived_audit_artifacts", []):
        path = repo / row.get("path", "")
        require(path.is_file(), f"manifest artifact missing: {row.get('path')}", errors)
        if path.is_file():
            require(sha256(path) == row.get("sha256"), f"artifact digest drifted: {row.get('path')}", errors)
    checks.append("manifest SHA-256 receipts and derived-artifact digests match committed bytes")

    audit_text = paths["audit"].read_text(encoding="utf-8")
    worklog_text = paths["worklog"].read_text(encoding="utf-8")
    for finding_id in finding_id_set:
        require(finding_id in audit_text, f"narrative audit omits {finding_id}", errors)
        require(finding_id in worklog_text, f"forensic worklog omits {finding_id}", errors)
    checks.append("narrative audit and forensic worklog contain every stable finding ID")

    handoff_text = paths["handoff"].read_text(encoding="utf-8")
    missing_sections = EXPECTED_HANDOFF_SECTIONS - headings(handoff_text)
    require(not missing_sections, f"handoff missing required sections: {sorted(missing_sections)}", errors)
    for command in (
        "python3 tests/red_team/verify_audit.py",
        "python3 tests/red_team/verify_audit.py --run",
        "python3 tests/red_team/run.py",
        "python3 tests/red_team/run.py --json",
    ):
        require(command in handoff_text or command in worklog_text,
                f"published replay instructions omit command: {command}", errors)
    required_handoff_paths = [
        "tests/red_team/verify_audit.py",
        "tests/red_team/fixtures/prompt_2_contract.json",
        "docs/audits/source-evidence-ledger.json",
        "docs/audits/people-graph-v2-source-manifest.json",
        "docs/audits/people-graph-v2-forensic-worklog-2026-08-06.md",
        "docs/audits/receipts/people-graph-v2-red-team-run-2026-08-06.json",
        "docs/audits/sources/parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt",
    ]
    for relative in required_handoff_paths:
        require(relative in handoff_text, f"handoff changed-path list omits {relative}", errors)
    checks.append("handoff contains required sections, replay commands, and evidence paths")

    if args.run:
        ctx = Context(repo)
        runner.verify_layout(ctx)
        rerun_results = [runner.execute(case, ctx) for case in case_list]
        rerun_counts = {status: 0 for status in ("PASS", "XFAIL", "FAIL", "XPASS", "ERROR")}
        for result in rerun_results:
            rerun_counts[result.status] += 1
            recorded = receipt_by_id.get(result.case_id, {})
            live = result_projection(result.__dict__, repo)
            stored = result_projection(recorded, repo)
            require(live == stored,
                    f"{result.case_id} replay evidence differs from committed receipt", errors)
        require(rerun_counts == EXPECTED_COUNTS,
                f"live replay counts are {rerun_counts}, expected {EXPECTED_COUNTS}", errors)
        checks.append("live 22-case replay matches committed non-volatile evidence")

    # Do not expose ephemeral/private agent topology in generated artifacts. The
    # exact user-supplied prompt bundle is excluded because it is immutable input.
    scan_paths = [
        paths["findings"], paths["traceability"], paths["manifest"], paths["ledger"],
        paths["contract"], paths["receipt_json"], paths["receipt_text"], paths["audit"],
        paths["worklog"], paths["audit_index"], paths["source_index"], paths["handoff"],
        repo / "tests/red_team/README.md",
    ]
    for path in scan_paths:
        text = path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_LOCAL_PREFIXES:
            require(prefix not in text,
                    f"agent-generated artifact exposes local path prefix {prefix}: {path.relative_to(repo)}",
                    errors)
    checks.append("agent-generated evidence contains no private/local filesystem prefixes")

    payload = {
        "ok": not errors,
        "checks": checks,
        "counts": {
            "cases": len(case_ids),
            "requirements": len(requirements),
            "findings": len(finding_rows),
            "source_files": len(manifest.get("source_files", [])),
            "local_blob_matches": local_blob_matches,
            "receipt_results": len(receipt_results),
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
