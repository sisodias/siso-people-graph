#!/usr/bin/env python3
"""The regression test for PG-AUDIT-004 / PGRT-001.

THIS TEST FAILS ON CURRENT MAIN. That is its purpose. On main,
build_people_graph_v2.py resolves its schema as

    os.path.join(os.path.dirname(os.path.abspath(__file__)), "people_schema_v2.sql")

which is `loaders/people_schema_v2.sql`, while the tracked file lives at
`schema/people_schema_v2.sql`. A clean checkout therefore raises
FileNotFoundError before reading a single byte of input, and the build only ever
worked in the original author's untracked local layout.

test_build_runs_from_temporary_directory is the direct proof: it copies nothing,
invokes the loader as a subprocess from a temp cwd, and requires exit 0.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from build_v3 import fixtures, paths  # noqa: E402


class TestPathResolution(unittest.TestCase):
    def test_schema_resolves_into_schema_dir_not_loaders(self):
        """The exact defect, asserted as a path fact."""
        resolved = paths.schema_v2()
        self.assertTrue(resolved.exists(),
                        f"schema not found at {resolved}")
        self.assertEqual(resolved.parent.name, "schema",
                         "schema must resolve into schema/, not loaders/ -- "
                         "the loaders/ assumption is the clean-checkout bug")

    def test_repo_root_is_independent_of_cwd(self):
        """Resolution must not depend on where the process was started."""
        before = paths.REPO_ROOT
        cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as td:
                os.chdir(td)
                import importlib
                importlib.reload(paths)
                self.assertEqual(paths.REPO_ROOT, before)
                self.assertTrue(paths.schema_v2().exists())
        finally:
            os.chdir(cwd)
            import importlib
            importlib.reload(paths)

    def test_environment_override_is_honoured(self):
        """An operator can redirect an artifact without editing source."""
        with tempfile.TemporaryDirectory() as td:
            fake = pathlib.Path(td) / "elsewhere.sql"
            fake.write_text("-- test\n")
            os.environ["PG_SCHEMA_V2"] = str(fake)
            try:
                import importlib
                importlib.reload(paths)
                self.assertEqual(paths.schema_v2(), fake.resolve())
            finally:
                del os.environ["PG_SCHEMA_V2"]
                importlib.reload(paths)

    def test_missing_artifact_error_names_the_repo_root(self):
        """A failure must tell the reader where resolution looked."""
        with self.assertRaises(FileNotFoundError) as ctx:
            paths.require(pathlib.Path("/nonexistent/nope.sql"), "test artifact")
        msg = str(ctx.exception)
        self.assertIn("test artifact", msg)
        self.assertIn("repo root resolved to", msg)


class TestCleanCheckoutBuild(unittest.TestCase):
    def test_build_runs_from_temporary_directory(self):
        """THE acceptance test for the P0. Fails on main, passes here.

        Deliberately uses ONLY the flags that exist on main (--v1 --people
        --books --out), so that when this fails on main it fails because of the
        schema-path defect and not because a new flag is missing. Verified: on
        unmodified main this raises

            FileNotFoundError: .../loaders/people_schema_v2.sql

        which is exactly PG-AUDIT-004 / PGRT-001.
        """
        with tempfile.TemporaryDirectory() as td:
            fx = fixtures.write_all(td)
            out = pathlib.Path(td) / "graph.sqlite"
            proc = subprocess.run(
                [sys.executable,
                 str(REPO / "loaders" / "build_people_graph_v2.py"),
                 "--v1", fx["v1"], "--people", fx["books_people"],
                 "--books", fx["books"], "--out", str(out)],
                capture_output=True, text=True, cwd=td,
            )
            self.assertNotIn(
                "FileNotFoundError", proc.stderr,
                "the clean-checkout schema-path defect (PG-AUDIT-004) is "
                f"present:\n{proc.stderr}")
            self.assertEqual(
                proc.returncode, 0,
                f"clean-checkout build failed from a temp cwd.\n"
                f"stderr:\n{proc.stderr}")
            self.assertTrue(out.exists(), "no database was produced")
            summary = json.loads(proc.stdout)
            self.assertGreater(summary["person"], 0)

    def test_reproducible_flags_exist(self):
        """Separate from the P0 test on purpose.

        The build needs --observed-at to be reproducible, but a missing flag is
        a different failure from the path defect, and folding both into one test
        would let a flag-parsing error masquerade as the P0 being fixed.
        """
        proc = subprocess.run(
            [sys.executable, str(REPO / "loaders" / "build_people_graph_v2.py"),
             "--help"], capture_output=True, text=True)
        self.assertIn("--observed-at", proc.stdout)

    def test_build_does_not_depend_on_a_file_beside_the_loader(self):
        """Guard against the fix regressing into the same shape.

        If anything ever again resolves an artifact as dirname(loader)/x, this
        catches it: there is no .sql file in loaders/ to find.
        """
        stray = list((REPO / "loaders").glob("*.sql"))
        self.assertEqual(
            stray, [],
            f"SQL files must not live beside loaders: {stray}. "
            "That layout is what made the build machine-dependent.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
