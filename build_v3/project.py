#!/usr/bin/env python3
"""Named, versioned ranking projections over observations.

This is where ranking lives now that canonical loading no longer writes a
universal rank_score. The v0 spec states the requirement directly: "any ranking
belongs to named, versioned projection code with method metadata."

Three properties make a projection honest, and each is enforced structurally:

  NAMED       -- 'github_popularity' and 'rated_value' are different questions
                 with different answers. Neither is "the" rank. Both can exist
                 in person_projection at once.
  VERSIONED   -- method_version is part of the primary key, so changing the rule
                 creates a new projection rather than silently rewriting the old
                 one. A stored ranking can always be traced to the rule that
                 produced it.
  DERIVED     -- a projection reads person_observation and writes
                 person_projection. It never mutates a canonical fact, so it can
                 be dropped and recomputed without touching the graph.

The two projections below are deliberately chosen to disagree. Measured in the
Foundry enrichment log against real data: dtolnay -- 10 repos rated >=90, 30,910
stars -- ranks ABOVE facebook at 801,473 stars under rated value, and far below
it under popularity. A single blended score cannot express that, and blending is
what destroyed the interesting signal. Keeping both, named, lets a caller pick
the question rather than inheriting someone else's answer.
"""
import json
import sqlite3
import time

PROJECTIONS = {
    "github_popularity": {
        "metric": "github_stars_sum",
        "method": "sum of stars across an owner's non-fork repos in the snapshot",
        "method_version": "1",
        "caveat": "Popularity, not quality. Correlates with age and audience "
                  "size. An organisation account will usually beat any human.",
    },
    "rated_value": {
        "metric": "rated_overall_mean",
        "method": "mean model-rated overall_value across an owner's rated repos",
        "method_version": "1",
        "caveat": "A model's judgement, not ground truth. Only covers repos that "
                  "were rated; an unrated owner is absent rather than zero.",
    },
    "book_output": {
        "metric": "book_work_count",
        "method": "count of catalogued works attributed to the person",
        "method_version": "1",
        "caveat": "Counts catalogue entries, not importance. A prolific editor "
                  "outranks a singular author.",
    },
}


def compute(graph_db, projection, computed_at=None, apply_changes=False):
    """Compute one named projection. Returns a summary dict."""
    if projection not in PROJECTIONS:
        raise ValueError(
            f"unknown projection {projection!r}; known: {sorted(PROJECTIONS)}"
        )
    spec = PROJECTIONS[projection]
    now = computed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    g = sqlite3.connect(graph_db)

    # Ordering is (value DESC, person_id ASC). The person_id tiebreak matters:
    # without it two people on the same value get ranks that depend on SQLite's
    # row order, and the projection stops being reproducible.
    rows = g.execute(
        """SELECT person_id, value FROM person_observation
           WHERE metric = ? ORDER BY value DESC, person_id ASC""",
        (spec["metric"],),
    ).fetchall()

    ranked = []
    prev_value = None
    rank = 0
    for i, (pid, value) in enumerate(rows):
        # Dense rank: equal values share a rank rather than being ordered
        # arbitrarily, because an arbitrary order would assert a distinction the
        # data does not support.
        if value != prev_value:
            rank = i + 1
            prev_value = value
        ranked.append((pid, projection, spec["method"], spec["method_version"],
                       float(value), rank, now))

    summary = {
        "projection": projection,
        "method": spec["method"],
        "method_version": spec["method_version"],
        "caveat": spec["caveat"],
        "metric": spec["metric"],
        "people_ranked": len(ranked),
        "applied": bool(apply_changes),
    }

    if apply_changes:
        # Delete this projection+version first, so a recompute after observation
        # changes cannot leave people ranked under a stale set.
        g.execute(
            "DELETE FROM person_projection WHERE projection=? AND method_version=?",
            (projection, spec["method_version"]),
        )
        g.executemany(
            """INSERT OR REPLACE INTO person_projection
               (person_id,projection,method,method_version,value,rank,computed_at)
               VALUES (?,?,?,?,?,?,?)""",
            ranked,
        )
        g.commit()

    summary["top"] = [
        {"person_id": r[0], "value": r[4], "rank": r[5]} for r in ranked[:10]
    ]
    g.close()
    return summary


def compute_all(graph_db, computed_at=None, apply_changes=False):
    return {
        name: compute(graph_db, name, computed_at, apply_changes)
        for name in sorted(PROJECTIONS)
    }


def main():
    import argparse
    import sys
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--projection", help="one name; omit for all")
    ap.add_argument("--computed-at", help="fixed timestamp for reproducibility")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.projection:
        out = compute(a.graph, a.projection, a.computed_at, a.apply)
    else:
        out = compute_all(a.graph, a.computed_at, a.apply)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
