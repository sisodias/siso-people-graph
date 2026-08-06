"""Command-line interface for the parallel integration contract harness."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

from .adapters import SourcePolicy, open_sqlite_adapter
from .capabilities import capability_report
from .contract import (
    canonical_json_bytes,
    iter_ndjson,
    repository_payload_resolver,
    validate_ndjson,
    write_ndjson,
)
from .lanes import load_lane_registry, validate_lane_registry
from .merge_risk import analyze_files


def _print(value: Mapping[str, Any], *, compact: bool = False) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=None if compact else 2,
            separators=(",", ":") if compact else None,
        )
    )


def _file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_source_policies(path: str | Path | None) -> dict[str, SourcePolicy]:
    if path is None:
        return {}
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("source policy file must be an object keyed by source_id")
    policies: dict[str, SourcePolicy] = {}
    for source_id, raw in value.items():
        if not isinstance(raw, dict):
            raise ValueError(f"source policy {source_id!r} must be an object")
        policies[str(source_id)] = SourcePolicy(
            snapshot_id=str(raw.get("snapshot_id", "legacy-v2-unrecorded")),
            terms_revision=str(raw.get("terms_revision", "documented-unknown")),
            rights_state=str(raw.get("rights_state", "pending")),
            retrieved_at=(
                str(raw["retrieved_at"]) if raw.get("retrieved_at") is not None else None
            ),
        )
    return policies


def command_validate(args: argparse.Namespace) -> int:
    resolver = (
        repository_payload_resolver(args.payload_root) if args.payload_root else None
    )
    report = validate_ndjson(args.path, payload_resolver=resolver)
    _print(report, compact=args.compact)
    return 0 if report["valid"] else 1


def command_roundtrip(args: argparse.Namespace) -> int:
    records = [record for _, record in iter_ndjson(args.input)]
    count = write_ndjson(args.output, records)
    reread = [record for _, record in iter_ndjson(args.output)]
    logically_equal = [canonical_json_bytes(item) for item in records] == [
        canonical_json_bytes(item) for item in reread
    ]
    report = {
        "input": str(args.input),
        "output": str(args.output),
        "record_count": count,
        "logical_roundtrip_equal": logically_equal,
        "output_sha256": _file_sha256(args.output),
    }
    _print(report, compact=args.compact)
    return 0 if logically_equal else 1


def command_adapt_sqlite(args: argparse.Namespace) -> int:
    policies = _load_source_policies(args.source_policies)
    adapter = open_sqlite_adapter(args.database, source_policies=policies)
    count = adapter.export(args.output)
    decisions = [item.to_dict() for item in adapter.iter_identity_decisions()]
    if args.decisions_output:
        Path(args.decisions_output).write_text(
            json.dumps(decisions, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    validation = validate_ndjson(args.output)
    report = {
        "database": str(args.database),
        "output": str(args.output),
        "records": count,
        "decisions": len(decisions),
        "decisions_output": (
            str(args.decisions_output) if args.decisions_output else None
        ),
        "capabilities": adapter.capabilities().to_dict(),
        "validation": validation,
        "output_sha256": _file_sha256(args.output),
    }
    _print(report, compact=args.compact)
    return 0 if validation["valid"] else 1


def command_capabilities(args: argparse.Namespace) -> int:
    report = capability_report(
        args.repo_root,
        databases=args.database,
        observations=args.observation,
    )
    _print(report, compact=args.compact)
    runtime_ok = all(
        item.get("status") == "available"
        for item in report["runtime_databases"] + report["runtime_observations"]
    )
    return 0 if runtime_ok else 1


def command_lanes(args: argparse.Namespace) -> int:
    report = validate_lane_registry(load_lane_registry(args.registry))
    _print(report, compact=args.compact)
    return 0 if report["valid"] else 1


def command_risk(args: argparse.Namespace) -> int:
    report = analyze_files(args.snapshot, args.registry)
    _print(report, compact=args.compact)
    blocking = any(risk.get("severity") == "P0" for risk in report.get("risks", []))
    return 0 if report.get("valid") and not blocking else 1


def _resolve_optional_paths(root: Path, values: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        paths.append(path if path.is_absolute() else root / path)
    return paths


def command_check(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve()
    registry_path = root / "integration/lane_registry.json"
    fixture_path = root / "tests/integration_parallel/fixtures/valid_observations.ndjson"
    default_snapshot = root / "tests/integration_parallel/fixtures/open_pr_snapshot_empty.json"
    snapshot_path = Path(args.pr_snapshot).resolve() if args.pr_snapshot else default_snapshot

    lane_report = validate_lane_registry(load_lane_registry(registry_path))
    fixture_report = validate_ndjson(
        fixture_path,
        payload_resolver=repository_payload_resolver(root),
    )
    risk_report = analyze_files(snapshot_path, registry_path)
    databases = _resolve_optional_paths(root, args.database)
    observations = _resolve_optional_paths(root, args.observation)
    capabilities = capability_report(
        root,
        databases=databases,
        observations=observations,
        metadata={
            "mode": "parallel-integration-check",
            "base_sha": args.base_sha,
        },
    )

    blocking_risks = [
        risk
        for risk in risk_report.get("risks", [])
        if risk.get("severity") == "P0"
    ]
    runtime_failures = [
        item
        for item in capabilities["runtime_databases"]
        + capabilities["runtime_observations"]
        if item.get("status") != "available"
    ]
    valid = (
        lane_report["valid"]
        and fixture_report["valid"]
        and risk_report.get("valid", False)
        and not blocking_risks
        and not runtime_failures
    )
    report = {
        "check_version": "pg-parallel-integration-check-0.1",
        "valid": valid,
        "repo_root": str(root),
        "base_sha": args.base_sha,
        "lane_registry": lane_report,
        "contract_fixture": fixture_report,
        "merge_risk": risk_report,
        "capabilities": capabilities,
        "blocking_risk_count": len(blocking_risks),
        "runtime_failure_count": len(runtime_failures),
        "rerun_command": "python3 -m integration check --repo-root .",
    }
    _print(report, compact=args.compact)
    return 0 if valid else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m integration",
        description=(
            "Validate the shared observation contract, detect partial capabilities, "
            "adapt legacy data read-only, and analyze parallel merge risk."
        ),
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit compact JSON",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate NDJSON")
    validate_parser.add_argument("path")
    validate_parser.add_argument(
        "--payload-root",
        help="verify repository-relative raw_pointer payload hashes beneath this root",
    )
    validate_parser.set_defaults(func=command_validate)

    roundtrip_parser = subparsers.add_parser(
        "roundtrip", help="validate and deterministically re-emit NDJSON"
    )
    roundtrip_parser.add_argument("input")
    roundtrip_parser.add_argument("output")
    roundtrip_parser.set_defaults(func=command_roundtrip)

    adapt_parser = subparsers.add_parser(
        "adapt-sqlite", help="export v2 or v3 SQLite observations without resolving identity"
    )
    adapt_parser.add_argument("database")
    adapt_parser.add_argument("output")
    adapt_parser.add_argument("--source-policies")
    adapt_parser.add_argument("--decisions-output")
    adapt_parser.set_defaults(func=command_adapt_sqlite)

    capabilities_parser = subparsers.add_parser(
        "capabilities", help="detect repository and runtime capabilities"
    )
    capabilities_parser.add_argument("--repo-root", default=".")
    capabilities_parser.add_argument("--database", action="append", default=[])
    capabilities_parser.add_argument("--observation", action="append", default=[])
    capabilities_parser.set_defaults(func=command_capabilities)

    lanes_parser = subparsers.add_parser(
        "lanes", help="validate exclusive lane ownership"
    )
    lanes_parser.add_argument(
        "--registry", default="integration/lane_registry.json"
    )
    lanes_parser.set_defaults(func=command_lanes)

    risk_parser = subparsers.add_parser(
        "risk", help="analyze an offline open-PR snapshot"
    )
    risk_parser.add_argument("snapshot")
    risk_parser.add_argument(
        "--registry", default="integration/lane_registry.json"
    )
    risk_parser.set_defaults(func=command_risk)

    check_parser = subparsers.add_parser(
        "check", help="run the reusable integration contract gate"
    )
    check_parser.add_argument("--repo-root", default=".")
    check_parser.add_argument("--database", action="append", default=[])
    check_parser.add_argument("--observation", action="append", default=[])
    check_parser.add_argument("--pr-snapshot")
    check_parser.add_argument("--base-sha")
    check_parser.set_defaults(func=command_check)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError) as exc:
        _print(
            {
                "valid": False,
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            },
            compact=getattr(args, "compact", False),
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
