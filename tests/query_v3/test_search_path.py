"""Prove WHICH execution path ran -- not merely that a result came back.

This is the explicit lesson from the reasoning ledger. The old query was:

    WHERE people.person_search MATCH ?

which raises `no such column: people.person_search`, because a schema-qualified
name is not a valid FTS5 MATCH left operand. The error was swallowed by a bare
`except sqlite3.Error`, and the code fell through to a LIKE scan. Every name
lookup in the system therefore ran a full table scan while the source read as if
it were using the index -- and a test asserting only "Kant was found" passes in
both worlds. Such a test proves nothing about the defect.

An alias is equally invalid (`... person_search s WHERE s MATCH ?` -> `no such
column: s`), which is why these tests assert against a real database rather than
a remembered rule.

So the contract is: every response declares `execution.search_path`, and these
tests assert on that declaration, plus an independent verification that the FTS
query is genuinely executable against the schema.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from query_v3 import QueryEngine  # noqa: E402
from tests.query_v3.fixtures import build_people_db  # noqa: E402


class SearchPathTest(unittest.TestCase):
    def test_fts_path_is_actually_used_when_index_exists(self):
        """The indexed path must run, and the response must say it ran."""
        with tempfile.TemporaryDirectory() as tmp:
            build_people_db(os.path.join(tmp, "people_v2.sqlite"), with_fts=True)
            with QueryEngine(root=tmp) as e:
                r = e.who("Kant")

        self.assertEqual(r["execution"]["search_path"], "fts5",
                         "with an FTS index present the fts5 path MUST execute")
        self.assertTrue(r["execution"]["search_path_is_indexed"])
        self.assertTrue(r["result"]["matches"], "and it must return results")

        # A degraded run declares itself as a coverage gap. There must be none.
        self.assertFalse(
            [g for g in r["coverage_gaps"] if "linear LIKE scan" in g],
            "the fts5 run must not report a LIKE-scan fallback",
        )

    def test_the_old_query_form_really_is_broken(self):
        """Pin the defect itself, so a regression to it is caught immediately.

        If someone reinstates the schema-qualified form, this test tells them
        exactly why it cannot work -- rather than the failure hiding behind an
        except clause for another six months.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "people_v2.sqlite")
            build_people_db(path, with_fts=True)
            con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            con.execute(f"ATTACH DATABASE 'file:{path}?mode=ro' AS people")

            with self.assertRaises(sqlite3.OperationalError) as ctx:
                con.execute(
                    "SELECT person_id FROM people.person_search "
                    "WHERE people.person_search MATCH ?", ("Kant",)
                ).fetchall()
            self.assertIn("no such column", str(ctx.exception))

            # The aliased form is broken too -- a plausible "fix" that is not one.
            with self.assertRaises(sqlite3.OperationalError):
                con.execute(
                    "SELECT person_id FROM people.person_search s "
                    "WHERE s MATCH ?", ("Kant",)
                ).fetchall()

            # The form the engine uses must work.
            rows = con.execute(
                "SELECT person_id FROM people.person_search "
                "WHERE person_search MATCH ?", ('"Kant"',)
            ).fetchall()
            self.assertTrue(rows, "the unaliased table name is the correct operand")
            con.close()

    def test_like_fallback_is_declared_when_index_is_absent(self):
        """Without an index the scan is legitimate -- but must be disclosed."""
        with tempfile.TemporaryDirectory() as tmp:
            build_people_db(os.path.join(tmp, "people_v2.sqlite"), with_fts=False)
            with QueryEngine(root=tmp) as e:
                r = e.who("Kant")

        self.assertEqual(r["execution"]["search_path"], "like_scan")
        self.assertFalse(r["execution"]["search_path_is_indexed"])
        self.assertTrue(
            any("linear LIKE scan" in g for g in r["coverage_gaps"]),
            "a degraded search path must be declared, never silent",
        )
        self.assertTrue(r["result"]["matches"], "and it must still answer")

    def test_fts_special_characters_do_not_break_or_change_meaning(self):
        """User text is a phrase, not query syntax.

        Unquoted, a name containing OR/NEAR/quotes is parsed as an FTS
        expression: it either errors or silently means something else. Either
        way the caller is misled.
        """
        with tempfile.TemporaryDirectory() as tmp:
            build_people_db(os.path.join(tmp, "people_v2.sqlite"), with_fts=True)
            with QueryEngine(root=tmp) as e:
                for hostile in ['Kant" OR name:*', "O'Brien", "NEAR(a b)",
                                "a-b", '"', "AND OR NOT"]:
                    r = e.who(hostile)
                    self.assertEqual(r["execution"]["search_path"], "fts5",
                                     f"{hostile!r} must not knock us off fts5")
                    self.assertIn("matches", r["result"])

    def test_empty_query_is_handled(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_people_db(os.path.join(tmp, "people_v2.sqlite"), with_fts=True)
            with QueryEngine(root=tmp) as e:
                r = e.who("")
        self.assertIn("matches", r["result"])


if __name__ == "__main__":
    unittest.main()
