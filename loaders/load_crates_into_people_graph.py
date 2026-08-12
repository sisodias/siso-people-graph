#!/usr/bin/env python3
"""Load a crates.io snapshot into the People Graph: owners, teams, dependencies.

WHY THIS FILE EXISTS AT ALL

It is a reconstruction. The published graph-v2 release asset contains four
tables that appeared in no tracked file on any branch of this repository:

    person_person          1,272,495 rows
    organisation_content      13,533 rows
    organisation               1,131 rows
    person_organisation            0 rows

Every one of those rows came from a crates.io load, and the code that wrote
them was never committed. The graph could therefore not be rebuilt from its own
source -- not because a step was broken, but because a step was absent. See
docs/handoffs/schema-divergence.md for the full account.

This loader restores that step, so the shipped shape is reproducible.

WHAT person_person ACTUALLY MEANS -- READ BEFORE EXTENDING

The release title calls person_person "person-to-person edges", and the
registry cited it as a relational layer. It is neither. Measured against the
shipped asset, all 1,272,495 rows are:

    relation   = 'depends_on'
    source     = 'crates_io_dependencies'
    confidence = 0.95, flat (min == max)

They are PACKAGE DEPENDENCIES projected onto package owners. Package A depends
on package B tells you nothing about whether person A and person B have ever
met, collaborated, or heard of each other. Writing these as person-to-person
edges is the owner -> creator category collapse; this loader reproduces the
shipped data faithfully but refuses to reproduce the claim about it.

Consequences encoded here rather than left to a reader's good judgement:

  * relation and source are written explicitly on every row, so a consumer can
    filter. A future genuine relation (co_maintainer, co_author) must use its
    own relation value and must not be mixed into this one.
  * confidence stays 0.95 to match the asset, but 0.95 here is a CONSTANT, not
    a measurement. It ranks nothing. Do not sort by it and call the result
    confidence-ordered.
  * meta_json records the two packages the edge was derived from, which the
    shipped table did not do. Without it an edge cannot be traced back to the
    dependency that caused it, and provenance is the whole point.

Teams become organisations rather than people. A crates team is not a human,
and the graph's central design decision is that institutions do not live in
person. That is why organisation_content exists.
"""
import argparse
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_v3 import paths  # noqa: E402

LOADER_VERSION = "load_crates/1"
SOURCE_OWNERS = "crates_io"
SOURCE_DEPS = "crates_io_dependencies"
SOURCE_TEAMS = "crates_io_teams"

# Matches the shipped asset exactly. Constant, not measured -- see module docs.
DEPENDENCY_CONFIDENCE = 0.95


def _person_id(login):
    return f"cr:{login}"


def _org_id(login):
    return f"org:crates:{login}"


def load(crates_db, graph_db, observed_at, snapshot, apply_changes=False):
    src = sqlite3.connect(f"file:{crates_db}?mode=ro", uri=True)
    g = sqlite3.connect(graph_db)
    try:
        crates = {
            name: (owner, kind)
            for name, owner, kind, _ in src.execute(
                "SELECT name, owner_login, owner_kind, downloads FROM crate "
                "ORDER BY name")
        }

        # --- people: individual crate owners ---------------------------------
        # Teams are deliberately excluded here; they become organisations.
        people = sorted({
            owner for owner, kind in crates.values() if kind == "user"
        })
        # kind='unknown' is deliberate and matches the shipped asset: a crates
        # login does not tell us whether the owner is a human or a company.
        # Guessing would manufacture the very human/organisation confusion the
        # schema exists to prevent.
        person_rows = [
            (_person_id(login), login, "unknown", "tracked", "crates_io",
             observed_at)
            for login in people
        ]

        # --- organisations: teams --------------------------------------------
        teams = sorted(set(src.execute(
            "SELECT team_login, team_name FROM crate_team ORDER BY 1,2")))
        org_rows = [
            (_org_id(login), name, "team", None, "tracked", SOURCE_TEAMS,
             observed_at, "{}")
            for login, name in teams
        ]
        org_content_rows = sorted({
            (_org_id(login), "crates", crate, "publisher", SOURCE_TEAMS,
             observed_at, "{}")
            for login, _name, crate in src.execute(
                "SELECT team_login, team_name, crate FROM crate_team")
        })

        # --- person_person: dependency edges projected onto owners -----------
        # This is the block whose output must never be described as social.
        dep_rows = {}
        for crate, depends_on in src.execute(
            "SELECT crate, depends_on FROM crate_dependency ORDER BY 1,2"
        ):
            a = crates.get(crate)
            b = crates.get(depends_on)
            if not a or not b:
                continue
            # Only user-owned crates project onto people. A team-owned crate's
            # dependency is an organisational fact, not a personal one.
            if a[1] != "user" or b[1] != "user":
                continue
            pa, pb = _person_id(a[0]), _person_id(b[0])
            # The schema's CHECK (person_a <> person_b) forbids self-edges, and
            # an owner depending on their own crate is common. Skip rather than
            # let the insert fail.
            if pa == pb:
                continue
            key = (pa, pb, "depends_on")
            # Multiple package-level dependencies between the same two owners
            # collapse to one edge with a weight, which is why weight exists.
            if key in dep_rows:
                dep_rows[key]["weight"] += 1
                dep_rows[key]["via"].append(f"{crate}->{depends_on}")
            else:
                dep_rows[key] = {"weight": 1, "via": [f"{crate}->{depends_on}"]}

        pperson_rows = [
            (pa, pb, rel, "a_to_b", v["weight"], DEPENDENCY_CONFIDENCE,
             SOURCE_DEPS, observed_at,
             json.dumps({"via": sorted(v["via"]), "snapshot": snapshot},
                        sort_keys=True))
            for (pa, pb, rel), v in sorted(dep_rows.items())
        ]

        result = {
            "loader": LOADER_VERSION,
            "snapshot": snapshot,
            "observed_at": observed_at,
            "applied": bool(apply_changes),
            "counts": {
                "person": len(person_rows),
                "organisation": len(org_rows),
                "organisation_content": len(org_content_rows),
                "person_person": len(pperson_rows),
            },
            "semantics": {
                "person_person.relation": "depends_on",
                "person_person.source": SOURCE_DEPS,
                "person_person.confidence": DEPENDENCY_CONFIDENCE,
                "warning": "person_person rows are crates.io PACKAGE "
                           "dependencies projected onto owners. They are not "
                           "social or collaboration edges and must not be "
                           "presented as such.",
            },
        }
        if not apply_changes:
            return result

        # built_at is pinned to observed_at, never to wall clock: a wall-clock
        # stamp here would make every row differ between two builds, which is
        # non-determinism source #1 from build_v3/build.py.
        g.executemany(
            "INSERT OR REPLACE INTO person "
            "(person_id,name,kind,state,origin,built_at) VALUES (?,?,?,?,?,?)",
            person_rows)
        g.executemany(
            "INSERT OR REPLACE INTO organisation "
            "(org_id,name,kind,github_org_id,state,source,observed_at,meta_json)"
            " VALUES (?,?,?,?,?,?,?,?)", org_rows)
        g.executemany(
            "INSERT OR REPLACE INTO organisation_content "
            "(org_id,domain,content_ref,role,source,observed_at,meta_json)"
            " VALUES (?,?,?,?,?,?,?)", org_content_rows)
        g.executemany(
            "INSERT OR REPLACE INTO person_person "
            "(person_a,person_b,relation,direction,weight,confidence,source,"
            "observed_at,meta_json) VALUES (?,?,?,?,?,?,?,?,?)", pperson_rows)
        g.commit()
        return result
    finally:
        src.close()
        g.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crates", required=True, help="crates.io snapshot sqlite")
    ap.add_argument("--graph", required=True, help="people graph to load into")
    ap.add_argument("--observed-at", required=True,
                    help="pinned observation timestamp; wall clock is not used")
    ap.add_argument("--snapshot", required=True, help="source snapshot id")
    ap.add_argument("--apply", action="store_true",
                    help="write; without this the loader only reports")
    a = ap.parse_args()
    paths.require(a.crates, "crates snapshot")
    paths.require(a.graph, "graph database")
    print(json.dumps(load(a.crates, a.graph, a.observed_at, a.snapshot,
                          a.apply), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
