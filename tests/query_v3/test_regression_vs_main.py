"""Prove the fix discriminates: run the OLD code and assert it is broken.

A regression test that passes both before and after a change proves nothing
about the change. This module pins the actual before/after by extracting
`loaders/ask.py` as it exists on origin/main, running it against the same
fixture the new engine uses, and asserting the old behaviour is the defective
one -- then asserting the new behaviour differs in the specific way that matters.

If PG-AUDIT-002 is ever reintroduced, `test_new_engine_resolves_what_old_missed`
fails. If someone deletes the defect from history and these fixtures stop
demonstrating it, `test_old_code_returned_duplicates` fails loudly rather than
quietly passing -- a broken proof must not look like a healthy one.

Skips (never silently passes) when git or origin/main is unavailable, e.g. in a
checkout without remotes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from query_v3 import QueryEngine  # noqa: E402
from tests.query_v3.fixtures import build_people_db  # noqa: E402


# Pinned pre-fix baseline. MUST NOT be a moving ref: once the query-surface fix
# merged to main, "origin/main" became the FIXED code and these regression tests
# failed because they had succeeded. de048bb is the last commit whose
# loaders/ask.py still carries the defects asserted below.
PRE_FIX_BASELINE = "de048bb3b34bf931b56fd741cb46c1334acdfb98"


def _old_ask_source() -> str | None:
    """loaders/ask.py as it stood BEFORE the query-surface fix (pinned)."""
    for ref in (PRE_FIX_BASELINE,):
        try:
            out = subprocess.run(
                ["git", "-C", REPO, "show", f"{ref}:loaders/ask.py"],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    return None


class RegressionVsMainTest(unittest.TestCase):
    """The before/after proof for PG-AUDIT-002 / PGRT-004."""

    @classmethod
    def setUpClass(cls):
        cls.old_src = _old_ask_source()
        cls.tmp = tempfile.TemporaryDirectory()
        build_people_db(os.path.join(cls.tmp.name, "people_v2.sqlite"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run_old(self, *args) -> dict:
        if self.old_src is None:
            self.skipTest("pinned baseline loaders/ask.py unavailable (shallow clone?)")
        script = os.path.join(self.tmp.name, "ask_main_snapshot.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(self.old_src)
        out = subprocess.run(
            [sys.executable, script, *args],
            cwd=self.tmp.name, capture_output=True, text=True, timeout=60,
        )
        self.assertTrue(out.stdout.strip(),
                        f"old ask.py produced no output: {out.stderr[:400]}")
        return json.loads(out.stdout)

    def test_old_code_returned_duplicates(self):
        """BEFORE: the accepted claim had no effect; two rows, one human."""
        data = self._run_old("--who", "Kant")
        ids = [m["person_id"] for m in data["matches"]]
        self.assertIn("bk:kant", ids)
        self.assertIn("gh:kant", ids)

        by_id = {m["person_id"]: m for m in data["matches"]}
        # Split coverage is the visible symptom: neither row knows about the other.
        self.assertEqual(set(by_id["bk:kant"]["produced"]), {"book"})
        self.assertEqual(set(by_id["gh:kant"]["produced"]), {"github"})

        # And no truth contract at all.
        for field in ("identity_resolution", "page", "coverage_gaps",
                      "capabilities"):
            self.assertNotIn(field, data)

    def test_new_engine_resolves_what_old_missed(self):
        """AFTER: one person, aggregated coverage, decision reported."""
        with QueryEngine(root=self.tmp.name) as e:
            new = e.who("Kant")

        kant = [m for m in new["result"]["matches"]
                if m["person_id"] in ("bk:kant", "gh:kant")]
        self.assertEqual(len(kant), 1)
        self.assertEqual(set(kant[0]["source_coverage"]["domains"]),
                         {"book", "github"})
        self.assertTrue(new["identity_resolution"]["applied"])

    def test_old_works_could_not_report_truncation(self):
        """BEFORE: count=len(rows) against a hard LIMIT 200.

        A person with exactly 200 works and a person with 40,000 are reported
        identically, and nothing in the payload lets a caller tell them apart.
        """
        data = self._run_old("--works", "Prolific Author")
        self.assertEqual(data["count"], 200,
                         "old code caps at 200 and calls that the count")
        self.assertEqual(len(data["works"]), 200)
        self.assertNotIn("page", data)
        self.assertNotIn("total_matched", data)

    def test_new_works_reports_truncation_honestly(self):
        """AFTER: the real total, the page size, and an explicit flag."""
        with QueryEngine(root=self.tmp.name) as e:
            new = e.works("Prolific Author", limit=200)
        page = new["page"]
        self.assertEqual(page["total_matched"], 250)
        self.assertEqual(page["returned"], 200)
        self.assertTrue(page["truncated"])
        self.assertTrue(page["counts_are_exact"])
        self.assertTrue(any("of 250 works" in g for g in new["coverage_gaps"]))

    def test_old_code_silently_used_the_scan(self):
        """BEFORE: the FTS query raised, was swallowed, and LIKE answered.

        The old payload has no field that could reveal this, which is precisely
        why it survived: the code reads as if it uses the index.
        """
        data = self._run_old("--who", "Kant")
        self.assertNotIn("execution", data)

        with QueryEngine(root=self.tmp.name) as e:
            new = e.who("Kant")
        self.assertEqual(new["execution"]["search_path"], "fts5",
                         "the new engine must actually reach the index")


if __name__ == "__main__":
    unittest.main()
