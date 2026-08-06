"""Command-line interface for safe identity resolution and reversible clusters."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from typing import Sequence

from .adapters import import_observation_ndjson, import_v2
from .engine import IdentityEngine, IdentityError
from .registry import registry_as_dict


def _dump(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="show evidence and resolution for one entity")
    inspect.add_argument("--db", required=True)
    inspect.add_argument("--entity", required=True)

    propose = sub.add_parser("propose", help="generate evidence-calibrated candidates")
    propose.add_argument("--db", required=True)
    propose.add_argument("--no-sync-v2", action="store_true")
    propose.add_argument("--dry-run", action="store_true")

    review = sub.add_parser("review", help="list candidate review queue")
    review.add_argument("--db", required=True)
    review.add_argument("--state", default="proposed", choices=("proposed", "accepted", "rejected", "all"))
    review.add_argument("--limit", type=int, default=100)

    accept = sub.add_parser("accept", help="accept a candidate and rebuild clusters")
    accept.add_argument("--db", required=True)
    accept.add_argument("--candidate", required=True)
    accept.add_argument("--decided-by", required=True)
    accept.add_argument("--rationale", default="")
    accept.add_argument("--automatic", action="store_true")
    accept.add_argument("--allow-conflicts", action="store_true")

    reject = sub.add_parser("reject", help="reject a candidate")
    reject.add_argument("--db", required=True)
    reject.add_argument("--candidate", required=True)
    reject.add_argument("--decided-by", required=True)
    reject.add_argument("--rationale", default="")

    resolve = sub.add_parser("resolve", help="resolve an entity to its canonical cluster member")
    resolve.add_argument("--db", required=True)
    resolve.add_argument("--entity", required=True)

    undo = sub.add_parser("undo", help="undo one active decision and rebuild clusters")
    undo.add_argument("--db", required=True)
    undo.add_argument("--decision")

    audit = sub.add_parser("audit", help="audit conflicts and identity invariants")
    audit.add_argument("--db", required=True)

    sync = sub.add_parser("sync-v2", help="import v2 entities, external fields, and claims")
    sync.add_argument("--db", required=True)

    envelope = sub.add_parser("import-envelope", help="import pg-observation-0.1 NDJSON")
    envelope.add_argument("--db", required=True)
    envelope.add_argument("--input", required=True)

    sub.add_parser("registry", help="print identifier registry")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "registry":
            _dump(registry_as_dict())
            return 0
        if args.command == "sync-v2":
            connection = sqlite3.connect(args.db)
            try:
                _dump(import_v2(connection))
            finally:
                connection.close()
            return 0
        if args.command == "import-envelope":
            connection = sqlite3.connect(args.db)
            try:
                _dump(import_observation_ndjson(connection, args.input))
            finally:
                connection.close()
            return 0

        with IdentityEngine(args.db) as engine:
            if args.command == "inspect":
                _dump(engine.inspect_entity(args.entity))
            elif args.command == "propose":
                sync_stats = None
                if not args.no_sync_v2 and engine.table_exists("person"):
                    sync_stats = import_v2(engine.connection)
                candidates = engine.generate_candidates(apply=not args.dry_run)
                _dump({
                    "sync_v2": sync_stats,
                    "applied": not args.dry_run,
                    "candidate_count": len(candidates),
                    "by_method": {
                        method: sum(1 for candidate in candidates if candidate["method"] == method)
                        for method in sorted({str(candidate["method"]) for candidate in candidates})
                    },
                    "auto_eligible": sum(1 for candidate in candidates if candidate["auto_eligible"]),
                    "review_only": sum(1 for candidate in candidates if not candidate["auto_eligible"]),
                    "samples": candidates[:10],
                })
            elif args.command == "review":
                _dump(engine.list_candidates(args.state, args.limit))
            elif args.command == "accept":
                _dump(engine.accept_candidate(
                    args.candidate,
                    decided_by=args.decided_by,
                    rationale=args.rationale,
                    automatic=args.automatic,
                    allow_conflicts=args.allow_conflicts,
                ))
            elif args.command == "reject":
                _dump(engine.reject_candidate(
                    args.candidate,
                    decided_by=args.decided_by,
                    rationale=args.rationale,
                ))
            elif args.command == "resolve":
                _dump(engine.resolve_entity(args.entity))
            elif args.command == "undo":
                _dump(engine.undo_decision(args.decision))
            elif args.command == "audit":
                _dump(engine.audit())
            else:  # pragma: no cover - argparse prevents this path
                raise IdentityError(f"unsupported command: {args.command}")
    except (IdentityError, sqlite3.Error, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
