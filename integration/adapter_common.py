"""Shared adapter types plus observation and Book NDJSON adapters.

Adapters never resolve identities.  Source observations and identity decisions
have separate iterators so an accepted decision cannot mutate or overwrite the
facts that caused it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Iterator, Mapping, Sequence
from urllib.parse import quote

from .contract import (
    ENVELOPE_VERSION,
    ContractValidationError,
    assert_valid,
    canonical_json_bytes,
    iter_ndjson,
    validate_record,
    write_ndjson,
)


class AdapterError(RuntimeError):
    """Base adapter failure."""


class UnsupportedAdapterError(AdapterError):
    """The detected schema does not expose a supported compatibility seam."""


@dataclass(frozen=True, slots=True)
class SourcePolicy:
    """Source metadata absent from legacy rows but required by the envelope.

    A caller should pass exact source metadata when known.  Defaults are
    deliberately explicit compatibility gaps rather than invented snapshots or
    rights claims.
    """

    snapshot_id: str = "legacy-v2-unrecorded"
    terms_revision: str = "documented-unknown"
    rights_state: str = "pending"
    retrieved_at: str | None = None


@dataclass(frozen=True, slots=True)
class IdentityDecision:
    """Identity decision emitted separately from source observations."""

    decision_native_id: str
    left_source_locator: str
    right_source_locator: str
    method: str
    confidence: float
    evidence: str
    status: str
    decided_by: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AdapterCapabilities:
    adapter: str
    schema_family: str
    observations: str
    identities: str
    works_roles: str
    topics: str
    rights: str
    claims: str
    evidence: tuple[str, ...]
    gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence"] = list(self.evidence)
        value["gaps"] = list(self.gaps)
        return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _coerce_time(value: Any, fallback: str | None = None) -> str:
    if isinstance(value, str) and value.strip():
        candidate = value.strip()
        if candidate.endswith("Z") or "+" in candidate[10:] or candidate.count("-") > 2:
            return candidate
        # SQLite rows commonly store a date only.  Retain the literal date while
        # making timezone semantics explicit for the exchange contract.
        if len(candidate) == 10:
            return candidate + "T00:00:00Z"
        return candidate + "Z"
    if fallback:
        return _coerce_time(fallback)
    # This timestamp is used only when a synthetic test/compatibility row has no
    # recorded time.  The evidence block names the gap.
    return "1970-01-01T00:00:00Z"


def _stable_row_bytes(table: str, row: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes({"table": table, "row": dict(row)})


def _row_hash(table: str, row: Mapping[str, Any]) -> str:
    return hashlib.sha256(_stable_row_bytes(table, row)).hexdigest()


def _legacy_person_locator(value: str) -> str:
    return "legacy-v2-person/" + quote(value, safe="")


def _identifier_semantics(platform: str) -> tuple[str, str, str]:
    key = platform.strip().lower().replace("-", "_")
    global_stable = {
        "orcid",
        "viaf",
        "isni",
        "wikidata",
        "loc_authority",
        "library_of_congress",
        "ror",
    }
    source_stable = {
        "github_id",
        "github_numeric_id",
        "github_user_id",
        "github_node_id",
        "youtube_channel_id",
        "openalex_author_id",
        "dblp_pid",
        "software_heritage_id",
    }
    mutable_aliases = {
        "github_login",
        "x_handle",
        "reddit_user",
        "mastodon_handle",
        "bluesky_handle",
        "youtube_handle",
        "username",
        "login",
        "handle",
    }
    if key in global_stable:
        return "global", "stable", "unique"
    if key in source_stable:
        return "source", "stable", "unique"
    if key in mutable_aliases:
        return "source", "mutable", "unknown"
    return "source", "unknown", "unknown"


def _connect_read_only(path: str | Path) -> sqlite3.Connection:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    con = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def sqlite_tables(path: str | Path) -> set[str]:
    with _connect_read_only(path) as con:
        return {
            str(row[0])
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            )
        }


class NDJSONObservationAdapter:
    """Adapter for source-pilot NDJSON using the shared observation envelope."""

    def __init__(self, path: str | Path, *, validate: bool = True):
        self.path = Path(path)
        self.validate = validate

    def iter_observations(self) -> Iterator[dict[str, Any]]:
        for line_number, record in iter_ndjson(self.path):
            if self.validate:
                result = validate_record(record)
                if not result.valid:
                    raise ContractValidationError(result)
            # json.loads produced a fresh object; callers may mutate it without
            # altering a hidden cache inside the adapter.
            yield record

    def iter_identity_decisions(self) -> Iterator[IdentityDecision]:
        # The envelope is an observation contract and carries no accepted
        # canonical decisions.  Identity-like relationships remain review-only.
        return iter(())

    def export(self, path: str | Path) -> int:
        return write_ndjson(path, self.iter_observations(), validate=self.validate)

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter=self.__class__.__name__,
            schema_family=ENVELOPE_VERSION,
            observations="present",
            identities="separate/not-present",
            works_roles="preserved when supplied",
            topics="preserved when supplied",
            rights="required per record",
            claims="observation-only",
            evidence=(str(self.path),),
            gaps=(),
        )


class BookLibraryObservationAdapter(NDJSONObservationAdapter):
    """Semantic alias for Book Library exports.

    The Book lane exports the same envelope as source pilots.  This adapter does
    not invent a second Book-specific ontology; it adds an inspectable summary
    useful during merge review.
    """

    def summary(self) -> dict[str, Any]:
        count = 0
        kinds: dict[str, int] = {}
        roles: dict[str, int] = {}
        source_ids: set[str] = set()
        rights_states: set[str] = set()
        for record in self.iter_observations():
            count += 1
            kind = str(record["subject"]["kind"])
            kinds[kind] = kinds.get(kind, 0) + 1
            source_ids.add(str(record["source"]["source_id"]))
            rights_states.add(str(record["source"]["rights_state"]))
            for contribution in record.get("contributions", []):
                role = str(contribution.get("role", "unknown"))
                roles[role] = roles.get(role, 0) + 1
        return {
            "records": count,
            "subject_kinds": dict(sorted(kinds.items())),
            "roles": dict(sorted(roles.items())),
            "source_ids": sorted(source_ids),
            "rights_states": sorted(rights_states),
        }


