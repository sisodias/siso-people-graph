"""Every response must be honest about what it did and did not see.

The governing rule from the lane spec: no query may say "all" without a declared
source universe. These tests hold the envelope to that standard -- counts,
truncation, provenance grade, rights state, missing capabilities, and the
acceptance scenarios (organisation, historical figure, missing database).
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from query_v3 import QueryEngine, SCHEMA_VERSION  # noqa: E402
from query_v3.evidence import GRADES  # noqa: E402
from tests.query_v3.fixtures import build_people_db, build_books_db  # noqa: E402

ENVELOPE_FIELDS = (
    "schema_version", "query_type", "query", "result", "page",
    "identity_resolution", "sources", "capabilities", "coverage_gaps",
    "warnings", "execution",
)


class EnvelopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        build_people_db(os.path.join(cls.tmp.name, "people_v2.sqlite"))
        build_books_db(os.path.join(cls.tmp.name, "books.sqlite"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def engine(self):
        return QueryEngine(root=self.tmp.name)

    def test_every_query_type_carries_the_full_envelope(self):
        with self.engine() as e:
            responses = {
                "who": e.who("Kant"),
                "works": e.works("Kant"),
                "relationships": e.relationships("Kant"),
                "path": e.path("Kant", "Adam Smith"),
                "claims": e.claims("Kant"),
                "inventory": e.inventory(),
                "source": e.source(),
            }
        for qtype, r in responses.items():
            for field in ENVELOPE_FIELDS:
                self.assertIn(field, r, f"{qtype} is missing {field}")
            self.assertEqual(r["schema_version"], SCHEMA_VERSION)
            self.assertEqual(r["query_type"], qtype)

    def test_counts_are_never_len_of_the_page(self):
        """The defect that made works() unable to distinguish 5 from 200-of-40k."""
        with self.engine() as e:
            r = e.works("Prolific Author", limit=25)
        self.assertEqual(r["page"]["returned"], 25)
        self.assertEqual(r["page"]["total_matched"], 250)
        self.assertTrue(r["page"]["truncated"])
        self.assertNotEqual(r["page"]["returned"], r["page"]["total_matched"])

    def test_untruncated_result_says_so(self):
        with self.engine() as e:
            r = e.works("Plato", limit=50)
        self.assertFalse(r["page"]["truncated"])
        self.assertEqual(r["page"]["returned"], r["page"]["total_matched"])

    def test_paging_reaches_the_tail(self):
        with self.engine() as e:
            first = e.works("Prolific Author", limit=100, offset=0)
            last = e.works("Prolific Author", limit=100, offset=200)
        self.assertTrue(first["page"]["truncated"])
        self.assertEqual(last["page"]["returned"], 50)
        self.assertFalse(last["page"]["truncated"],
                         "the final page must not claim more remains")
        firsts = {w["ref"] for w in first["result"]["works"]}
        lasts = {w["ref"] for w in last["result"]["works"]}
        self.assertFalse(firsts & lasts, "pages must not overlap")

    def test_limit_is_capped(self):
        with self.engine() as e:
            r = e.works("Prolific Author", limit=10_000)
        self.assertLessEqual(r["page"]["limit"], 500)

    def test_every_asserted_fact_carries_a_provenance_grade(self):
        with self.engine() as e:
            who = e.who("Kant")
            works = e.works("Kant", limit=10)
        person = who["result"]["matches"][0]
        self.assertIn(person["evidence"]["grade"], GRADES)
        for w in works["result"]["works"]:
            self.assertIn(w["evidence"]["grade"], GRADES)
            self.assertEqual(w["evidence"]["grade"], "source_observation")
        for d in who["identity_resolution"]["applied"]:
            self.assertEqual(d["evidence"]["grade"], "accepted_identity_decision")

    def test_derived_relations_are_labelled_derived_not_observed(self):
        """Co-contribution is adjacency we computed, not a relation anyone asserted."""
        with self.engine() as e:
            r = e.relationships("David Hume")
        self.assertTrue(r["result"]["neighbours"])
        for n in r["result"]["neighbours"]:
            self.assertEqual(n["evidence"]["grade"], "derived_relation")
        self.assertTrue(any("person_relation" in g for g in r["coverage_gaps"]))

    def test_missing_capabilities_are_declared(self):
        with self.engine() as e:
            r = e.who("Kant")
        gaps = " ".join(r["coverage_gaps"])
        self.assertIn("person_relation", gaps)
        self.assertIn("claim", gaps)
        self.assertTrue(r["capabilities"]["v3_tables_absent"])

    def test_claims_absence_is_a_capability_gap_not_an_empty_answer(self):
        with self.engine() as e:
            r = e.claims("Kant")
        self.assertEqual(r["result"]["claims"], [])
        self.assertTrue(
            any("missing capability" in g.lower() for g in r["coverage_gaps"]),
            "an absent table must not read as 'this person has no claims'",
        )

    def test_rights_state_is_undeclared_not_assumed_clean(self):
        with self.engine() as e:
            r = e.source()
        for domain, meta in r["result"]["sources"].items():
            if meta.get("attached"):
                self.assertIn("rights", meta)
                self.assertIn("undeclared", str(meta["rights"]).lower())
        self.assertTrue(any("UNDECLARED" in g for g in r["coverage_gaps"]))

    def test_inventory_declares_its_universe(self):
        with self.engine() as e:
            r = e.inventory()
        self.assertTrue(
            any("THIS machine" in g for g in r["coverage_gaps"]),
            "inventory must not imply a canonical corpus",
        )

    def test_source_paths_and_their_origin_are_reported(self):
        with self.engine() as e:
            r = e.who("Kant")
        people = r["sources"]["people"]
        self.assertTrue(people["path"].endswith("people_v2.sqlite"))
        self.assertEqual(people["path_origin"], "default_local")


class AcceptanceScenariosTest(unittest.TestCase):
    """The scenarios the lane spec requires be demonstrated offline."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        build_people_db(os.path.join(cls.tmp.name, "people_v2.sqlite"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_organisation_is_not_reported_as_a_human(self):
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("United States")
        match = r["result"]["matches"][0]
        self.assertEqual(match["kind"], "organisation")

    def test_historical_figure_with_bce_dates(self):
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("Plato")
        match = r["result"]["matches"][0]
        self.assertEqual(match["lived"], "428 BCE-348 BCE")
        self.assertEqual(match["birth_year"], -428)

    def test_relationship_path_is_explainable(self):
        with QueryEngine(root=self.tmp.name) as e:
            r = e.path("Kant", "Adam Smith")
        path = r["result"]["path"]
        self.assertIsNotNone(path, "Kant -> Hume -> Smith must be reachable")
        self.assertEqual(r["result"]["hops"], 2)
        for edge in path:
            self.assertIn("via", edge)
            self.assertEqual(edge["evidence"]["grade"], "derived_relation")

    def test_unreachable_path_does_not_claim_no_relationship_exists(self):
        with QueryEngine(root=self.tmp.name) as e:
            r = e.path("Plato", "Prolific Author")
        self.assertIsNone(r["result"]["path"])
        self.assertTrue(
            any("not evidence that no relationship exists" in g
                for g in r["coverage_gaps"]),
            "absence of a path is not absence of a relationship",
        )

    def test_multi_source_person_reports_both_domains(self):
        with QueryEngine(root=self.tmp.name) as e:
            r = e.who("Kant")
        match = [m for m in r["result"]["matches"] if m["person_id"] == "bk:kant"][0]
        self.assertEqual(set(match["source_coverage"]["domains"]),
                         {"book", "github"})


class MissingDatabaseTest(unittest.TestCase):
    """A machine with nothing attached must answer honestly, not crash."""

    def test_no_database_is_explicit_and_non_fatal(self):
        with tempfile.TemporaryDirectory() as empty:
            with QueryEngine(root=empty) as e:
                who = e.who("Kant")
                works = e.works("Kant")
                inv = e.inventory()

        for r in (who, works):
            self.assertEqual(r["result"], {})
            self.assertTrue(
                any("no people database" in w.lower() for w in r["warnings"]),
                "a missing database must be stated, not returned as no results",
            )
            self.assertIn("absent: people_domain", r["coverage_gaps"])
        self.assertEqual(inv["result"]["domains"], {})

    def test_partial_estate_answers_what_it_can(self):
        """Only a people DB: person queries work, book routes degrade quietly."""
        with tempfile.TemporaryDirectory() as tmp:
            build_people_db(os.path.join(tmp, "people_v2.sqlite"))
            with QueryEngine(root=tmp) as e:
                r = e.works("Kant", limit=10)
        self.assertTrue(r["result"]["works"])
        book = [w for w in r["result"]["works"] if w["domain"] == "book"][0]
        routes = {rt["route"] for rt in book["fetch"]}
        self.assertIn("origin", routes)
        self.assertNotIn("byte_range", routes,
                         "no locator attached, so no byte-range route may be offered")


if __name__ == "__main__":
    unittest.main()
