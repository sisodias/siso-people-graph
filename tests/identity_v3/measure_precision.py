#!/usr/bin/env python3
"""Measure identity policy behavior on the adversarial synthetic fixture."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TEST_ROOT = Path(__file__).resolve().parent
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from identity_v3.engine import IdentityEngine, IdentityError  # noqa: E402
from common import load_adversarial, pair_key  # noqa: E402


def _bucket(candidates: list[dict[str, object]], truth: set[tuple[str, str]], distinct: set[tuple[str, str]]) -> dict[str, object]:
    true_positive = 0
    false_positive = 0
    unknown = 0
    for candidate in candidates:
        key = pair_key(str(candidate["entity_a"]), str(candidate["entity_b"]))
        if key in truth:
            true_positive += 1
        elif key in distinct:
            false_positive += 1
        else:
            unknown += 1
    labeled = true_positive + false_positive
    return {
        "proposed": len(candidates),
        "labeled": labeled,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "unknown_or_conflict_fixture": unknown,
        "precision": round(true_positive / labeled, 6) if labeled else None,
    }


def measure() -> dict[str, object]:
    with IdentityEngine(":memory:") as engine:
        fixture = load_adversarial(engine)
        candidates = engine.generate_candidates(apply=True)
        truth = {pair_key(*pair) for pair in fixture["truth_pairs"]}
        distinct = {pair_key(*pair) for pair in fixture["known_distinct_pairs"]}
        conflict_pairs = {pair_key(*pair) for pair in fixture["conflict_pairs"]}
        automatic = [candidate for candidate in candidates if candidate["auto_eligible"]]
        review = [candidate for candidate in candidates if not candidate["auto_eligible"]]

        accepted = 0
        blocked = 0
        for candidate in automatic:
            try:
                engine.accept_candidate(
                    str(candidate["candidate_id"]),
                    decided_by="precision-fixture:auto",
                    automatic=True,
                    decided_at=f"2026-08-06T00:00:{accepted + blocked:02d}Z",
                )
                accepted += 1
            except IdentityError:
                blocked += 1

        audit = engine.audit()
        return {
            "fixture": "synthetic_adversarial_v1",
            "method_version": audit["method_version"],
            "entities": len(fixture["entities"]),
            "truth_pairs": len(truth),
            "known_distinct_pairs": len(distinct),
            "conflict_pairs": len(conflict_pairs),
            "automatic_candidates": _bucket(automatic, truth, distinct),
            "review_only_candidates": _bucket(review, truth, distinct),
            "automatic_acceptance_policy": {
                "accepted": accepted,
                "blocked_by_cluster_conflict": blocked,
                "cluster_invariants_ok": audit["invariants_ok"],
            },
            "notes": [
                "Precision is fixture precision, not a production estimate.",
                "Conflict-pair candidates are excluded from labeled precision because the fixture intentionally carries mutually incompatible stable identifiers.",
                "Review-only candidates are hypotheses and are never automatic decisions.",
            ],
        }


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2, ensure_ascii=False, sort_keys=True))
