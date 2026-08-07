"""Epistemic tagging: how do we know each thing we are about to assert?

The lane spec requires every result to distinguish four grades. They are not
decoration -- an agent acting on this graph needs to know whether it is looking
at something a source said, something a reviewer decided, something we computed,
or something a model guessed. Collapsing them is how a graph starts asserting
falsehoods with confidence.
"""
from __future__ import annotations

from dataclasses import dataclass

# The four grades, ordered from most to least directly attested.
SOURCE_OBSERVATION = "source_observation"
IDENTITY_DECISION = "accepted_identity_decision"
DERIVED_RELATION = "derived_relation"
MODEL_INFERENCE = "model_inference"

GRADES = (SOURCE_OBSERVATION, IDENTITY_DECISION, DERIVED_RELATION, MODEL_INFERENCE)


@dataclass(frozen=True)
class Evidence:
    """Provenance for one asserted fact."""

    grade: str
    source: str | None = None
    observed_at: str | None = None
    detail: str | None = None
    method: str | None = None
    confidence: float | None = None
    decided_by: str | None = None

    def as_dict(self) -> dict:
        d = {"grade": self.grade}
        for k in (
            "source",
            "observed_at",
            "detail",
            "method",
            "confidence",
            "decided_by",
        ):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        return d


def observed(source: str | None, observed_at: str | None = None,
             detail: str | None = None) -> Evidence:
    return Evidence(SOURCE_OBSERVATION, source=source, observed_at=observed_at,
                    detail=detail)


def decided(method: str, confidence: float | None, decided_by: str | None,
            detail: str | None = None, observed_at: str | None = None) -> Evidence:
    return Evidence(IDENTITY_DECISION, method=method, confidence=confidence,
                    decided_by=decided_by, detail=detail, observed_at=observed_at)


def derived(detail: str, source: str | None = None) -> Evidence:
    return Evidence(DERIVED_RELATION, detail=detail, source=source)
