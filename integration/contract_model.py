"""Types and invariant registries for ``pg-observation-0.1``.

The contract is intentionally an observation format, not an entity-resolution
format.  It preserves source-native facts while refusing canonical People Graph
IDs, silent name merges, or identifier semantics that promote attributes into
identity keys.

Only Python's standard library is used so every parallel lane can execute the
validator in a clean checkout.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Iterator, Mapping, MutableSequence, Sequence

ENVELOPE_VERSION = "pg-observation-0.1"

RIGHTS_STATES = frozenset(
    {
        "public_metadata",
        "open_data",
        "restricted",
        "discovery_only",
        "pending",
    }
)
SUBJECT_KINDS = frozenset(
    {
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
)
IDENTIFIER_SCOPES = frozenset({"global", "source", "organisation"})
IDENTIFIER_STABILITIES = frozenset({"stable", "mutable", "unknown"})
IDENTIFIER_UNIQUENESS = frozenset({"unique", "non_unique", "unknown"})

# These are observations/attributes, never identifier schemes.  A source may
# retain their literal values under subject.attributes instead.
ATTRIBUTE_ONLY_SCHEMES = frozenset(
    {
        "name",
        "full_name",
        "display_name",
        "real_name",
        "company",
        "employer",
        "organisation_name",
        "location",
        "city",
        "country",
        "biography",
        "bio",
        "topic",
        "subject",
    }
)

# Handles/logins can be useful source-scoped identifiers, but they are mutable
# aliases and may be reused.  The validator therefore forbids global/stable/
# universally-unique semantics for them.
HANDLE_SCHEMES = frozenset(
    {
        "handle",
        "username",
        "login",
        "github_login",
        "x_handle",
        "mastodon_handle",
        "bluesky_handle",
        "youtube_handle",
    }
)

FORBIDDEN_CANONICAL_KEYS = frozenset(
    {
        "canonical_id",
        "canonical_person_id",
        "canonical_entity_id",
        "canonical_people_graph_id",
        "people_graph_id",
        "cluster_id",
        "resolved_entity_id",
        "merged_into",
        "canonical_redirect",
    }
)
FORBIDDEN_MERGE_KEYS = frozenset(
    {
        "auto_merge",
        "merge_on_name",
        "name_only_merge",
        "resolve_by_name",
        "canonicalize",
    }
)
IDENTITY_RELATION_TYPES = frozenset(
    {
        "same_as",
        "sameas",
        "identity_match",
        "identical_to",
        "equivalent_to",
        "merged_into",
        "canonicalizes",
    }
)
NAME_ONLY_METHODS = frozenset(
    {
        "name",
        "name_only",
        "exact_name",
        "normalised_name",
        "normalized_name",
        "surname_initial",
    }
)
ALLOWED_IDENTITY_REVIEW_STATES = frozenset(
    {"observed", "proposed", "needs_review", "review_only"}
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_POINTER_PATTERNS = (
    re.compile(r"^/(?:Users|home|Volumes)/"),
    re.compile(r"^[A-Za-z]:[\\/]"),
    re.compile(r"^file://", re.IGNORECASE),
)

PayloadResolver = Callable[[str], bytes]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One machine-readable validation finding."""

    code: str
    path: str
    message: str
    severity: str = "error"

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(slots=True)
class ValidationResult:
    """Validation result with stable error codes for cross-lane automation."""

    issues: MutableSequence[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def valid(self) -> bool:
        return not self.errors

    def add(
        self,
        code: str,
        path: str,
        message: str,
        *,
        severity: str = "error",
    ) -> None:
        self.issues.append(ValidationIssue(code, path, message, severity))

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues.extend(issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [issue.to_dict() for issue in self.issues],
        }


class ContractValidationError(ValueError):
    """Raised by :func:`assert_valid` with all contract findings attached."""

    def __init__(self, result: ValidationResult):
        self.result = result
        summary = "; ".join(
            f"{issue.code} at {issue.path}: {issue.message}"
            for issue in result.errors[:8]
        )
        if len(result.errors) > 8:
            summary += f"; and {len(result.errors) - 8} more"
        super().__init__(summary or "observation contract validation failed")


