#!/usr/bin/env python3
"""Generate tiny synthetic source databases for offline builds, tests and CI.

Nothing here is real data. Every person, repo and book is invented, so the
fixtures can be regenerated anywhere with no network, no vault and no corpus,
and committing them costs nothing -- the whole point being that CI must prove
reproducibility without a production asset.

The fixtures are small but not trivial. They deliberately encode the cases that
have actually broken this pipeline:

  * an owner who is ALSO a book author (the cross-domain join path)
  * an organisation-looking login (the kind='unknown' vs 'organisation' split)
  * a person with life dates including a BCE year (negative-year handling)
  * a high-star / low-rating owner AND a low-star / high-rating owner, so a
    ranking that confuses fame with value produces a visibly different order
  * a corporate "author" that must be excluded from people
  * unicode and diacritics in names (digest rendering, FTS)

Determinism: the generator seeds nothing random. Every value is literal, so two
invocations produce identical databases -- which the reproducibility test relies
on when it builds twice from freshly-generated inputs.
"""
import pathlib
import sqlite3

FIXTURE_SNAPSHOT = "fixture-2026-08-06-a"

# --- v1 canonical graph -----------------------------------------------------
V1_PEOPLE = [
    # person_id, name, origin, primary_tier, rank_score
    ("yt:sketchpad", "Ada Sketchpad", "youtube", "A", 12.0),
    ("reg:plato", "Plato", "registry", "S", 99.0),
    ("gh:dtolnay-like", "Renée Bäcker", "github", None, 4.0),
]
V1_CONTENT = [
    # person_id, domain, content_ref, score, title, meta_json
    ("yt:sketchpad", "youtube_video", "vid_0001", 5.0, "How sorting works", "{}"),
    ("reg:plato", "registry", "reg_0001", None, "Curated entry", "{}"),
]
V1_EXTIDS = [
    ("yt:sketchpad", "youtube_channel_id", "UC_sketchpad"),
    ("gh:dtolnay-like", "github_login", "dtolnay-like"),
]

# --- books people -----------------------------------------------------------
BK_PEOPLE = [
    # person_key, display_name, birth_year, death_year, work_count, is_corporate
    ("plato|-428--348", "Plato", -428, -348, 71, 0),
    ("backer|1970-", "Renée Bäcker", 1970, None, 3, 0),
    ("woolf|1882-1941", "Virginia Woolf", 1882, 1941, 12, 0),
    ("united-states", "United States", None, None, 40, 1),
]
BK_PERSON_WORK = [
    # person_key, gid, role
    ("plato|-428--348", 1497, "author"),
    ("plato|-428--348", 1656, "author"),
    ("woolf|1882-1941", 144, "author"),
    ("woolf|1882-1941", 145, "translator"),
    ("backer|1970-", 900, "author"),
]
BK_BOOKS = [
    (1497, "The Republic"),
    (1656, "Apology"),
    (144, "The Voyage Out"),
    (145, "A Translated Work"),
    (900, "Modern Perl Notes"),
]
BK_SUBJECTS = [
    (1497, "Political science"),
    (1497, "Philosophy, Ancient"),
    (1656, "Philosophy, Ancient"),
    (144, "English fiction"),
    (900, "Perl (Computer program language)"),
]

# --- github identity corpus -------------------------------------------------
# The fame-vs-value pair is the important part of this table.
#   megacorp-labs : 500,000 stars across 3 repos, rated 42 -- famous, mediocre
#   quietcrafter  :   1,200 stars across 2 repos, rated 95 -- obscure, excellent
# Any ranking that uses summed stars puts megacorp-labs first; any ranking that
# uses rated value puts quietcrafter first. The projection tests assert exactly
# that inversion, which is the Foundry dtolnay-vs-facebook finding in miniature.
GH_REPOS = [
    # full_name, stars, language, description, topics_json, url, fork
    ("megacorp-labs/bigthing", 400000, "Java", "A very popular thing",
     '["framework","java","enterprise"]', "https://example.invalid/1", 0),
    ("megacorp-labs/otherthing", 90000, "Java", "Also popular",
     '["framework","java"]', "https://example.invalid/2", 0),
    ("megacorp-labs/smallthing", 10000, "Go", "Popular too",
     '["cli","go"]', "https://example.invalid/3", 0),
    ("quietcrafter/serde-ish", 1000, "Rust", "Careful serialisation",
     '["serialization","rust","compilers"]', "https://example.invalid/4", 0),
    ("quietcrafter/macro-ish", 200, "Rust", "Careful macros",
     '["macros","rust","compilers"]', "https://example.invalid/5", 0),
    ("dtolnay-like/perl-tools", 300, "Perl", "Tools",
     '["perl","tooling"]', "https://example.invalid/6", 0),
    # A fork and a below-threshold repo: both must be filtered out, and the
    # fixture exists so the filter is actually exercised.
    ("someone/forked-copy", 99999, "Java", "A fork",
     '["framework"]', "https://example.invalid/7", 1),
    ("tiny/unnoticed", 0, "C", "Nobody starred this",
     '["c"]', "https://example.invalid/8", 0),
]
GH_CATEGORIES = [
    # full_name, overall_value, reuse_value, info_value
    ("megacorp-labs/bigthing", 45.0, 40.0, 50.0),
    ("megacorp-labs/otherthing", 40.0, 35.0, 45.0),
    ("megacorp-labs/smallthing", 41.0, 38.0, 44.0),
    ("quietcrafter/serde-ish", 96.0, 97.0, 95.0),
    ("quietcrafter/macro-ish", 94.0, 95.0, 93.0),
    ("dtolnay-like/perl-tools", 70.0, 68.0, 72.0),
]


def _w(conn, sql, rows=None):
    if rows is None:
        conn.execute(sql)
    else:
        conn.executemany(sql, rows)


def write_v1(path):
    if pathlib.Path(path).exists():
        pathlib.Path(path).unlink()
    c = sqlite3.connect(path)
    _w(c, """CREATE TABLE person (person_id TEXT PRIMARY KEY, name TEXT,
             origin TEXT, primary_tier TEXT, rank_score REAL)""")
    _w(c, """CREATE TABLE person_content (person_id TEXT, domain TEXT,
             content_ref TEXT, score REAL, title TEXT, meta_json TEXT)""")
    _w(c, """CREATE TABLE external_ids (person_id TEXT, platform TEXT, value TEXT)""")
    _w(c, "INSERT INTO person VALUES (?,?,?,?,?)", V1_PEOPLE)
    _w(c, "INSERT INTO person_content VALUES (?,?,?,?,?,?)", V1_CONTENT)
    _w(c, "INSERT INTO external_ids VALUES (?,?,?)", V1_EXTIDS)
    c.commit()
    c.close()
    return path


def write_books_people(path):
    if pathlib.Path(path).exists():
        pathlib.Path(path).unlink()
    c = sqlite3.connect(path)
    _w(c, """CREATE TABLE person (person_key TEXT PRIMARY KEY, display_name TEXT,
             birth_year INTEGER, death_year INTEGER, work_count INTEGER,
             is_corporate INTEGER)""")
    _w(c, """CREATE TABLE person_work (person_key TEXT, gid INTEGER, role TEXT)""")
    _w(c, "INSERT INTO person VALUES (?,?,?,?,?,?)", BK_PEOPLE)
    _w(c, "INSERT INTO person_work VALUES (?,?,?)", BK_PERSON_WORK)
    c.commit()
    c.close()
    return path


def write_books(path):
    if pathlib.Path(path).exists():
        pathlib.Path(path).unlink()
    c = sqlite3.connect(path)
    _w(c, "CREATE TABLE book (gid INTEGER PRIMARY KEY, title TEXT)")
    _w(c, "CREATE TABLE book_subject (gid INTEGER, subject TEXT)")
    _w(c, "INSERT INTO book VALUES (?,?)", BK_BOOKS)
    _w(c, "INSERT INTO book_subject VALUES (?,?)", BK_SUBJECTS)
    c.commit()
    c.close()
    return path


def write_identity(path):
    if pathlib.Path(path).exists():
        pathlib.Path(path).unlink()
    c = sqlite3.connect(path)
    _w(c, """CREATE TABLE repo_card (full_name TEXT PRIMARY KEY, stars INTEGER,
             language TEXT, description TEXT, topics_json TEXT, url TEXT,
             fork INTEGER)""")
    _w(c, """CREATE TABLE repo_category (full_name TEXT PRIMARY KEY,
             overall_value REAL, reuse_value REAL, info_value REAL)""")
    _w(c, "INSERT INTO repo_card VALUES (?,?,?,?,?,?,?)", GH_REPOS)
    _w(c, "INSERT INTO repo_category VALUES (?,?,?,?)", GH_CATEGORIES)
    c.commit()
    c.close()
    return path


def write_all(directory):
    """Materialise the full fixture set into a directory. Returns the paths."""
    d = pathlib.Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    return {
        "v1": str(write_v1(d / "fixture_v1.sqlite")),
        "books_people": str(write_books_people(d / "fixture_bkpeople.sqlite")),
        "books": str(write_books(d / "fixture_books.sqlite")),
        "identity": str(write_identity(d / "fixture_identity.sqlite")),
    }


def main():
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="directory to write fixtures into")
    a = ap.parse_args()
    print(json.dumps(write_all(a.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
