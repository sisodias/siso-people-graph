"""Offline merge-risk analysis for parallel-lane pull request snapshots.

GitHub access is deliberately outside this module.  A launch or release agent
exports the visible PR metadata and changed paths to JSON, then this analyzer can
be rerun in a clean checkout without credentials or network access.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from .lanes import (
    changed_paths_outside_lane,
    expected_handoff_path,
    lane_by_branch,
    load_lane_registry,
)

SNAPSHOT_VERSION = "pg-open-pr-snapshot-0.1"
REPORT_VERSION = "pg-merge-risk-0.1"

ROOT_SHARED_FILES = {
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "pytest.ini",
    "package.json",
    "package-lock.json",
    "Makefile",
}
SOURCE_PREFIXES = (
    "sources/",
    "loaders/",
    "build_v3/",
    "scripts/",
    "index/",
)
RIGHTS_DOC_MARKERS = (
    "rights",
    "license",
    "terms",
    "source-methods/",
    "handoff",
    "manifest",
)
SCHEMA_MARKERS = ("schema/", "migration", "ddl")
CONTRACT_MARKERS = (
    "pg_observation",
    "pg-observation",
    "observation_contract",
    "observation-contract",
)


@dataclass(frozen=True, slots=True)
class MergeRisk:
    risk_id: str
    severity: str
    category: str
    summary: str
    pull_requests: tuple[int, ...] = ()
    paths: tuple[str, ...] = ()
    resolution: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["pull_requests"] = list(self.pull_requests)
        value["paths"] = list(self.paths)
        return value


def load_pr_snapshot(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("PR snapshot root must be an object")
    return value


def _norm(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/"))).lstrip("./")


def _changed_paths(pr: Mapping[str, Any]) -> list[str]:
    value = pr.get("changed_paths", [])
    if not isinstance(value, list):
        return []
    return sorted({_norm(str(path)) for path in value if str(path).strip()})


def _has_rights_surface(paths: Iterable[str]) -> bool:
    lowered = [path.lower() for path in paths]
    return any(marker in path for path in lowered for marker in RIGHTS_DOC_MARKERS)


def _is_source_change(paths: Iterable[str]) -> bool:
    return any(path.startswith(SOURCE_PREFIXES) for path in paths)


def _schema_change(paths: Iterable[str]) -> bool:
    return any(any(marker in path.lower() for marker in SCHEMA_MARKERS) for path in paths)


def _contract_change(paths: Iterable[str]) -> bool:
    return any(any(marker in path.lower() for marker in CONTRACT_MARKERS) for path in paths)


def validate_snapshot(snapshot: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if snapshot.get("snapshot_version") != SNAPSHOT_VERSION:
        errors.append(f"snapshot_version must equal {SNAPSHOT_VERSION!r}")
    if not isinstance(snapshot.get("repository"), str) or not snapshot.get("repository"):
        errors.append("repository must be a non-empty string")
    if not isinstance(snapshot.get("pull_requests"), list):
        errors.append("pull_requests must be an array")
    for index, pr in enumerate(snapshot.get("pull_requests", [])):
        if not isinstance(pr, Mapping):
            errors.append(f"pull_requests[{index}] must be an object")
            continue
        for key in ("number", "title", "head_branch", "changed_paths"):
            if key not in pr:
                errors.append(f"pull_requests[{index}] is missing {key}")
        if not isinstance(pr.get("changed_paths", []), list):
            errors.append(f"pull_requests[{index}].changed_paths must be an array")
    return errors


def analyze_merge_risks(
    snapshot: Mapping[str, Any], registry: Mapping[str, Any]
) -> dict[str, Any]:
    """Analyze path ownership, contracts, migrations, and rights/security seams."""

    validation_errors = validate_snapshot(snapshot)
    if validation_errors:
        return {
            "report_version": REPORT_VERSION,
            "valid": False,
            "validation_errors": validation_errors,
            "risks": [],
        }

    repository = str(snapshot["repository"])
    prs = [pr for pr in snapshot.get("pull_requests", []) if isinstance(pr, Mapping)]
    risks: list[MergeRisk] = []
    seen_ids: set[str] = set()

    def add(risk: MergeRisk) -> None:
        if risk.risk_id not in seen_ids:
            risks.append(risk)
            seen_ids.add(risk.risk_id)

    path_to_prs: dict[str, list[int]] = {}
    schema_prs: list[int] = []
    contract_prs: list[int] = []
    root_path_prs: dict[str, list[int]] = {}

    for pr in prs:
        number = int(pr["number"])
        branch = str(pr.get("head_branch", ""))
        paths = _changed_paths(pr)
        lane = lane_by_branch(registry, repository, branch)
        for path in paths:
            path_to_prs.setdefault(path, []).append(number)
            if path in ROOT_SHARED_FILES or path.startswith(".github/workflows/"):
                root_path_prs.setdefault(path, []).append(number)

        if lane is None:
            add(
                MergeRisk(
                    risk_id=f"MR-UNKNOWN-LANE-{number}",
                    severity="P1",
                    category="ownership",
                    summary=f"PR #{number} does not map to a registered parallel lane branch.",
                    pull_requests=(number,),
                    paths=tuple(paths[:20]),
                    resolution="Register the branch explicitly or review every changed path before combination.",
                )
            )
        else:
            outside = changed_paths_outside_lane(lane, paths)
            if outside:
                add(
                    MergeRisk(
                        risk_id=f"MR-OUTSIDE-OWNERSHIP-{number}",
                        severity="P0" if any(path.startswith("schema/") for path in outside) else "P1",
                        category="ownership",
                        summary=f"PR #{number} changes paths outside lane {lane['id']} ownership.",
                        pull_requests=(number,),
                        paths=tuple(outside),
                        resolution="Move the change into the owning lane, use a lane-local adapter, or obtain an explicit reviewed handoff before merge.",
                    )
                )
            handoff = expected_handoff_path(lane)
            if handoff and handoff not in paths:
                add(
                    MergeRisk(
                        risk_id=f"MR-MISSING-HANDOFF-{number}",
                        severity="P1",
                        category="handoff",
                        summary=f"PR #{number} does not include its expected handoff file.",
                        pull_requests=(number,),
                        paths=(handoff,),
                        resolution="Add the lane handoff with commands, tests, assumptions, seams, risks, rights notes, and merge considerations.",
                    )
                )

        if _is_source_change(paths) and not _has_rights_surface(paths):
            add(
                MergeRisk(
                    risk_id=f"MR-RIGHTS-SURFACE-{number}",
                    severity="P1",
                    category="rights",
                    summary=f"PR #{number} changes ingestion/source paths without an obvious rights, terms, manifest, method-card, or handoff surface.",
                    pull_requests=(number,),
                    paths=tuple(paths),
                    resolution="Require source snapshot, terms revision, rights state, update/deletion handling, and data-retention notes before ingestion is enabled.",
                )
            )

        if _schema_change(paths):
            schema_prs.append(number)
        if _contract_change(paths):
            contract_prs.append(number)

    for path, numbers in sorted(path_to_prs.items()):
        unique = sorted(set(numbers))
        if len(unique) > 1:
            add(
                MergeRisk(
                    risk_id="MR-PATH-OVERLAP-" + "-".join(map(str, unique)) + "-" + path.replace("/", "-")[:60],
                    severity="P0",
                    category="path_overlap",
                    summary=f"Multiple open PRs change the same path: {path}.",
                    pull_requests=tuple(unique),
                    paths=(path,),
                    resolution="Choose one owner, rebase the other lane onto the accepted contract, and resolve semantics before combining commits.",
                )
            )

    for path, numbers in sorted(root_path_prs.items()):
        unique = sorted(set(numbers))
        if len(unique) > 1:
            add(
                MergeRisk(
                    risk_id="MR-ROOT-CONFLICT-" + "-".join(map(str, unique)) + "-" + path.replace("/", "-")[:60],
                    severity="P1",
                    category="root_configuration",
                    summary=f"Multiple PRs change shared configuration surface {path}.",
                    pull_requests=tuple(unique),
                    paths=(path,),
                    resolution="Consolidate root configuration in a dedicated follow-up after lane-local tests pass; do not resolve by taking either file wholesale.",
                )
            )

    if len(set(schema_prs)) > 1:
        numbers = tuple(sorted(set(schema_prs)))
        add(
            MergeRisk(
                risk_id="MR-MULTIPLE-SCHEMAS-" + "-".join(map(str, numbers)),
                severity="P0",
                category="migration",
                summary="Multiple PRs change schema or migration surfaces.",
                pull_requests=numbers,
                resolution="Select one additive schema authority, map other lanes through adapters, and prove source reconstruction plus downgrade/undo behavior.",
            )
        )

    if len(set(contract_prs)) > 1:
        numbers = tuple(sorted(set(contract_prs)))
        add(
            MergeRisk(
                risk_id="MR-DUPLICATED-CONTRACT-" + "-".join(map(str, numbers)),
                severity="P0",
                category="contract",
                summary="Multiple PRs appear to define the shared observation contract.",
                pull_requests=numbers,
                resolution="Keep pg-observation-0.1 fields unchanged; converge on the integration validator and move lane-specific extensions behind versioned adapters.",
            )
        )

    severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    risks.sort(key=lambda item: (severity_order.get(item.severity, 9), item.risk_id))
    counts: dict[str, int] = {}
    for risk in risks:
        counts[risk.severity] = counts.get(risk.severity, 0) + 1
    return {
        "report_version": REPORT_VERSION,
        "valid": True,
        "repository": repository,
        "captured_at": snapshot.get("captured_at"),
        "base_sha": snapshot.get("base_sha"),
        "open_pr_count": len(prs),
        "risk_counts": dict(sorted(counts.items())),
        "risks": [risk.to_dict() for risk in risks],
        "launch_state": (
            "no_open_prs" if not prs else "open_prs_analyzed"
        ),
    }


def analyze_files(
    snapshot_path: str | Path, registry_path: str | Path
) -> dict[str, Any]:
    return analyze_merge_risks(
        load_pr_snapshot(snapshot_path), load_lane_registry(registry_path)
    )
