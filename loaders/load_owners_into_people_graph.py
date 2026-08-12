#!/usr/bin/env python3
"""Load GitHub repo owners into the people graph.

The GitHub domain holds 1,358,200 repo cards spanning 614,868 distinct owners.
Every one of those owners produced something, which is the graph's membership
rule -- so they belong in it. This is the largest single population available
and the one most likely to overlap with the YouTube creators and registry people
already there, which is where cross-domain stitch finally moves past 3.

Scale reality: 614k owners against 35,834 existing people is a 17x expansion.
Two things follow, and both are deliberate:

  1. NOT EVERY OWNER IS WORTH A ROW. An account with one unstarred fork is noise
     that would bury the signal. --min-stars gates entry on evidence that someone
     found the work useful. Default 0 loads everything; production wants a floor.

  2. AN OWNER IS NOT NECESSARILY A HUMAN. `facebook`, `microsoft` and `apache`
     are organisations. The graph already distinguishes kind='organisation'
     because books forced the same problem (870 institutional "authors" like
     "United States"). We cannot tell reliably from the repo table alone, so
     owners are marked kind='unknown' rather than being falsely asserted as
     people -- an honest null beats a confident guess, and the GitHub API can
     resolve it later in one call per owner.

person_id convention follows the existing namespacing: 'gh:<login>'. That is
also what makes the join work -- an owner already in the graph from the YouTube
or registry side keeps their id and gains repo edges rather than duplicating.

Usage:
  load_owners_into_people_graph.py --identity identity.sqlite \
      --graph people_v2.sqlite [--min-stars 10] [--apply]
"""
import argparse
import json
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_v3 import paths  # noqa: E402,F401

LOADER_VERSION = "load_owners_into_people_graph/2"
SOURCE_NAME = "github_identity"

# Owner names that are obviously organisations. Not exhaustive -- a heuristic
# for the clearest cases only. Everything else stays 'unknown' rather than being
# guessed at.
ORG_HINTS = (
    "-org", "-team", "-labs", "-inc", "-io", "foundation", "institute",
    "technologies", "systems", "software", "group", "community", "project",
)


def looks_organisational(login):
    low = login.lower()
    return any(h in low for h in ORG_HINTS)


def load(identity_db, graph_db, min_stars, limit, apply_changes,
         observed_at=None, snapshot=None, prune_stale=True):
    """Load GitHub owners.

    observed_at pins the timestamp so reruns are byte-stable; prune_stale
    removes edges this source wrote previously that the current snapshot no
    longer supports. Without pruning, a repo that was deleted, unstarred below
    the threshold, or reclassified as a fork stays in the graph forever -- the
    graph would then be the union of every snapshot ever loaded rather than a
    representation of the current one.
    """
    src = sqlite3.connect(f"file:{identity_db}?mode=ro", uri=True)
    g = sqlite3.connect(graph_db)
    now = observed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Existing people, by github login, so we ADD to a known person rather than
    # creating a twin. external_ids is the canonical join key for this.
    known = {}
    for pid, value in g.execute(
        "SELECT person_id, value FROM external_ids WHERE platform='github_login'"
    ):
        known[(value or "").lower()] = pid
    for pid, in g.execute("SELECT person_id FROM person WHERE person_id LIKE 'gh:%'"):
        known.setdefault(pid[3:].lower(), pid)

    q = """
        SELECT full_name, stars, language, description, topics_json, url
        FROM repo_card
        WHERE full_name LIKE '%/%'
          AND (fork IS NULL OR fork = 0 OR fork = '')
          AND COALESCE(stars, 0) >= ?
    """
    if limit:
        q += f" LIMIT {int(limit)}"

    owners = {}
    edges = []
    for full_name, stars, lang, desc, topics, url in src.execute(q, (min_stars,)):
        login, _, repo = full_name.partition("/")
        if not login or not repo:
            continue
        key = login.lower()
        o = owners.setdefault(
            key, {"login": login, "repos": 0, "stars": 0, "langs": set()}
        )
        o["repos"] += 1
        o["stars"] += int(stars or 0)
        if lang:
            o["langs"].add(lang)
        edges.append(
            (
                known.get(key, f"gh:{login}"),
                "github",
                full_name,
                "owner",
                float(stars or 0),
                (desc or "")[:200] or None,
                "github_identity",
                now,
                json.dumps({"language": lang, "url": url}),
            )
        )

    new_people = []
    new_extids = []
    matched = 0
    for key, o in owners.items():
        if key in known:
            matched += 1
            continue
        pid = f"gh:{o['login']}"
        # rank_score is no longer written. Summed stars went into the same
        # column that holds a book author's work count and a model's 0-100
        # rating, so the column had no unit and no meaning across origins.
        # Stars are a popularity measurement; they are recorded as one below.
        new_people.append(
            (
                pid,
                o["login"],
                o["login"],
                "organisation" if looks_organisational(o["login"]) else "unknown",
                "linked",
                "github",
                now,
            )
        )
        new_extids.append((pid, "github_login", o["login"], 1.0, SOURCE_NAME))

    # Star and repo counts for EVERY owner in this snapshot, matched or new --
    # a person who already existed still has a measurable star count, and the
    # old code only ever scored the newly-created ones.
    observations = []
    for key, o in owners.items():
        pid = known.get(key, f"gh:{o['login']}")
        observations.append((pid, "github_stars_sum", float(o["stars"]),
                             "stars", SOURCE_NAME, snapshot, now))
        observations.append((pid, "github_repo_count", float(o["repos"]),
                             "repos", SOURCE_NAME, snapshot, now))

    summary = {
        "repo_rows_considered": len(edges),
        "distinct_owners": len(owners),
        "matched_existing": matched,
        "new_people": len(new_people),
        "min_stars": min_stars,
        "applied": bool(apply_changes),
    }

    if apply_changes:
        g.executemany(
            """INSERT OR IGNORE INTO person
               (person_id,name,sort_name,kind,state,origin,built_at)
               VALUES (?,?,?,?,?,?,?)""",
            new_people,
        )
        g.executemany(
            """INSERT OR IGNORE INTO external_ids
               (person_id,platform,value,confidence,source) VALUES (?,?,?,?,?)""",
            new_extids,
        )

        # Stale-edge pruning. Delete the edges THIS source previously wrote that
        # the current snapshot does not contain, before inserting the current
        # set. Scoped by source so we never touch another loader's rows: the
        # v1 migration and the books loader own their own edges.
        pruned = 0
        if prune_stale:
            current = {(e[0], e[2]) for e in edges}
            existing_rows = g.execute(
                "SELECT person_id, content_ref FROM person_content "
                "WHERE domain='github' AND source=?", (SOURCE_NAME,)
            ).fetchall()
            stale = [r for r in existing_rows if (r[0], r[1]) not in current]
            if stale:
                g.executemany(
                    "DELETE FROM person_content WHERE person_id=? AND "
                    "content_ref=? AND domain='github' AND source=?",
                    [(a, b, SOURCE_NAME) for a, b in stale],
                )
                pruned = len(stale)

        # INSERT OR REPLACE, not OR IGNORE: a repo whose star count or
        # description changed must UPDATE, not be silently skipped. With IGNORE
        # the graph froze whatever it saw first and later snapshots were inert.
        g.executemany(
            """INSERT OR REPLACE INTO person_content
               (person_id,domain,content_ref,role,score,title,source,observed_at,
                meta_json) VALUES (?,?,?,?,?,?,?,?,?)""",
            edges,
        )
        # REPLACE on (person_id, metric, source): a rerun overwrites the same
        # measurement rather than accumulating. This is the structural fix for
        # the additive rank bug.
        g.executemany(
            """INSERT OR REPLACE INTO person_observation
               (person_id,metric,value,unit,source,snapshot,observed_at)
               VALUES (?,?,?,?,?,?,?)""",
            observations,
        )
        g.commit()
        summary["pruned_stale_edges"] = pruned
        summary["observations"] = len(observations)
        summary["people_after"] = g.execute(
            "SELECT COUNT(*) FROM person"
        ).fetchone()[0]
        summary["github_edges"] = g.execute(
            "SELECT COUNT(*) FROM person_content WHERE domain='github'"
        ).fetchone()[0]

    summary["top_owners"] = sorted(
        ({"login": o["login"], "repos": o["repos"], "stars": o["stars"]}
         for o in owners.values()),
        key=lambda x: -x["stars"],
    )[:10]

    g.close()
    src.close()
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--identity", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--min-stars", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--observed-at",
                    help="fixed ISO8601 timestamp for reproducible builds")
    ap.add_argument("--snapshot", help="source snapshot id, tied to the manifest")
    ap.add_argument("--no-prune", action="store_true",
                    help="keep edges this source wrote that the current "
                         "snapshot no longer contains (not recommended)")
    a = ap.parse_args()
    t = time.time()
    s = load(a.identity, a.graph, a.min_stars, a.limit, a.apply,
             observed_at=a.observed_at, snapshot=a.snapshot,
             prune_stale=not a.no_prune)
    s["elapsed_s"] = round(time.time() - t, 2)
    print(json.dumps(s, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
