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


# How many times the cluster walk may iterate before it gives up. Exceeding it
# means the cluster is incomplete, which is reported -- never silently returned
# as though it were whole.
MAX_EXPANSION_PASSES = 8


# The display-representative rule, VERSIONED. Bump this whenever the ordering
# below changes, so a stored answer can be told apart from a current one.
#
# Why a version and a recorded reason at all: every possible rule (most-recent,
# source-authority, most-evidence) is a POLICY that will be wrong for some
# person, and wrong invisibly. A cluster of equals has no intrinsic king. What
# callers actually need is a stable row to render plus the ability to see WHY it
# was chosen and to disagree with it -- so the reason ships with the answer.
REPRESENTATIVE_RULE_VERSION = "display-representative-1.0.0"


@dataclass
class Resolution:
    """One identity cluster, plus the member chosen to represent it on screen.

    The cluster is the answer. The representative is a RENDERING CHOICE over
    that cluster -- not a claim that one row is more truthful than its peers.
    """

    canonical_id: str
    member_ids: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    unresolved: list[dict] = field(default_factory=list)
    blocked: list[dict] = field(default_factory=list)
    complete: bool = True
    representative_reason: dict = field(default_factory=dict)

    @property
    def display_representative(self) -> str:
        """The member chosen for display. Preferred name for `canonical_id`."""
        return self.canonical_id

    def as_dict(self) -> dict:
        return {
            # New, accurate names. `display_representative` is what this IS.
            "display_representative": self.canonical_id,
            "representative_selection": self.representative_reason,
            # Retained for callers written against the previous shape. This is a
            # rendering choice, NOT an assertion that this row is canonical
            # truth; `display_representative` is the name that says so.
            "canonical_id": self.canonical_id,
            "member_ids": sorted(self.member_ids),
            "cluster_size": len(self.member_ids),
            "merged_row_count": max(0, len(self.member_ids) - 1),
            "decisions": self.decisions,
            "unresolved_candidates": self.unresolved,
            "refused_merges": self.blocked,
            "cluster_complete": self.complete,
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
            out[pid] = Resolution(
                canonical_id=pid,
                member_ids=[pid],
                representative_reason={
                    "rule": REPRESENTATIVE_RULE_VERSION,
                    "basis": "no_identity_machinery",
                    "reason": (
                        "No identity decisions are available, so every row is "
                        "its own cluster and represents only itself."
                    ),
                    "contested": False,
                },
            )
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

    def _contradicted_pairs(self, ids: set[str]) -> dict[frozenset[str], str]:
        """Pairs an applied merge joins but a claim actively does NOT accept.

        `merged_into` and `identity_claim` are independent signals and they can
        contradict: a build can apply a merge whose claim was later rejected, or
        that was never accepted at all. Trusting the applied merge alone means a
        rejected pair silently stays merged -- which falsifies the guarantee this
        module exists to make, that only accepted decisions affect reads.

        Both a rejected claim and a merely proposed one defeat an applied merge.
        Under this lane's contract `identity_claim.status='accepted'` is the
        AUTHORIZATION and `person.merged_into` is materialized execution state,
        not an independent decision -- so a proposed claim is a hypothesis that
        was executed without ever being authorized. Merging it while flagging it
        would still merge a non-accepted decision, which is finding #1 in a
        narrower form, and would quietly restate the contract as "applied merges
        affect reads unless explicitly rejected". That is a weaker guarantee and
        not the one this lane promises.
        """
        if not self.caps.has("people", "identity_claim") or not ids:
            return {}
        marks = ",".join("?" * len(ids))
        rows = self.con.execute(
            f"""SELECT person_a, person_b, status FROM people.identity_claim
                WHERE status IN ('rejected', 'proposed')
                  AND (person_a IN ({marks}) OR person_b IN ({marks}))""",
            list(ids) + list(ids),
        ).fetchall()
        out: dict[frozenset[str], str] = {}
        for a, b, status in rows:
            key = frozenset((a, b))
            # A rejection is the stronger statement; never let a proposal mask it.
            if out.get(key) != "rejected":
                out[key] = status
        return out

    def _claim_backed(self, a: str, b: str) -> bool:
        """Does an ACCEPTED claim exist for this exact pair?

        Distinguishes "authorized by a reviewer" from "applied by a build with no
        claim at all". Only the latter gets the legacy carve-out.
        """
        if not self.caps.has("people", "identity_claim"):
            return False
        lo, hi = sorted((a, b))  # schema stores pairs as person_a < person_b
        row = self.con.execute(
            "SELECT 1 FROM people.identity_claim WHERE status = 'accepted' "
            "AND person_a = ? AND person_b = ? LIMIT 1",
            (lo, hi),
        ).fetchone()
        return row is not None

    def _merge_targets(self, ids: set[str]) -> list[tuple]:
        """Applied merges recorded on the person row itself, BOTH directions.

        Following only `merged_into` forward finds the winner from a loser, but
        not the losers from a winner. Since the query matches whichever name the
        caller happened to type, a forward-only walk returns different data for
        the same person depending on which row matched -- the winner's page would
        omit the merged row's works entirely.
        """
        if not ids:
            return []
        marks = ",".join("?" * len(ids))
        params = list(ids) + list(ids)
        return self.con.execute(
            f"""SELECT person_id, merged_into, state FROM people.person
                WHERE merged_into IS NOT NULL
                  AND (person_id IN ({marks}) OR merged_into IN ({marks}))""",
            params,
        ).fetchall()

    def _expand(self, seed: set[str]) -> tuple[set[str], bool]:
        """Pull in rows connected to the seed by a decision, transitively.

        A search hit is a starting point, not the whole cluster: the winning row
        of a merge is often the one the query did not match.

        Returns (rows, complete). The walk is bounded so a pathological chain
        cannot turn one lookup into a corpus walk -- but hitting that bound means
        the cluster is INCOMPLETE, and silently returning a partial cluster as if
        it were whole is exactly the class of quiet wrongness this lane removes.
        The caller reports `complete=False` as a coverage gap.
        """
        known = set(seed)
        for _ in range(MAX_EXPANSION_PASSES):
            grew = False
            for a, b, *_ in self._accepted_claims(known):
                for x in (a, b):
                    if x not in known:
                        known.add(x)
                        grew = True
            for pid, target, _state in self._merge_targets(known):
                for x in (pid, target):
                    if x and x not in known:
                        known.add(x)
                        grew = True
            if not grew:
                return known, True
        # One more pass purely to detect whether anything remained.
        for a, b, *_ in self._accepted_claims(known):
            if a not in known or b not in known:
                return known, False
        for pid, target, _state in self._merge_targets(known):
            if (pid and pid not in known) or (target and target not in known):
                return known, False
        return known, True

    def resolve(self, person_ids: list[str]) -> dict[str, Resolution]:
        seed = {p for p in person_ids if p}
        if not seed:
            return {}
        universe, complete = self._expand(seed)
        contradicted = self._contradicted_pairs(universe)

        uf = _Union()
        for pid in universe:
            uf.add(pid)

        decisions: dict[tuple[str, str], dict] = {}
        blocked: list[dict] = []

        # Applied merges, checked against the claim record rather than trusted.
        winners: set[str] = set()
        for pid, target, state in self._merge_targets(universe):
            if not target:
                continue
            status = contradicted.get(frozenset((pid, target)))
            if status in ("rejected", "proposed"):
                # Accepted-only contract: a claim that is not accepted does not
                # authorize a merge, however the build materialised it. Reads
                # return the rows separately AND surface the inconsistency --
                # which is more actionable than serving an unauthorized merged
                # identity as truth.
                blocked.append({
                    "person_a": pid,
                    "person_b": target,
                    "signal": "person.merged_into",
                    "claim_status": status,
                    "action": "merge_refused",
                    "person_state": state,
                    "note": (
                        f"person.merged_into records {pid} -> {target}, but the "
                        f"identity_claim for this pair is '{status}', not "
                        "'accepted'. merged_into is materialised execution "
                        "state, not an authorization: these rows are reported "
                        "separately and the applied merge is inconsistent with "
                        "the decision record."
                    ),
                })
                continue
            uf.union(target, pid)
            winners.add(target)
            entry = {
                "signal": "person.merged_into",
                "person_state": state,
                "evidence": ev.decided(
                    method="applied_merge",
                    confidence=None,
                    decided_by=None,
                    detail=f"{pid} superseded by {target} (person.state={state})",
                ).as_dict(),
            }
            if not self._claim_backed(pid, target):
                # LEGACY CARVE-OUT, deliberate and narrow. Merges predate
                # identity_claim entirely: production currently holds zero claim
                # rows, so refusing every unbacked merge would discard the whole
                # applied merge history and make reads contradict the database
                # for no reviewer's benefit. Applied merges with NO claim keep
                # their historical authority -- but they are labelled, so an
                # unreviewed merge is never mistaken for a reviewed one.
                #
                # KNOWN LIMIT (accepted, tracked as follow-up debt): "absent"
                # means only "no claim row for this pair". It cannot distinguish
                # a genuine pre-claim-table merge from a NEWLY written bad one,
                # so it is not proof of legacy provenance. The durable fix is an
                # explicit migration cutoff timestamp or a legacy allowlist --
                # NOT a "refuse absent once the claim table is non-empty" switch,
                # which would let the first reviewed pair invalidate unrelated
                # historical merges and make behaviour depend on migration order
                # rather than on this pair's evidence.
                #
                # Precedence is deliberately PAIR-LEVEL: an explicit accepted
                # claim authorizes, an explicit proposed/rejected claim blocks,
                # and only a total absence of evidence falls through to legacy
                # authority. Every future decision record therefore wins over
                # legacy state without disturbing any other pair.
                entry["claim_status"] = "absent"
                entry["authority"] = "legacy_applied_merge"
                entry["warning"] = (
                    "Applied via person.merged_into with NO identity_claim of "
                    "any status. Honoured under the legacy carve-out for merges "
                    "predating the claim table; it carries no reviewer "
                    "authorization."
                )
            decisions[(pid, target)] = entry

        # Accepted claims. Applied at read time even if the build has not yet
        # written merged_into -- this is the reviewer-invisible window closing.
        for a, b, method, conf, evid, decided_by, created in self._accepted_claims(
            universe
        ):
            uf.union(a, b)
            key = (a, b)
            if key not in decisions:
                decisions[key] = {
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
            canonical, rep_reason = self._representative(members, winners)

            # Direction is assigned HERE, once the canonical row is known --
            # never from the order the pair happens to be stored in.
            # identity_claim enforces person_a < person_b as a uniqueness device,
            # which is lexical bookkeeping and says nothing about which row
            # survives. Reporting the stored order as from/to produced
            # "from zz:live to aa:merged": a decision pointing away from the
            # surviving person, contradicting this function's own choice.
            cluster_decisions = []
            for (x, y), d in decisions.items():
                if uf.find(x) != root:
                    continue
                d = dict(d)
                other = y if x == canonical else x
                d["from"] = other
                d["to"] = canonical
                if canonical not in (x, y):
                    # Transitive cluster: this pair joins two rows, neither of
                    # which is canonical. Say so rather than implying otherwise.
                    d["from"], d["to"] = x, y
                    d["note"] = (
                        f"pair-level decision within the cluster; the cluster's "
                        f"canonical row is {canonical}"
                    )
                cluster_decisions.append(d)

            res = Resolution(
                canonical_id=canonical,
                member_ids=members,
                decisions=cluster_decisions,
                unresolved=unresolved_by_cluster.get(root, []),
                representative_reason=rep_reason,
            )
            res.blocked = [b for b in blocked
                           if uf.find(b["person_a"]) == root
                           or uf.find(b["person_b"]) == root]
            res.complete = complete
            for pid in members:
                out[pid] = res
        return {pid: out[pid] for pid in person_ids if pid in out}

    # Origin ranking, ADOPTED VERBATIM from Lane 4's identity_v3/_clusters.py
    # `_canonical_sort_key`. It is duplicated rather than imported because Lane 4
    # has not merged and query_v3 must not take a hard dependency on an unmerged
    # module -- but it is deliberately the SAME table, because two independently
    # invented rankings would make identity_v3 and query_v3 disagree about who a
    # person is, which is precisely the two-authorities failure this lane exists
    # to prevent. If Lane 4's table changes, this one must change with it; the
    # cross-check is asserted in tests/query_v3/test_display_representative.py.
    _ORIGIN_PRIORITY = {
        "registry": 0, "curated": 0, "manual": 0,
        "authority": 1,
        "book": 2, "books": 2,
        "github": 3, "youtube": 3,
    }
    _ORIGIN_UNRANKED = 9

    def _origins(self, members: list[str]) -> dict[str, str]:
        """Declared `person.origin` per row. NEVER parsed from the id.

        Entity ids are OPAQUE by v3's own design, so `bk:` is not evidence of
        anything -- the `origin` column is the declared fact. Reading the prefix
        instead is how the alphabetical hierarchy got in the first time.
        """
        if not members:
            return {}
        marks = ",".join("?" * len(members))
        try:
            rows = self.con.execute(
                f"SELECT person_id, origin FROM people.person "
                f"WHERE person_id IN ({marks})",
                members,
            ).fetchall()
        except sqlite3.Error:
            return {}
        return {pid: (o or "").casefold() for pid, o in rows}

    def _strong_id_counts(self, members: list[str]) -> dict[str, int]:
        """Distinct authority identifiers per row (viaf, wikidata, ...).

        These are the corroboration that makes one row better evidenced than
        another. Counted DISTINCT by kind so ten copies of one viaf id do not
        outrank two independent authorities.
        """
        if not members or not self.caps.has("people", "external_ids"):
            return {}
        marks = ",".join("?" * len(members))
        try:
            rows = self.con.execute(
                f"SELECT person_id, COUNT(DISTINCT platform) "
                f"FROM people.external_ids "
                f"WHERE person_id IN ({marks}) GROUP BY person_id",
                members,
            ).fetchall()
        except sqlite3.Error:
            return {}
        return {pid: int(n) for pid, n in rows}

    def _canonical(self, members: list[str], winners: set[str]) -> str:
        """Back-compat shim. Prefer `_representative`, which reports its reason."""
        return self._representative(members, winners)[0]

    def _representative(
        self, members: list[str], winners: set[str]
    ) -> tuple[str, dict]:
        """Choose the row to DISPLAY for this cluster, and say why.

        Returns (representative_id, reason). The reason is part of the answer,
        not a debug aid: a caller must be able to see that the choice was policy
        and disagree with it. This is a presentation decision over an unordered
        cluster -- NOT a ranking of whose data is true.

        Rule `display-representative-1.0.0`, applied in order:

          1. LIVENESS. A superseded row is never shown while a live one exists.
             Order matters: in a chain A->B->C every intermediate row is both a
             merge target and itself merged away, so preferring "was merged into"
             first elects a dead row -- a 12-long chain once resolved to
             bk:chain-1 (state='merged') while live bk:chain-11 was ignored.
          2. APPLIED WINNER. Among live rows, one that something merged INTO
             carries an actual decision; an untouched peer carries none.
          3. MOST INDEPENDENT STRONG IDENTIFIERS. The most corroborated row.
          4. ORIGIN PRIORITY (Lane 4's table). Curated beats scraped.
          5. EARLIEST OBSERVATION. The longest-standing row is the stablest
             thing to render.
          6. LEXICAL ID -- LAST RESORT ONLY, and reported as such.

        Rung 6 previously did the work of all six. Because ids are prefixed by
        origin, plain `sorted()` silently encoded bk: < crates: < gh: < yt:, an
        origin hierarchy nobody chose, reading as policy. It is retained ONLY as
        a final tie-break for genuine equals, where it means "stable", not "best".
        """
        if len(members) == 1:
            return members[0], {
                "rule": REPRESENTATIVE_RULE_VERSION,
                "basis": "sole_member",
                "reason": "Cluster has one member; no selection was made.",
                "contested": False,
            }

        marks = ",".join("?" * len(members))
        rows = self.con.execute(
            f"SELECT person_id, state FROM people.person "
            f"WHERE person_id IN ({marks})",
            members,
        ).fetchall()
        states = dict(rows)

        pool = sorted(p for p in members if states.get(p) != "merged"
                      and p in states)
        basis = "live_row"
        if pool:
            live_winners = sorted(p for p in pool if p in winners)
            if live_winners:
                pool, basis = live_winners, "live_applied_merge_winner"
        else:
            # Every row is superseded (a cycle, or a chain whose head is absent).
            pool = sorted(p for p in members if p in winners)
            basis = "superseded_merge_target"
            if not pool:
                pool, basis = sorted(members), "all_rows_superseded"

        observed = self._first_observed(pool)
        origins = self._origins(pool)
        strong = self._strong_id_counts(pool)

        def _discriminators(p: str) -> tuple:
            """Every rung ABOVE the alphabetical last resort."""
            return (
                -strong.get(p, 0),
                self._ORIGIN_PRIORITY.get(origins.get(p, ""),
                                          self._ORIGIN_UNRANKED),
                observed.get(p) or "9999",
            )

        ranked = sorted(pool, key=lambda p: (_discriminators(p), p))
        chosen = ranked[0]

        # Was the winner decided by a real signal, or did it come down to the
        # alphabet? A caller must be able to tell those apart.
        tied = [p for p in ranked if _discriminators(p) == _discriminators(chosen)]
        by_alpha = len(tied) > 1

        reason = {
            "rule": REPRESENTATIVE_RULE_VERSION,
            "basis": basis,
            "strong_identifier_count": strong.get(chosen, 0),
            "origin": origins.get(chosen) or None,
            "origin_rank": self._ORIGIN_PRIORITY.get(origins.get(chosen, ""),
                                                     self._ORIGIN_UNRANKED),
            "first_observed": observed.get(chosen),
            "decided_by_alphabetical_tiebreak": by_alpha,
            "candidates_considered": list(pool),
            "contested": len(pool) > 1,
            "reason": (
                f"Selected {chosen} to represent a {len(members)}-row cluster "
                f"by {basis}"
                + (
                    f"; {len(tied)} members were otherwise equal, so the "
                    "alphabetical last-resort tie-break decided it. This is a "
                    "stable rendering choice, NOT a judgement that this row is "
                    "more truthful."
                    if by_alpha else
                    "; discriminated by strong-identifier count, then origin "
                    "priority, then earliest observation."
                )
            ),
        }
        return chosen, reason

    def _first_observed(self, members: list[str]) -> dict[str, str]:
        """Earliest observation per row: MIN(person_content.observed_at).

        The longest-standing row is the most stable thing to render. This reads
        observation history rather than `person.built_at`, which records when
        the current build wrote the row and is usually identical across a
        cluster -- a column that cannot discriminate is not a tie-break.
        """
        if not members or not self.caps.has("people", "person_content"):
            return {}
        marks = ",".join("?" * len(members))
        try:
            rows = self.con.execute(
                f"SELECT person_id, MIN(observed_at) FROM people.person_content "
                f"WHERE person_id IN ({marks}) GROUP BY person_id",
                members,
            ).fetchall()
        except sqlite3.Error:
            return {}
        return {pid: ts for pid, ts in rows if ts}

    def warnings(self) -> list[str]:
        return []


class V3Resolver(V2Resolver):
    """Additive v3 decision/cluster tables, falling back to v2 signals.

    Lane 3/4 have not merged, so this path is unexercised against a real v3
    database. It is written to the documented shape and reports itself as
    provisional rather than pretending to be verified.
    """

    mode = "v3"

    def __init__(self, con, caps) -> None:
        super().__init__(con, caps)
        self._cluster_error: str | None = None

    def _clusters_for(self, ids: set[str]) -> dict[str, str]:
        """person_id -> cluster_id, for rows the v3 tables place in a cluster."""
        if not ids:
            return {}
        marks = ",".join("?" * len(ids))
        try:
            rows = self.con.execute(
                f"SELECT person_id, cluster_id FROM people.identity_cluster "
                f"WHERE cluster_id IN (SELECT cluster_id FROM "
                f"people.identity_cluster WHERE person_id IN ({marks}))",
                list(ids),
            ).fetchall()
        except sqlite3.Error as exc:
            # A malformed identity_cluster must NEVER read as "no clusters".
            # Silently degrading on a schema error is precisely the bug this
            # lane exists to remove -- it is how the broken FTS query hid.
            self._cluster_error = str(exc)
            return {}
        return {pid: cid for pid, cid in rows}

    def resolve(self, person_ids: list[str]) -> dict[str, Resolution]:
        base = super().resolve(person_ids)
        if not self.caps.has("people", "identity_cluster") or not base:
            return base

        # Cluster membership is an ACCEPTED v3 decision and must fold rows into
        # one person, exactly as an accepted v2 claim does. Recording it as an
        # annotation while still returning two people would reproduce the very
        # defect this lane fixes, one schema version later.
        seen: set[str] = set()
        for res in base.values():
            seen.update(res.member_ids)
        membership = self._clusters_for(seen)
        if not membership:
            return base

        by_cluster: dict[str, set[str]] = {}
        for pid, cid in membership.items():
            by_cluster.setdefault(cid, set()).add(pid)

        merged: dict[str, Resolution] = {}
        for pid, res in base.items():
            cid = membership.get(res.canonical_id) or membership.get(pid)
            if not cid:
                merged[pid] = res
                continue
            members = sorted(set(res.member_ids) | by_cluster.get(cid, set()))
            joined = merged.get(cid)
            if joined is None:
                v3_rep, v3_reason = self._representative(members, set())
                joined = Resolution(
                    canonical_id=v3_rep,
                    member_ids=members,
                    decisions=list(res.decisions),
                    unresolved=list(res.unresolved),
                    representative_reason=v3_reason,
                )
                joined.blocked = list(res.blocked)
                joined.complete = res.complete
                joined.decisions.append({
                    "signal": "identity_cluster",
                    "cluster_id": cid,
                    "from": None,
                    "to": joined.canonical_id,
                    "evidence": ev.decided(
                        method="v3_cluster",
                        confidence=None,
                        decided_by=None,
                        detail=f"cluster {cid} groups {', '.join(members)}",
                    ).as_dict(),
                })
                merged[cid] = joined
            else:
                joined.member_ids = sorted(set(joined.member_ids) | set(members))
                # The cluster just grew, so the previous representative was
                # chosen over a smaller pool. Re-run the rule over the whole
                # membership -- a stale winner would silently outrank a better
                # evidenced row that arrived with the second half of the cluster.
                joined.canonical_id, joined.representative_reason = (
                    self._representative(joined.member_ids, set())
                )
            merged[pid] = joined

        return {pid: merged[pid] for pid in person_ids if pid in merged}

    def warnings(self) -> list[str]:
        out = [
            "v3 identity tables detected. The v3 adapter has not been validated "
            "against a merged v3 database and is provisional."
        ]
        if self._cluster_error:
            out.append(
                "identity_cluster is present but UNREADABLE "
                f"({self._cluster_error}). v3 cluster decisions were NOT applied; "
                "this result may contain duplicate rows for one person. This is "
                "a failure, not an absence of clusters."
            )
        return out


def for_capabilities(con: sqlite3.Connection, caps) -> Resolver:
    mode = caps.identity_mode()
    if mode == "v3":
        return V3Resolver(con, caps)
    if mode == "v2":
        return V2Resolver(con, caps)
    return NullResolver(con, caps)
