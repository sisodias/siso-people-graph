"""Common source-receipt and edge helpers for media adapters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from sources.creators.envelope import source_block


@dataclass(frozen=True)
class SourceContext:
    source_id: str
    snapshot_id: str
    observed_at: str
    retrieved_at: str
    terms_revision: str
    rights_state: str
    raw_pointer: str

    def block(self, record_native_id: str, payload: Any) -> dict[str, Any]:
        return source_block(
            source_id=self.source_id,
            snapshot_id=self.snapshot_id,
            record_native_id=record_native_id,
            observed_at=self.observed_at,
            retrieved_at=self.retrieved_at,
            terms_revision=self.terms_revision,
            rights_state=self.rights_state,
            payload=payload,
        )


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def first_text(*values: Any, default: str = "") -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def agent(
    *,
    source_native_id: str,
    label: str,
    kind: str = "unknown",
    identifiers: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source_native_id": source_native_id,
        "label": label,
        "kind": kind,
    }
    if identifiers:
        result["identifiers"] = [dict(item) for item in identifiers]
    return result


def contribution(
    *,
    role: str,
    agent_record: Mapping[str, Any],
    evidence: str,
    order: int | None = None,
    identity_evidence: str = "source_native",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "role": role,
        "agent": dict(agent_record),
        "evidence": evidence,
        "identity_evidence": identity_evidence,
    }
    if order is not None:
        result["order"] = order
    return result


def relationship(
    *,
    predicate: str,
    object_kind: str,
    object_native_id: str,
    object_label: str,
    evidence: str,
    valid_at: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "predicate": predicate,
        "object": {
            "kind": object_kind,
            "source_native_id": object_native_id,
            "label": object_label,
        },
        "evidence": evidence,
    }
    if valid_at:
        result["valid_at"] = valid_at
    return result
