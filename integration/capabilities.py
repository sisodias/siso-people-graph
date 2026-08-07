"""Capability detection for partially merged People Graph lanes.

The detector distinguishes repository declarations from executable runtime
capabilities.  A schema file on disk is evidence that a contract is declared;
it is not evidence that a production database or populated source snapshot
exists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .adapters import (
    AdapterError,
    NDJSONObservationAdapter,
    open_sqlite_adapter,
)
from .contract import validate_ndjson

REPORT_VERSION = "pg-capabilities-0.1"


@dataclass(frozen=True, slots=True)
class Capability:
    key: str
    status: str
    summary: str
    evidence: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence"] = list(self.evidence)
        value["gaps"] = list(self.gaps)
        return value


def _present(root: Path, *paths: str) -> tuple[str, ...]:
    return tuple(path for path in paths if (root / path).exists())


def _capability(
    key: str,
    *,
    evidence: Iterable[str],
    available_summary: str,
    missing_summary: str,
    declared_only: bool = False,
    gaps: Iterable[str] = (),
) -> Capability:
    evidence_tuple = tuple(evidence)
    if evidence_tuple:
        status = "declared" if declared_only else "available"
        summary = available_summary
    else:
        status = "missing"
        summary = missing_summary
    return Capability(
        key=key,
        status=status,
        summary=summary,
        evidence=evidence_tuple,
        gaps=tuple(gaps) if evidence_tuple else (),
    )


def detect_repository_capabilities(repo_root: str | Path) -> list[Capability]:
    """Detect repository-level capabilities without opening untracked assets."""

    root = Path(repo_root)
    capabilities: list[Capability] = []

    capabilities.append(
        _capability(
            "integration.observation_contract",
            evidence=_present(
                root,
                "integration/contract.py",
                "integration/pg_observation_0_1.schema.json",
            ),
            available_summary="Executable pg-observation-0.1 validation is present.",
            missing_summary="No shared executable observation contract detected.",
        )
    )
    capabilities.append(
        _capability(
            "integration.adapter_spine",
            evidence=_present(root, "integration/adapters.py"),
            available_summary="Capability-detecting v2, NDJSON, Book, and v3 adapter seams are present.",
            missing_summary="No integration adapter spine detected.",
        )
    )
    capabilities.append(
        _capability(
            "integration.merge_risk",
            evidence=_present(
                root,
                "integration/merge_risk.py",
                "integration/lane_registry.json",
            ),
            available_summary="Offline path-ownership and merge-risk analysis is present.",
            missing_summary="No executable merge-risk analyzer detected.",
        )
    )

    capabilities.append(
        _capability(
            "v2.schema",
            evidence=_present(root, "schema/people_schema_v2.sql"),
            available_summary="The current v2 SQLite schema is declared.",
            missing_summary="The current v2 schema is not present.",
            declared_only=True,
            gaps=(
                "A schema file does not prove a populated database or release asset exists.",
                "The v2 schema does not declare identifier scope, mutability, uniqueness, source snapshots, or per-row rights.",
            ),
        )
    )
    capabilities.append(
        _capability(
            "v2.build",
            evidence=_present(
                root,
                "loaders/build_people_graph_v2.py",
                "loaders/build_people_graph_books.py",
            ),
            available_summary="Legacy v2 build scripts are declared.",
            missing_summary="No v2 build scripts detected.",
            declared_only=True,
            gaps=(
                "Declared scripts are not proof of a clean-checkout build, idempotency, source manifests, or logical reproducibility.",
            ),
        )
    )
    capabilities.append(
        _capability(
            "v2.identity_claims",
            evidence=_present(root, "loaders/match_identities.py"),
            available_summary="A v2 identity-claim proposal surface is declared.",
            missing_summary="No v2 identity-claim proposal surface detected.",
            declared_only=True,
            gaps=(
                "Accepted claims are not equivalent to a canonical cluster interface.",
                "Legacy external_ids semantics are not declared in the v2 schema.",
            ),
        )
    )
    capabilities.append(
        _capability(
            "v2.query",
            evidence=_present(root, "loaders/ask.py"),
            available_summary="The legacy read-only query script is declared.",
            missing_summary="No v2 query script detected.",
            declared_only=True,
            gaps=(
                "A script on disk is not proof that any domain database is available.",
                "The legacy surface does not expose rights, source snapshots, build digests, or generic claims.",
            ),
        )
    )

    capabilities.append(
        _capability(
            "v3.schema",
            evidence=_present(root, "schema/v3"),
            available_summary="An additive v3 schema path is present.",
            missing_summary="No additive v3 schema path detected.",
            declared_only=True,
        )
    )
    capabilities.append(
        _capability(
            "v3.identity_resolution",
            evidence=_present(root, "identity_v3"),
            available_summary="A v3 identity-resolution module is present.",
            missing_summary="No v3 identity-resolution module detected.",
        )
    )
    capabilities.append(
        _capability(
            "v3.reproducible_build",
            evidence=_present(root, "build_v3", "manifests"),
            available_summary="Versioned build/release paths are present.",
            missing_summary="No v3 reproducible-build paths detected.",
        )
    )
    capabilities.append(
        _capability(
            "v3.query_library",
            evidence=_present(root, "query_v3"),
            available_summary="A versioned query library is present.",
            missing_summary="No v3 query library detected.",
        )
    )
    capabilities.append(
        _capability(
            "v3.http_api",
            evidence=_present(root, "api"),
            available_summary="An HTTP API path is present.",
            missing_summary="No HTTP API path detected.",
        )
    )
    capabilities.append(
        _capability(
            "v3.mcp",
            evidence=_present(root, "mcp"),
            available_summary="An MCP path is present.",
            missing_summary="No MCP path detected.",
        )
    )
    capabilities.append(
        _capability(
            "reasoning.claims",
            evidence=_present(root, "claims"),
            available_summary="A claims path is present.",
            missing_summary="No generic claims layer detected.",
        )
    )
    capabilities.append(
        _capability(
            "reasoning.projections",
            evidence=_present(root, "projections"),
            available_summary="A named-projections path is present.",
            missing_summary="No versioned projections layer detected.",
        )
    )
    capabilities.append(
        _capability(
            "sources.scholarly",
            evidence=_present(root, "sources/scholarly"),
            available_summary="Scholarly/authority adapters are present.",
            missing_summary="No scholarly/authority adapters detected.",
        )
    )
    capabilities.append(
        _capability(
            "sources.software_ai",
            evidence=_present(root, "sources/software", "sources/ai"),
            available_summary="Software or AI source adapters are present.",
            missing_summary="No software/AI source adapters detected.",
        )
    )
    capabilities.append(
        _capability(
            "sources.creators_media",
            evidence=_present(root, "sources/creators", "sources/media"),
            available_summary="Living-creator or media adapters are present.",
            missing_summary="No living-creator/media adapters detected.",
        )
    )
    capabilities.append(
        _capability(
            "testing.red_team",
            evidence=_present(root, "tests/red_team"),
            available_summary="Executable red-team fixtures are present.",
            missing_summary="No red-team fixture lane detected.",
        )
    )
    return capabilities


def detect_runtime_database(path: str | Path) -> dict[str, Any]:
    """Open one database read-only and report the selected adapter seam."""

    try:
        adapter = open_sqlite_adapter(path)
        return {
            "path": str(path),
            "status": "available",
            "adapter": adapter.capabilities().to_dict(),
        }
    except (OSError, AdapterError) as exc:
        return {
            "path": str(path),
            "status": "unsupported",
            "error": str(exc),
        }


def detect_runtime_observations(path: str | Path) -> dict[str, Any]:
    """Validate one source-pilot or Book Library NDJSON export."""

    report = validate_ndjson(path)
    adapter = NDJSONObservationAdapter(path, validate=False)
    return {
        "path": str(path),
        "status": "available" if report["valid"] else "invalid",
        "validation": report,
        "adapter": adapter.capabilities().to_dict(),
    }


def capability_report(
    repo_root: str | Path,
    *,
    databases: Iterable[str | Path] = (),
    observations: Iterable[str | Path] = (),
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a stable, JSON-serializable capability matrix."""

    repository = detect_repository_capabilities(repo_root)
    counts: dict[str, int] = {}
    for capability in repository:
        counts[capability.status] = counts.get(capability.status, 0) + 1
    return {
        "report_version": REPORT_VERSION,
        "repo_root": str(Path(repo_root)),
        "metadata": dict(metadata or {}),
        "repository": [item.to_dict() for item in repository],
        "runtime_databases": [detect_runtime_database(path) for path in databases],
        "runtime_observations": [
            detect_runtime_observations(path) for path in observations
        ],
        "status_counts": dict(sorted(counts.items())),
    }
