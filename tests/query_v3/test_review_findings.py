"""Regression guards for the six defects found by independent cold review.

Every test here failed before the review. They are kept because each one guards
a claim the PR makes about itself, and an unguarded fix rots: the headline claim
"accepted identity decisions affect reads, and only accepted ones do" was FALSE
as originally shipped, and nothing in the original suite caught it.

The gap was a fixture blind spot, not a logic oversight. The fixtures only ever
built states where `merged_into` and `identity_claim` AGREED, so the code could
trust `merged_into` alone and every test still passed. The review supplied the
disagreeing states. That is the transferable lesson: a test suite written by the
same author as the code inherits the author's assumptions about what states are
possible.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from query_v3 import QueryEngine  # noqa: E402
from query_v3.resolver import MAX_EXPANSION_PASSES  # noqa: E402
from tests.query_v3.fixtures import build_people_db  # noqa: E402

SCHEMA = os.path.join(REPO, "schema", "people_schema_v2.sql")


def _fresh(tmp: str, extra: list[tuple]) -> str:
    """A people DB plus hand-built rows describing a contested state."""
    path = os.path.join(tmp, "people_v2.sqlite")
    build_people_db(path)
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=OFF")
    for sql, args in extra:
        con.execute(sql, args)
    con.commit()
    con.close()
    return path


P = ("INSERT INTO person(person_id,name,kind,state,merged_into,origin,built_at) "
     "VALUES(?,?,'human',?,?,'book','2026-08-06')")
S = "INSERT INTO person_search(person_id,name,aliases) VALUES(?,?,?)"
C = ("INSERT INTO identity_claim(person_a,person_b,method,confidence,evidence,"
     "status,decided_by,created_at) VALUES(?,?,'manual',1.0,'x',?,'rev',"
     "'2026-08-06')")
W = ("INSERT INTO person_content(person_id,domain,content_ref,role,score,title,"
     "source,observed_at) VALUES(?,?,?,'author',1.0,?,'loader','2026-08-06')")


class Finding1RejectedMergeTest(unittest.TestCase):
    """CRITICAL: merged_into was applied without checking the claim record.

    A build can apply a merge whose claim is later rejected. Trusting the applied
    merge alone means a REJECTED pair stays merged -- which falsifies the guarantee
    that only accepted decisions affect reads.
    """

    def test_rejected_claim_defeats_an_applied_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fresh(tmp, [
                (P, ("r:rej-b", "Rejected Merge", "linked", None)),
                (P, ("r:rej-a", "Rejected Merge", "merged", "r:rej-b")),
                (S, ("r:rej-a", "Rejected Merge", "Rejected")),
                (S, ("r:rej-b", "Rejected Merge", "Rejected")),
                (C, ("r:rej-a", "r:rej-b", "rejected")),
            ])
            with QueryEngine(root=tmp) as e:
                r = e.who("Rejected Merge")

        self.assertEqual(len(r["result"]["matches"]), 2,
                         "a rejected pair must NOT stay merged")
        refused = r["identity_resolution"].get("refused", [])
        self.assertTrue(refused, "the refusal must be reported, not silent")
        self.assertTrue(any("REJECT" in g for g in r["coverage_gaps"]))

    def test_applied_merge_with_only_a_proposed_claim_is_flagged(self):
        """Merging matches the build, but an unreviewed merge must say so."""
        with tempfile.TemporaryDirectory() as tmp:
            _fresh(tmp, [
                (P, ("p:prop-b", "Proposed Merge", "linked", None)),
                (P, ("p:prop-a", "Proposed Merge", "merged", "p:prop-b")),
                (S, ("p:prop-a", "Proposed Merge", "Proposed")),
                (S, ("p:prop-b", "Proposed Merge", "Proposed")),
                (C, ("p:prop-a", "p:prop-b", "proposed")),
            ])
            with QueryEngine(root=tmp) as e:
                r = e.who("Proposed Merge")

        decisions = r["result"]["matches"][0]["identity"]["decisions"]
        self.assertTrue(any(d.get("claim_status") == "proposed"
                            for d in decisions),
                        "an unreviewed merge must be distinguishable")
        self.assertTrue(any("no reviewer accepted it" in g
                            for g in r["coverage_gaps"]))


class Finding2ReverseTraversalTest(unittest.TestCase):
    """HIGH: expansion followed merged_into forward only.

    Searching the winner did not pull in rows merged INTO it, so the same person
    returned different works depending on which name the caller typed.
    """

    def test_winner_and_loser_return_the_same_person(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fresh(tmp, [
                (P, ("rev:winner", "Reverse Winner", "linked", None)),
                (P, ("rev:loser", "Different Loser", "merged", "rev:winner")),
                (S, ("rev:winner", "Reverse Winner", "Reverse")),
                (S, ("rev:loser", "Different Loser", "Different")),
                (W, ("rev:winner", "book", "8001", "Winner Work")),
                (W, ("rev:loser", "book", "8002", "Loser Work")),
            ])
            with QueryEngine(root=tmp) as e:
                winner = e.works("Reverse Winner", limit=20)
                loser = e.works("Different Loser", limit=20)

        self.assertEqual(winner["page"]["total_matched"], 2,
                         "the winner must include works of rows merged into it")
        self.assertEqual(loser["page"]["total_matched"], 2)
        self.assertEqual(set(winner["result"]["person"]["member_ids"]),
                         set(loser["result"]["person"]["member_ids"]),
                         "which name was typed must not change the person")


class Finding3ExpansionBoundTest(unittest.TestCase):
    """HIGH: the pass cap truncated valid clusters silently.

    The bound stays -- an unbounded walk would let one lookup traverse the
    corpus -- but a truncated cluster must be DECLARED, not returned as whole.
    """

    def test_truncated_cluster_declares_itself_incomplete(self):
        chain = []
        n = MAX_EXPANSION_PASSES + 6
        for i in range(n):
            chain.append((P, (f"long:{i:02d}",
                              "Long Seed" if i == 0 else f"Hidden {i:02d}",
                              "linked", None)))
            chain.append((S, (f"long:{i:02d}",
                              "Long Seed" if i == 0 else f"Hidden {i:02d}",
                              "Long" if i == 0 else "Hidden")))
            chain.append((W, (f"long:{i:02d}", "book", f"95{i:03d}",
                              f"Work {i}")))
        for i in range(n - 1):
            lo, hi = sorted((f"long:{i:02d}", f"long:{i + 1:02d}"))
            chain.append((C, (lo, hi, "accepted")))

        with tempfile.TemporaryDirectory() as tmp:
            _fresh(tmp, chain)
            with QueryEngine(root=tmp) as e:
                r = e.who("Long Seed")

        ident = r["result"]["matches"][0]["identity"]
        if len(ident["member_ids"]) < n:
            self.assertFalse(ident["cluster_complete"],
                             "a partial cluster must not claim completeness")
            self.assertTrue(any("INCOMPLETE" in g for g in r["coverage_gaps"]))
        else:
            self.assertTrue(ident["cluster_complete"])


class Finding4DirectionTest(unittest.TestCase):
    """MEDIUM: from/to echoed the schema's lexical pair ordering.

    identity_claim enforces person_a < person_b purely as a uniqueness device.
    Reporting that as direction produced decisions pointing FROM the surviving
    row TO the merged one -- contradicting canonical selection in the same
    response.
    """

    def test_direction_never_points_away_from_the_canonical_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fresh(tmp, [
                # 'aa:merged' sorts BEFORE 'zz:live', so stored order and merge
                # direction disagree -- which is the whole point of the case.
                (P, ("aa:merged", "Direction Pair", "merged", None)),
                (P, ("zz:live", "Direction Pair", "linked", None)),
                (S, ("aa:merged", "Direction Pair", "Direction")),
                (S, ("zz:live", "Direction Pair", "Direction")),
                (C, ("aa:merged", "zz:live", "accepted")),
            ])
            with QueryEngine(root=tmp) as e:
                r = e.who("Direction Pair")

        match = r["result"]["matches"][0]
        canonical = match["person_id"]
        self.assertEqual(canonical, "zz:live", "the live row must be canonical")
        for d in match["identity"]["decisions"]:
            if d.get("to") is not None and "note" not in d:
                self.assertEqual(d["to"], canonical,
                                 "a decision must point AT the canonical row")
                self.assertNotEqual(d["from"], canonical)


class Finding5And6V3ClusterTest(unittest.TestCase):
    """HIGH/MEDIUM: v3 clusters annotated instead of merging; errors swallowed."""

    @staticmethod
    def _with_cluster(tmp: str, ddl: str, rows: list[tuple]) -> str:
        path = _fresh(tmp, [
            (P, ("v3:a", "V3 Pair", "linked", None)),
            (P, ("v3:b", "V3 Pair", "linked", None)),
            (S, ("v3:a", "V3 Pair", "V3")),
            (S, ("v3:b", "V3 Pair", "V3")),
            (W, ("v3:a", "book", "7701", "A Work")),
            (W, ("v3:b", "book", "7702", "B Work")),
        ])
        con = sqlite3.connect(path)
        con.execute(ddl)
        for row in rows:
            con.execute(
                f"INSERT INTO identity_cluster VALUES({','.join('?' * len(row))})",
                row)
        con.commit()
        con.close()
        return path

    def test_v3_cluster_actually_merges(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._with_cluster(
                tmp,
                "CREATE TABLE identity_cluster(person_id TEXT, cluster_id TEXT)",
                [("v3:a", "c1"), ("v3:b", "c1")])
            with QueryEngine(root=tmp) as e:
                r = e.who("V3 Pair")

        self.assertEqual(r["capabilities"]["identity_mode"], "v3")
        self.assertEqual(len(r["result"]["matches"]), 1,
                         "a v3 cluster decision must fold rows into one person, "
                         "not merely annotate them")
        self.assertEqual(set(r["result"]["matches"][0]["identity"]["member_ids"]),
                         {"v3:a", "v3:b"})

    def test_unreadable_cluster_table_is_reported_not_swallowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._with_cluster(
                tmp, "CREATE TABLE identity_cluster(wrong_col TEXT)",
                [("junk",)])
            with QueryEngine(root=tmp) as e:
                r = e.who("V3 Pair")

        self.assertTrue(
            any("UNREADABLE" in w for w in r["warnings"]),
            "a malformed identity_cluster must not read as 'no clusters' -- "
            "that is the swallowed-error class this lane exists to remove",
        )


if __name__ == "__main__":
    unittest.main()
