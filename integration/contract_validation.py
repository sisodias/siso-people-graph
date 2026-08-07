"""Semantic validator implementation for ``pg-observation-0.1``."""
from __future__ import annotations

from datetime import datetime
import hashlib
from typing import Any, Iterator, Mapping, Sequence

from .contract_model import (
    ALLOWED_IDENTITY_REVIEW_STATES,
    ATTRIBUTE_ONLY_SCHEMES,
    ContractValidationError,
    ENVELOPE_VERSION,
    FORBIDDEN_CANONICAL_KEYS,
    FORBIDDEN_MERGE_KEYS,
    HANDLE_SCHEMES,
    IDENTIFIER_SCOPES,
    IDENTIFIER_STABILITIES,
    IDENTIFIER_UNIQUENESS,
    IDENTITY_RELATION_TYPES,
    NAME_ONLY_METHODS,
    PayloadResolver,
    RIGHTS_STATES,
    SUBJECT_KINDS,
    ValidationIssue,
    ValidationResult,
    _PRIVATE_POINTER_PATTERNS,
    _SHA256_RE,
)

def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _require_mapping(
    value: Any, path: str, result: ValidationResult
) -> Mapping[str, Any] | None:
    if not _is_mapping(value):
        result.add("type.mapping", path, "must be an object")
        return None
    return value


def _require_list(
    value: Any, path: str, result: ValidationResult
) -> Sequence[Any] | None:
    if not isinstance(value, list):
        result.add("type.list", path, "must be an array")
        return None
    return value


def _require_text(
    mapping: Mapping[str, Any], key: str, path: str, result: ValidationResult
) -> str | None:
    value = mapping.get(key)
    item_path = f"{path}.{key}"
    if not isinstance(value, str) or not value.strip():
        result.add("required.text", item_path, "must be a non-empty string")
        return None
    return value


def _validate_iso8601(value: str | None, path: str, result: ValidationResult) -> None:
    if value is None:
        return
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        result.add("format.iso8601", path, "must be an ISO-8601 timestamp")
        return
    if parsed.tzinfo is None:
        result.add(
            "format.timezone",
            path,
            "must include a timezone offset or Z",
        )


def _walk_keys(value: Any, path: str = "$") -> Iterator[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            yield key_text, child_path, child
            yield from _walk_keys(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield from _walk_keys(child, child_path)


def _validate_no_canonical_fields(record: Mapping[str, Any], result: ValidationResult) -> None:
    for key, path, _ in _walk_keys(record):
        normalised = key.strip().lower()
        canonical_key = (
            normalised in FORBIDDEN_CANONICAL_KEYS
            or normalised.startswith("canonical_")
            or normalised.endswith("_canonical_id")
        )
        if canonical_key:
            result.add(
                "identity.canonical_id_forbidden",
                path,
                "observation envelopes must not assign or carry canonical People Graph IDs",
            )
        if normalised in FORBIDDEN_MERGE_KEYS:
            result.add(
                "identity.merge_directive_forbidden",
                path,
                "observation envelopes cannot direct automatic identity merging",
            )


def _validate_identifier(
    identifier: Any, index: int, result: ValidationResult
) -> None:
    path = f"$.identifiers[{index}]"
    mapping = _require_mapping(identifier, path, result)
    if mapping is None:
        return

    scheme = _require_text(mapping, "scheme", path, result)
    _require_text(mapping, "value", path, result)
    scope = _require_text(mapping, "scope", path, result)
    stability = _require_text(mapping, "stability", path, result)
    uniqueness = _require_text(mapping, "uniqueness", path, result)
    _require_text(mapping, "evidence", path, result)

    if scope and scope not in IDENTIFIER_SCOPES:
        result.add(
            "identifier.scope",
            f"{path}.scope",
            f"must be one of {sorted(IDENTIFIER_SCOPES)}",
        )
    if stability and stability not in IDENTIFIER_STABILITIES:
        result.add(
            "identifier.stability",
            f"{path}.stability",
            f"must be one of {sorted(IDENTIFIER_STABILITIES)}",
        )
    if uniqueness and uniqueness not in IDENTIFIER_UNIQUENESS:
        result.add(
            "identifier.uniqueness",
            f"{path}.uniqueness",
            f"must be one of {sorted(IDENTIFIER_UNIQUENESS)}",
        )

    if scheme:
        scheme_key = scheme.strip().lower().replace("-", "_")
        if scheme_key in ATTRIBUTE_ONLY_SCHEMES:
            result.add(
                "identifier.attribute_promoted",
                f"{path}.scheme",
                f"{scheme!r} is an attribute, not an identifier scheme",
            )
        if scheme_key in HANDLE_SCHEMES:
            if scope == "global":
                result.add(
                    "identifier.handle_global",
                    f"{path}.scope",
                    "handles/logins are source-scoped aliases, never global identifiers",
                )
            if stability == "stable":
                result.add(
                    "identifier.handle_stable",
                    f"{path}.stability",
                    "handles/logins are mutable aliases",
                )
            if uniqueness == "unique":
                result.add(
                    "identifier.handle_unique",
                    f"{path}.uniqueness",
                    "handles/logins may be renamed or reused and cannot be declared universally unique",
                )


def _normalised_relation_type(mapping: Mapping[str, Any]) -> str:
    value = mapping.get("type", mapping.get("predicate", ""))
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _validate_relationship(
    relationship: Any, index: int, result: ValidationResult
) -> None:
    path = f"$.relationships[{index}]"
    mapping = _require_mapping(relationship, path, result)
    if mapping is None:
        return

    relation_type = _normalised_relation_type(mapping)
    if not relation_type:
        result.add(
            "relationship.type",
            path,
            "relationship objects must include a non-empty type or predicate",
        )
        return

    if relation_type not in IDENTITY_RELATION_TYPES:
        return

    state = str(mapping.get("review_state", mapping.get("status", ""))).strip().lower()
    if state not in ALLOWED_IDENTITY_REVIEW_STATES:
        result.add(
            "identity.relationship_not_review_only",
            f"{path}.review_state",
            "identity-like source relationships must remain observed/proposed/review-only, never accepted or resolved",
        )

    method = str(mapping.get("method", mapping.get("match_method", ""))).strip().lower()
    basis = mapping.get("basis", mapping.get("match_basis", []))
    if isinstance(basis, str):
        basis_values = {basis.strip().lower()}
    elif isinstance(basis, list):
        basis_values = {str(item).strip().lower() for item in basis}
    else:
        basis_values = set()

    evidence = mapping.get("evidence")
    evidence_present = bool(evidence)
    name_only = method in NAME_ONLY_METHODS or (
        basis_values and basis_values.issubset(NAME_ONLY_METHODS)
    )
    if name_only or not evidence_present:
        result.add(
            "identity.name_only_merge",
            path,
            "identity relationships require literal non-name evidence and remain review-only",
        )


def _validate_collection_of_objects(
    value: Any, path: str, result: ValidationResult
) -> None:
    items = _require_list(value, path, result)
    if items is None:
        return
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            result.add(
                "type.object_item",
                f"{path}[{index}]",
                "must be an object",
            )


def _validate_raw_pointer(pointer: str | None, result: ValidationResult) -> None:
    if pointer is None:
        return
    for pattern in _PRIVATE_POINTER_PATTERNS:
        if pattern.search(pointer):
            result.add(
                "pointer.private_path",
                "$.raw_pointer",
                "must be a repository-relative path, public locator, or content-addressed receipt—not a private absolute path",
            )
            break


def validate_record(
    record: Any,
    *,
    payload_resolver: PayloadResolver | None = None,
) -> ValidationResult:
    """Validate one observation record.

    ``payload_resolver`` is optional because many pilots retain raw payloads
    outside Git.  When supplied it receives ``raw_pointer`` and must return the
    exact bytes whose SHA-256 is declared in ``source.payload_sha256``.
    """

    result = ValidationResult()
    root = _require_mapping(record, "$", result)
    if root is None:
        return result

    version = _require_text(root, "envelope_version", "$", result)
    if version and version != ENVELOPE_VERSION:
        result.add(
            "envelope.version",
            "$.envelope_version",
            f"must equal {ENVELOPE_VERSION!r}",
        )

    source = _require_mapping(root.get("source"), "$.source", result)
    payload_hash: str | None = None
    if source is not None:
        _require_text(source, "source_id", "$.source", result)
        _require_text(source, "snapshot_id", "$.source", result)
        _require_text(source, "record_native_id", "$.source", result)
        observed_at = _require_text(source, "observed_at", "$.source", result)
        retrieved_at = _require_text(source, "retrieved_at", "$.source", result)
        _require_text(source, "terms_revision", "$.source", result)
        rights_state = _require_text(source, "rights_state", "$.source", result)
        payload_hash = _require_text(source, "payload_sha256", "$.source", result)

        _validate_iso8601(observed_at, "$.source.observed_at", result)
        _validate_iso8601(retrieved_at, "$.source.retrieved_at", result)
        if rights_state and rights_state not in RIGHTS_STATES:
            result.add(
                "rights.state",
                "$.source.rights_state",
                f"must be one of {sorted(RIGHTS_STATES)}",
            )
        if payload_hash and not _SHA256_RE.fullmatch(payload_hash):
            result.add(
                "payload.sha256",
                "$.source.payload_sha256",
                "must be exactly 64 lowercase hexadecimal characters",
            )

    subject = _require_mapping(root.get("subject"), "$.subject", result)
    if subject is not None:
        kind = _require_text(subject, "kind", "$.subject", result)
        _require_text(subject, "source_native_id", "$.subject", result)
        _require_text(subject, "label", "$.subject", result)
        attributes = subject.get("attributes")
        if not isinstance(attributes, Mapping):
            result.add(
                "subject.attributes",
                "$.subject.attributes",
                "must be an object (use an empty object when no attributes are observed)",
            )
        if kind and kind not in SUBJECT_KINDS:
            result.add(
                "subject.kind",
                "$.subject.kind",
                f"must be one of {sorted(SUBJECT_KINDS)}",
            )

    identifiers = _require_list(root.get("identifiers"), "$.identifiers", result)
    if identifiers is not None:
        for index, identifier in enumerate(identifiers):
            _validate_identifier(identifier, index, result)

    _validate_collection_of_objects(root.get("contributions"), "$.contributions", result)

    relationships = _require_list(root.get("relationships"), "$.relationships", result)
    if relationships is not None:
        for index, relationship in enumerate(relationships):
            _validate_relationship(relationship, index, result)

    _validate_collection_of_objects(root.get("evidence"), "$.evidence", result)

    raw_pointer = _require_text(root, "raw_pointer", "$", result)
    _validate_raw_pointer(raw_pointer, result)

    _validate_no_canonical_fields(root, result)

    if (
        payload_resolver is not None
        and raw_pointer is not None
        and payload_hash is not None
        and _SHA256_RE.fullmatch(payload_hash)
    ):
        try:
            payload = payload_resolver(raw_pointer)
        except (OSError, KeyError, ValueError) as exc:
            result.add(
                "payload.unavailable",
                "$.raw_pointer",
                f"could not resolve payload: {exc}",
            )
        else:
            observed_hash = hashlib.sha256(payload).hexdigest()
            if observed_hash != payload_hash:
                result.add(
                    "payload.digest_mismatch",
                    "$.source.payload_sha256",
                    f"declared {payload_hash}; resolved payload hashes to {observed_hash}",
                )

    return result


def assert_valid(
    record: Any,
    *,
    payload_resolver: PayloadResolver | None = None,
) -> Mapping[str, Any]:
    """Return ``record`` when valid, otherwise raise :class:`ContractValidationError`."""

    result = validate_record(record, payload_resolver=payload_resolver)
    if not result.valid:
        raise ContractValidationError(result)
    assert isinstance(record, Mapping)
    return record


