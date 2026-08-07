#!/usr/bin/env python3
"""Propose safe, evidenced identity claims without silently merging people.

Compatibility:
  match_identities.py --graph people_v2.sqlite
  match_identities.py --graph people_v2.sqlite --apply
  match_identities.py --graph people_v2.sqlite --apply --accept shared_external_id

`shared_external_id` now means an exact match in a scheme explicitly marked
unique and auto-resolution eligible by identity_v3.registry. Company, location,
real name, topic, biography, follower count, websites, and mutable handles can
never enter that automatic path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from identity_v3.adapters import import_v2  # noqa: E402
from identity_v3.engine import IdentityEngine, IdentityError, stable_json, utc_now  # noqa: E402
from identity_v3.registry import name_parts, normalize_name, years_compatible  # noqa: E402

# Backward-compatible helper name used by older callers.
norm_name = normalize_name


def _candidate_identifier_scheme(candidate: dict[str, object]) -> str | None:
    positive = candidate.get("positive_evidence")
    if not isinstance(positive, list):
        return None
    schemes = {
        str(item.get("scheme"))
        for item in positive
        if isinstance(item, dict) and item.get("scheme")
    }
    return next(iter(schemes)) if len(schemes) == 1 else None


def _write_v2_claims(
    connection: sqlite3.Connection,
    candidates: list[dict[str, object]],
    *,
    auto_accept: str | None,
) -> tuple[int, int]:
    if auto_accept and auto_accept != "shared_external_id":
        raise IdentityError(
            "automatic acceptance is restricted to registry-eligible shared_external_id candidates"
        )
    now = utc_now()
    written = 0
    accepted = 0
    for candidate in candidates:
        a = str(candidate["entity_a"])
        b = str(candidate["entity_b"])
        method = str(candidate["method"])
        status = "accepted" if (
            auto_accept == "shared_external_id"
            and method == "shared_external_id"
            and bool(candidate["auto_eligible"])
        ) else "proposed"
        evidence = stable_json({
            "method_version": candidate["method_version"],
            "scheme": _candidate_identifier_scheme(candidate),
            "positive": candidate["positive_evidence"],
            "negative": candidate["negative_evidence"],
            "conflicts": candidate["conflict_reasons"],
        })
        existing = connection.execute(
            """SELECT claim_id,status FROM identity_claim
               WHERE person_a=? AND person_b=? AND method=?
               ORDER BY claim_id LIMIT 1""",
            (a, b, method),
        ).fetchone()
        if existing:
            if status == "accepted" and existing["status"] != "accepted":
                connection.execute(
                    """UPDATE identity_claim
                       SET confidence=?,evidence=?,status='accepted',decided_by='identity_v3:auto'
                       WHERE claim_id=?""",
                    (float(candidate["confidence"]), evidence, existing["claim_id"]),
                )
                accepted += 1
            continue
        connection.execute(
            """INSERT INTO identity_claim
               (person_a,person_b,method,confidence,evidence,status,decided_by,created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                a, b, method, float(candidate["confidence"]), evidence, status,
                "identity_v3:auto" if status == "accepted" else None, now,
            ),
        )
        written += 1
        accepted += int(status == "accepted")
    return written, accepted


def propose(graph_db: str, apply_changes: bool, auto_accept: str | None) -> dict[str, object]:
    if auto_accept and auto_accept != "shared_external_id":
        raise IdentityError(
            "automatic acceptance is restricted to registry-eligible shared_external_id candidates"
        )
    source = sqlite3.connect(graph_db)
    source.row_factory = sqlite3.Row
    if apply_changes:
        work = source
    else:
        work = sqlite3.connect(":memory:")
        work.row_factory = sqlite3.Row
        source.backup(work)
        source.close()

    try:
        import_stats = import_v2(work)
        engine = IdentityEngine(work)
        candidates = engine.generate_candidates(apply=apply_changes)
        auto_accepted = 0
        claims_written = 0
        v2_auto_marked = 0
        if apply_changes:
            claims_written, v2_auto_marked = _write_v2_claims(
                work, candidates, auto_accept=auto_accept,
            )
            if auto_accept:
                for candidate in candidates:
                    if (
                        candidate["method"] == auto_accept
                        and candidate["auto_eligible"]
                    ):
                        row = work.execute(
                            "SELECT review_state FROM identity_v3_candidate WHERE candidate_id=?",
                            (candidate["candidate_id"],),
                        ).fetchone()
                        if row and row["review_state"] != "accepted":
                            engine.accept_candidate(
                                str(candidate["candidate_id"]),
                                decided_by="identity_v3:auto",
                                rationale="Exact match in an auto-resolution eligible identifier scheme",
                                automatic=True,
                            )
                            auto_accepted += 1
            work.commit()
        by_method: dict[str, int] = {}
        for candidate in candidates:
            method = str(candidate["method"])
            by_method[method] = by_method.get(method, 0) + 1
        summary: dict[str, object] = {
            "people_considered": work.execute(
                "SELECT COUNT(*) FROM identity_v3_entity"
            ).fetchone()[0],
            "claims_proposed": len(candidates),
            "by_method": by_method,
            "auto_eligible": sum(1 for c in candidates if c["auto_eligible"]),
            "review_only": sum(1 for c in candidates if not c["auto_eligible"]),
            "conflicted": sum(1 for c in candidates if c["conflict_reasons"]),
            "applied": bool(apply_changes),
            "claims_written_v2": claims_written,
            "auto_accepted": auto_accepted,
            "v2_claims_auto_marked": v2_auto_marked,
            "v2_import": import_stats,
            "samples": [
                {
                    "candidate_id": c["candidate_id"],
                    "method": c["method"],
                    "confidence": c["confidence"],
                    "auto_eligible": c["auto_eligible"],
                    "positive_evidence": c["positive_evidence"],
                    "conflict_reasons": c["conflict_reasons"],
                }
                for c in sorted(
                    candidates,
                    key=lambda item: (-int(bool(item["auto_eligible"])), -float(item["confidence"])),
                )[:8]
            ],
        }
        if apply_changes:
            summary["claims_in_db"] = work.execute(
                "SELECT COUNT(*) FROM identity_claim"
            ).fetchone()[0]
        return summary
    finally:
        work.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--accept",
        help="auto-accept one method; only shared_external_id is permitted",
    )
    args = parser.parse_args()
    try:
        result = propose(args.graph, args.apply, args.accept)
    except (IdentityError, sqlite3.Error, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
