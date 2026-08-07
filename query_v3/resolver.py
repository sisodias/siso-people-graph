"""Apply identity decisions that have already been made. Never make one.

This module is the fix for PG-AUDIT-002 / PGRT-004: a reviewer could accept an
identity claim, the queue would report success, and every read path would keep
returning both rows as separate people. Reviewers worked and the system ignored
them.

The division of labour matters and is easy to get wrong in the direction of
disaster. Deciding whether two rows are the same human is Lane 4's job
(`identity_v3/`, method card identity-v3.1.0) -- it owns the thresholds, the
conflict checks, the deny-by-default registry. This module contains NO matching
logic whatsoever: no name comparison, no confidence threshold, no heuristic. It
reads decisions that a reviewer or an audited automatic policy already recorded
and applies them to reads. If it ever starts deciding, two systems will disagree
about who is who and neither will be authoritative.

Three adapters, selected by capability detection:

  v2       person.merged_into + identity_claim(status='accepted')
  v3       additive decision/cluster tables when present (Lane 3/4 merge)
  none     no identity machinery -- duplicates reported honestly as duplicates

The v2 adapter treats two signals as one decision surface. `merged_into` is the
applied state; an accepted `identity_claim` is the decision record. They can
disagree -- a claim accepted after the last build has no merge applied yet -- and
that disagreement is exactly the reviewer-invisible window this lane exists to
close. So accepted claims are applied at READ time even when the build has not
yet written merged_into, and the response says which signal carried each merge.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from . import evidence as ev


@dataclass
class Resolution:
    """One canonical person plus the rows that fold into it."""

    canonical_id: str
    member_ids: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    unresolved: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "canonical_id": self.canonical_id,
            "member_ids": sorted(self.member_ids),
            "merged_row_count": max(0, len(self.member_ids) - 1),
            "decisions": self.decisions,
            "unresolved_candidates": self.unresolved,
        }


class _Union:
    """Union-find over person ids. Pure bookkeeping over decisions given to it.

    Transitivity is a property of the decisions, not an inference this module
    makes: if a reviewer accepted A=B and B=C, then A, B and C are one person by
    the reviewer's own decisions. We are composing accepted decisions, not
    generating a new one.
    """

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, x: str) -> None:
        self.parent.setdefault(x, x)

    def find(self, x: str) -> str:
        self.add(x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


class Resolver:
    """Base adapter. Subclasses apply whatever decision surface exists."""

    mode = "none"

    def __init__(self, con: sqlite3.Connection, caps) -> None:
        self.con = con
        self.caps = caps

    def resolve(self, person_ids: list[str]) -> dict[str, Resolution]:
        """Map every input id to the Resolution that now represents it."""
        out: dict[str, Resolution] = {}
        for pid in person_ids:
            out[pid] = Resolution(canonical_id=pid, member_ids=[pid])
        return out

    def warnings(self) -> list[str]:
        return [
            "No identity decisions are available; two rows describing the same "
            "person are returned as two people."
        ]


class NullResolver(Resolver):
    """Explicitly does nothing, and says so. Used when no identity tables exist."""

    mode = "none"


class V2Resolver(Resolver):
    """person.merged_into plus accepted identity_claim rows."""

    mode = "v2"

    def _accepted_claims(self, ids: set[str]) -> list[tuple]:
        if not self.caps.has("people", "identity_claim") or not ids:
            return []
        marks = ",".join("?" * len(ids))
        params = list(ids) + list(ids)
        return self.con.execute(
            f"""SELECT person_a, person_b, method, confidence, evidence,
                       decided_by, created_at
                FROM people.identity_claim
                WHERE status = 'accepted'
                  AND (person_a IN ({marks}) OR person_b IN ({marks}))""",
            params,
        ).fetchall()

    def _open_claims(self, ids: set[str]) -> list[tuple]:
        """Proposed claims: reported as unresolved ambiguity, never applied."""
        if not self.caps.has("people", "identity_claim") or not ids:
            return []
        marks = ",".join("?" * len(ids))
        params = list(ids) + list(ids)
        return self.con.execute(
            f"""SELECT person_a, person_b, method, confidence, evidence, created_at
                FROM people.identity_claim
                WHERE status = 'proposed'
                  AND (person_a IN ({marks}) OR person_b IN ({marks}))""",
            params,
        ).fetchall()

    def _merge_targets(self, ids: set[str]) -> list[tuple]:
        """Applied merges recorded on the person row itself."""
        if not ids:
            return []
        marks = ",".join("?" * len(ids))
        return self.con.execute(
            f"""SELECT person_id, merged_into, state FROM people.person
                WHERE person_id IN ({marks}) AND merged_into IS NOT NULL""",
            list(ids),
        ).fetchall()

    def _expand(self, seed: set[str]) -> set[str]:
        """Pull in rows connected to the seed by a decision, transitively.

        A search hit is a starting point, not the whole cluster: the winning row
        of a merge is often the one the query did not match. Bounded so a
        pathological chain cannot turn one lookup into a corpus walk.
        """
        known = set(seed)
        for _ in range(8):
            grew = False
            for a, b, *_ in self._accepted_claims(known):
                for x in (a, b):
                    if x not in known:
                        known.add(x)
                        grew = True
            for pid, target, _state in self._merge_targets(known):
                if target and target not in known:
                    known.add(target)
                    grew = True
            if not grew:
                break
        return known

    def resolve(self, person_ids: list[str]) -> dict[str, Resolution]:
        seed = {p for p in person_ids if p}
        if not seed:
            return {}
        universe = self._expand(seed)

        uf = _Union()
        for pid in universe:
            uf.add(pid)

        decisions: dict[tuple[str, str], dict] = {}

        # Applied merges. The merged row is never the canonical one.
        winners: set[str] = set()
        for pid, target, state in self._merge_targets(universe):
            if not target:
                continue
            uf.union(target, pid)
            winners.add(target)
            decisions[(pid, target)] = {
                "from": pid,
                "to": target,
                "signal": "person.merged_into",
                "person_state": state,
                "evidence": ev.decided(
                    method="applied_merge",
                    confidence=None,
                    decided_by=None,
                    detail=f"{pid} superseded by {target} (person.state={state})",
                ).as_dict(),
            }

        # Accepted claims. Applied at read time even if the build has not yet
        # written merged_into -- this is the reviewer-invisible window closing.
        for a, b, method, conf, evid, decided_by, created in self._accepted_claims(
            universe
        ):
            uf.union(a, b)
            key = (a, b)
            if key not in decisions:
                decisions[key] = {
                    "from": b,
                    "to": a,
                    "signal": "identity_claim.accepted",
                    "evidence": ev.decided(
                        method=method,
                        confidence=conf,
                        decided_by=decided_by,
                        detail=evid,
                        observed_at=created,
                    ).as_dict(),
                }

        # Group, then pick each cluster's canonical row.
        clusters: dict[str, list[str]] = {}
        for pid in universe:
            clusters.setdefault(uf.find(pid), []).append(pid)

        unresolved_by_cluster: dict[str, list[dict]] = {}
        for a, b, method, conf, evid, created in self._open_claims(universe):
            root = uf.find(a)
            unresolved_by_cluster.setdefault(root, []).append(
                {
                    "person_a": a,
                    "person_b": b,
                    "method": method,
                    "confidence": conf,
                    "evidence": evid,
                    "created_at": created,
                    "status": "proposed",
                    "note": "Not applied. A proposed claim is a hypothesis "
                            "awaiting review, not a decision.",
                }
            )

        out: dict[str, Resolution] = {}
        for root, members in clusters.items():
            canonical = self._canonical(members, winners)
            res = Resolution(
                canonical_id=canonical,
                member_ids=members,
                decisions=[
                    d for k, d in decisions.items()
                    if uf.find(k[0]) == root
                ],
                unresolved=unresolved_by_cluster.get(root, []),
            )
            for pid in members:
                out[pid] = res
        return {pid: out[pid] for pid in person_ids if pid in out}

    def _canonical(self, members: list[str], winners: set[str]) -> str:
        """Which row represents the cluster.

        Deterministic policy, not a truth claim (the identity method card makes
        the same caveat about canonical selection).

        LIVENESS IS CHECKED FIRST, and the order matters. In a merge chain
        A->B->C, every intermediate row is simultaneously a merge target (some
        row merged into it) and itself merged away. Preferring "was merged into"
        ahead of "is not merged" therefore elects a superseded row: a 12-long
        chain resolved to bk:chain-1, a row with state='merged', while the only
        live row bk:chain-11 was ignored. A superseded row must never be the
        answer while a live row exists in the same cluster.
        """
        if len(members) == 1:
            return members[0]

        marks = ",".join("?" * len(members))
        rows = self.con.execute(
            f"SELECT person_id, state FROM people.person "
            f"WHERE person_id IN ({marks})",
            members,
        ).fetchall()
        states = dict(rows)

        live = sorted(p for p in members if states.get(p) != "merged"
                      and p in states)
        if live:
            # Among live rows, one that something merged INTO is the applied
            # winner and beats an untouched peer.
            live_winners = [p for p in live if p in winners]
            return sorted(live_winners)[0] if live_winners else live[0]

        # Every row in the cluster is superseded (a cycle, or a chain whose head
        # is absent). Fall back to a merge target, then to lexical order, so the
        # answer is at least stable and reproducible.
        applied = sorted(p for p in members if p in winners)
        if applied:
            return applied[0]
        return sorted(members)[0]

    def warnings(self) -> list[str]:
        return []


class V3Resolver(V2Resolver):
    """Additive v3 decision/cluster tables, falling back to v2 signals.

    Lane 3/4 have not merged, so this path is unexercised against a real v3
    database. It is written to the documented shape and reports itself as
    provisional rather than pretending to be verified.
    """

    mode = "v3"

    def resolve(self, person_ids: list[str]) -> dict[str, Resolution]:
        base = super().resolve(person_ids)
        if not self.caps.has("people", "identity_cluster"):
            return base
        for pid, res in base.items():
            try:
                row = self.con.execute(
                    "SELECT cluster_id FROM people.identity_cluster "
                    "WHERE person_id = ? LIMIT 1",
                    (pid,),
                ).fetchone()
            except sqlite3.Error:
                continue
            if row:
                res.decisions.append(
                    {
                        "signal": "identity_cluster",
                        "cluster_id": row[0],
                        "evidence": ev.decided(
                            method="v3_cluster",
                            confidence=None,
                            decided_by=None,
                            detail=f"{pid} is a member of cluster {row[0]}",
                        ).as_dict(),
                    }
                )
        return base

    def warnings(self) -> list[str]:
        return [
            "v3 identity tables detected. The v3 adapter has not been validated "
            "against a merged v3 database and is provisional."
        ]


def for_capabilities(con: sqlite3.Connection, caps) -> Resolver:
    mode = caps.identity_mode()
    if mode == "v3":
        return V3Resolver(con, caps)
    if mode == "v2":
        return V2Resolver(con, caps)
    return NullResolver(con, caps)
