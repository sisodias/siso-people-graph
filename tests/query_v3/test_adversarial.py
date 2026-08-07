"""Malformed and hostile database states must degrade, never hang or lie.

The read layer runs against whatever the builders produced, including states a
correct builder would not create -- half-applied merges, cycles from a
partially-undone operation, rows pointing at people who no longer exist. The
failure mode to avoid is the one this lane exists to fix: an error that looks
like a legitimate empty answer.
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


def _mutate(path, statements):
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=OFF")
    for sql, args in statements:
        con.execute(sql, args)
    con.commit()
    con.close()


ADD_PERSON = (
    "INSERT INTO person(person_id,name,kind,state,merged_into,origin,built_at) "
    "VALUES(?,?,?,?,?,?,'2026-08-06')"
)
ADD_SEARCH = "INSERT INTO person_search(person_id,name,aliases) VALUES(?,?,?)"


class MalformedStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "people_v2.sqlite")
        build_people_db(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_merge_cycle_terminates(self):
        """A <-> B merged into each other must collapse, not loop forever."""
        _mutate(self.path, [
            (ADD_PERSON, ("bk:cyc-a", "Cycle Person", "human", "merged",
                          "bk:cyc-b", "book")),
            (ADD_PERSON, ("bk:cyc-b", "Cycle Person", "human", "merged",
                          "bk:cyc-a", "book")),
            (ADD_SEARCH, ("bk:cyc-a", "Cycle Person", "Cycle")),
            (ADD_SEARCH, ("bk:cyc-b", "Cycle Person", "Cycle")),
        ])
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("Cycle Person")
        matches = r["result"]["matches"]
        self.assertEqual(len(matches), 1, "a cycle is one cluster, not two")
        self.assertEqual(set(matches[0]["identity"]["member_ids"]),
                         {"bk:cyc-a", "bk:cyc-b"})

    def test_self_merge_terminates(self):
        _mutate(self.path, [
            (ADD_PERSON, ("bk:selfie", "Selfie Person", "human", "merged",
                          "bk:selfie", "book")),
            (ADD_SEARCH, ("bk:selfie", "Selfie Person", "Selfie")),
        ])
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("Selfie Person")
        self.assertEqual(len(r["result"]["matches"]), 1)

    def test_claim_referencing_a_missing_person_does_not_crash(self):
        """A dangling decision must not take down the read path."""
        _mutate(self.path, [
            ("INSERT INTO identity_claim(person_a,person_b,method,confidence,"
             "evidence,status,decided_by,created_at) "
             "VALUES('bk:kant','zz:ghost','manual',1.0,'dangling','accepted',"
             "'reviewer','2026-08-06')", ()),
        ])
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("Kant")
        self.assertTrue(r["result"]["matches"])
        ids = {m["person_id"] for m in r["result"]["matches"]}
        self.assertNotIn("zz:ghost", ids,
                         "a person row that does not exist must not be invented")

    def test_merged_into_pointing_at_a_missing_person(self):
        _mutate(self.path, [
            (ADD_PERSON, ("bk:orphan", "Orphan Person", "human", "merged",
                          "zz:nowhere", "book")),
            (ADD_SEARCH, ("bk:orphan", "Orphan Person", "Orphan")),
        ])
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("Orphan Person")
        self.assertIsInstance(r["result"]["matches"], list)

    def test_long_merge_chain_resolves_to_one_person(self):
        """Transitivity over accepted decisions, past the expansion bound."""
        stmts = []
        for i in range(12):
            nxt = f"bk:chain-{i + 1}" if i < 11 else None
            stmts.append((ADD_PERSON, (f"bk:chain-{i}", "Chain Person", "human",
                                       "merged" if nxt else "linked", nxt,
                                       "book")))
            stmts.append((ADD_SEARCH, (f"bk:chain-{i}", "Chain Person", "Chain")))
        _mutate(self.path, stmts)
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("Chain Person", limit=20)
        matches = r["result"]["matches"]
        self.assertEqual(len(matches), 1,
                         f"a 12-long chain must be ONE person, got "
                         f"{[m['person_id'] for m in matches]}")
        self.assertEqual(matches[0]["person_id"], "bk:chain-11",
                         "the only live row must be canonical")

    def test_names_with_sql_metacharacters_are_bound_not_interpolated(self):
        hostile = ["'; DROP TABLE person; --", '" OR 1=1 --', "100%", "_", "\\"]
        with QueryEngine(root=self.tmp.name) as e:
            for name in hostile:
                r = e.who(name)
                self.assertIn("matches", r["result"], name)
            # The table must still be there afterwards.
            still = e.who("Kant")
        self.assertTrue(still["result"]["matches"], "person table survived")

    def test_unreadable_database_is_reported_not_swallowed(self):
        """A corrupt file must produce a stated failure, not a clean empty."""
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "people_v2.sqlite")
            with open(bad, "wb") as fh:
                fh.write(b"this is definitely not a sqlite database")
            try:
                with QueryEngine(root=tmp) as e:
                    r = e.who("anyone")
            except sqlite3.DatabaseError:
                return  # an explicit raise is an acceptable, honest failure
        self.assertTrue(
            r["warnings"] or r["coverage_gaps"],
            "a corrupt database must never look like a healthy empty result",
        )


if __name__ == "__main__":
    unittest.main()
