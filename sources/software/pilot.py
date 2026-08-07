#!/usr/bin/env python3
"""Offline software/AI ecosystem pilot runner.

The command consumes tiny replayable fixtures, emits deterministic
``pg-observation-0.1`` NDJSON, and calculates evidence-first pilot metrics. It
performs no network I/O and never assigns canonical People Graph identifiers.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from sources.ai.huggingface import adapt_huggingface_fixture
from sources.software.envelope import canonical_json, read_ndjson, validate_envelope, write_ndjson
from sources.software.github import adapt_github_fixture
from sources.software.packages import (
    adapt_crates_fixture,
    adapt_ecosystems_fixture,
    adapt_pypi_fixture,
)
from sources.software.software_heritage import adapt_software_heritage_fixture

PILOT_VERSION = "software-ai-pilot-0.1"
FIXTURE_FILES = {
    "github": "github.json",
    "pypi": "pypi.json",
    "crates": "crates.json",
    "ecosystems": "ecosystems.json",
    "software_heritage": "software_heritage.json",
    "huggingface": "huggingface.json",
}

SOURCE_COST_PROFILES = [
    {
        "source": "github_rest",
        "acquisition": "bounded REST/GraphQL enrichment with conditional requests",
        "relative_cost": "high_at_scale",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Use numeric IDs from cohort manifests; batch GraphQL only where snapshots cannot answer.",
    },
    {
        "source": "gh_archive",
        "acquisition": "hourly public event archives or BigQuery",
        "relative_cost": "low_for_temporal_events",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Use bounded time windows and retain event locators rather than replaying all history.",
    },
    {
        "source": "ecosystems_packages",
        "acquisition": "normalized package/repository API and exports",
        "relative_cost": "low_to_medium",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Preferred first pass for npm and cross-registry dependency/maintainer coverage.",
    },
    {
        "source": "pypi",
        "acquisition": "Index API for change detection plus per-project JSON only for selected cohort",
        "relative_cost": "medium",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Use serials and HTTP caching; do not infer ownership from author strings.",
    },
    {
        "source": "crates_io",
        "acquisition": "Cargo sparse/git index plus bounded owner API lookups",
        "relative_cost": "low_for_versions_medium_for_owners",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Read checksums/dependencies from the index; reserve API calls for owner edges.",
    },
    {
        "source": "software_heritage",
        "acquisition": "point lookups for known origins/SWHIDs",
        "relative_cost": "high_for_discovery_low_for_verification",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Verify known repositories and revisions; do not use the public API for bulk extraction.",
    },
    {
        "source": "huggingface_hub",
        "acquisition": "paginated public model/dataset/Space metadata plus revision heads",
        "relative_cost": "medium",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Scale metadata first; fetch cards selectively and keep gated/private content out of the pilot.",
    },
    {
        "source": "npm_registry_direct",
        "acquisition": "deferred",
        "relative_cost": "not_measured",
        "network_calls_in_fixture_pilot": 0,
        "scale_recommendation": "Use ecosyste.ms first; add direct registry deltas only after gap and terms review.",
    },
]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"fixture must contain a JSON object: {path}")
    return value


def load_fixtures(fixture_dir: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(fixture_dir)
    fixtures: dict[str, dict[str, Any]] = {}
    for key, filename in FIXTURE_FILES.items():
        path = root / filename
        if not path.is_file():
            raise FileNotFoundError(f"missing required fixture: {path}")
        fixtures[key] = _load_json(path)
    return fixtures


def build_records(fixture_dir: str | Path) -> list[dict[str, Any]]:
    fixtures = load_fixtures(fixture_dir)
    records: list[dict[str, Any]] = []
    records.extend(adapt_github_fixture(fixtures["github"]))
    records.extend(adapt_pypi_fixture(fixtures["pypi"]))
    records.extend(adapt_crates_fixture(fixtures["crates"]))
    records.extend(adapt_ecosystems_fixture(fixtures["ecosystems"]))
    records.extend(adapt_software_heritage_fixture(fixtures["software_heritage"]))
    records.extend(adapt_huggingface_fixture(fixtures["huggingface"]))
    for record in records:
        validate_envelope(record)
    return records


def _walk_values(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_values(child)


def _all_identifiers(record: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for mapping in _walk_values(record):
        if {"scheme", "value", "scope", "stability", "uniqueness", "evidence"} <= mapping.keys():
            yield mapping


def _round_pct(numerator: int, denominator: int) -> float:
    return round((100.0 * numerator / denominator), 2) if denominator else 0.0


def _license_conflicts(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    observations: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for record in records:
        attributes = record["subject"]["attributes"]
        if attributes.get("work_type") != "software_package":
            continue
        license_value = attributes.get("license")
        if license_value:
            observations[record["subject"]["source_native_id"]].append(
                (record["source"]["source_id"], str(license_value))
            )
    conflicts: list[dict[str, Any]] = []
    for subject_id, values in sorted(observations.items()):
        distinct = sorted({license_value for _, license_value in values})
        if len(distinct) > 1:
            conflicts.append(
                {
                    "subject_native_id": subject_id,
                    "field": "license",
                    "observations": [
                        {"source_id": source_id, "value": license_value}
                        for source_id, license_value in sorted(values)
                    ],
                    "distinct_values": distinct,
                    "resolution": "preserve_conflict_for_review",
                }
            )
    return conflicts


def compute_metrics(records: Iterable[Mapping[str, Any]], *, fixture_dir: str | Path | None = None) -> dict[str, Any]:
    materialized = list(records)
    sources = Counter(record["source"]["source_id"] for record in materialized)
    subject_kinds = Counter(record["subject"]["kind"] for record in materialized)
    work_types = Counter(
        record["subject"]["attributes"].get("work_type", "unspecified")
        for record in materialized
        if record["subject"]["kind"] == "work"
    )
    contribution_roles = Counter()
    relationship_types = Counter()
    identifier_schemes = Counter()
    stable_unique_identifiers: set[tuple[str, str]] = set()
    cross_platform_receipts: list[dict[str, str]] = []
    metric_observations = 0

    for record in materialized:
        for contribution in record.get("contributions", []):
            contribution_roles[str(contribution.get("role", "unspecified"))] += 1
        for relationship in record.get("relationships", []):
            relationship_types[str(relationship.get("predicate", "unspecified"))] += 1
        metric_observations += len(record["subject"]["attributes"].get("metrics", []))
        for identifier in _all_identifiers(record):
            scheme = str(identifier["scheme"])
            value = str(identifier["value"])
            identifier_schemes[scheme] += 1
            if identifier["stability"] == "stable" and identifier["uniqueness"] == "unique":
                stable_unique_identifiers.add((scheme, value))
            if scheme == "github_account_id" and record["source"]["source_id"] not in {
                "github_rest",
                "gh_archive",
            }:
                cross_platform_receipts.append(
                    {
                        "source_id": record["source"]["source_id"],
                        "github_account_id": value,
                        "subject_native_id": record["subject"]["source_native_id"],
                        "evidence": str(identifier["evidence"]),
                    }
                )

    works = [record for record in materialized if record["subject"]["kind"] == "work"]
    licensed_works = [record for record in works if record["subject"]["attributes"].get("license")]
    rights_complete = [
        record
        for record in materialized
        if record["source"].get("terms_revision")
        and record["source"].get("rights_state") not in {"pending", "restricted"}
    ]
    archived_works = [
        record
        for record in works
        if record["subject"]["attributes"].get("archived")
        or str(record["subject"]["attributes"].get("work_type", "")).startswith("software_archive_")
    ]
    abandoned_works = [
        record for record in works if record["subject"]["attributes"].get("abandoned") is True
    ]
    temporal_relationship_count = sum(
        1
        for record in materialized
        for relationship in record.get("relationships", [])
        if relationship.get("valid_time") or relationship.get("predicate") in {"renamed_from", "transferred_from"}
    )

    fixture_bytes = None
    if fixture_dir is not None:
        root = Path(fixture_dir)
        fixture_bytes = sum((root / filename).stat().st_size for filename in FIXTURE_FILES.values())

    source_conflicts = _license_conflicts(materialized)
    unique_cross_platform_receipts = {
        (item["source_id"], item["github_account_id"], item["subject_native_id"], item["evidence"])
        for item in cross_platform_receipts
    }

    return {
        "metric_version": PILOT_VERSION,
        "pilot_mode": "offline_replayable_fixture",
        "network_calls": 0,
        "record_count": len(materialized),
        "source_count": len(sources),
        "records_by_source": dict(sorted(sources.items())),
        "subjects_by_kind": dict(sorted(subject_kinds.items())),
        "works_by_type": dict(sorted(work_types.items())),
        "contribution_edges": sum(contribution_roles.values()),
        "contribution_roles": dict(sorted(contribution_roles.items())),
        "relationship_edges": sum(relationship_types.values()),
        "relationship_types": dict(sorted(relationship_types.items())),
        "identifier_observations": sum(identifier_schemes.values()),
        "identifier_schemes": dict(sorted(identifier_schemes.items())),
        "stable_unique_identifiers": len(stable_unique_identifiers),
        "stable_unique_identifier_schemes": sorted({scheme for scheme, _ in stable_unique_identifiers}),
        "cross_platform_identity_evidence_receipts": len(unique_cross_platform_receipts),
        "temporal_events": subject_kinds.get("event", 0),
        "temporal_relationships": temporal_relationship_count,
        "metric_observations": metric_observations,
        "archived_works": len(archived_works),
        "abandoned_works": len(abandoned_works),
        "license_coverage": {
            "eligible_works": len(works),
            "works_with_declared_license": len(licensed_works),
            "percent": _round_pct(len(licensed_works), len(works)),
        },
        "rights_coverage": {
            "records_with_non_pending_terms_and_rights": len(rights_complete),
            "records": len(materialized),
            "percent": _round_pct(len(rights_complete), len(materialized)),
        },
        "source_conflicts": source_conflicts,
        "source_conflict_count": len(source_conflicts),
        "fixture_bytes": fixture_bytes,
        "source_cost_profiles": SOURCE_COST_PROFILES,
    }


def write_json(value: Mapping[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _command_export(args: argparse.Namespace) -> int:
    records = build_records(args.fixtures)
    write_ndjson(records, args.out)
    metrics = compute_metrics(records, fixture_dir=args.fixtures)
    write_json(metrics, args.metrics_out)
    print(canonical_json({"records": len(records), "out": str(args.out), "metrics": str(args.metrics_out)}))
    return 0


def _command_validate(args: argparse.Namespace) -> int:
    records = read_ndjson(args.path)
    print(canonical_json({"valid": True, "records": len(records), "path": str(args.path)}))
    return 0


def _command_metrics(args: argparse.Namespace) -> int:
    if args.path:
        records = read_ndjson(args.path)
        metrics = compute_metrics(records)
    else:
        records = build_records(args.fixtures)
        metrics = compute_metrics(records, fixture_dir=args.fixtures)
    if args.out:
        write_json(metrics, args.out)
    print(json.dumps(metrics, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="convert fixtures to deterministic NDJSON")
    export.add_argument("--fixtures", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)
    export.add_argument("--metrics-out", type=Path, required=True)
    export.set_defaults(func=_command_export)

    validate = subparsers.add_parser("validate", help="validate an emitted NDJSON file")
    validate.add_argument("path", type=Path)
    validate.set_defaults(func=_command_validate)

    metrics = subparsers.add_parser("metrics", help="calculate pilot metrics")
    metrics.add_argument("--fixtures", type=Path)
    metrics.add_argument("--path", type=Path)
    metrics.add_argument("--out", type=Path)
    metrics.set_defaults(func=_command_metrics)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "metrics" and not args.path and not args.fixtures:
        parser.error("metrics requires --path or --fixtures")
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
