#!/usr/bin/env python3
"""One query surface over every Foundry domain -- the CLI projection.

The problem this solves: an agent holding a Frontier Question should not need to
know that books live in books.sqlite, people in people_v2.sqlite, repos in
identity.sqlite, and that each has its own schema. It should ask, and the answer
should already be here.

WHAT CHANGED, and why (PG-AUDIT-002 / PGRT-004):

This file used to query person rows directly and never read identity_claim or
person.merged_into. A reviewer could accept an identity merge, the review queue
would report success, and `--who` would still return the same two duplicate rows
afterwards. The reviewer's decision had no observable effect anywhere in the
system -- people did the work and the graph ignored them.

Two smaller defects lived in the same code and had the same shape, a failure
that looked like a success:

  * the name search ran `WHERE people.person_search MATCH ?`, which raises
    `no such column: people.person_search` because a schema-qualified name is not
    a valid FTS5 MATCH operand. A bare `except sqlite3.Error` swallowed it and
    fell through to a LIKE scan, so every lookup was a full table scan while the
    code read as if it used the index.
  * `--works` capped at 200 rows and reported `count = len(rows)`, so a person
    with 200 works and a person with 40,000 produced identical output.

All three are fixed in `query_v3/`, which is now the single source of truth. This
file is a thin projection over it: it parses arguments and prints JSON. It
contains no SQL, and if it ever grows any, the read layer can drift away from the
identity layer again -- which is the whole defect.

Design notes, unchanged in spirit from the original:
  * Read-only, always. Every attach uses ?mode=ro, per the single-writer law.
  * Missing domains are non-fatal -- but they are now DECLARED in the output
    rather than silently skipped, so a thin answer cannot be mistaken for a
    complete one.
  * Output is JSON because the primary caller is an agent, not a human.

Usage:
  ask.py --who "Spinoza"                  who is this, across every domain
  ask.py --about "Justice"                what do we have on this topic
  ask.py --contemporaries "Spinoza"       who was alive at the same time
  ask.py --works "Plato"                  everything a person produced
  ask.py --relationships "Plato"          evidenced neighbours
  ask.py --path "Kant" --to "Adam Smith"  an explainable route between two people
  ask.py --claims "Plato"                 evidence-backed assertions
  ask.py --inventory                      what data exists at all
  ask.py --source                         snapshots, rights, freshness

Configuration (replaces the old hardcoded machine-specific path list):
  PEOPLE_GRAPH_CONFIG    JSON file mapping domain -> path
  PEOPLE_GRAPH_PEOPLE    direct path to the people database (and _BOOKS, etc.)
  PEOPLE_GRAPH_ROOT      directory to look in for <domain>.sqlite
  --root / --people      the same, per invocation
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_v3 import QueryEngine  # noqa: E402


def main():
    ap = argparse.ArgumentParser(
        description="Read-only, evidence-first query surface over the People Graph."
    )
    ap.add_argument("--who", metavar="NAME")
    ap.add_argument("--works", metavar="NAME")
    ap.add_argument("--about", metavar="TOPIC")
    ap.add_argument("--contemporaries", metavar="NAME")
    ap.add_argument("--relationships", metavar="NAME")
    ap.add_argument("--claims", metavar="NAME")
    ap.add_argument("--path", metavar="FROM",
                    help="start of a relationship path; use with --to")
    ap.add_argument("--to", metavar="TO", help="end of a relationship path")
    ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--source", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--max-hops", type=int, default=3)
    ap.add_argument("--root", help="directory holding <domain>.sqlite fixtures")
    ap.add_argument("--people", help="explicit path to the people database")
    ap.add_argument("--html", action="store_true",
                    help="render the human explorer projection instead of JSON")
    a = ap.parse_args()

    explicit = {"people": a.people} if a.people else None
    engine = QueryEngine(explicit_paths=explicit, root=a.root)

    try:
        if a.inventory:
            result = engine.inventory()
        elif a.source:
            result = engine.source()
        elif a.who is not None:
            result = engine.who(a.who, limit=a.limit or 8, offset=a.offset)
        elif a.works is not None:
            result = engine.works(a.works, limit=a.limit or 100, offset=a.offset)
        elif a.relationships is not None:
            result = engine.relationships(a.relationships, limit=a.limit or 25)
        elif a.claims is not None:
            result = engine.claims(a.claims, limit=a.limit or 25)
        elif a.path is not None:
            if not a.to:
                ap.error("--path requires --to")
            result = engine.path(a.path, a.to, max_hops=a.max_hops)
        elif a.contemporaries is not None:
            # Kept for compatibility with the original CLI. The underlying
            # v_contemporaries view is a v2 artifact; when it is absent the
            # response says so rather than returning an empty list.
            result = engine.who(a.contemporaries, limit=a.limit or 8)
            result["query_type"] = "contemporaries"
            result["coverage_gaps"].append(
                "--contemporaries currently resolves the person only; temporal "
                "overlap requires the v_contemporaries view or v3 temporal "
                "relations. Use --relationships for evidenced neighbours."
            )
        elif a.about is not None:
            result = engine.who(a.about, limit=a.limit or 15)
            result["query_type"] = "about"
            result["coverage_gaps"].append(
                "--about is resolved as a name query in this build; namespaced "
                "topic vocabularies and crosswalks require the v3 topic tables."
            )
        else:
            ap.print_help()
            return 2

        if a.html:
            from viewer import render
            print(render(result))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    sys.exit(main())
