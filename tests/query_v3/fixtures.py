"""Tiny offline fixtures. No network, no production database, no large assets.

The acceptance list from the lane spec, one scenario each:

  multi-source person   Immanuel Kant -- a book row and a github row, ACCEPTED
                        identity claim plus an applied merge. The PG-AUDIT-002
                        case: reads must fold these into one person.
  reviewer-pending      Ada Lovelace -- accepted claim, merged_into NOT yet
                        written by a build. Reads must still apply the decision;
                        this is the reviewer-invisible window.
  ambiguous name        two distinct John Murrays with only a PROPOSED claim.
                        Must stay two people and report the ambiguity.
  organisation          "United States" -- kind='organisation', not a human.
  historical figure     Plato -- BCE dates stored negative.
  relationship path     Kant -> shared work -> Hume -> shared work -> Smith.
  truncation            Prolific Author with 250 works, over any sane page size.
  missing database      handled by pointing config at an empty directory.
"""
from __future__ import annotations

import os
import sqlite3

SCHEMA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "schema",
    "people_schema_v2.sql",
)

BUILT_AT = "2026-08-06T00:00:00Z"


def _person(con, pid, name, *, kind="human", state="linked", merged_into=None,
            birth=None, death=None, origin="registry"):
    con.execute(
        """INSERT INTO person(person_id, name, sort_name, kind, state,
                              merged_into, birth_year, death_year, origin,
                              built_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (pid, name, name, kind, state, merged_into, birth, death, origin,
         BUILT_AT),
    )


def _content(con, pid, domain, ref, role, title, source="test_loader"):
    con.execute(
        """INSERT INTO person_content(person_id, domain, content_ref, role,
                                      score, title, source, observed_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (pid, domain, ref, role, 1.0, title, source, BUILT_AT),
    )


def _claim(con, a, b, method, conf, evidence, status, decided_by=None):
    lo, hi = sorted((a, b))  # schema enforces person_a < person_b
    con.execute(
        """INSERT INTO identity_claim(person_a, person_b, method, confidence,
                                      evidence, status, decided_by, created_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (lo, hi, method, conf, evidence, status, decided_by, BUILT_AT),
    )


def build_people_db(path: str, *, with_fts: bool = True) -> str:
    """Create the people fixture. Returns the path."""
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    with open(SCHEMA, encoding="utf-8") as fh:
        con.executescript(fh.read())

    # --- multi-source person, merge already applied by a build ---------------
    _person(con, "bk:kant", "Immanuel Kant", birth=1724, death=1804,
            origin="book")
    _person(con, "gh:kant", "Immanuel Kant", state="merged",
            merged_into="bk:kant", origin="github")
    _claim(con, "bk:kant", "gh:kant", "shared_external_id", 0.995,
           "viaf:7524651 on both rows", "accepted", "reviewer:shaan")
    _content(con, "bk:kant", "book", "4280", "author",
             "The Critique of Pure Reason")
    _content(con, "bk:kant", "book", "5682", "author",
             "The Critique of Practical Reason")
    _content(con, "gh:kant", "github", "kant/categorical-imperative", "owner",
             "categorical-imperative")
    con.execute("INSERT INTO external_ids VALUES('bk:kant','viaf','7524651',1.0,'authority')")
    con.execute("INSERT INTO external_ids VALUES('gh:kant','viaf','7524651',1.0,'authority')")
    con.execute("INSERT INTO person_topic VALUES('bk:kant','Ethics','lcsh',3.0,'books')")

    # --- accepted claim with NO merge applied yet ---------------------------
    # The reviewer decided; the build has not re-run. A read layer that only
    # trusted merged_into would still show two people here.
    _person(con, "bk:lovelace", "Ada Lovelace", birth=1815, death=1852,
            origin="book")
    _person(con, "gh:lovelace", "Ada Lovelace", origin="github")
    _claim(con, "bk:lovelace", "gh:lovelace", "shared_external_id", 0.995,
           "wikidata:Q7259 on both rows", "accepted", "reviewer:shaan")
    _content(con, "bk:lovelace", "book", "9001", "author",
             "Notes on the Analytical Engine")
    _content(con, "gh:lovelace", "github", "lovelace/analytical-engine", "owner",
             "analytical-engine")

    # --- ambiguous common name: PROPOSED only, must NOT merge ---------------
    _person(con, "bk:murray-1", "John Murray", birth=1778, death=1843,
            origin="book")
    _person(con, "bk:murray-2", "John Murray", birth=1808, death=1892,
            origin="book")
    _claim(con, "bk:murray-1", "bk:murray-2", "exact_name", 0.52,
           "identical normalised name, incompatible life dates", "proposed")
    _content(con, "bk:murray-1", "book", "1111", "publisher", "Quarterly Review")
    _content(con, "bk:murray-2", "book", "2222", "publisher", "Murray Handbooks")

    # --- organisation -------------------------------------------------------
    _person(con, "bk:united-states", "United States", kind="organisation",
            origin="book")
    _content(con, "bk:united-states", "book", "3333", "author",
             "Declaration of Independence")

    # --- historical figure, BCE --------------------------------------------
    _person(con, "bk:plato", "Plato", birth=-428, death=-348, origin="book")
    _content(con, "bk:plato", "book", "1497", "author", "The Republic")

    # --- relationship path: Kant -- Hume -- Smith --------------------------
    _person(con, "bk:hume", "David Hume", birth=1711, death=1776, origin="book")
    _person(con, "bk:smith", "Adam Smith", birth=1723, death=1790, origin="book")
    # Kant and Hume share an anthology; Hume and Smith share another.
    _content(con, "bk:kant", "book", "7000", "contributor",
             "Enlightenment Anthology")
    _content(con, "bk:hume", "book", "7000", "contributor",
             "Enlightenment Anthology")
    _content(con, "bk:hume", "book", "7001", "contributor",
             "Scottish Enlightenment Reader")
    _content(con, "bk:smith", "book", "7001", "contributor",
             "Scottish Enlightenment Reader")

    # --- truncation case: more works than any sane page ---------------------
    _person(con, "bk:prolific", "Prolific Author", origin="book")
    for i in range(250):
        _content(con, "bk:prolific", "book", str(90000 + i), "author",
                 f"Collected Volume {i:03d}")

    # --- a rejected claim, which must never be applied ---------------------
    _person(con, "bk:decoy", "Immanuel Kant Decoy", origin="book")
    _claim(con, "bk:kant", "bk:decoy", "exact_name", 0.52,
           "similar name, different person", "rejected", "reviewer:shaan")

    if with_fts:
        for pid, name in con.execute("SELECT person_id, name FROM person"):
            con.execute(
                "INSERT INTO person_search(person_id, name, aliases) "
                "VALUES(?,?,?)",
                (pid, name, name),
            )
    else:
        con.execute("DROP TABLE IF EXISTS person_search")

    con.commit()
    con.close()
    return path


def build_books_db(path: str) -> str:
    """A minimal books domain so multi-domain paths have something to attach."""
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE book (gid INTEGER PRIMARY KEY, title TEXT);
        CREATE TABLE book_subject (gid INTEGER, subject TEXT);
        """
    )
    con.execute("INSERT INTO book VALUES(4280, 'The Critique of Pure Reason')")
    con.execute("INSERT INTO book_subject VALUES(4280, 'Knowledge, Theory of')")
    con.commit()
    con.close()
    return path
