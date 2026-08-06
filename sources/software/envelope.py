"""Shared ``pg-observation-0.1`` envelope helpers.

This module deliberately models source observations only.  It rejects fields that
would turn a source adapter into an identity resolver or universal ranking system.
The functions use only the Python standard library so fixtures remain replayable
from a clean checkout.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ENVELOPE_VERSION = "pg-observation-0.1"
RIGHTS_STATES = {
    "public_metadata",
    "open_data",
    "restricted",
    "discovery_only",
    "pending",
}
SUBJECT_KINDS = {
    "person",
    "organisation",
    "account",
    "work",
    "event",
    "venue",
    "place",
    "concept",
    "claim",
}
SCOPES = {"global", "source", "organisation"}
STABILITIES = {"stable", "mutable", "unknown"}
UNIQUENESS = {"unique", "non_unique", "unknown"}
FORBIDDEN_IDENTIFIER_SCHEMES = {"name", "real_name", "company", "location", "biography", "bio"}
FORBIDDEN_KEYS = {
    "canonical_id",
    "canonical_person_id",
    "canonical_entity_id",
    "merged_into",
    "rank_score",
    "universal_score",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EnvelopeError(ValueError):
    """Raised when an observation envelope violates the interim contract."""


def canonical_json(value: Any) -> str:
    """Return a deterministic, Unicode-preserving JSON representation."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _parse_iso8601(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise EnvelopeError("timestamp must be a non-empty ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EnvelopeError(f"invalid ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise EnvelopeError(f"timestamp lacks an explicit timezone: {value!r}")
    return parsed


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, key
            yield from _walk(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def make_envelope(
    *,
    source_id: str,
    snapshot_id: str,
    record_native_id: str,
    observed_at: str,
    retrieved_at: str,
    terms_revision: str,
    rights_state: str,
    raw_record: Any,
    subject_kind: str,
    subject_native_id: str,
    subject_label: str,
    attributes: Mapping[str, Any] | None = None,
    identifiers: Sequence[Mapping[str, Any]] | None = None,
    contributions: Sequence[Mapping[str, Any]] | None = None,
    relationships: Sequence[Mapping[str, Any]] | None = None,
    evidence: Sequence[Mapping[str, Any]] | None = None,
    raw_pointer: str,
) -> dict[str, Any]:
    """Build and validate one observation envelope.

    ``payload_sha256`` is computed over the replayable raw record, not the
    normalized envelope.  That keeps the observation tied to the exact fixture
    or cached response from which it was derived.
    """

    envelope = {
        "envelope_version": ENVELOPE_VERSION,
        "source": {
            "source_id": source_id,
            "snapshot_id": snapshot_id,
            "record_native_id": record_native_id,
            "observed_at": observed_at,
            "retrieved_at": retrieved_at,
            "terms_revision": terms_revision,
            "rights_state": rights_state,
            "payload_sha256": sha256_json(raw_record),
        },
        "subject": {
            "kind": subject_kind,
            "source_native_id": subject_native_id,
            "label": subject_label,
            "attributes": dict(attributes or {}),
        },
        "identifiers": [dict(item) for item in identifiers or ()],
        "contributions": [dict(item) for item in contributions or ()],
        "relationships": [dict(item) for item in relationships or ()],
        "evidence": [dict(item) for item in evidence or ()],
        "raw_pointer": raw_pointer,
    }
    validate_envelope(envelope)
    return envelope


def validate_identifier(identifier: Mapping[str, Any], index: int) -> None:
    required = {"scheme", "value", "scope", "stability", "uniqueness", "evidence"}
    missing = required - identifier.keys()
    if missing:
        raise EnvelopeError(f"identifier[{index}] missing fields: {sorted(missing)}")
    if identifier["scope"] not in SCOPES:
        raise EnvelopeError(f"identifier[{index}] has invalid scope")
    if identifier["stability"] not in STABILITIES:
        raise EnvelopeError(f"identifier[{index}] has invalid stability")
    if identifier["uniqueness"] not in UNIQUENESS:
        raise EnvelopeError(f"identifier[{index}] has invalid uniqueness")
    if not str(identifier["scheme"]).strip() or not str(identifier["value"]).strip():
        raise EnvelopeError(f"identifier[{index}] scheme/value must be non-empty")
    if not str(identifier["evidence"]).strip():
        raise EnvelopeError(f"identifier[{index}] evidence must be literal and non-empty")
    if str(identifier["scheme"]).strip().lower() in FORBIDDEN_IDENTIFIER_SCHEMES:
        raise EnvelopeError(
            f"identifier[{index}] uses a non-identifier attribute scheme: {identifier['scheme']!r}"
        )


def validate_envelope(envelope: Mapping[str, Any]) -> None:
    top_required = {
        "envelope_version",
        "source",
        "subject",
        "identifiers",
        "contributions",
        "relationships",
        "evidence",
        "raw_pointer",
    }
    missing = top_required - envelope.keys()
    if missing:
        raise EnvelopeError(f"envelope missing fields: {sorted(missing)}")
    if envelope["envelope_version"] != ENVELOPE_VERSION:
        raise EnvelopeError("unsupported envelope version")

    source = envelope["source"]
    source_required = {
        "source_id",
        "snapshot_id",
        "record_native_id",
        "observed_at",
        "retrieved_at",
        "terms_revision",
        "rights_state",
        "payload_sha256",
    }
    source_missing = source_required - source.keys()
    if source_missing:
        raise EnvelopeError(f"source missing fields: {sorted(source_missing)}")
    for field in ("source_id", "snapshot_id", "record_native_id", "terms_revision"):
        if not str(source[field]).strip():
            raise EnvelopeError(f"source.{field} must be non-empty")
    if source["rights_state"] not in RIGHTS_STATES:
        raise EnvelopeError(f"invalid rights_state: {source['rights_state']!r}")
    if not _SHA256_RE.fullmatch(str(source["payload_sha256"])):
        raise EnvelopeError("payload_sha256 must be lowercase hexadecimal SHA-256")
    observed_at = _parse_iso8601(str(source["observed_at"]))
    retrieved_at = _parse_iso8601(str(source["retrieved_at"]))
    if retrieved_at < observed_at:
        raise EnvelopeError("source.retrieved_at cannot precede source.observed_at")

    subject = envelope["subject"]
    subject_required = {"kind", "source_native_id", "label", "attributes"}
    subject_missing = subject_required - subject.keys()
    if subject_missing:
        raise EnvelopeError(f"subject missing fields: {sorted(subject_missing)}")
    if subject["kind"] not in SUBJECT_KINDS:
        raise EnvelopeError(f"invalid subject kind: {subject['kind']!r}")
    if not str(subject["source_native_id"]).strip():
        raise EnvelopeError("subject source_native_id must be non-empty")

    identifiers = envelope["identifiers"]
    if not isinstance(identifiers, list):
        raise EnvelopeError("identifiers must be a list")
    for index, identifier in enumerate(identifiers):
        validate_identifier(identifier, index)

    for collection in ("contributions", "relationships", "evidence"):
        if not isinstance(envelope[collection], list):
            raise EnvelopeError(f"{collection} must be a list")

    for index, contribution in enumerate(envelope["contributions"]):
        if not isinstance(contribution, Mapping):
            raise EnvelopeError(f"contribution[{index}] must be an object")
        required = {"role", "agent", "observed_at"}
        missing = required - contribution.keys()
        if missing:
            raise EnvelopeError(f"contribution[{index}] missing fields: {sorted(missing)}")
        if not str(contribution["role"]).strip():
            raise EnvelopeError(f"contribution[{index}].role must be non-empty")
        _parse_iso8601(str(contribution["observed_at"]))
        agent = contribution["agent"]
        if not isinstance(agent, Mapping):
            raise EnvelopeError(f"contribution[{index}].agent must be an object")
        agent_required = {"kind", "source_native_id", "label"}
        agent_missing = agent_required - agent.keys()
        if agent_missing:
            raise EnvelopeError(
                f"contribution[{index}].agent missing fields: {sorted(agent_missing)}"
            )
        if agent["kind"] not in {"person", "organisation", "account"}:
            raise EnvelopeError(f"contribution[{index}].agent has invalid kind")
        if not str(agent["source_native_id"]).strip():
            raise EnvelopeError(f"contribution[{index}].agent source_native_id must be non-empty")
        nested_identifiers = agent.get("identifiers", [])
        if not isinstance(nested_identifiers, list):
            raise EnvelopeError(f"contribution[{index}].agent.identifiers must be a list")
        for nested_index, identifier in enumerate(nested_identifiers):
            validate_identifier(identifier, nested_index)

    for index, relationship in enumerate(envelope["relationships"]):
        if not isinstance(relationship, Mapping):
            raise EnvelopeError(f"relationship[{index}] must be an object")
        required = {"predicate", "object", "observed_at", "evidence"}
        missing = required - relationship.keys()
        if missing:
            raise EnvelopeError(f"relationship[{index}] missing fields: {sorted(missing)}")
        if not str(relationship["predicate"]).strip():
            raise EnvelopeError(f"relationship[{index}].predicate must be non-empty")
        if not str(relationship["evidence"]).strip():
            raise EnvelopeError(f"relationship[{index}].evidence must be non-empty")
        _parse_iso8601(str(relationship["observed_at"]))
        obj = relationship["object"]
        if not isinstance(obj, Mapping):
            raise EnvelopeError(f"relationship[{index}].object must be an object")
        object_required = {"kind", "source_native_id", "label"}
        object_missing = object_required - obj.keys()
        if object_missing:
            raise EnvelopeError(
                f"relationship[{index}].object missing fields: {sorted(object_missing)}"
            )
        if obj["kind"] not in SUBJECT_KINDS:
            raise EnvelopeError(f"relationship[{index}].object has invalid kind")
        if not str(obj["source_native_id"]).strip():
            raise EnvelopeError(f"relationship[{index}].object source_native_id must be non-empty")
        valid_time = relationship.get("valid_time", {})
        if valid_time is not None:
            if not isinstance(valid_time, Mapping):
                raise EnvelopeError(f"relationship[{index}].valid_time must be an object")
            for field in ("at", "from", "to"):
                if valid_time.get(field):
                    _parse_iso8601(str(valid_time[field]))

    for index, evidence_item in enumerate(envelope["evidence"]):
        if not isinstance(evidence_item, Mapping):
            raise EnvelopeError(f"evidence[{index}] must be an object")
        required = {"kind", "locator", "observed_at"}
        missing = required - evidence_item.keys()
        if missing:
            raise EnvelopeError(f"evidence[{index}] missing fields: {sorted(missing)}")
        if not str(evidence_item["kind"]).strip() or not str(evidence_item["locator"]).strip():
            raise EnvelopeError(f"evidence[{index}] kind/locator must be non-empty")
        _parse_iso8601(str(evidence_item["observed_at"]))

    if not str(envelope["raw_pointer"]).strip():
        raise EnvelopeError("raw_pointer must be non-empty")

    for path, key in _walk(envelope):
        if key in FORBIDDEN_KEYS:
            raise EnvelopeError(f"forbidden canonical/ranking field at {path}")

    metrics = subject["attributes"].get("metrics", [])
    if metrics and not isinstance(metrics, list):
        raise EnvelopeError("subject.attributes.metrics must be a list")
    for index, metric in enumerate(metrics):
        if not {"name", "value", "observed_at"} <= metric.keys():
            raise EnvelopeError(f"metric[{index}] must include name, value, observed_at")
        _parse_iso8601(str(metric["observed_at"]))


def sort_key(envelope: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(envelope["source"]["source_id"]),
        str(envelope["source"]["record_native_id"]),
        str(envelope["subject"]["source_native_id"]),
        str(envelope["source"]["payload_sha256"]),
    )


def write_ndjson(records: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted((dict(record) for record in records), key=sort_key)
    for record in ordered:
        validate_envelope(record)
    text = "".join(canonical_json(record) + "\n" for record in ordered)
    destination.write_text(text, encoding="utf-8")


def read_ndjson(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        try:
            validate_envelope(record)
        except EnvelopeError as exc:
            raise EnvelopeError(f"{path}:{line_number}: {exc}") from exc
        records.append(record)
    return records
