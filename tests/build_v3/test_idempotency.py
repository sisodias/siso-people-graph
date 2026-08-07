#!/usr/bin/env python3
"""Double-run and stale-source tests for the three loaders this lane owns.

The defects these guard against, all of which were live on main:

  RANK DRIFT       load_owner_topics.py ran
                     UPDATE person SET rank_score = COALESCE(rank_score,0) + ?
                   so every rerun over an unchanged source added the rating
                   again. Two runs doubled it. The graph's ranking depended on
                   execution count rather than on the data.

  STALE EDGES      loaders used INSERT OR IGNORE and never deleted. A repo that
                   was removed, dropped below the star threshold, or turned out
                   to be a fork stayed in the graph forever, so the graph became
                   the union of every snapshot ever loaded.

  FROZEN VALUES    INSERT OR IGNORE also meant a CHANGED row was silently
                   skipped -- the first snapshot's star count and description
                   were kept and every later snapshot was inert.

  UNIT COLLAPSE    four loaders wrote incompatible quantities (work count,
                   summed stars, a 0-100 rating, a legacy score) into one
                   unitless REAL column.
"""
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from build_v3 import digest, fixtures  # noqa: E402

FIXED_TIME = "2026-08-06T00:00:00Z"


def _run(script, *args):
    proc = subprocess.run(
        [sys.executable, str(REPO / "loaders" / script), *args],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"{script} failed:\n{proc.stderr}")
    return proc.stdout


class LoaderChainCase(unittest.TestCase):
    """Builds a graph and runs the owner loaders N times."""

    def _build(self, td, runs=1, identity_override=None):
        fx = fixtures.write_all(td)
        graph = str(pathlib.Path(td) / "graph.sqlite")
        _run("build_people_graph_v2.py",
             "--v1", fx["v1"], "--people", fx["books_people"],
             "--books", fx["books"], "--out", graph,
             "--observed-at", FIXED_TIME, "--books-snapshot", "fx")
        identity = identity_override or fx["identity"]
        for _ in range(runs):
            _run("load_owners_into_people_graph.py",
                 "--identity", identity, "--graph", graph,
                 "--min-stars", "100", "--apply",
                 "--observed-at", FIXED_TIME, "--snapshot", "fx")
            _run("load_owner_topics.py",
                 "--identity", identity, "--graph", graph,
                 "--min-stars", "100", "--apply",
                 "--observed-at", FIXED_TIME, "--snapshot", "fx")
        return graph, fx


class TestDoubleRun(LoaderChainCase):
    def test_second_run_changes_nothing(self):
        """One run and two runs must produce the same logical digest."""
        with tempfile.TemporaryDirectory() as td1, \
             tempfile.TemporaryDirectory() as td2:
            g1, _ = self._build(td1, runs=1)
            g2, _ = self._build(td2, runs=2)
            d1, d2 = digest.logical_digest(g1), digest.logical_digest(g2)
            cmp = digest.compare(d1, d2)
            self.assertTrue(
                cmp["equal"],
                f"a second run changed the graph. Differing tables: "
                f"{cmp['differing_tables']}")

    def test_five_runs_change_nothing(self):
        """Idempotency must not decay with repetition."""
        with tempfile.TemporaryDirectory() as td1, \
             tempfile.TemporaryDirectory() as td2:
            g1, _ = self._build(td1, runs=1)
            g5, _ = self._build(td2, runs=5)
            self.assertEqual(digest.logical_digest(g1)["overall"],
                             digest.logical_digest(g5)["overall"])

    def test_no_rank_drift(self):
        """The specific additive bug: observations must not accumulate."""
        with tempfile.TemporaryDirectory() as td1, \
             tempfile.TemporaryDirectory() as td2:
            g1, _ = self._build(td1, runs=1)
            g3, _ = self._build(td2, runs=3)
            def ratings(path):
                c = sqlite3.connect(path)
                try:
                    return dict(c.execute(
                        "SELECT person_id, value FROM person_observation "
                        "WHERE metric='rated_overall_mean' ORDER BY person_id"))
                finally:
                    c.close()
            one, three = ratings(g1), ratings(g3)
            self.assertTrue(one, "fixture produced no rating observations")
            self.assertEqual(
                one, three,
                "rated values drifted across runs -- the additive rank bug is back")

    def test_canonical_rank_score_is_never_written(self):
        """No loader may write the universal score column."""
        with tempfile.TemporaryDirectory() as td:
            g, _ = self._build(td, runs=2)
            c = sqlite3.connect(g)
            try:
                n = c.execute(
                    "SELECT COUNT(*) FROM person WHERE rank_score IS NOT NULL"
                ).fetchone()[0]
            finally:
                c.close()
            self.assertEqual(
                n, 0,
                f"{n} person rows carry rank_score. Canonical loading must not "
                "write a universal score; use observations and projections.")

    def test_every_observation_has_a_unit(self):
        """The absence of a unit is what made rank_score meaningless."""
        with tempfile.TemporaryDirectory() as td:
            g, _ = self._build(td)
            c = sqlite3.connect(g)
            try:
                bad = c.execute(
                    "SELECT COUNT(*) FROM person_observation "
                    "WHERE unit IS NULL OR unit=''").fetchone()[0]
                units = dict(c.execute(
                    "SELECT metric, unit FROM person_observation GROUP BY metric"))
            finally:
                c.close()
            self.assertEqual(bad, 0)
            # A metric must not appear under two different units.
            self.assertIn("github_stars_sum", units)
            self.assertEqual(units["github_stars_sum"], "stars")
            self.assertEqual(units["rated_overall_mean"], "rating_0_100")


class TestStaleSource(LoaderChainCase):
    def test_removed_repo_edge_is_pruned(self):
        """A repo absent from the new snapshot must lose its edge."""
        with tempfile.TemporaryDirectory() as td:
            fx = fixtures.write_all(td)
            graph = str(pathlib.Path(td) / "graph.sqlite")
            _run("build_people_graph_v2.py",
                 "--v1", fx["v1"], "--people", fx["books_people"],
                 "--books", fx["books"], "--out", graph,
                 "--observed-at", FIXED_TIME, "--books-snapshot", "fx")
            _run("load_owners_into_people_graph.py",
                 "--identity", fx["identity"], "--graph", graph,
                 "--min-stars", "100", "--apply",
                 "--observed-at", FIXED_TIME, "--snapshot", "fx")

            c = sqlite3.connect(graph)
            before = c.execute(
                "SELECT COUNT(*) FROM person_content WHERE domain='github' "
                "AND content_ref='megacorp-labs/smallthing'").fetchone()[0]
            c.close()
            self.assertEqual(before, 1, "fixture edge missing; test is invalid")

            # Second snapshot: that repo no longer exists.
            src = sqlite3.connect(fx["identity"])
            src.execute("DELETE FROM repo_card WHERE full_name=?",
                        ("megacorp-labs/smallthing",))
            src.commit()
            src.close()

            _run("load_owners_into_people_graph.py",
                 "--identity", fx["identity"], "--graph", graph,
                 "--min-stars", "100", "--apply",
                 "--observed-at", FIXED_TIME, "--snapshot", "fx2")

            c = sqlite3.connect(graph)
            after = c.execute(
                "SELECT COUNT(*) FROM person_content WHERE domain='github' "
                "AND content_ref='megacorp-labs/smallthing'").fetchone()[0]
            c.close()
            self.assertEqual(
                after, 0,
                "a repo removed from the source kept its edge -- the graph is "
                "accumulating every snapshot rather than reflecting the current one")

    def test_changed_star_count_updates(self):
        """INSERT OR IGNORE froze the first value seen; REPLACE must update."""
        with tempfile.TemporaryDirectory() as td:
            fx = fixtures.write_all(td)
            graph = str(pathlib.Path(td) / "graph.sqlite")
            _run("build_people_graph_v2.py",
                 "--v1", fx["v1"], "--people", fx["books_people"],
                 "--books", fx["books"], "--out", graph,
                 "--observed-at", FIXED_TIME, "--books-snapshot", "fx")
            _run("load_owners_into_people_graph.py",
                 "--identity", fx["identity"], "--graph", graph,
                 "--min-stars", "100", "--apply",
                 "--observed-at", FIXED_TIME, "--snapshot", "fx")

            src = sqlite3.connect(fx["identity"])
            src.execute("UPDATE repo_card SET stars=? WHERE full_name=?",
                        (777777, "quietcrafter/serde-ish"))
            src.commit()
            src.close()

            _run("load_owners_into_people_graph.py",
                 "--identity", fx["identity"], "--graph", graph,
                 "--min-stars", "100", "--apply",
                 "--observed-at", FIXED_TIME, "--snapshot", "fx2")

            c = sqlite3.connect(graph)
            score = c.execute(
                "SELECT score FROM person_content WHERE content_ref=?",
                ("quietcrafter/serde-ish",)).fetchone()[0]
            c.close()
            self.assertEqual(
                score, 777777.0,
                "a changed star count did not update -- later snapshots are inert")

    def test_stale_topic_is_pruned(self):
        """A dropped GitHub topic must lose its person_topic edge."""
        with tempfile.TemporaryDirectory() as td:
            fx = fixtures.write_all(td)
            graph = str(pathlib.Path(td) / "graph.sqlite")
            _run("build_people_graph_v2.py",
                 "--v1", fx["v1"], "--people", fx["books_people"],
                 "--books", fx["books"], "--out", graph,
                 "--observed-at", FIXED_TIME, "--books-snapshot", "fx")
            for script in ("load_owners_into_people_graph.py",
                           "load_owner_topics.py"):
                _run(script, "--identity", fx["identity"], "--graph", graph,
                     "--min-stars", "100", "--apply",
                     "--observed-at", FIXED_TIME, "--snapshot", "fx")

            c = sqlite3.connect(graph)
            before = c.execute(
                "SELECT COUNT(*) FROM person_topic WHERE topic='compilers'"
            ).fetchone()[0]
            c.close()
            self.assertGreater(before, 0, "fixture topic missing; test invalid")

            src = sqlite3.connect(fx["identity"])
            src.execute(
                "UPDATE repo_card SET topics_json=? WHERE full_name LIKE ?",
                ('["rust"]', "quietcrafter/%"))
            src.commit()
            src.close()

            _run("load_owner_topics.py", "--identity", fx["identity"],
                 "--graph", graph, "--min-stars", "100", "--apply",
                 "--observed-at", FIXED_TIME, "--snapshot", "fx2")

            c = sqlite3.connect(graph)
            after = c.execute(
                "SELECT COUNT(*) FROM person_topic WHERE topic='compilers'"
            ).fetchone()[0]
            lcsh = c.execute(
                "SELECT COUNT(*) FROM person_topic WHERE scheme='lcsh'"
            ).fetchone()[0]
            c.close()
            self.assertEqual(after, 0, "a dropped topic kept its edge")
            self.assertGreater(
                lcsh, 0,
                "pruning github topics destroyed lcsh edges -- pruning must be "
                "scoped to the source that owns the rows")


if __name__ == "__main__":
    unittest.main(verbosity=2)
