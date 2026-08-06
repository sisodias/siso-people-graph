"""Loader, enrichment, rerun, and rank red-team cases."""
from __future__ import annotations

from support import *  # lane-local fixture primitives; no third-party dependencies

def case_topic_loader_rerun(ctx: Context) -> tuple[bool, dict[str, Any]]:
    loader = ctx.module("loaders/load_owner_topics.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-topic-rerun-") as td:
        tmp = Path(td)
        source, graph = tmp / "identity.sqlite", tmp / "graph.sqlite"
        make_identity_source(source, [("alice/project", 100, "Python", "", '["databases"]', "https://example.invalid", 0)])
        con = connect(source)
        try:
            con.execute("INSERT INTO repo_category VALUES ('alice/project',8.0,7.0)")
            con.commit()
        finally:
            con.close()
        make_graph(ctx, graph)
        con = connect(graph)
        try:
            add_person(con, "gh:alice", "alice", origin="github", rank_score=100.0)
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            loader.load(str(source), str(graph), 0, True)
        con = connect(graph)
        try:
            first_rank = con.execute("SELECT rank_score FROM person WHERE person_id='gh:alice'").fetchone()[0]
            first_topics = con.execute("SELECT COUNT(*) FROM person_topic").fetchone()[0]
        finally:
            con.close()
        with quiet_stdio():
            loader.load(str(source), str(graph), 0, True)
        con = connect(graph)
        try:
            second_rank = con.execute("SELECT rank_score FROM person WHERE person_id='gh:alice'").fetchone()[0]
            second_topics = con.execute("SELECT COUNT(*) FROM person_topic").fetchone()[0]
        finally:
            con.close()
        holds = first_rank == second_rank and first_topics == second_topics
        return holds, {
            "rank_after_first": first_rank,
            "rank_after_second": second_rank,
            "topics_after_first": first_topics,
            "topics_after_second": second_topics,
        }

def case_owner_loader_exact_rerun(ctx: Context) -> tuple[bool, dict[str, Any]]:
    loader = ctx.module("loaders/load_owners_into_people_graph.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-owner-exact-") as td:
        tmp = Path(td)
        source, graph = tmp / "identity.sqlite", tmp / "graph.sqlite"
        make_identity_source(source, [("alice/project", 10, "Python", "A project", "[]", "https://example.invalid", 0)])
        make_graph(ctx, graph)
        with quiet_stdio():
            loader.load(str(source), str(graph), 0, 0, True)
            loader.load(str(source), str(graph), 0, 0, True)
        con = connect(graph)
        try:
            people = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
            edges = con.execute("SELECT COUNT(*) FROM person_content").fetchone()[0]
            extids = con.execute("SELECT COUNT(*) FROM external_ids").fetchone()[0]
        finally:
            con.close()
        holds = (people, edges, extids) == (1, 1, 1)
        return holds, {"people": people, "edges": edges, "external_ids": extids}

def case_owner_loader_stale_source(ctx: Context) -> tuple[bool, dict[str, Any]]:
    loader = ctx.module("loaders/load_owners_into_people_graph.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-owner-stale-") as td:
        tmp = Path(td)
        source, graph = tmp / "identity.sqlite", tmp / "graph.sqlite"
        make_identity_source(source, [("oldorg/project", 10, "Python", "Old", "[]", "https://example.invalid/old", 0)])
        make_graph(ctx, graph)
        with quiet_stdio():
            loader.load(str(source), str(graph), 0, 0, True)
        con = connect(source)
        try:
            con.execute("DELETE FROM repo_card")
            con.execute(
                "INSERT INTO repo_card VALUES (?,?,?,?,?,?,?)",
                ("neworg/project", 10, "Python", "Transferred", "[]", "https://example.invalid/new", 0),
            )
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            loader.load(str(source), str(graph), 0, 0, True)
        con = connect(graph)
        try:
            people = [r[0] for r in con.execute("SELECT person_id FROM person ORDER BY person_id")]
            edges = [r[0] for r in con.execute("SELECT content_ref FROM person_content ORDER BY content_ref")]
        finally:
            con.close()
        holds = "oldorg/project" not in edges and "gh:oldorg" not in people
        return holds, {"people_after_replacement": people, "edges_after_replacement": edges}

def case_enrichment_mutates_canonical(ctx: Context) -> tuple[bool, dict[str, Any]]:
    enricher = ctx.module("loaders/enrich_owners.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-enrich-mutation-") as td:
        graph = Path(td) / "graph.sqlite"
        make_graph(ctx, graph)
        con = connect(graph)
        try:
            add_person(
                con,
                "gh:alice",
                "alice",
                origin="github",
                rank_score=999.0,
                built_at="canonical-build",
            )
            con.commit()
        finally:
            con.close()

        def fake_fetch(login: str, token: str | None) -> tuple[dict[str, Any], int]:
            return (
                {
                    "id": 42,
                    "name": "Alice Example",
                    "type": "User",
                    "followers": 12,
                    "twitter_username": None,
                    "blog": None,
                    "company": None,
                    "location": None,
                },
                100,
            )

        enricher.fetch = fake_fetch
        with quiet_stdio():
            enricher.enrich(str(graph), 1, None, 0.0)
        con = connect(graph)
        try:
            row = dict(
                con.execute(
                    "SELECT name,kind,rank_score,built_at FROM person WHERE person_id='gh:alice'"
                ).fetchone()
            )
            ids = [dict(r) for r in con.execute("SELECT platform,value FROM external_ids ORDER BY platform")]
        finally:
            con.close()
        holds = row == {
            "name": "alice",
            "kind": "human",
            "rank_score": 999.0,
            "built_at": "canonical-build",
        }
        return holds, {"canonical_row_after_enrichment": row, "observed_external_ids": ids}

def case_enrichment_partial_field_block(ctx: Context) -> tuple[bool, dict[str, Any]]:
    enricher = ctx.module("loaders/enrich_owners.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-enrich-partial-") as td:
        graph = Path(td) / "graph.sqlite"
        make_graph(ctx, graph)
        con = connect(graph)
        try:
            add_person(con, "gh:alice", "alice", origin="github", rank_score=1.0)
            con.execute(
                "INSERT INTO external_ids VALUES ('gh:alice','real_name','Alice Example',1.0,'fixture')"
            )
            con.commit()
        finally:
            con.close()
        calls: list[str] = []

        def fake_fetch(login: str, token: str | None) -> tuple[dict[str, Any], int]:
            calls.append(login)
            return (
                {
                    "id": 42,
                    "name": "Alice Example",
                    "type": "User",
                    "followers": 1,
                    "twitter_username": "alice",
                    "blog": "https://alice.invalid",
                    "company": None,
                    "location": None,
                },
                100,
            )

        enricher.fetch = fake_fetch
        with quiet_stdio():
            stats = enricher.enrich(str(graph), 1, None, 0.0)
        con = connect(graph)
        try:
            platforms = [r[0] for r in con.execute("SELECT platform FROM external_ids ORDER BY platform")]
        finally:
            con.close()
        holds = calls == ["alice"] and "github_id" in platforms and "x_handle" in platforms and "website" in platforms
        return holds, {"fetch_calls": calls, "stats": stats, "platforms_after": platforms}

def case_non_gh_canonical_gap(ctx: Context) -> tuple[bool, dict[str, Any]]:
    topic_loader = ctx.module("loaders/load_owner_topics.py")
    enricher = ctx.module("loaders/enrich_owners.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-non-gh-") as td:
        tmp = Path(td)
        source, graph = tmp / "identity.sqlite", tmp / "graph.sqlite"
        make_identity_source(source, [("alice/project", 10, "Python", "", '["databases"]', "https://example.invalid", 0)])
        make_graph(ctx, graph)
        con = connect(graph)
        try:
            add_person(con, "reg:alice", "Alice Example", origin="registry", rank_score=5.0)
            con.execute(
                "INSERT INTO external_ids VALUES ('reg:alice','github_login','alice',1.0,'fixture')"
            )
            con.commit()
        finally:
            con.close()
        with quiet_stdio():
            topic_loader.load(str(source), str(graph), 0, True)
        calls: list[str] = []

        def fake_fetch(login: str, token: str | None) -> tuple[dict[str, Any], int]:
            calls.append(login)
            return ({"id": 42, "name": "Alice Example", "type": "User", "followers": 5}, 100)

        enricher.fetch = fake_fetch
        with quiet_stdio():
            enricher.enrich(str(graph), 1, None, 0.0)
        con = connect(graph)
        try:
            topic_count = con.execute(
                "SELECT COUNT(*) FROM person_topic WHERE person_id='reg:alice'"
            ).fetchone()[0]
            github_id_count = con.execute(
                "SELECT COUNT(*) FROM external_ids WHERE person_id='reg:alice' AND platform='github_id'"
            ).fetchone()[0]
        finally:
            con.close()
        holds = topic_count > 0 and github_id_count == 1 and calls == ["alice"]
        return holds, {
            "canonical_id": "reg:alice",
            "origin": "registry",
            "github_login_external_id": "alice",
            "topic_count": topic_count,
            "github_id_count": github_id_count,
            "fetch_calls": calls,
        }

def case_rank_score_unit_mix(ctx: Context) -> tuple[bool, dict[str, Any]]:
    owner_loader = ctx.module("loaders/load_owners_into_people_graph.py")
    topic_loader = ctx.module("loaders/load_owner_topics.py")
    enricher = ctx.module("loaders/enrich_owners.py")
    with tempfile.TemporaryDirectory(prefix="pg-red-team-rank-units-") as td:
        tmp = Path(td)
        source, graph = tmp / "identity.sqlite", tmp / "graph.sqlite"
        make_identity_source(source, [("alice/project", 100, "Python", "", '["databases"]', "https://example.invalid", 0)])
        con = connect(source)
        try:
            con.execute("INSERT INTO repo_category VALUES ('alice/project',8.0,7.0)")
            con.commit()
        finally:
            con.close()
        make_graph(ctx, graph)
        with quiet_stdio():
            owner_loader.load(str(source), str(graph), 0, 0, True)
        con = connect(graph)
        try:
            after_stars = con.execute("SELECT rank_score FROM person WHERE person_id='gh:alice'").fetchone()[0]
        finally:
            con.close()
        with quiet_stdio():
            topic_loader.load(str(source), str(graph), 0, True)
        con = connect(graph)
        try:
            after_rating = con.execute("SELECT rank_score FROM person WHERE person_id='gh:alice'").fetchone()[0]
        finally:
            con.close()

        def fake_fetch(login: str, token: str | None) -> tuple[dict[str, Any], int]:
            return (
                {
                    "id": 42,
                    "name": "alice",
                    "type": "User",
                    "followers": 7,
                    "twitter_username": None,
                    "blog": None,
                    "company": None,
                    "location": None,
                },
                100,
            )

        enricher.fetch = fake_fetch
        with quiet_stdio():
            enricher.enrich(str(graph), 1, None, 0.0)
        con = connect(graph)
        try:
            after_followers = con.execute("SELECT rank_score FROM person WHERE person_id='gh:alice'").fetchone()[0]
        finally:
            con.close()
        trace = [after_stars, after_rating, after_followers]
        holds = trace == [after_stars, after_stars, after_stars]
        return holds, {
            "rank_score_trace": trace,
            "semantic_units": ["sum(repo stars)", "previous + mean repo rating", "followers"],
        }
