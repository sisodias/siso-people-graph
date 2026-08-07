"""Identity, query, temporal, and cross-repository red-team cases."""
from __future__ import annotations

from support import *  # lane-local fixture primitives; no third-party dependencies

def case_nonunique_external_ids(ctx: Context) -> tuple[bool, dict[str, Any]]:
    matcher = ctx.module("loaders/match_identities.py")
    unsafe: dict[str, list[dict[str, Any]]] = {}
    for platform, value in (
        ("company", "Acme"),
        ("location", "London"),
        ("real_name", "Alex Smith"),
    ):
        with tempfile.TemporaryDirectory(prefix=f"pg-red-team-{platform}-") as td:
            db = Path(td) / "graph.sqlite"
            make_graph(ctx, db)
            con = connect(db)
            try:
                add_person(con, "a", "Person One", origin="github")
                add_person(con, "b", "Person Two", origin="books")
                con.executemany(
                    "INSERT INTO external_ids(person_id,platform,value,confidence,source) VALUES (?,?,?,?,?)",
                    [("a", platform, value, 0.5, "fixture"), ("b", platform, value, 0.5, "fixture")],
                )
                con.commit()
            finally:
                con.close()
            with quiet_stdio():
                matcher.propose(str(db), True, "shared_external_id")
            con = connect(db)
            try:
                unsafe[platform] = [
                    dict(r)
                    for r in con.execute(
                        "SELECT method,confidence,evidence,status FROM identity_claim WHERE status='accepted'"
                    )
                ]
            finally:
                con.close()
    holds = all(not rows for rows in unsafe.values())
    return holds, {"accepted_nonunique_claims": unsafe}

def case_accepted_claims_inert(ctx: Context) -> tuple[bool, dict[str, Any]]:
    ask = ctx.module("loaders/ask.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-claim-query-") as td:
        db = Path(td) / "graph.sqlite"
        make_graph(ctx, db)
        con = connect(db)
        try:
            add_person(con, "reg:jordan", "Jordan Vale", origin="registry")
            add_person(con, "bk:jordan", "Jordan Vale", origin="books")
            con.execute(
                """INSERT INTO person_content
                   (person_id,domain,content_ref,role,title,source)
                   VALUES ('reg:jordan','github','jordan/project','owner','Project','fixture')"""
            )
            con.execute(
                """INSERT INTO person_content
                   (person_id,domain,content_ref,role,title,source)
                   VALUES ('bk:jordan','book','1','author','Book','fixture')"""
            )
            con.execute(
                """INSERT INTO identity_claim
                   (person_a,person_b,method,confidence,evidence,status,created_at)
                   VALUES ('bk:jordan','reg:jordan','manual',1.0,'fixture','accepted','2026-08-06T00:00:00Z')"""
            )
            con.executemany(
                "INSERT INTO person_search(person_id,name,aliases) VALUES (?,?,?)",
                [("reg:jordan", "Jordan Vale", ""), ("bk:jordan", "Jordan Vale", "")],
            )
            con.commit()
        finally:
            con.close()
        found = {"people": str(db)}
        query_con = ask.connect(found)
        try:
            who = ask.who(query_con, found, "Jordan Vale")
            works = ask.works(query_con, found, "Jordan Vale")
        finally:
            query_con.close()
        holds = len(who["matches"]) == 1 and works.get("count") == 2
        return holds, {
            "who_match_ids": [m["person_id"] for m in who["matches"]],
            "works_person_id": works.get("person_id"),
            "works_count": works.get("count"),
            "accepted_claim_present": True,
        }

def case_matcher_rerun(ctx: Context) -> tuple[bool, dict[str, Any]]:
    matcher = ctx.module("loaders/match_identities.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-matcher-rerun-") as td:
        db = Path(td) / "graph.sqlite"
        make_graph(ctx, db)
        con = connect(db)
        try:
            add_person(con, "a", "Alex Smith", origin="github")
            add_person(con, "b", "Alex Smith", origin="books")
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            matcher.propose(str(db), True, None)
        con = connect(db)
        try:
            first = con.execute("SELECT COUNT(*) FROM identity_claim").fetchone()[0]
        finally:
            con.close()
        with quiet_stdio():
            matcher.propose(str(db), True, None)
        con = connect(db)
        try:
            second = con.execute("SELECT COUNT(*) FROM identity_claim").fetchone()[0]
            pairs = [dict(r) for r in con.execute("SELECT person_a,person_b,method,status FROM identity_claim")]
        finally:
            con.close()
        return first == second, {"first_run_claims": first, "second_run_claims": second, "rows": pairs}

def case_github_rename_stable_id(ctx: Context) -> tuple[bool, dict[str, Any]]:
    loader = ctx.module("loaders/load_owners_into_people_graph.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-gh-rename-") as td:
        tmp = Path(td)
        source, graph = tmp / "identity.sqlite", tmp / "graph.sqlite"
        make_identity_source(source, [("newlogin/project", 10, "Python", "", "[]", "https://example.invalid", 0)])
        make_graph(ctx, graph)
        con = connect(graph)
        try:
            add_person(con, "gh:oldlogin", "oldlogin", origin="github", rank_score=10.0)
            con.executemany(
                "INSERT INTO external_ids VALUES (?,?,?,?,?)",
                [
                    ("gh:oldlogin", "github_login", "oldlogin", 1.0, "fixture"),
                    ("gh:oldlogin", "github_id", "42", 1.0, "fixture"),
                ],
            )
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            loader.load(str(source), str(graph), 0, 0, True)
        con = connect(graph)
        try:
            people = [r[0] for r in con.execute("SELECT person_id FROM person ORDER BY person_id")]
            edges = [dict(r) for r in con.execute("SELECT person_id,content_ref FROM person_content")]
        finally:
            con.close()
        holds = people == ["gh:oldlogin"] and edges == [{"person_id": "gh:oldlogin", "content_ref": "newlogin/project"}]
        return holds, {"stable_github_id": "42", "people": people, "edges": edges}

def case_common_name_review_only(ctx: Context) -> tuple[bool, dict[str, Any]]:
    matcher = ctx.module("loaders/match_identities.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-common-name-") as td:
        db = Path(td) / "graph.sqlite"
        make_graph(ctx, db)
        con = connect(db)
        try:
            add_person(con, "a", "Alex Smith", origin="github")
            add_person(con, "b", "Alex Smith", origin="books")
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            matcher.propose(str(db), True, None)
        con = connect(db)
        try:
            row = dict(
                con.execute(
                    "SELECT method,confidence,status FROM identity_claim WHERE person_a='a' AND person_b='b'"
                ).fetchone()
            )
        finally:
            con.close()
        # The invariant is that exact-name evidence alone stays PROPOSED at LOW
        # confidence -- not that the score equals one particular constant. The
        # identity_v3 matcher scores this at 0.52 with auto_eligible=False
        # (identity_v3/_candidates.py), replacing the previous 0.55; that is
        # strictly more conservative, so pinning the old constant would fail a
        # tightening of the very property under test.
        holds = (
            row["method"] == "exact_name"
            and row["status"] == "proposed"
            and 0.0 < row["confidence"] < 0.6
        )
        return holds, row

def case_kind_and_pseudonym_conflicts(ctx: Context) -> tuple[bool, dict[str, Any]]:
    matcher = ctx.module("loaders/match_identities.py")
    fixture = json.loads(ctx.fixture("adversarial_people.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="pg-red-team-kinds-") as td:
        db = Path(td) / "graph.sqlite"
        make_graph(ctx, db)
        con = connect(db)
        try:
            for person in fixture["people"]:
                add_person(
                    con,
                    person["person_id"],
                    person["name"],
                    kind=person["kind"],
                    origin=person["origin"],
                )
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            matcher.propose(str(db), True, None)
        con = connect(db)
        try:
            claims = [
                dict(r)
                for r in con.execute(
                    """SELECT c.person_a,c.person_b,c.method,c.status,
                              a.kind AS kind_a,b.kind AS kind_b
                       FROM identity_claim c
                       JOIN person a ON a.person_id=c.person_a
                       JOIN person b ON b.person_id=c.person_b
                       ORDER BY c.person_a,c.person_b"""
                )
            ]
        finally:
            con.close()
        incompatible = [r for r in claims if r["kind_a"] != r["kind_b"]]
        holds = not incompatible
        return holds, {"claims": claims, "incompatible_kind_candidates": incompatible}

def case_unknown_death_contemporaries(ctx: Context) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="pg-red-team-contemporaries-") as td:
        db = Path(td) / "graph.sqlite"
        make_graph(ctx, db)
        con = connect(db)
        try:
            add_person(con, "unknown-death", "Unknown Death", birth_year=1900, death_year=None)
            add_person(con, "late-person", "Late Person", birth_year=1979, death_year=2000)
            con.commit()
            rows = [
                dict(r)
                for r in con.execute(
                    """SELECT person_id,contemporary_id,overlap_start,overlap_end
                       FROM v_contemporaries
                       WHERE person_id='unknown-death' AND contemporary_id='late-person'"""
                )
            ]
        finally:
            con.close()
        holds = not rows
        return holds, {"unknown_death_year": None, "assumed_end": 1980, "derived_rows": rows}

def case_missing_domain_diagnostics(ctx: Context) -> tuple[bool, dict[str, Any]]:
    ask = ctx.module("loaders/ask.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-missing-domain-") as td:
        books = Path(td) / "books.sqlite"
        con = connect(books)
        try:
            con.execute("CREATE TABLE book(gid INTEGER PRIMARY KEY,title TEXT)")
            con.execute("INSERT INTO book VALUES (1,'Only Book Domain')")
            con.commit()
        finally:
            con.close()
        found = {"books": str(books)}
        query_con = ask.connect(found)
        try:
            who = ask.who(query_con, found, "Alice")
            inv = ask.inventory(query_con, found)
        finally:
            query_con.close()
        explicit_missing = bool(
            who.get("error")
            or who.get("missing_capabilities")
            or inv.get("missing_domains")
            or inv.get("capabilities")
        )
        holds = explicit_missing
        return holds, {"who_output": who, "inventory_keys": sorted(inv), "domains_reported": sorted(inv["domains"])}

def _simulate_book_export(contract: dict[str, Any]) -> dict[str, Any]:
    def norm(value: str) -> str:
        return " ".join((value or "").split()).lower()

    existing: dict[str, str] = {
        norm(row["name"]): row["person_id"] for row in contract["canonical_people"]
    }
    mapped: dict[str, str] = {}
    for person in contract["book_people"]:
        key = norm(person["display_name"])
        if key in existing:
            pid = existing[key]
        else:
            pid = f"bk:{person['person_key']}"
            existing[key] = pid
        mapped[person["person_key"]] = pid
    allowed = set(contract["observed_export_contract"]["authorship_allowlist"])
    exported = [
        {
            "person_id": mapped[row["person_key"]],
            "gid": row["gid"],
            "role": row["role"],
        }
        for row in contract["contributions"]
        if row["role"] in allowed
    ]
    return {"person_mapping": mapped, "exported_contributions": exported}

def case_book_export_contract(ctx: Context) -> tuple[bool, dict[str, Any]]:
    contract = json.loads(ctx.fixture("book_library_export_contract.json").read_text(encoding="utf-8"))
    result = _simulate_book_export(contract)
    unrelated = contract["book_people"][0]
    merged_on_name = result["person_mapping"][unrelated["person_key"]] == "gh:alex-kim"
    exported_roles = {row["role"] for row in result["exported_contributions"]}
    expected_roles = {row["role"] for row in contract["contributions"]}
    holds = not merged_on_name and exported_roles == expected_roles
    return holds, {
        "source": contract["source"],
        "merged_distinct_book_person_on_name": merged_on_name,
        "expected_roles": sorted(expected_roles),
        "exported_roles": sorted(exported_roles),
        "person_mapping": result["person_mapping"],
    }
