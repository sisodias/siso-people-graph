#!/usr/bin/env python3
"""Reproducibility, digest, manifest and projection tests.

The headline test is test_two_clean_builds_are_logically_equal, which is the
acceptance criterion both specs state: two clean fixture builds in separate
directories with equal logical digests and row counts.
"""
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from build_v3 import (build, digest, fixtures, manifest, project,  # noqa: E402
                      validate, verify_reproducible)


class TestTwoCleanBuilds(unittest.TestCase):
    def test_two_clean_builds_are_logically_equal(self):
        """THE acceptance criterion."""
        with tempfile.TemporaryDirectory() as td:
            rep = verify_reproducible.verify(td)
            self.assertTrue(
                rep["logically_equal"],
                f"digests differ. Tables: {rep['differing_tables']}")
            self.assertTrue(rep["counts_equal"], "row counts differ")
            self.assertNotEqual(rep["validation_a"], "fail")
            self.assertNotEqual(rep["validation_b"], "fail")

    def test_binary_stability_is_measured_not_assumed(self):
        """We must report the byte answer, whatever it is.

        The test asserts that the measurement is PRESENT and self-consistent,
        not that byte identity holds -- asserting byte identity would encode an
        assumption the spec explicitly says to measure instead.
        """
        with tempfile.TemporaryDirectory() as td:
            rep = verify_reproducible.verify(td)
            binary = rep["binary_reproducibility"]
            self.assertIn("byte_identical", binary)
            self.assertIsInstance(binary["byte_identical"], bool)
            self.assertEqual(
                binary["byte_identical"],
                binary["sha256_a"] == binary["sha256_b"],
                "the reported byte verdict disagrees with the hashes")

    def test_distinct_run_ids_do_not_change_the_digest(self):
        """Run metadata must not leak into canonical facts."""
        with tempfile.TemporaryDirectory() as td:
            a = build.build_fixture(pathlib.Path(td) / "a", run_id="alpha")
            b = build.build_fixture(pathlib.Path(td) / "b", run_id="beta")
            self.assertEqual(a["digest"], b["digest"])
            # ...and the run rows genuinely differ, so the test is not vacuous.
            ca = sqlite3.connect(a["graph"])
            cb = sqlite3.connect(b["graph"])
            try:
                ra = ca.execute("SELECT run_id FROM build_run").fetchall()
                rb = cb.execute("SELECT run_id FROM build_run").fetchall()
            finally:
                ca.close()
                cb.close()
            self.assertNotEqual(ra, rb, "run ids were not actually different")


class TestDigest(unittest.TestCase):
    def _db(self, path, rows):
        c = sqlite3.connect(path)
        c.execute("CREATE TABLE t (a TEXT, b REAL)")
        c.executemany("INSERT INTO t VALUES (?,?)", rows)
        c.commit()
        c.close()

    def test_insertion_order_does_not_change_the_digest(self):
        """Rows are sorted, so load order is irrelevant."""
        with tempfile.TemporaryDirectory() as td:
            p1 = str(pathlib.Path(td) / "1.sqlite")
            p2 = str(pathlib.Path(td) / "2.sqlite")
            self._db(p1, [("x", 1.0), ("y", 2.0), ("z", 3.0)])
            self._db(p2, [("z", 3.0), ("x", 1.0), ("y", 2.0)])
            self.assertEqual(digest.logical_digest(p1)["overall"],
                             digest.logical_digest(p2)["overall"])

    def test_integral_float_and_int_render_identically(self):
        """3 and 3.0 are the same measurement and must not differ."""
        with tempfile.TemporaryDirectory() as td:
            p1 = str(pathlib.Path(td) / "1.sqlite")
            p2 = str(pathlib.Path(td) / "2.sqlite")
            self._db(p1, [("x", 3)])
            self._db(p2, [("x", 3.0)])
            self.assertEqual(digest.logical_digest(p1)["overall"],
                             digest.logical_digest(p2)["overall"])

    def test_a_changed_value_changes_the_digest(self):
        """The digest must actually be sensitive, or it proves nothing."""
        with tempfile.TemporaryDirectory() as td:
            p1 = str(pathlib.Path(td) / "1.sqlite")
            p2 = str(pathlib.Path(td) / "2.sqlite")
            self._db(p1, [("x", 1.0)])
            self._db(p2, [("x", 1.5)])
            self.assertNotEqual(digest.logical_digest(p1)["overall"],
                                digest.logical_digest(p2)["overall"])

    def test_build_run_is_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            self.assertNotIn("build_run", digest.logical_digest(res["graph"])["tables"])

    def test_every_canonical_table_is_covered(self):
        """Regression test for a digest FALSE PASS found in review.

        _is_fts_shadow matched on suffix alone, so `person_content` -- the
        graph's central edge table -- was stripped to `person`, found to exist,
        and silently classified as an FTS shadow. It was therefore absent from
        the digest entirely: two builds differing in EVERY content edge would
        have produced identical digests, which is precisely the failure the
        digest exists to catch.

        This test pins the covered set explicitly. Adding a canonical table
        without adding it here is a deliberate act, not an accident.
        """
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            covered = set(digest.covered_tables(res["graph"]))
            must_cover = {
                "person", "person_content", "person_topic", "external_ids",
                "identity_claim", "person_observation", "person_projection",
            }
            missing = must_cover - covered
            self.assertEqual(
                missing, set(),
                f"canonical tables missing from the digest: {sorted(missing)}. "
                "A digest that skips a table certifies less than it appears to.")

    def test_a_changed_content_edge_changes_the_digest(self):
        """The direct proof that the false pass is closed.

        Mutating one person_content row must move the digest. Under the old
        suffix rule it did not.
        """
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            before = digest.logical_digest(res["graph"])["overall"]
            c = sqlite3.connect(res["graph"])
            try:
                c.execute("UPDATE person_content SET score = score + 1 "
                          "WHERE content_ref = 'quietcrafter/serde-ish'")
                self.assertEqual(c.total_changes, 1, "fixture row not found")
                c.commit()
            finally:
                c.close()
            self.assertNotEqual(
                before, digest.logical_digest(res["graph"])["overall"],
                "a changed content edge did not change the digest")

    def test_fts_shadows_are_still_excluded(self):
        """The fix must not over-correct into including the shadows."""
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            covered = set(digest.covered_tables(res["graph"]))
            for shadow in ("person_search_data", "person_search_idx",
                           "person_search_docsize", "person_search_config"):
                self.assertNotIn(shadow, covered,
                                 f"{shadow} is an FTS shadow and must be excluded")
            # ...while the virtual table itself remains covered.
            self.assertIn("person_search", covered)

    def test_pinned_build_run_is_deterministic(self):
        """finished_at used wall-clock even when the caller pinned a timestamp."""
        with tempfile.TemporaryDirectory() as td:
            a = build.build_fixture(pathlib.Path(td) / "a", run_id="same")
            b = build.build_fixture(pathlib.Path(td) / "b", run_id="same")
            def run_rows(p):
                c = sqlite3.connect(p)
                try:
                    return c.execute(
                        "SELECT run_id, started_at, finished_at, builder, "
                        "schema_version FROM build_run").fetchall()
                finally:
                    c.close()
            self.assertEqual(
                run_rows(a["graph"]), run_rows(b["graph"]),
                "build_run differs between two pinned builds with the same run id")


class TestManifests(unittest.TestCase):
    def test_manifest_round_trips(self):
        with tempfile.TemporaryDirectory() as td:
            m = manifest.SourceManifest(
                source_id="s", snapshot="snap-1", uri_class="fixture",
                digest="deadbeef", rights_revision="r1",
                acquired_at="2026-08-06T00:00:00Z", loader_version="l1",
                schema_version="people_schema_v2",
                row_contracts=[manifest.RowContract("t", 1, 10, ["a"])])
            p = m.write(td)
            back = manifest.SourceManifest.read(p)
            self.assertEqual(back.to_dict(), m.to_dict())

    def test_literal_uri_is_rejected(self):
        """A manifest must not publish vault topology."""
        with self.assertRaises(ValueError):
            manifest.SourceManifest(
                source_id="s", snapshot="s", uri_class="/Volumes/vault/x.sqlite",
                digest="d", rights_revision="r", acquired_at="t",
                loader_version="l", schema_version="v")

    def test_manifests_are_written_for_every_source(self):
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            mans = manifest.load_all(pathlib.Path(res["out_dir"]) / "manifests")
            self.assertGreater(len(mans), 0)
            for m in mans:
                self.assertTrue(m.digest)
                self.assertTrue(m.rights_revision)
                self.assertTrue(m.snapshot)
                self.assertTrue(m.row_contracts, f"{m.source_id} has no contract")

    def test_digest_verification_detects_a_changed_source(self):
        with tempfile.TemporaryDirectory() as td:
            fx = fixtures.write_all(td)
            m = manifest.SourceManifest(
                source_id="identity", snapshot="s", uri_class="fixture",
                digest=manifest.sha256_file(fx["identity"]),
                rights_revision="r", acquired_at="t", loader_version="l",
                schema_version="v")
            ok, _ = manifest.verify_digest(m, fx["identity"])
            self.assertTrue(ok)
            c = sqlite3.connect(fx["identity"])
            c.execute("UPDATE repo_card SET stars=1 WHERE full_name LIKE '%'")
            c.commit()
            c.close()
            ok2, actual = manifest.verify_digest(m, fx["identity"])
            self.assertFalse(ok2, "a modified source was not detected")
            self.assertNotEqual(actual, m.digest)


class TestProjections(unittest.TestCase):
    def test_fame_and_value_rank_differently(self):
        """The whole reason a single rank_score was wrong.

        quietcrafter has 1,200 stars and a 95 rating; megacorp-labs has 500,000
        stars and a 42 rating. Popularity and rated value must therefore produce
        DIFFERENT leaders -- which one blended score cannot express. This is the
        Foundry dtolnay-vs-facebook inversion in miniature.
        """
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            c = sqlite3.connect(res["graph"])
            try:
                pop = c.execute(
                    "SELECT person_id FROM person_projection WHERE "
                    "projection='github_popularity' ORDER BY rank LIMIT 1"
                ).fetchone()[0]
                val = c.execute(
                    "SELECT person_id FROM person_projection WHERE "
                    "projection='rated_value' ORDER BY rank LIMIT 1"
                ).fetchone()[0]
            finally:
                c.close()
            self.assertEqual(pop, "gh:megacorp-labs")
            self.assertEqual(val, "gh:quietcrafter")
            self.assertNotEqual(
                pop, val,
                "popularity and rated value produced the same leader; the "
                "fixture no longer exercises the fame-vs-value distinction")

    def test_projection_carries_method_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            c = sqlite3.connect(res["graph"])
            try:
                rows = c.execute(
                    "SELECT DISTINCT projection, method, method_version "
                    "FROM person_projection").fetchall()
            finally:
                c.close()
            self.assertGreater(len(rows), 1)
            for proj, method, version in rows:
                self.assertTrue(method, f"{proj} has no method description")
                self.assertTrue(version, f"{proj} has no method_version")

    def test_recompute_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            before = digest.logical_digest(res["graph"])["overall"]
            project.compute_all(res["graph"], computed_at=build.FIXTURE_OBSERVED_AT,
                                apply_changes=True)
            self.assertEqual(before, digest.logical_digest(res["graph"])["overall"])

    def test_ties_get_the_same_rank(self):
        """Equal values must not be ordered arbitrarily."""
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            c = sqlite3.connect(res["graph"])
            try:
                c.execute(
                    "INSERT OR REPLACE INTO person_observation VALUES "
                    "('gh:quietcrafter','tie_metric',5.0,'x','t','s','2026-01-01T00:00:00Z')")
                c.execute(
                    "INSERT OR REPLACE INTO person_observation VALUES "
                    "('gh:megacorp-labs','tie_metric',5.0,'x','t','s','2026-01-01T00:00:00Z')")
                c.commit()
            finally:
                c.close()
            project.PROJECTIONS["_tie_test"] = {
                "metric": "tie_metric", "method": "test", "method_version": "1",
                "caveat": "test only"}
            try:
                out = project.compute(res["graph"], "_tie_test",
                                      computed_at="2026-01-01T00:00:00Z")
                ranks = [t["rank"] for t in out["top"]]
                self.assertEqual(ranks, [1, 1], f"ties not handled: {out['top']}")
            finally:
                del project.PROJECTIONS["_tie_test"]


class TestValidation(unittest.TestCase):
    def test_clean_build_validates(self):
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            rep = validate.validate(res["graph"],
                                    pathlib.Path(res["out_dir"]) / "manifests")
            self.assertNotEqual(rep["status"], "fail",
                                f"failed stages: {rep['failed_stages']}")

    def test_validator_detects_an_orphan_edge(self):
        """The validator must actually catch things, or it is decoration."""
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            c = sqlite3.connect(res["graph"])
            c.execute("PRAGMA foreign_keys=OFF")
            c.execute("INSERT INTO person_content "
                      "(person_id,domain,content_ref,role,source) "
                      "VALUES ('gh:ghost','github','ghost/repo','owner','x')")
            c.commit()
            c.close()
            rep = validate.validate(res["graph"])
            self.assertEqual(rep["status"], "fail")
            self.assertIn("orphan_edges", rep["failed_stages"])

    def test_validator_detects_rank_score_regression(self):
        """If a loader ever writes rank_score again, validation must fail."""
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            c = sqlite3.connect(res["graph"])
            c.execute("UPDATE person SET rank_score=1.0 "
                      "WHERE person_id='gh:megacorp-labs'")
            c.commit()
            c.close()
            rep = validate.validate(res["graph"])
            self.assertEqual(rep["status"], "fail")
            self.assertIn("observations", rep["failed_stages"])

    def test_validator_detects_duplicate_external_identity(self):
        with tempfile.TemporaryDirectory() as td:
            res = build.build_fixture(pathlib.Path(td) / "a")
            c = sqlite3.connect(res["graph"])
            c.execute("INSERT INTO person (person_id,name,origin,built_at) "
                      "VALUES ('gh:twin','Twin','github','2026-01-01T00:00:00Z')")
            c.execute("INSERT INTO external_ids VALUES "
                      "('gh:twin','github_login','quietcrafter',1.0,'x')")
            c.commit()
            c.close()
            rep = validate.validate(res["graph"])
            self.assertIn("duplicate_ids", rep["failed_stages"])


class TestNoAssetsCommitted(unittest.TestCase):
    def test_no_sqlite_or_archive_in_the_tree(self):
        """Spec: no SQLite/corpus asset is committed."""
        bad = []
        for pattern in ("*.sqlite", "*.sqlite-wal", "*.sqlite-shm", "*.gz", "*.zst"):
            bad.extend(p for p in REPO.rglob(pattern) if ".git" not in p.parts)
        self.assertEqual(bad, [], f"data assets present in the tree: {bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
