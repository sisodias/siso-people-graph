"""Build, Book, Unicode, and FTS red-team cases."""
from __future__ import annotations

from support import *  # lane-local fixture primitives; no third-party dependencies

def case_schema_lookup(ctx: Context) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="pg-red-team-schema-") as td:
        tmp = Path(td)
        v1, people, books, out = (tmp / n for n in ("v1.sqlite", "people.sqlite", "books.sqlite", "out.sqlite"))
        for path in (v1, people, books):
            sqlite3.connect(path).close()
        proc = subprocess.run(
            [
                sys.executable,
                str(ctx.production("loaders/build_people_graph_v2.py")),
                "--v1",
                str(v1),
                "--people",
                str(people),
                "--books",
                str(books),
                "--out",
                str(out),
            ],
            cwd=tmp,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
        expected_schema = ctx.production("schema/people_schema_v2.sql")
        mistaken_schema = ctx.production("loaders/build_people_graph_v2.py").parent / "people_schema_v2.sql"
        holds = proc.returncode == 0
        return holds, {
            "returncode": proc.returncode,
            "tracked_schema_exists": expected_schema.is_file(),
            "resolved_schema_exists": mistaken_schema.is_file(),
            "stderr_tail": proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "",
        }

def case_silent_name_merge(ctx: Context) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="pg-red-team-name-merge-") as td:
        tmp = Path(td)
        v1, people, books, out = (tmp / n for n in ("v1.sqlite", "people.sqlite", "books.sqlite", "out.sqlite"))
        make_v1(v1, [("reg:alex", "Alex Lee", "registry", "A", 10.0)])
        make_book_people(
            people,
            [("book-author-1", "  Alex   Lee ", 1975, None, 1, 0, '["Alex Lee, 1975-"]')],
            [("book-author-1", 1, "author")],
        )
        make_books(books, [(1, "A Different Alex's Book")])
        build_v2_with_tracked_schema(ctx, v1, people, books, out)
        con = connect(out)
        try:
            person_rows = [dict(r) for r in con.execute("SELECT person_id,name,origin FROM person ORDER BY person_id")]
            book_edge = dict(
                con.execute(
                    "SELECT person_id,domain,content_ref FROM person_content WHERE domain='book'"
                ).fetchone()
            )
            claim_count = con.execute("SELECT COUNT(*) FROM identity_claim").fetchone()[0]
        finally:
            con.close()
        holds = len(person_rows) == 2 and book_edge["person_id"].startswith("bk:") and claim_count >= 1
        return holds, {
            "people": person_rows,
            "book_edge": book_edge,
            "identity_claims": claim_count,
            "normalized_labels": ["alex lee", "alex lee"],
        }

def case_book_builder_stale_source(ctx: Context) -> tuple[bool, dict[str, Any]]:
    builder = ctx.module("loaders/build_people_graph_books.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-books-stale-") as td:
        tmp = Path(td)
        source, out = tmp / "books.sqlite", tmp / "people.sqlite"
        con = connect(source)
        try:
            con.execute("CREATE TABLE book(gid INTEGER PRIMARY KEY, authors TEXT, media_type TEXT)")
            con.execute("INSERT INTO book VALUES (1,'Doe, Jane, 1970-','Text')")
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            builder.build(str(source), str(out))
        con = connect(source)
        try:
            con.execute("DELETE FROM book")
            con.execute("INSERT INTO book VALUES (2,'Roe, Richard, 1980-','Text')")
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            builder.build(str(source), str(out))
        con = connect(out)
        try:
            gids = [r[0] for r in con.execute("SELECT gid FROM person_work ORDER BY gid")]
            names = [r[0] for r in con.execute("SELECT display_name FROM person ORDER BY display_name")]
        finally:
            con.close()
        holds = gids == [2] and names == ["Roe, Richard"]
        return holds, {"gids_after_source_replacement": gids, "people_after_source_replacement": names}

def case_unicode_collision(ctx: Context) -> tuple[bool, dict[str, Any]]:
    builder = ctx.module("loaders/build_people_graph_books.py")
    left = builder.person_key("李, 白", None, None)
    right = builder.person_key("王, 維", None, None)
    with tempfile.TemporaryDirectory(prefix="pg-red-team-unicode-") as td:
        tmp = Path(td)
        source, out = tmp / "books.sqlite", tmp / "people.sqlite"
        con = connect(source)
        try:
            con.execute("CREATE TABLE book(gid INTEGER PRIMARY KEY, authors TEXT, media_type TEXT)")
            con.execute("INSERT INTO book VALUES (1,'李, 白; 王, 維','Text')")
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            builder.build(str(source), str(out))
        con = connect(out)
        try:
            people = [dict(r) for r in con.execute("SELECT person_key,display_name,raw_variants FROM person")]
            edge_count = con.execute("SELECT COUNT(*) FROM person_work").fetchone()[0]
        finally:
            con.close()
    holds = left != right and len(people) == 2 and edge_count == 2
    return holds, {
        "key_for_李白": left,
        "key_for_王維": right,
        "people_rows": people,
        "edge_count": edge_count,
    }

def case_aliases_absent_from_fts(ctx: Context) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="pg-red-team-alias-fts-") as td:
        tmp = Path(td)
        v1, people, books, out = (tmp / n for n in ("v1.sqlite", "people.sqlite", "books.sqlite", "out.sqlite"))
        make_v1(v1, [])
        make_book_people(
            people,
            [("clemens", "Clemens, Samuel", 1835, 1910, 1, 0, '["Twain, Mark", "Mark Twain"]')],
            [("clemens", 1, "author")],
        )
        make_books(books, [(1, "Adventures")])
        build_v2_with_tracked_schema(ctx, v1, people, books, out)
        con = connect(out)
        try:
            fts_rows = [dict(r) for r in con.execute("SELECT person_id,name,aliases FROM person_search")]
            match_count = con.execute(
                "SELECT COUNT(*) FROM person_search WHERE person_search MATCH 'Twain'"
            ).fetchone()[0]
        finally:
            con.close()
        holds = match_count == 1 and any("Twain" in row["aliases"] for row in fts_rows)
        return holds, {"fts_rows": fts_rows, "twain_matches": match_count}

def case_v2_preserves_book_roles(ctx: Context) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="pg-red-team-v2-roles-") as td:
        tmp = Path(td)
        v1, people, books, out = (tmp / n for n in ("v1.sqlite", "people.sqlite", "books.sqlite", "out.sqlite"))
        make_v1(v1, [])
        make_book_people(
            people,
            [("jane", "Doe, Jane", 1970, None, 2, 0, '["Doe, Jane, 1970-"]')],
            [("jane", 1, "author"), ("jane", 1, "translator")],
        )
        make_books(books, [(1, "Dual Role Work")])
        build_v2_with_tracked_schema(ctx, v1, people, books, out)
        con = connect(out)
        try:
            roles = [r[0] for r in con.execute("SELECT role FROM person_content WHERE domain='book' ORDER BY role")]
        finally:
            con.close()
        holds = roles == ["author", "translator"]
        return holds, {"roles_in_v2_builder_output": roles}
