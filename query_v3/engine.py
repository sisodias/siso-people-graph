"""The query library. One source of truth; every surface calls this.

CLI, HTTP API, MCP and the viewer are projections of this module -- none of them
carries its own SQL. That is not tidiness for its own sake: duplicated SQL is how
the read layer drifted away from the identity layer in the first place, so a
second copy of "find a person by name" is the exact defect this lane is fixing,
reintroduced one layer up.

Safety properties held here rather than at each surface:
  * every connection is opened ?mode=ro and every attach is ?mode=ro
  * every value is bound; no query is built by string interpolation of user input
    (schema names in f-strings are internal constants, never caller input)
  * every list query is bounded by an explicit limit and reports its true total
  * a busy/locked database fails as a declared error, never as a silent empty
"""
from __future__ import annotations

import sqlite3
import time

from . import capability, config as cfgmod, evidence as ev, resolver as resmod
from .response import Page, Response

MAX_LIMIT = 500


class QueryEngine:
    def __init__(self, config: cfgmod.Config | None = None,
                 explicit_paths: dict[str, str] | None = None,
                 root: str | None = None) -> None:
        self.config = config or cfgmod.load(explicit=explicit_paths, root=root)
        self.con: sqlite3.Connection | None = None
        self.caps = capability.Capabilities()
        self.resolver: resmod.Resolver | None = None
        self._connect()

    # ---------------------------------------------------------------- setup

    def _connect(self) -> None:
        paths = self.config.paths
        if not paths:
            self.caps = capability.Capabilities()
            self.caps.missing.append("people_domain")
            self.caps.notes.append("No databases configured or found.")
            self.resolver = resmod.NullResolver(None, self.caps)
            return
        first = paths.get("people") or next(iter(paths.values()))
        self.con = sqlite3.connect(f"file:{first}?mode=ro", uri=True,
                                   timeout=self.config.timeout_ms / 1000)
        attached: dict[str, str] = {}
        for name, path in paths.items():
            try:
                self.con.execute(
                    "ATTACH DATABASE ? AS " + name, (f"file:{path}?mode=ro",)
                )
                attached[name] = path
            except sqlite3.Error as exc:
                self.caps.notes.append(f"Could not attach {name}: {exc}")
        self.caps = capability.detect(self.con, attached)
        self.resolver = resmod.for_capabilities(self.con, self.caps)

    def close(self) -> None:
        if self.con is not None:
            self.con.close()
            self.con = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # ------------------------------------------------------------ envelope

    def _envelope(self, query_type: str, query: dict) -> Response:
        r = Response(query_type=query_type, query=query)
        r.capabilities = self.caps.as_dict()
        r.sources = self._sources()
        r.identity = {
            "mode": self.caps.identity_mode(),
            "applied": [],
            "unresolved": [],
        }
        if self.resolver is not None:
            for w in self.resolver.warnings():
                r.warn(w)
        for note in self.caps.notes:
            r.warn(note)
        for miss in sorted(set(self.caps.missing)):
            r.gap(f"absent: {miss}")
        # Additive v3 tables are reported as gaps too. Their absence is the
        # difference between "this person has no typed relations" and "this
        # database cannot express typed relations", and a caller that cannot
        # tell those apart will read a capability limit as a fact about a person.
        for t in capability.V3_TABLES:
            if not self.caps.has("people", t):
                r.gap(f"absent: people.{t} (additive v3 capability)")
        return r

    def _sources(self) -> dict:
        """Source snapshots: what was attached, from where, how big, how fresh."""
        out = {}
        for domain, path in sorted(self.config.paths.items()):
            entry = {
                "path": path,
                "path_origin": self.config.origins.get(domain, "unknown"),
                "attached": domain in self.caps.domains,
            }
            if domain in self.caps.domains:
                entry["tables"] = sorted(self.caps.tables.get(domain, ()))
                if self.caps.has(domain, "source_snapshot"):
                    entry["rights"] = self._rights(domain)
                else:
                    entry["rights"] = "undeclared: no source_snapshot table"
            out[domain] = entry
        return out

    def _rights(self, domain: str) -> object:
        try:
            rows = self.con.execute(
                f"SELECT source, rights_state, retrieved_at "
                f"FROM {domain}.source_snapshot"
            ).fetchall()
        except sqlite3.Error:
            return "undeclared: source_snapshot unreadable"
        return [
            {"source": s, "rights_state": r, "retrieved_at": t} for s, r, t in rows
        ]

    def _people_ready(self, r: Response) -> bool:
        if self.con is None or "people" not in self.caps.domains:
            r.warn("No people database available; this query cannot be answered.")
            r.result = {}
            return False
        if not self.caps.has("people", "person"):
            r.warn("people.person table is absent; this query cannot be answered.")
            r.result = {}
            return False
        return True

    # ------------------------------------------------------------- searching

    def _search_people(self, name: str, limit: int) -> tuple[list[tuple], str, int]:
        """Find candidate person rows. Returns (rows, path_used, total_matched).

        `path_used` is returned rather than logged because a caller must be able
        to tell whether the fast index or the linear scan answered -- the old
        code silently degraded from FTS to LIKE and looked identical either way.
        Values are always bound; `name` never reaches SQL as text.
        """
        cols = ("person_id", "name", "birth_year", "death_year", "kind", "origin",
                "state", "merged_into")
        select = ", ".join(f"p.{c}" for c in cols)

        if self.caps.has("people", "person_search"):
            try:
                # FTS5's MATCH left operand must be the table's UNQUALIFIED,
                # UNALIASED name. Two forms that look right are both errors,
                # verified against SQLite rather than assumed:
                #   people.person_search MATCH ?  -> no such column: people.person_search
                #   ... person_search s WHERE s MATCH ? -> no such column: s
                # The first is what the old code shipped; because the failure was
                # swallowed by a bare `except sqlite3.Error`, every name lookup
                # silently ran the linear scan while the code read as if indexed.
                fts = self._fts_query(name)
                total = self.con.execute(
                    "SELECT COUNT(*) FROM people.person_search "
                    "WHERE person_search MATCH ?",
                    (fts,),
                ).fetchone()[0]
                rows = self.con.execute(
                    f"""SELECT {select}
                        FROM people.person_search
                        JOIN people.person p
                          ON p.person_id = people.person_search.person_id
                        WHERE person_search MATCH ?
                        ORDER BY rank
                        LIMIT ?""",
                    (fts, limit),
                ).fetchall()
                return rows, "fts5", total
            except sqlite3.Error as exc:
                # Degradation is reported, never silent.
                self.caps.notes.append(
                    f"person_search present but unusable ({exc}); "
                    "fell back to a linear name scan."
                )

        like = f"%{name}%"
        total = self.con.execute(
            "SELECT COUNT(*) FROM people.person WHERE name LIKE ?", (like,)
        ).fetchone()[0]
        rows = self.con.execute(
            f"SELECT {select} FROM people.person p WHERE p.name LIKE ? "
            f"ORDER BY p.name LIMIT ?",
            (like, limit),
        ).fetchall()
        return rows, "like_scan", total

    @staticmethod
    def _fts_query(name: str) -> str:
        """Quote user text so FTS treats it as terms, not operator syntax.

        Without this a name containing a quote, NEAR, OR, or a bare hyphen is
        parsed as a query expression and either errors or silently means
        something else. Doubling embedded quotes and wrapping makes it a phrase.
        """
        cleaned = name.replace('"', '""').strip()
        return f'"{cleaned}"' if cleaned else '""'

    # ---------------------------------------------------------------- who

    def who(self, name: str, limit: int = 8, offset: int = 0) -> dict:
        limit = max(1, min(limit, MAX_LIMIT))
        r = self._envelope("who", {"name": name, "limit": limit, "offset": offset})
        if not self._people_ready(r):
            return r.as_dict()

        started = time.perf_counter()
        rows, path_used, total = self._search_people(name, limit + offset)
        rows = rows[offset:]
        r.execution = {"search_path": path_used, "search_path_is_indexed":
                       path_used == "fts5"}
        if path_used == "like_scan":
            r.gap(
                "Name search used a linear LIKE scan, not the FTS index: results "
                "are substring matches and ordering is alphabetical, not relevance."
            )

        by_id = {row[0]: row for row in rows}
        resolutions = self.resolver.resolve(list(by_id))

        # Fold source rows into the person each decision says they are.
        clusters: dict[str, dict] = {}
        for pid, row in by_id.items():
            res = resolutions.get(pid)
            canonical = res.canonical_id if res else pid
            entry = clusters.setdefault(
                canonical,
                {
                    "person_id": canonical,
                    "matched_rows": [],
                    "identity": (res.as_dict() if res else
                                 {"canonical_id": canonical,
                                  "member_ids": [canonical],
                                  "merged_row_count": 0,
                                  "decisions": [],
                                  "unresolved_candidates": []}),
                },
            )
            entry["matched_rows"].append(pid)

        matches = []
        for canonical, entry in clusters.items():
            rec = self._person_record(canonical, entry)
            if rec:
                matches.append(rec)
                for d in entry["identity"]["decisions"]:
                    if d not in r.identity["applied"]:
                        r.identity["applied"].append(d)
                for u in entry["identity"]["unresolved_candidates"]:
                    if u not in r.identity["unresolved"]:
                        r.identity["unresolved"].append(u)

        matches.sort(key=lambda m: (-m["source_coverage"]["content_count"],
                                    m["person_id"]))
        r.result = {"matches": matches}

        # Paging is counted in SOURCE ROWS, the unit the limit is applied in.
        # Counting resolved people against a row total would make a successful
        # merge look like truncation -- 3 rows folding into 2 people is complete,
        # not a partial page -- and would then advise the caller to page for
        # results that do not exist.
        rows_scanned = len(by_id) + offset
        r.page = Page(returned=rows_scanned - offset, total_matched=total,
                      limit=limit, offset=offset)
        r.result["people_returned"] = len(matches)
        r.result["source_rows_matched"] = total
        if r.page.truncated:
            r.gap(
                f"{total} person rows matched; this page covers "
                f"{rows_scanned - offset} of them (offset {offset}), yielding "
                f"{len(matches)} people. Page for the rest."
            )
        elif len(matches) < rows_scanned - offset:
            r.gap(
                f"{rows_scanned - offset} source rows resolved to "
                f"{len(matches)} people by accepted identity decisions; the "
                "row count and the people count differ for that reason."
            )
        if r.identity["unresolved"]:
            r.gap(
                "Proposed identity claims touch this result and were NOT applied; "
                "some rows shown separately may be the same person."
            )
        r.execution["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return r.as_dict()

    def _person_record(self, canonical: str, entry: dict) -> dict | None:
        row = self.con.execute(
            """SELECT person_id, name, birth_year, death_year, kind, origin,
                      state, merged_into
               FROM people.person WHERE person_id = ?""",
            (canonical,),
        ).fetchone()
        if not row:
            return None
        pid, nm, b, d, kind, origin, state, merged_into = row

        members = entry["identity"]["member_ids"] or [pid]
        marks = ",".join("?" * len(members))

        produced: dict[str, int] = {}
        for domain, n in self.con.execute(
            f"SELECT domain, COUNT(*) FROM people.person_content "
            f"WHERE person_id IN ({marks}) GROUP BY 1",
            members,
        ):
            produced[domain] = n

        rec = {
            "person_id": pid,
            "name": nm,
            "lived": fmt_life(b, d),
            "birth_year": b,
            "death_year": d,
            "kind": kind,
            "state": state,
            "merged_into": merged_into,
            "first_seen_in": origin,
            "evidence": ev.observed(source=origin,
                                    detail="person row as materialised by the "
                                           "originating loader").as_dict(),
            "identity": entry["identity"],
            "source_coverage": {
                "domains": sorted(produced),
                "by_domain": produced,
                "content_count": sum(produced.values()),
                "counted_across_rows": sorted(members),
            },
        }

        if self.caps.has("people", "external_ids"):
            rec["identifiers"] = [
                {"platform": p, "value": v, "confidence": c, "source": s,
                 "evidence": ev.observed(source=s).as_dict()}
                for p, v, c, s in self.con.execute(
                    f"SELECT platform, value, confidence, source "
                    f"FROM people.external_ids WHERE person_id IN ({marks}) "
                    f"ORDER BY platform, value LIMIT 50",
                    members,
                )
            ]
        else:
            rec["identifiers"] = []
            rec["identifiers_note"] = "external_ids table absent"

        if self.caps.has("people", "person_topic"):
            rec["topics"] = [
                {"topic": t, "scheme": sc, "weight": w,
                 "evidence": ev.derived(
                     "topic weight aggregated from produced works").as_dict()}
                for t, sc, w in self.con.execute(
                    f"SELECT topic, scheme, weight FROM people.person_topic "
                    f"WHERE person_id IN ({marks}) ORDER BY weight DESC LIMIT 6",
                    members,
                )
            ]
        else:
            rec["topics"] = []
            rec["topics_note"] = "person_topic table absent"
        return rec

    # -------------------------------------------------------------- works

    def works(self, name: str, limit: int = 100, offset: int = 0) -> dict:
        """Everything a person produced, with honest counts and fetch routes."""
        limit = max(1, min(limit, MAX_LIMIT))
        r = self._envelope("works", {"name": name, "limit": limit,
                                     "offset": offset})
        if not self._people_ready(r):
            return r.as_dict()

        started = time.perf_counter()
        who = self.who(name, limit=8)
        matches = who["result"].get("matches", [])
        r.execution["search_path"] = who["execution"].get("search_path")
        r.identity = who["identity_resolution"]
        for g in who["coverage_gaps"]:
            r.gap(g)
        for w in who["warnings"]:
            r.warn(w)

        if not matches:
            r.result = {"person": None, "works": []}
            r.page = Page(returned=0, total_matched=0, limit=limit, offset=offset)
            r.gap("No person matched; no works can be listed.")
            return r.as_dict()

        best = matches[0]
        members = best["identity"]["member_ids"] or [best["person_id"]]
        marks = ",".join("?" * len(members))

        # The honest total: a real COUNT over the same predicate as the page.
        # The old code reported count=len(rows) against a hard LIMIT 200, so a
        # person with 40,000 works and a person with 200 were indistinguishable.
        total = self.con.execute(
            f"SELECT COUNT(*) FROM people.person_content "
            f"WHERE person_id IN ({marks})",
            members,
        ).fetchone()[0]

        rows = self.con.execute(
            f"""SELECT domain, content_ref, role, title, source, observed_at,
                       person_id
                FROM people.person_content
                WHERE person_id IN ({marks})
                ORDER BY domain, title, content_ref
                LIMIT ? OFFSET ?""",
            members + [limit, offset],
        ).fetchall()

        works = [
            {
                "domain": d,
                "ref": ref,
                "role": role,
                "title": title,
                "contributed_by_row": pid,
                "evidence": ev.observed(source=src, observed_at=obs,
                                        detail=f"person_content edge from {src}"
                                        ).as_dict(),
                "fetch": fetch_routes(self.con, self.caps, d, ref),
            }
            for d, ref, role, title, src, obs, pid in rows
        ]

        r.result = {
            "person": {
                "person_id": best["person_id"],
                "name": best["name"],
                "member_ids": members,
            },
            "works": works,
        }
        r.page = Page(returned=len(works), total_matched=total, limit=limit,
                      offset=offset)
        if r.page.truncated:
            r.gap(
                f"Showing {len(works)} of {total} works "
                f"(offset {offset}). This is a page, not the complete set."
            )
        if len(members) > 1:
            r.gap(
                "Works are aggregated across "
                f"{len(members)} source rows merged by accepted identity "
                "decisions; see identity_resolution.applied."
            )
        r.execution["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return r.as_dict()

    # ------------------------------------------------------- relationships

    def relationships(self, name: str, limit: int = 25) -> dict:
        """Typed, evidenced neighbours. Honest about which types exist."""
        limit = max(1, min(limit, MAX_LIMIT))
        r = self._envelope("relationships", {"name": name, "limit": limit})
        if not self._people_ready(r):
            return r.as_dict()

        who = self.who(name, limit=4)
        matches = who["result"].get("matches", [])
        if not matches:
            r.result = {"person": None, "neighbours": []}
            r.page = Page(returned=0, total_matched=0, limit=limit)
            r.gap("No person matched.")
            return r.as_dict()

        best = matches[0]
        members = best["identity"]["member_ids"] or [best["person_id"]]
        marks = ",".join("?" * len(members))
        neighbours: list[dict] = []

        if not self.caps.has("people", "person_relation"):
            r.gap(
                "No person_relation table: typed/temporal relations are "
                "unavailable. Neighbours below are DERIVED from shared works "
                "only, which is a weaker claim than an asserted relation."
            )

        # Co-contribution: two people on the same content_ref. Derived, and
        # labelled as derived -- it is evidence of adjacency, not of a relationship.
        rows = self.con.execute(
            f"""SELECT c2.person_id, p.name, c1.domain, c1.content_ref,
                       c1.role, c2.role, COUNT(*) OVER () AS total
                FROM people.person_content c1
                JOIN people.person_content c2
                  ON c2.domain = c1.domain
                 AND c2.content_ref = c1.content_ref
                 AND c2.person_id NOT IN ({marks})
                JOIN people.person p ON p.person_id = c2.person_id
                WHERE c1.person_id IN ({marks})
                LIMIT ?""",
            members + members + [limit],
        ).fetchall()

        total = rows[0][6] if rows else 0
        for other_id, other_name, domain, ref, role_a, role_b, _t in rows:
            neighbours.append({
                "person_id": other_id,
                "name": other_name,
                "relation": "co_contributor",
                "via": {"domain": domain, "ref": ref,
                        "roles": [role_a, role_b]},
                "evidence": ev.derived(
                    f"both rows carry a person_content edge to {domain}:{ref}"
                ).as_dict(),
            })

        r.result = {
            "person": {"person_id": best["person_id"], "name": best["name"]},
            "neighbours": neighbours,
        }
        r.page = Page(returned=len(neighbours), total_matched=total, limit=limit)
        if r.page.truncated:
            r.gap(f"Showing {len(neighbours)} of {total} adjacency edges.")
        return r.as_dict()

    # --------------------------------------------------------------- path

    def path(self, from_name: str, to_name: str, max_hops: int = 3) -> dict:
        """An explainable route between two people, with per-edge provenance."""
        max_hops = max(1, min(max_hops, 4))
        r = self._envelope("path", {"from": from_name, "to": to_name,
                                    "max_hops": max_hops})
        if not self._people_ready(r):
            return r.as_dict()

        a = self.who(from_name, limit=2)["result"].get("matches", [])
        b = self.who(to_name, limit=2)["result"].get("matches", [])
        if not a or not b:
            r.result = {"path": None}
            r.gap("One or both endpoints did not match a person.")
            return r.as_dict()

        start_members = set(a[0]["identity"]["member_ids"] or [a[0]["person_id"]])
        goal_members = set(b[0]["identity"]["member_ids"] or [b[0]["person_id"]])

        # Breadth-first over co-contribution edges, bounded by hops and by a
        # node budget so a hub person cannot turn one query into a graph walk.
        frontier = [(pid, []) for pid in start_members]
        seen = set(start_members)
        budget = self.config.budget_rows
        found = None
        while frontier and budget > 0 and found is None:
            nxt = []
            for pid, trail in frontier:
                if len(trail) >= max_hops:
                    continue
                rows = self.con.execute(
                    """SELECT c2.person_id, p.name, c1.domain, c1.content_ref,
                              c1.source
                       FROM people.person_content c1
                       JOIN people.person_content c2
                         ON c2.domain = c1.domain
                        AND c2.content_ref = c1.content_ref
                        AND c2.person_id != c1.person_id
                       JOIN people.person p ON p.person_id = c2.person_id
                       WHERE c1.person_id = ?
                       LIMIT 60""",
                    (pid,),
                ).fetchall()
                budget -= len(rows)
                for other, other_name, domain, ref, src in rows:
                    edge = {
                        "from": pid,
                        "to": other,
                        "to_name": other_name,
                        "relation": "co_contributor",
                        "via": {"domain": domain, "ref": ref},
                        "evidence": ev.derived(
                            f"shared person_content edge to {domain}:{ref}",
                            source=src,
                        ).as_dict(),
                    }
                    if other in goal_members:
                        found = trail + [edge]
                        break
                    if other not in seen:
                        seen.add(other)
                        nxt.append((other, trail + [edge]))
                if found:
                    break
            frontier = nxt

        r.result = {
            "from": {"person_id": a[0]["person_id"], "name": a[0]["name"]},
            "to": {"person_id": b[0]["person_id"], "name": b[0]["name"]},
            "path": found,
            "hops": len(found) if found else None,
        }
        r.page = Page(returned=1 if found else 0, total_matched=1 if found else 0,
                      limit=1)
        if found is None:
            r.gap(
                f"No path within {max_hops} hops over co-contribution edges "
                f"(node budget {self.config.budget_rows}). Absence of a path here "
                "is not evidence that no relationship exists."
            )
        if not self.caps.has("people", "person_relation"):
            r.gap("Only derived co-contribution edges were traversable; typed "
                  "relations are unavailable.")
        return r.as_dict()

    # ------------------------------------------------------------- claims

    def claims(self, name: str, limit: int = 25) -> dict:
        """Evidence-backed assertions, with review/inference state."""
        limit = max(1, min(limit, MAX_LIMIT))
        r = self._envelope("claims", {"name": name, "limit": limit})
        if not self._people_ready(r):
            return r.as_dict()
        if not self.caps.has("people", "claim"):
            r.result = {"claims": []}
            r.page = Page(returned=0, total_matched=0, limit=limit)
            r.gap("No claim table in this database: assertion-level evidence is "
                  "unavailable. This is a missing capability, not an empty result.")
            return r.as_dict()

        who = self.who(name, limit=4)
        matches = who["result"].get("matches", [])
        if not matches:
            r.result = {"claims": []}
            r.page = Page(returned=0, total_matched=0, limit=limit)
            return r.as_dict()
        members = matches[0]["identity"]["member_ids"]
        marks = ",".join("?" * len(members))
        total = self.con.execute(
            f"SELECT COUNT(*) FROM people.claim WHERE person_id IN ({marks})",
            members,
        ).fetchone()[0]
        rows = self.con.execute(
            f"SELECT claim_id, statement, review_state, source, observed_at "
            f"FROM people.claim WHERE person_id IN ({marks}) LIMIT ?",
            members + [limit],
        ).fetchall()
        r.result = {"claims": [
            {"claim_id": cid, "statement": st, "review_state": rs,
             "evidence": ev.observed(source=src, observed_at=obs).as_dict()}
            for cid, st, rs, src, obs in rows
        ]}
        r.page = Page(returned=len(rows), total_matched=total, limit=limit)
        return r.as_dict()

    # ---------------------------------------------------------- inventory

    def inventory(self) -> dict:
        """What data exists at all, plus what is missing. Never says 'all'."""
        r = self._envelope("inventory", {})
        domains: dict[str, dict] = {}
        if self.con is not None:
            for domain in sorted(self.caps.domains):
                tables = {}
                for t in sorted(self.caps.tables.get(domain, ())):
                    try:
                        tables[t] = self.con.execute(
                            f"SELECT COUNT(*) FROM {domain}.{t}"
                        ).fetchone()[0]
                    except sqlite3.Error as exc:
                        tables[t] = f"uncountable: {exc}"
                domains[domain] = {
                    "path": self.config.paths.get(domain),
                    "path_origin": self.config.origins.get(domain),
                    "tables": tables,
                }
        r.result = {"domains": domains}
        r.page = Page(returned=len(domains), total_matched=len(domains))
        r.gap("Row counts describe THIS machine's attached snapshots only, not "
              "any canonical corpus.")
        return r.as_dict()

    def source(self) -> dict:
        """Source snapshots, rights and freshness."""
        r = self._envelope("source", {})
        r.result = {"sources": r.sources}
        r.page = Page(returned=len(r.sources), total_matched=len(r.sources))
        if not any(self.caps.has(d, "source_snapshot") for d in self.caps.domains):
            r.gap("No source_snapshot table in any attached domain: rights state, "
                  "retrieval time and build digest are UNDECLARED, not clean.")
        return r.as_dict()


# ------------------------------------------------------------------ helpers


def fmt_life(b, d):
    if b is None and d is None:
        return None
    f = lambda y: "?" if y is None else (f"{abs(y)} BCE" if y < 0 else str(y))
    return f"{f(b)}-{f(d)}"


def fetch_routes(con, caps, domain: str, ref: str) -> list[dict]:
    """Every route to the actual bytes for one work, cheapest first."""
    routes: list[dict] = []
    if domain == "book":
        routes.append({
            "route": "origin",
            "url": f"https://www.gutenberg.org/ebooks/{ref}.txt.utf-8",
            "note": "direct plaintext, no auth, no local copy needed",
        })
        routes.append({
            "route": "html",
            "url": f"https://www.gutenberg.org/ebooks/{ref}",
            "note": "human reading surface",
        })
        if "locator" in caps.domains and caps.has("locator", "location"):
            try:
                gid = int(ref)
            except (TypeError, ValueError):
                return routes
            for container, member, off, ln, uri in con.execute(
                "SELECT container, member, offset, length, uri "
                "FROM locator.location WHERE gid = ?",
                (gid,),
            ):
                routes.append({
                    "route": "byte_range",
                    "container": container,
                    "uri": uri,
                    "member": member,
                    "offset": off,
                    "length": ln,
                    "note": f"seek+read, or HTTP Range: bytes={off}-{off + ln - 1}",
                })
    elif domain == "github":
        routes.append({"route": "origin", "url": f"https://github.com/{ref}"})
        routes.append({"route": "api",
                       "url": f"https://api.github.com/repos/{ref}",
                       "note": "metadata without cloning"})
    elif domain.startswith("youtube"):
        routes.append({"route": "origin",
                       "url": f"https://www.youtube.com/watch?v={ref}"})
    return routes
