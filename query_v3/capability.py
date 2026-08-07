"""What this database can actually answer, detected rather than assumed.

The rule from the lane spec: missing capabilities must be EXPLICIT in output,
never hidden and never blocking. A machine holding only v2 tables still answers
v2 questions; it must not silently pretend it answered a v3 question.

So capability detection is not a convenience -- it is the mechanism by which a
result can honestly say "I could not consider X" instead of returning a smaller
answer that looks complete. Every absent capability that would have widened or
narrowed a result becomes a declared gap on the response.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

# Tables the read layer knows how to exploit, grouped by the question they let
# us answer. Detection is by probe, not by version number: a v2 database that
# has been additively upgraded is common, and asking "which version are you"
# would get the wrong answer for it.
V2_CORE = ("person", "person_content")
V2_IDENTITY = ("identity_claim",)
V2_OPTIONAL = ("person_topic", "external_ids", "person_search")
V2_VIEWS = ("v_person_layers", "v_contemporaries")

# Additive v3 tables (Lane 3 ontology / Lane 4 identity). Absent on current main.
# Named here so their absence is reportable rather than invisible.
V3_TABLES = (
    "identity_decision",   # explicit accept/reject decisions, reversible
    "identity_cluster",    # derived canonical clusters
    "person_alias",        # time-bounded handle history
    "claim",               # evidence-backed assertions
    "person_relation",     # typed temporal relations
    "source_snapshot",     # rights/freshness/digest per source
)


@dataclass
class Capabilities:
    """Everything the read layer detected about one attached domain set."""

    domains: dict[str, str] = field(default_factory=dict)
    tables: dict[str, set[str]] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def has(self, domain: str, table: str) -> bool:
        return table in self.tables.get(domain, set())

    def identity_mode(self) -> str:
        """Which resolver adapter applies. Reported on every response.

        v3      -- explicit decision/cluster tables present
        v2      -- identity_claim + person.merged_into only
        none    -- no identity machinery at all; results are raw source rows
        """
        if self.has("people", "identity_decision") or self.has(
            "people", "identity_cluster"
        ):
            return "v3"
        if self.has("people", "identity_claim"):
            return "v2"
        return "none"

    def as_dict(self) -> dict:
        return {
            "domains_available": sorted(self.domains),
            "identity_mode": self.identity_mode(),
            "v3_tables_present": sorted(
                t for t in V3_TABLES if self.has("people", t)
            ),
            "v3_tables_absent": sorted(
                t for t in V3_TABLES if not self.has("people", t)
            ),
            "missing_capabilities": sorted(set(self.missing)),
            "notes": list(self.notes),
        }


def _tables(con: sqlite3.Connection, domain: str) -> set[str]:
    """Real table/view names in one attached schema.

    sqlite_master is the authority. Probing with `SELECT 1 FROM x LIMIT 1` --
    what the old ask.py did -- cannot distinguish "table missing" from "table
    present but the query is malformed", which is precisely how the broken FTS
    query hid for so long.
    """
    try:
        rows = con.execute(
            f"SELECT name FROM {domain}.sqlite_master "
            "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    except sqlite3.Error:
        return set()
    return {r[0] for r in rows}


def detect(con: sqlite3.Connection, domains: dict[str, str]) -> Capabilities:
    caps = Capabilities(domains=dict(domains))
    for domain in domains:
        caps.tables[domain] = _tables(con, domain)

    if "people" not in domains:
        caps.missing.append("people_domain")
        caps.notes.append(
            "No people database attached; person queries cannot be answered."
        )
        return caps

    for t in V2_CORE:
        if not caps.has("people", t):
            caps.missing.append(f"people.{t}")
    for t in V2_IDENTITY + V2_OPTIONAL + V2_VIEWS:
        if not caps.has("people", t):
            caps.missing.append(f"people.{t}")

    mode = caps.identity_mode()
    if mode == "none":
        caps.notes.append(
            "No identity_claim or v3 decision tables: results are raw source "
            "rows and MAY contain duplicate records for the same person."
        )
    elif mode == "v2":
        caps.notes.append(
            "v2 identity mode: accepted identity_claim rows and person.merged_into "
            "are applied. Proposed and rejected claims are reported, never applied."
        )
    return caps
