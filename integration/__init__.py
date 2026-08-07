"""Parallel integration contract for the SISO People Graph."""

from .contract import (
    ENVELOPE_VERSION,
    ContractValidationError,
    ValidationIssue,
    ValidationResult,
    assert_valid,
    canonical_json_bytes,
    iter_ndjson,
    record_sha256,
    validate_ndjson,
    validate_record,
    write_ndjson,
)

__all__ = [
    "ENVELOPE_VERSION",
    "ContractValidationError",
    "ValidationIssue",
    "ValidationResult",
    "assert_valid",
    "canonical_json_bytes",
    "iter_ndjson",
    "record_sha256",
    "validate_ndjson",
    "validate_record",
    "write_ndjson",
]
