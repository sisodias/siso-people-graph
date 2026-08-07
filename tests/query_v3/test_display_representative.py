"""The cluster representative is an explicit, versioned, REPORTED choice.

Every test here is built so that it FAILS under the previous rule, whose final
rung was `sorted(members)[0]`. Because entity ids carry an origin prefix, that
sort silently encoded bk: < crates: < gh: < yt: -- an origin hierarchy nobody
chose, produced by string sort, reading as policy. A test that passes under both
rules would guard nothing, so each case below is arranged so the alphabetical
winner and the evidence-based winner are DIFFERENT rows.

The other half of the fix is not the ranking but the honesty: the answer must
say which rule chose the representative, why, and whether the alphabet broke the
tie. A caller that cannot see the choice cannot disagree with it.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from query_v3 import capability, resolver as resmod
from tests.query_v3 import fixtures

SCHEMA = fixtures.SCHEMA
AT = "2026-08-06T00:00:00Z"


def _con(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("ATTACH DATABASE ? AS people", (path,))
    return con


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "people.db")
        con = sqlite3.connect(self.path)
        with open(SCHEMA, encoding="utf-8") as fh:
            con.executescript(fh.read())
        con.commit()
        con.close()

    def person(self, con, pid, name, *, origin, state="linked",
               merged_into=None, kind="human"):
        con.execute(
            """INSERT INTO person(person_id, name, sort_name, kind, state,
                                  merged_into, origin, built_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (pid, name, name, kind, state, merged_into, origin, AT),
        )

    def claim(self, con, a, b, status="accepted"):
        lo, hi = sorted((a, b))
        con.execute(
            """INSERT INTO identity_claim(person_a, person_b, method,
                                          confidence, evidence, status,
                                          decided_by, created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (lo, hi, "shared_external_id", 0.99, "same authority id", status,
             "reviewer:test", AT),
        )

    def ext(self, con, pid, platform, value):
        con.execute("INSERT INTO external_ids VALUES(?,?,?,1.0,'authority')",
                    (pid, platform, value))

    def resolve(self, ids):
        con = _con(self.path)
        caps = capability.detect(con, {"people": self.path})
        res = resmod.for_capabilities(con, caps).resolve(ids)
        con.close()
        return res


class TestEvidenceBeatsAlphabet(_Base):
    """The worked example: alphabetical and evidence-based DISAGREE."""

    def setUp(self) -> None:
        super().setUp()
        con = _con(self.path)
        # aa:sparse sorts FIRST alphabetically and has one identifier.
        # zz:rich sorts LAST and carries three independent authority ids.
        self.person(con, "aa:sparse", "Grace Hopper", origin="github")
        self.person(con, "zz:rich", "Grace Hopper", origin="github")
        self.ext(con, "aa:sparse", "viaf", "111")
        self.ext(con, "zz:rich", "viaf", "111")
        self.ext(con, "zz:rich", "wikidata", "Q11641")
        self.ext(con, "zz:rich", "orcid", "0000-0001")
        self.claim(con, "aa:sparse", "zz:rich")
        con.commit()
        con.close()

    def test_best_evidenced_row_represents_the_cluster(self):
        """FAILS under the old rule, which returned aa:sparse by string sort."""
        res = self.resolve(["aa:sparse", "zz:rich"])["aa:sparse"]
        self.assertEqual(
            res.display_representative, "zz:rich",
            "the row with three independent authority identifiers must "
            "represent the cluster; the old rule picked aa:sparse purely "
            "because 'a' < 'z'",
        )

    def test_the_choice_reports_that_it_was_not_alphabetical(self):
        res = self.resolve(["aa:sparse", "zz:rich"])["aa:sparse"]
        reason = res.as_dict()["representative_selection"]
        self.assertFalse(reason["decided_by_alphabetical_tiebreak"])
        self.assertEqual(reason["strong_identifier_count"], 3)
        self.assertTrue(reason["contested"])

    def test_the_rule_is_versioned(self):
        res = self.resolve(["aa:sparse"])["aa:sparse"]
        self.assertEqual(res.as_dict()["representative_selection"]["rule"],
                         resmod.REPRESENTATIVE_RULE_VERSION)


class TestOriginHierarchyIsNotAlphabetical(_Base):
    """bk: < gh: was never a decision. Curated origin is."""

    def setUp(self) -> None:
        super().setUp()
        con = _con(self.path)
        # Alphabetically zz:curated LOSES to bk:scraped. By declared origin it
        # wins: 'registry' outranks 'book' in Lane 4's own table.
        self.person(con, "bk:scraped", "Ada Lovelace", origin="book")
        self.person(con, "zz:curated", "Ada Lovelace", origin="registry")
        self.claim(con, "bk:scraped", "zz:curated")
        con.commit()
        con.close()

    def test_declared_origin_decides_not_the_id_prefix(self):
        """FAILS under the old rule, which returned bk:scraped ('b' < 'z')."""
        res = self.resolve(["bk:scraped", "zz:curated"])["bk:scraped"]
        self.assertEqual(
            res.display_representative, "zz:curated",
            "origin must come from the person.origin column, not from the "
            "alphabetical accident of the id prefix",
        )

    def test_origin_is_read_from_the_column_not_the_prefix(self):
        res = self.resolve(["bk:scraped", "zz:curated"])["bk:scraped"]
        self.assertEqual(
            res.as_dict()["representative_selection"]["origin"], "registry")


class TestEqualStrongIdentifiers(_Base):
    """Two members, equal on every discriminator. The tie must be DECLARED."""

    def setUp(self) -> None:
        super().setUp()
        con = _con(self.path)
        self.person(con, "gh:twin-a", "Alan Turing", origin="github")
        self.person(con, "gh:twin-b", "Alan Turing", origin="github")
        self.ext(con, "gh:twin-a", "viaf", "222")
        self.ext(con, "gh:twin-b", "viaf", "222")
        self.claim(con, "gh:twin-a", "gh:twin-b")
        con.commit()
        con.close()

    def test_genuine_ties_are_reported_as_alphabetical(self):
        """The old rule was alphabetical and SILENT. Silence was the defect."""
        res = self.resolve(["gh:twin-a", "gh:twin-b"])["gh:twin-a"]
        reason = res.as_dict()["representative_selection"]
        self.assertTrue(
            reason["decided_by_alphabetical_tiebreak"],
            "when members are genuinely equal the answer must SAY the "
            "alphabet broke the tie, rather than presenting it as judgement",
        )
        self.assertIn("NOT a judgement", reason["reason"])

    def test_a_tie_is_still_deterministic(self):
        first = self.resolve(["gh:twin-a", "gh:twin-b"])["gh:twin-a"]
        second = self.resolve(["gh:twin-b", "gh:twin-a"])["gh:twin-b"]
        self.assertEqual(first.display_representative,
                         second.display_representative,
                         "a last-resort tie-break must still be stable")


class TestNonLatinRepresentative(_Base):
    """A non-Latin id must not lose for being non-Latin."""

    def setUp(self) -> None:
        super().setUp()
        con = _con(self.path)
        # Cyrillic sorts after ASCII in codepoint order, so the old rule could
        # never return it while any ASCII peer existed.
        self.person(con, "aa:ascii", "Sofia Kovalevskaya", origin="github")
        self.person(con, "gh:Ковалевская", "Софья Ковалевская", origin="registry")
        self.ext(con, "gh:Ковалевская", "viaf", "333")
        self.ext(con, "gh:Ковалевская", "wikidata", "Q133280")
        self.claim(con, "aa:ascii", "gh:Ковалевская")
        con.commit()
        con.close()

    def test_non_latin_row_can_represent_the_cluster(self):
        """FAILS under the old rule: ASCII always sorted first."""
        res = self.resolve(["aa:ascii", "gh:Ковалевская"])["aa:ascii"]
        self.assertEqual(
            res.display_representative, "gh:Ковалевская",
            "a better-evidenced, curated row must represent the cluster even "
            "when its id is non-Latin; codepoint order is not authority",
        )


class TestOrgVersusHuman(_Base):
    """An organisation and a human are not silently one person."""

    def setUp(self) -> None:
        super().setUp()
        con = _con(self.path)
        self.person(con, "bk:acme-org", "Acme Corporation", origin="book",
                    kind="organisation")
        self.person(con, "zz:acme-human", "Acme Smith", origin="registry")
        con.commit()
        con.close()

    def test_no_decision_means_no_cluster(self):
        res = self.resolve(["bk:acme-org", "zz:acme-human"])
        self.assertEqual(res["bk:acme-org"].display_representative,
                         "bk:acme-org")
        self.assertEqual(res["zz:acme-human"].display_representative,
                         "zz:acme-human")
        for r in res.values():
            self.assertEqual(len(r.member_ids), 1)
            self.assertFalse(r.as_dict()["representative_selection"]["contested"])


class TestLivenessStillOutranksEvidence(_Base):
    """Guards the fix that already existed: a merged row is never shown."""

    def setUp(self) -> None:
        super().setUp()
        con = _con(self.path)
        # The merged row is the better-evidenced one. Liveness must still win:
        # showing a superseded row would be a regression of an earlier fix.
        self.person(con, "aa:dead", "Emmy Noether", origin="registry",
                    state="merged", merged_into="zz:live")
        self.person(con, "zz:live", "Emmy Noether", origin="github")
        self.ext(con, "aa:dead", "viaf", "444")
        self.ext(con, "aa:dead", "wikidata", "Q57187")
        self.claim(con, "aa:dead", "zz:live")
        con.commit()
        con.close()

    def test_a_merged_row_never_represents_the_cluster(self):
        res = self.resolve(["aa:dead", "zz:live"])["aa:dead"]
        self.assertEqual(res.display_representative, "zz:live")
        self.assertNotEqual(
            res.as_dict()["representative_selection"]["basis"], "sole_member")


class TestRankingMatchesLaneFour(_Base):
    """query_v3 and identity_v3 must not invent competing rankings.

    Two independently invented orderings would make the two modules disagree
    about who a person is -- the exact two-authorities failure this lane exists
    to prevent. Lane 4's table is the source; this asserts it was adopted, not
    reinvented.
    """

    def test_origin_priority_matches_the_identity_method_card(self):
        table = resmod.V2Resolver._ORIGIN_PRIORITY
        # As published in identity_v3/_clusters.py::_canonical_sort_key.
        self.assertEqual(table["registry"], 0)
        self.assertEqual(table["curated"], 0)
        self.assertEqual(table["manual"], 0)
        self.assertEqual(table["authority"], 1)
        self.assertEqual(table["book"], 2)
        self.assertEqual(table["github"], 3)
        self.assertEqual(table["youtube"], 3)
        self.assertEqual(
            resmod.V2Resolver._ORIGIN_UNRANKED, 9,
            "an unknown origin must rank last, never accidentally first")


if __name__ == "__main__":
    unittest.main()
