"""Deterministic NDJSON and payload I/O for the observation contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from .contract_validation import (
    PayloadResolver,
    ValidationResult,
    assert_valid,
    validate_record,
)

def canonical_json_bytes(record: Mapping[str, Any]) -> bytes:
    """Stable UTF-8 JSON bytes used for logical digests and adapter receipts."""

    return json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def record_sha256(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def iter_ndjson(path: str | Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield ``(line_number, record)`` from a UTF-8 NDJSON file."""

    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{file_path}:{line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"{file_path}:{line_number}: each NDJSON line must be an object"
                )
            yield line_number, value


def write_ndjson(
    path: str | Path,
    records: Iterable[Mapping[str, Any]],
    *,
    validate: bool = True,
) -> int:
    """Write deterministic NDJSON and return the number of records written."""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with file_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            if validate:
                assert_valid(record)
            handle.write(canonical_json_bytes(record).decode("utf-8"))
            handle.write("\n")
            count += 1
    return count


def repository_payload_resolver(repo_root: str | Path) -> PayloadResolver:
    """Resolve repository-relative fixture pointers without allowing traversal."""

    root = Path(repo_root).resolve()

    def resolve(pointer: str) -> bytes:
        if "://" in pointer:
            raise ValueError("network or opaque locators are not dereferenced offline")
        candidate = (root / pointer).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("raw_pointer escapes repository root") from exc
        return candidate.read_bytes()

    return resolve


def validate_ndjson(
    path: str | Path,
    *,
    payload_resolver: PayloadResolver | None = None,
) -> dict[str, Any]:
    """Validate a file and return a stable report suitable for CI JSON output."""

    reports: list[dict[str, Any]] = []
    valid_count = 0
    invalid_count = 0
    try:
        records = list(iter_ndjson(path))
    except ValueError as exc:
        return {
            "path": str(path),
            "valid": False,
            "record_count": 0,
            "valid_count": 0,
            "invalid_count": 1,
            "records": [],
            "file_error": str(exc),
        }

    for line_number, record in records:
        result = validate_record(record, payload_resolver=payload_resolver)
        if result.valid:
            valid_count += 1
        else:
            invalid_count += 1
        reports.append({"line": line_number, **result.to_dict()})

    return {
        "path": str(path),
        "valid": invalid_count == 0,
        "record_count": len(reports),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "records": reports,
    }
