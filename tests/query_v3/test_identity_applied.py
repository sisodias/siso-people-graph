"""PG-AUDIT-002 / PGRT-004: accepted identity decisions must affect reads.

This is the regression suite for the defect this lane exists to fix. Before the
change, a reviewer could accept an identity claim, the queue would report
success, and `who()` would still return both rows as separate people -- the
reviewer's decision had no observable effect anywhere.

`test_accepted_claim_changes_the_read` is the test that fails against the old
loaders/ask.py and passes against the query library. It is the proof that the
review loop is now connected to the read path.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from query_v3 import QueryEngine  # noqa: E402
from tests.query_v3.fixtures import build_people_db  # noqa: E402


class IdentityAppliedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        build_people_db(os.path.join(cls.tmp.name, "people_v2.sqlite"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def engine(self):
        return QueryEngine(root=self.tmp.name)

    # ------------------------------------------------------------------ V1

    def test_accepted_claim_changes_the_read(self):
        """THE regression test. Two source rows, one accepted claim, one person.

        Old behaviour: two matches, both named "Immanuel Kant", each showing
        only its own domain -- the accepted claim was never read.
        New behaviour: one person, coverage aggregated across both rows, and the
        decision that caused it reported in the response.
        """
        with self.engine() as e:
            r = e.who("Kant")

        kant = [m for m in r["result"]["matches"]
                if m["person_id"] in ("bk:kant", "gh:kant")]
        self.assertEqual(len(kant), 1,
                         "gh:kant and bk:kant must resolve to ONE person")

        person = kant[0]
        self.assertEqual(set(person["identity"]["member_ids"]),
                         {"bk:kant", "gh:kant"})
        self.assertEqual(person["identity"]["merged_row_count"], 1)

        # Coverage must span both source rows: this is the user-visible payoff.
        self.assertEqual(set(person["source_coverage"]["domains"]),
                         {"book", "github"})
        self.assertEqual(person["source_coverage"]["by_domain"]["github"], 1)

        # And the response must say WHY, not merge silently.
        signals = {d["signal"] for d in r["identity_resolution"]["applied"]}
        self.assertIn("identity_claim.accepted", signals)
        for d in r["identity_resolution"]["applied"]:
            self.assertEqual(d["evidence"]["grade"],
                             "accepted_identity_decision")

    def test_accepted_claim_applies_without_merged_into(self):
        """The reviewer-invisible window: decided, but not yet rebuilt.

        Ada Lovelace has an accepted claim and NO merged_into on either row. A
        read layer that trusted only the applied merge would still show two
        people until the next build -- exactly the gap where a reviewer's work
        disappears.
        """
        with self.engine() as e:
            r = e.who("Lovelace")
        matches = r["result"]["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(set(matches[0]["identity"]["member_ids"]),
                         {"bk:lovelace", "gh:lovelace"})
        signals = {d["signal"] for d in r["identity_resolution"]["applied"]}
        self.assertEqual(signals, {"identity_claim.accepted"})

    def test_proposed_claim_is_reported_but_never_applied(self):
        """Two different John Murrays. A hypothesis must not become a merge."""
        with self.engine() as e:
            r = e.who("John Murray")
        ids = {m["person_id"] for m in r["result"]["matches"]}
        self.assertEqual(ids, {"bk:murray-1", "bk:murray-2"},
                         "a proposed claim must NOT merge two people")

        unresolved = r["identity_resolution"]["unresolved"]
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]["status"], "proposed")
        self.assertTrue(
            any("proposed identity claims" in g.lower()
                for g in r["coverage_gaps"]),
            "ambiguity must be declared as a coverage gap",
        )

    def test_rejected_claim_is_never_applied(self):
        """A rejected claim is a decision NOT to merge. It must be honoured."""
        with self.engine() as e:
            r = e.who("Kant")
        ids = {m["person_id"] for m in r["result"]["matches"]}
        self.assertIn("bk:decoy", ids,
                      "a rejected claim must leave the decoy separate")
        for m in r["result"]["matches"]:
            self.assertNotIn("bk:decoy", m["identity"]["member_ids"]
                             if m["person_id"] != "bk:decoy" else [])

    def test_merged_row_is_never_the_canonical_answer(self):
        """The losing row of an applied merge must not represent the person."""
        with self.engine() as e:
            r = e.who("Kant")
        for m in r["result"]["matches"]:
            if "gh:kant" in m["identity"]["member_ids"]:
                self.assertEqual(m["person_id"], "bk:kant")
                self.assertEqual(m["state"], "linked")

    def test_works_aggregate_across_merged_rows(self):
        """Works must follow the person, not the row that happened to match."""
        with self.engine() as e:
            r = e.works("Kant", limit=50)
        domains = {w["domain"] for w in r["result"]["works"]}
        self.assertIn("github", domains,
                      "the github row's works must appear under the merged person")
        self.assertIn("book", domains)
        self.assertEqual(set(r["result"]["person"]["member_ids"]),
                         {"bk:kant", "gh:kant"})

    def test_identity_mode_is_declared(self):
        with self.engine() as e:
            r = e.who("Kant")
        self.assertEqual(r["identity_resolution"]["mode"], "v2")
        self.assertEqual(r["capabilities"]["identity_mode"], "v2")


class NoIdentityTablesTest(unittest.TestCase):
    """A database with no identity machinery must SAY so, not merge silently."""

    def test_missing_identity_claim_is_declared_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "people_v2.sqlite")
            build_people_db(path)
            import sqlite3
            con = sqlite3.connect(path)
            con.execute("DROP TABLE identity_claim")
            con.commit()
            con.close()

            with QueryEngine(root=tmp) as e:
                r = e.who("Lovelace")

            self.assertEqual(r["identity_resolution"]["mode"], "none")
            self.assertTrue(
                any("duplicate" in w.lower() for w in r["warnings"]),
                "no-identity mode must warn that duplicates are possible",
            )
            # Without decisions, the two Lovelace rows are honestly two rows.
            self.assertEqual(len(r["result"]["matches"]), 2)


if __name__ == "__main__":
    unittest.main()
