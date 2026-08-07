#!/usr/bin/env python3
"""Give GitHub people topics and value, from data already sitting in the corpus.

Two things the GitHub domain already computed and the people graph was throwing
away:

  1. TOPICS. repo_card.topics_json holds GitHub's own topic tags per repo
     ("sqlite", "python", "datasets"), plus `language`. Books people get topics
     from librarian-assigned LCSH subjects -- 167,585 edges -- so GitHub people
     having none made the two populations incomparable. A question like "who
     works on databases" could reach book authors and not a single engineer.

  2. VALUE. repo_category holds 385,964 rows of MiniMax-rated repos with
     reuse_value, info_value and overall_value. That is a judgement already paid
     for. Rolling it up per owner gives a defensible ranking of PEOPLE by the
     rated quality of what they produced, rather than by raw star count, which
     mostly measures popularity and age.

Both land in person_topic, the same table books uses, so a topic query spans
domains instead of stopping at one. scheme= records provenance: 'github_topic'
and 'github_lang' are GitHub's own tags; 'lcsh' is the library taxonomy. Never
merge the vocabularies -- "python" and "Philosophy, Ancient" are not the same
kind of fact, and flattening them would make both untrustworthy.

Usage:
  load_owner_topics.py --identity identity.sqlite --graph people_v2.sqlite --apply
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_v3 import paths  # noqa: E402,F401

LOADER_VERSION = "load_owner_topics/2"
SOURCE_NAME = "repo_card"
VALUE_SOURCE = "repo_category"

# Topics too generic to carry signal. Tagging someone "javascript" says little;
# tagging them "compilers" says a lot. Kept short deliberately -- over-filtering
# is worse than a few weak tags, because the weight column already ranks them.
NOISE = {
    "awesome", "list", "lists", "hacktoberfest", "github", "opensource",
    "open-source", "tutorial", "example", "examples", "demo", "test",
    "boilerplate", "starter", "template", "library", "framework", "tool",
    "tools", "app", "api", "cli", "web", "software",
}


def load(identity_db, graph_db, min_stars, apply_changes,
         observed_at=None, snapshot=None, prune_stale=True):
    src = sqlite3.connect(f"file:{identity_db}?mode=ro", uri=True)
    g = sqlite3.connect(graph_db)
    now = observed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Which logins are actually in the graph -- no point computing topics for
    # owners we never loaded.
    known = set()
    for (pid,) in g.execute("SELECT person_id FROM person WHERE person_id LIKE 'gh:%'"):
        known.add(pid[3:].lower())

    topics = defaultdict(lambda: defaultdict(int))   # login -> topic -> count
    langs = defaultdict(lambda: defaultdict(int))

    for full_name, topics_json, lang in src.execute(
        "SELECT full_name, topics_json, language FROM repo_card "
        "WHERE full_name LIKE '%/%' AND COALESCE(stars,0) >= ?",
        (min_stars,),
    ):
        login = full_name.split("/", 1)[0].lower()
        if login not in known:
            continue
        if lang:
            langs[login][lang] += 1
        if not topics_json:
            continue
        try:
            for t in json.loads(topics_json):
                t = (t or "").strip().lower()
                if t and t not in NOISE and len(t) > 2:
                    topics[login][t] += 1
        except (ValueError, TypeError):
            continue

    # Value roll-up: the mean rated value of an owner's repos, weighted by how
    # many were rated. A single 9/10 repo is weaker evidence than twenty 7s.
    value = {}
    try:
        for full_name, n, avg_overall, avg_reuse in src.execute(
            """SELECT full_name, COUNT(*), AVG(overall_value), AVG(reuse_value)
               FROM repo_category WHERE full_name LIKE '%/%'
               GROUP BY full_name"""
        ):
            login = full_name.split("/", 1)[0].lower()
            if login not in known:
                continue
            cur = value.setdefault(login, {"rated": 0, "sum": 0.0, "reuse": 0.0})
            cur["rated"] += n
            cur["sum"] += (avg_overall or 0) * n
            cur["reuse"] += (avg_reuse or 0) * n
    except sqlite3.Error:
        pass  # repo_category absent on some machines; topics still work

    # Sorting is (-count, name), not -count alone. With ties broken only by
    # dict insertion order, the top-25 cut could select a DIFFERENT set of
    # equally-frequent topics depending on the order rows came back from the
    # source -- two builds of the same snapshot would then disagree. The name
    # is the tiebreak that makes the cut deterministic.
    rows = []
    for login in sorted(topics):
        for t, n in sorted(topics[login].items(), key=lambda kv: (-kv[1], kv[0]))[:25]:
            rows.append((f"gh:{login}", t, "github_topic", float(n), SOURCE_NAME))
    for login in sorted(langs):
        for l, n in sorted(langs[login].items(), key=lambda kv: (-kv[1], kv[0]))[:8]:
            rows.append((f"gh:{login}", l, "github_lang", float(n), SOURCE_NAME))

    summary = {
        "owners_in_graph": len(known),
        "owners_with_topics": len(topics),
        "owners_with_value": len(value),
        "topic_edges": len(rows),
        "applied": bool(apply_changes),
    }

    if apply_changes:
        # person_topic uses the login-cased id; graph rows may differ in case,
        # so resolve against what actually exists rather than assuming.
        real = {}
        for pid, in g.execute("SELECT person_id FROM person WHERE person_id LIKE 'gh:%'"):
            real[pid.lower()] = pid
        fixed = [(real.get(r[0].lower(), r[0]),) + r[1:] for r in rows]

        # Stale-topic pruning, scoped to the topic schemes and source this
        # loader owns. A repo that lost a GitHub topic between snapshots must
        # lose the corresponding edge; otherwise person_topic accumulates every
        # tag the owner ever carried. lcsh edges belong to the books loader and
        # are never touched here.
        pruned = 0
        if prune_stale:
            current = {(r[0], r[1], r[2]) for r in fixed}
            existing = g.execute(
                "SELECT person_id, topic, scheme FROM person_topic "
                "WHERE source=? AND scheme IN ('github_topic','github_lang')",
                (SOURCE_NAME,),
            ).fetchall()
            stale = [r for r in existing if tuple(r) not in current]
            if stale:
                g.executemany(
                    "DELETE FROM person_topic WHERE person_id=? AND topic=? "
                    "AND scheme=? AND source=?",
                    [(a, b, c, SOURCE_NAME) for a, b, c in stale],
                )
                pruned = len(stale)

        # REPLACE, not IGNORE: a changed weight must update rather than be
        # skipped, or the first snapshot's counts are frozen forever.
        g.executemany(
            "INSERT OR REPLACE INTO person_topic "
            "(person_id,topic,scheme,weight,source) VALUES (?,?,?,?,?)",
            fixed,
        )

        # THE ADDITIVE RANK BUG, removed.
        #
        # This loader previously ran:
        #     UPDATE person SET rank_score = COALESCE(rank_score,0) + ?
        # so a second run over the same unchanged source DOUBLED every owner's
        # contribution, a third tripled it, and the graph's ranking depended on
        # how many times the loader had been executed rather than on what the
        # source said. That single line is why reruns were non-idempotent.
        #
        # It also blended a 0-100 model rating into a column already holding
        # summed stars and book counts -- three incompatible units summed
        # together. A mean rating is a measurement, so it is stored as one,
        # keyed by (person_id, metric, source) so a rerun REPLACES it.
        obs = []
        for login, v in sorted(value.items()):
            pid = real.get(f"gh:{login}", f"gh:{login}")
            if v["rated"]:
                obs.append((pid, "rated_overall_mean", v["sum"] / v["rated"],
                            "rating_0_100", VALUE_SOURCE, snapshot, now))
                obs.append((pid, "rated_reuse_mean", v["reuse"] / v["rated"],
                            "rating_0_100", VALUE_SOURCE, snapshot, now))
                obs.append((pid, "rated_repo_count", float(v["rated"]),
                            "repos", VALUE_SOURCE, snapshot, now))
        g.executemany(
            """INSERT OR REPLACE INTO person_observation
               (person_id,metric,value,unit,source,snapshot,observed_at)
               VALUES (?,?,?,?,?,?,?)""",
            obs,
        )
        g.commit()
        summary["pruned_stale_topics"] = pruned
        summary["observations"] = len(obs)
        summary["person_topic_total"] = g.execute(
            "SELECT COUNT(*) FROM person_topic"
        ).fetchone()[0]

    g.close()
    src.close()
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--identity", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--min-stars", type=int, default=100)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--observed-at",
                    help="fixed ISO8601 timestamp for reproducible builds")
    ap.add_argument("--snapshot", help="source snapshot id, tied to the manifest")
    ap.add_argument("--no-prune", action="store_true",
                    help="keep topic edges the current snapshot no longer supports")
    a = ap.parse_args()
    t = time.time()
    s = load(a.identity, a.graph, a.min_stars, a.apply,
             observed_at=a.observed_at, snapshot=a.snapshot,
             prune_stale=not a.no_prune)
    s["elapsed_s"] = round(time.time() - t, 2)
    print(json.dumps(s, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
