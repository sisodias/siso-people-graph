"""Shared ``pg-observation-0.1`` envelope helpers.

This module is deliberately independent of the current People Graph schema.  It
validates source observations and refuses canonical identity fields, so media
adapters can be reviewed and replayed without silently resolving people.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

ENVELOPE_VERSION = "pg-observation-0.1"
ALLOWED_SUBJECT_KINDS = {
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
ALLOWED_RIGHTS_STATES = {
    "public_metadata",
    "open_data",
    "restricted",
    "discovery_only",
    "pending",
}
ALLOWED_SCOPES = {"global", "source", "organisation"}
ALLOWED_STABILITY = {"stable", "mutable", "unknown"}
ALLOWED_UNIQUENESS = {"unique", "non_unique", "unknown"}

# These values may be useful source observations, but they must never be
# represented as globally unique identity keys.
NON_GLOBAL_IDENTIFIER_SCHEMES = {
    "name",
    "display_name",
    "real_name",
    "company",
    "employer",
    "location",
    "biography",
    "topic",
    "handle",
    "username",
    "youtube_handle",
    "podcast_person_name",
}
CANONICAL_FIELD_NAMES = {
    "canonical_id",
    "canonical_person_id",
    "people_graph_id",
    "person_id",
    "merged_into",
    "cluster_id",
    "resolved_identity",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EnvelopeError(ValueError):
    """Raised when an observation violates the exchange contract."""


def canonical_json(value: Any) -> str:
    """Return stable JSON suitable for content hashing and deterministic NDJSON."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def payload_sha256(payload: bytes | str | Mapping[str, Any] | Sequence[Any]) -> str:
    """Hash the replayable source payload, not the derived envelope."""

    if isinstance(payload, bytes):
        raw = payload
    elif isinstance(payload, str):
        raw = payload.encode("utf-8")
    else:
        raw = canonical_json(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def source_block(
    *,
    source_id: str,
    snapshot_id: str,
    record_native_id: str,
    observed_at: str,
    retrieved_at: str,
    terms_revision: str,
    rights_state: str,
    payload: bytes | str | Mapping[str, Any] | Sequence[Any],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "snapshot_id": snapshot_id,
        "record_native_id": record_native_id,
        "observed_at": observed_at,
        "retrieved_at": retrieved_at,
        "terms_revision": terms_revision,
        "rights_state": rights_state,
        "payload_sha256": payload_sha256(payload),
    }


def identifier(
    *,
    scheme: str,
    value: str,
    scope: str,
    stability: str,
    uniqueness: str,
    evidence: str,
) -> dict[str, str]:
    return {
        "scheme": scheme,
        "value": value,
        "scope": scope,
        "stability": stability,
        "uniqueness": uniqueness,
        "evidence": evidence,
    }


def evidence(
    *,
    kind: str,
    locator: str,
    literal: str | None = None,
    source_field: str | None = None,
    inference: bool = False,
    model: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact evidence receipt.

    A model-generated classification is permitted only when ``inference`` is
    true and the model/version/input digest is explicit.
    """

    item: dict[str, Any] = {"kind": kind, "locator": locator, "inference": inference}
    if literal is not None:
        item["literal"] = literal
    if source_field is not None:
        item["source_field"] = source_field
    if model is not None:
        item["model"] = dict(model)
    return item


def make_envelope(
    *,
    source: Mapping[str, Any],
    subject_kind: str,
    subject_native_id: str,
    label: str,
    attributes: Mapping[str, Any] | None = None,
    identifiers: Sequence[Mapping[str, Any]] | None = None,
    contributions: Sequence[Mapping[str, Any]] | None = None,
    relationships: Sequence[Mapping[str, Any]] | None = None,
    evidence_items: Sequence[Mapping[str, Any]] | None = None,
    raw_pointer: str,
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "envelope_version": ENVELOPE_VERSION,
        "source": dict(source),
        "subject": {
            "kind": subject_kind,
            "source_native_id": subject_native_id,
            "label": label,
            "attributes": dict(attributes or {}),
        },
        "identifiers": [dict(item) for item in (identifiers or [])],
        "contributions": [dict(item) for item in (contributions or [])],
        "relationships": [dict(item) for item in (relationships or [])],
        "evidence": [dict(item) for item in (evidence_items or [])],
        "raw_pointer": raw_pointer,
    }
    validate_envelope(envelope)
    return envelope


def _require(mapping: Mapping[str, Any], keys: Iterable[str], path: str) -> None:
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise EnvelopeError(f"{path} missing required fields: {', '.join(missing)}")


def _validate_iso8601(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value:
        raise EnvelopeError(f"{path} must be a non-empty ISO-8601 string")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise EnvelopeError(f"{path} is not valid ISO-8601: {value!r}") from exc


def _walk_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower()
            if normalized in CANONICAL_FIELD_NAMES:
                raise EnvelopeError(
                    f"{path}.{key} is forbidden: observations never assign canonical identity"
                )
            _walk_forbidden(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _walk_forbidden(nested, f"{path}[{index}]")


def _validate_identifiers(value: Any, path: str) -> None:
    if not isinstance(value, list):
        raise EnvelopeError(f"{path} must be an array")
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, Mapping):
            raise EnvelopeError(f"{item_path} must be an object")
        _require(
            item,
            ["scheme", "value", "scope", "stability", "uniqueness", "evidence"],
            item_path,
        )
        for field in ("scheme", "value", "evidence"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise EnvelopeError(f"{item_path}.{field} must be a non-empty string")
        if item["scope"] not in ALLOWED_SCOPES:
            raise EnvelopeError(f"{item_path}.scope is invalid")
        if item["stability"] not in ALLOWED_STABILITY:
            raise EnvelopeError(f"{item_path}.stability is invalid")
        if item["uniqueness"] not in ALLOWED_UNIQUENESS:
            raise EnvelopeError(f"{item_path}.uniqueness is invalid")
        scheme = item["scheme"].lower()
        if scheme in NON_GLOBAL_IDENTIFIER_SCHEMES and item["scope"] == "global":
            raise EnvelopeError(
                f"{item_path}: {scheme!r} is an observation/alias, never a global identifier"
            )
        key = (scheme, item["value"], item["scope"])
        if key in seen:
            raise EnvelopeError(f"{item_path} duplicates identifier {key!r}")
        seen.add(key)


def validate_envelope(envelope: Mapping[str, Any]) -> None:
    """Validate a single ``pg-observation-0.1`` record.

    The validator is intentionally stricter than JSON syntax.  It guards the
    identity and rights invariants most likely to be lost when adapters are
    developed independently.
    """

    _walk_forbidden(envelope)
    _require(
        envelope,
        [
            "envelope_version",
            "source",
            "subject",
            "identifiers",
            "contributions",
            "relationships",
            "evidence",
            "raw_pointer",
        ],
        "$",
    )
    if envelope["envelope_version"] != ENVELOPE_VERSION:
        raise EnvelopeError(
            f"unsupported envelope_version: {envelope['envelope_version']!r}"
        )

    source = envelope["source"]
    if not isinstance(source, Mapping):
        raise EnvelopeError("$.source must be an object")
    _require(
        source,
        [
            "source_id",
            "snapshot_id",
            "record_native_id",
            "observed_at",
            "retrieved_at",
            "terms_revision",
            "rights_state",
            "payload_sha256",
        ],
        "$.source",
    )
    for field in ("source_id", "snapshot_id", "record_native_id", "terms_revision"):
        if not isinstance(source[field], str) or not source[field].strip():
            raise EnvelopeError(f"$.source.{field} must be a non-empty string")
    _validate_iso8601(source["observed_at"], "$.source.observed_at")
    _validate_iso8601(source["retrieved_at"], "$.source.retrieved_at")
    if source["rights_state"] not in ALLOWED_RIGHTS_STATES:
        raise EnvelopeError(
            f"$.source.rights_state must be one of {sorted(ALLOWED_RIGHTS_STATES)}"
        )
    digest = source["payload_sha256"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise EnvelopeError("$.source.payload_sha256 must be lowercase sha256 hex")

    subject = envelope["subject"]
    if not isinstance(subject, Mapping):
        raise EnvelopeError("$.subject must be an object")
    _require(subject, ["kind", "source_native_id", "label", "attributes"], "$.subject")
    if subject["kind"] not in ALLOWED_SUBJECT_KINDS:
        raise EnvelopeError(f"unsupported subject kind: {subject['kind']!r}")
    if not isinstance(subject["source_native_id"], str) or not subject[
        "source_native_id"
    ].strip():
        raise EnvelopeError("$.subject.source_native_id must be a non-empty string")
    if not isinstance(subject["label"], str):
        raise EnvelopeError("$.subject.label must be a string")
    if not isinstance(subject["attributes"], Mapping):
        raise EnvelopeError("$.subject.attributes must be an object")

    _validate_identifiers(envelope["identifiers"], "$.identifiers")

    for list_name in ("contributions", "relationships", "evidence"):
        if not isinstance(envelope[list_name], list):
            raise EnvelopeError(f"$.{list_name} must be an array")

    for index, item in enumerate(envelope["contributions"]):
        path = f"$.contributions[{index}]"
        if not isinstance(item, Mapping):
            raise EnvelopeError(f"{path} must be an object")
        _require(item, ["role", "agent", "evidence"], path)
        for field in ("role", "evidence"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise EnvelopeError(f"{path}.{field} must be a non-empty string")
        if not isinstance(item["agent"], Mapping):
            raise EnvelopeError(f"{path}.agent must be an object")
        agent = item["agent"]
        _require(agent, ["source_native_id", "label"], f"{path}.agent")
        for field in ("source_native_id", "label"):
            if not isinstance(agent[field], str) or not agent[field].strip():
                raise EnvelopeError(f"{path}.agent.{field} must be a non-empty string")
        if "kind" in agent and agent["kind"] not in ALLOWED_SUBJECT_KINDS | {"unknown"}:
            raise EnvelopeError(f"{path}.agent.kind is invalid")
        if "identifiers" in agent:
            _validate_identifiers(agent["identifiers"], f"{path}.agent.identifiers")

    for index, item in enumerate(envelope["relationships"]):
        if not isinstance(item, Mapping):
            raise EnvelopeError(f"$.relationships[{index}] must be an object")
        _require(
            item,
            ["predicate", "object", "evidence"],
            f"$.relationships[{index}]",
        )

    for index, item in enumerate(envelope["evidence"]):
        path = f"$.evidence[{index}]"
        if not isinstance(item, Mapping):
            raise EnvelopeError(f"{path} must be an object")
        _require(item, ["kind", "locator", "inference"], path)
        if item.get("model") is not None and not item.get("inference"):
            raise EnvelopeError(f"{path}: model evidence must be marked as inference")
        if item.get("inference") and item.get("model") is not None:
            model = item["model"]
            if not isinstance(model, Mapping):
                raise EnvelopeError(f"{path}.model must be an object")
            _require(model, ["name", "version", "input_sha256"], f"{path}.model")
            for field in ("name", "version"):
                if not isinstance(model[field], str) or not model[field].strip():
                    raise EnvelopeError(f"{path}.model.{field} must be a non-empty string")
            if not isinstance(model["input_sha256"], str) or not _SHA256_RE.fullmatch(
                model["input_sha256"]
            ):
                raise EnvelopeError(f"{path}.model.input_sha256 must be lowercase sha256 hex")

    if not isinstance(envelope["raw_pointer"], str) or not envelope[
        "raw_pointer"
    ].strip():
        raise EnvelopeError("$.raw_pointer must be a non-empty string")


def write_ndjson(records: Iterable[Mapping[str, Any]], destination: Path | str) -> int:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            validate_envelope(record)
            handle.write(canonical_json(record))
            handle.write("\n")
            count += 1
    return count


def read_ndjson(source: Path | str) -> list[dict[str, Any]]:
    path = Path(source)
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise EnvelopeError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            validate_envelope(record)
            records.append(record)
    return records


def strip_unlicensed_payload(
    envelope: MutableMapping[str, Any], *, keep_attribute_keys: Iterable[str]
) -> MutableMapping[str, Any]:
    """Drop attributes not explicitly allowed by the source method card.

    This is used for restricted APIs whose metadata may be cached only within a
    documented retention window.  Identifiers, evidence locators and provenance
    remain; arbitrary descriptions, transcript text, thumbnails and media bytes
    do not.
    """

    allowed = set(keep_attribute_keys)
    attributes = envelope.get("subject", {}).get("attributes", {})
    if isinstance(attributes, MutableMapping):
        for key in list(attributes):
            if key not in allowed:
                del attributes[key]
    validate_envelope(envelope)
    return envelope
