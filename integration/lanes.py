"""Lane registry validation and path-ownership helpers."""
from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

REGISTRY_VERSION = "pg-parallel-lanes-0.1"


@dataclass(frozen=True, slots=True)
class RegistryFinding:
    code: str
    message: str
    lane_ids: tuple[int, ...] = ()
    paths: tuple[str, ...] = ()
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "lane_ids": list(self.lane_ids),
            "paths": list(self.paths),
            "severity": self.severity,
        }


def load_lane_registry(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("lane registry root must be an object")
    return value


def _ownership_root(pattern: str) -> str:
    normalized = str(PurePosixPath(pattern.replace("\\", "/"))).lstrip("./")
    while normalized.endswith("/**") or normalized.endswith("/*"):
        normalized = normalized.rsplit("/", 1)[0]
    return normalized.rstrip("/")


def path_matches(pattern: str, path: str) -> bool:
    """Match a repository path against the simple lane ownership grammar."""

    normalized_path = str(PurePosixPath(path.replace("\\", "/"))).lstrip("./")
    normalized_pattern = pattern.replace("\\", "/").lstrip("./")
    if normalized_pattern.endswith("/**"):
        root = normalized_pattern[:-3].rstrip("/")
        return normalized_path == root or normalized_path.startswith(root + "/")
    return fnmatch.fnmatchcase(normalized_path, normalized_pattern)


def owner_for_path(
    registry: Mapping[str, Any], repository: str, path: str
) -> list[Mapping[str, Any]]:
    owners: list[Mapping[str, Any]] = []
    for lane in registry.get("lanes", []):
        if lane.get("repository") != repository:
            continue
        if any(path_matches(pattern, path) for pattern in lane.get("owned_paths", [])):
            owners.append(lane)
    return owners


def validate_lane_registry(registry: Mapping[str, Any]) -> dict[str, Any]:
    findings: list[RegistryFinding] = []
    if registry.get("registry_version") != REGISTRY_VERSION:
        findings.append(
            RegistryFinding(
                "registry.version",
                f"registry_version must equal {REGISTRY_VERSION!r}",
            )
        )

    lanes = registry.get("lanes")
    if not isinstance(lanes, list):
        findings.append(RegistryFinding("registry.lanes", "lanes must be an array"))
        lanes = []

    ids: dict[int, int] = {}
    branches: dict[tuple[str, str], int] = {}
    ownership: list[tuple[str, int, str, str]] = []
    required = {
        "id",
        "name",
        "repository",
        "branch",
        "owned_paths",
        "expected_artifacts",
        "validation_commands",
        "compatibility_seam",
    }
    for index, lane in enumerate(lanes):
        if not isinstance(lane, Mapping):
            findings.append(
                RegistryFinding("lane.type", f"lanes[{index}] must be an object")
            )
            continue
        missing = sorted(required - set(lane))
        if missing:
            findings.append(
                RegistryFinding(
                    "lane.required",
                    f"lane at index {index} is missing {missing}",
                )
            )
            continue
        lane_id = lane["id"]
        if not isinstance(lane_id, int):
            findings.append(
                RegistryFinding("lane.id", f"lanes[{index}].id must be an integer")
            )
            continue
        if lane_id in ids:
            findings.append(
                RegistryFinding(
                    "lane.duplicate_id",
                    f"lane id {lane_id} is duplicated",
                    lane_ids=(ids[lane_id], lane_id),
                )
            )
        ids[lane_id] = lane_id
        key = (str(lane["repository"]), str(lane["branch"]))
        if key in branches:
            findings.append(
                RegistryFinding(
                    "lane.duplicate_branch",
                    f"branch {key[1]!r} is duplicated in {key[0]}",
                    lane_ids=(branches[key], lane_id),
                )
            )
        branches[key] = lane_id
        paths = lane.get("owned_paths", [])
        if not isinstance(paths, list) or not paths:
            findings.append(
                RegistryFinding(
                    "lane.owned_paths",
                    "owned_paths must be a non-empty array",
                    lane_ids=(lane_id,),
                )
            )
            continue
        for pattern in paths:
            root = _ownership_root(str(pattern))
            if not root or root == ".":
                findings.append(
                    RegistryFinding(
                        "lane.root_ownership",
                        "lanes may not own the repository root",
                        lane_ids=(lane_id,),
                        paths=(str(pattern),),
                    )
                )
            ownership.append((str(lane["repository"]), lane_id, str(pattern), root))

    expected_ids = set(range(1, 14))
    if set(ids) != expected_ids:
        findings.append(
            RegistryFinding(
                "registry.expected_lanes",
                f"expected lane IDs 1-13; found {sorted(ids)}",
                lane_ids=tuple(sorted(ids)),
            )
        )

    for index, left in enumerate(ownership):
        left_repo, left_id, left_pattern, left_root = left
        for right in ownership[index + 1 :]:
            right_repo, right_id, right_pattern, right_root = right
            if left_repo != right_repo or left_id == right_id:
                continue
            overlap = (
                left_root == right_root
                or left_root.startswith(right_root + "/")
                or right_root.startswith(left_root + "/")
            )
            if overlap:
                findings.append(
                    RegistryFinding(
                        "lane.path_overlap",
                        f"exclusive ownership overlaps in {left_repo}",
                        lane_ids=(left_id, right_id),
                        paths=(left_pattern, right_pattern),
                    )
                )

    errors = [finding for finding in findings if finding.severity == "error"]
    return {
        "valid": not errors,
        "lane_count": len(lanes),
        "error_count": len(errors),
        "warning_count": len(findings) - len(errors),
        "findings": [finding.to_dict() for finding in findings],
    }


def expected_handoff_path(lane: Mapping[str, Any]) -> str | None:
    for artifact in lane.get("expected_artifacts", []):
        text = str(artifact)
        if text.endswith(".md") and "handoff" in text:
            return text
    for pattern in lane.get("owned_paths", []):
        text = str(pattern)
        if "handoff" in text and not text.endswith("/**"):
            return text
    return None


def lane_by_branch(
    registry: Mapping[str, Any], repository: str, branch: str
) -> Mapping[str, Any] | None:
    for lane in registry.get("lanes", []):
        if lane.get("repository") == repository and lane.get("branch") == branch:
            return lane
    return None


def changed_paths_outside_lane(
    lane: Mapping[str, Any], paths: Iterable[str]
) -> list[str]:
    patterns = [str(pattern) for pattern in lane.get("owned_paths", [])]
    return sorted(
        path
        for path in paths
        if not any(path_matches(pattern, path) for pattern in patterns)
    )
