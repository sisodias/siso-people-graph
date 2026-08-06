"""Read-only compatibility adapter for the current People Graph v2 schema."""
from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any, Iterator, Mapping

from .contract import write_ndjson
from .adapter_v2_projection import V2ProjectionMixin
from .adapter_common import (
    AdapterCapabilities,
    IdentityDecision,
    SourcePolicy,
    UnsupportedAdapterError,
    _coerce_time,
    _connect_read_only,
    _legacy_person_locator,
    sqlite_tables,
)

class V2SQLiteAdapter(V2ProjectionMixin):
    """Read-only compatibility projection over the current People Graph v2.

    The adapter preserves legacy row identity as *source-native locators* under
    the synthetic ``legacy-v2`` source.  It never treats those keys as new
    canonical IDs.  Accepted ``identity_claim`` rows are available only through
    :meth:`iter_identity_decisions`.
    """

    REQUIRED_TABLES = {"person", "person_content", "external_ids"}

    def __init__(
        self,
        path: str | Path,
        *,
        source_policies: Mapping[str, SourcePolicy] | None = None,
        default_policy: SourcePolicy | None = None,
    ):
        self.path = Path(path)
        self.source_policies = dict(source_policies or {})
        self.default_policy = default_policy or SourcePolicy()
        tables = sqlite_tables(self.path)
        missing = sorted(self.REQUIRED_TABLES - tables)
        if missing:
            raise UnsupportedAdapterError(
                f"not a supported People Graph v2 database; missing tables: {missing}"
            )
        self.tables = tables

    def iter_observations(self) -> Iterator[dict[str, Any]]:
        with _connect_read_only(self.path) as con:
            yield from self._iter_people(con)
            yield from self._iter_works(con)
            yield from self._iter_topics(con)

    def iter_identity_decisions(self) -> Iterator[IdentityDecision]:
        if "identity_claim" not in self.tables:
            return iter(())

        def generate() -> Iterator[IdentityDecision]:
            with _connect_read_only(self.path) as con:
                for row in con.execute(
                    "SELECT claim_id, person_a, person_b, method, confidence, "
                    "evidence, status, decided_by, created_at "
                    "FROM identity_claim ORDER BY claim_id"
                ):
                    yield IdentityDecision(
                        decision_native_id=f"legacy-v2-identity-claim/{row['claim_id']}",
                        left_source_locator=_legacy_person_locator(str(row["person_a"])),
                        right_source_locator=_legacy_person_locator(str(row["person_b"])),
                        method=str(row["method"]),
                        confidence=float(row["confidence"]),
                        evidence=str(row["evidence"]),
                        status=str(row["status"]),
                        decided_by=row["decided_by"],
                        created_at=_coerce_time(row["created_at"]),
                    )

        return generate()

    def export(self, path: str | Path) -> int:
        return write_ndjson(path, self.iter_observations())

    def capabilities(self) -> AdapterCapabilities:
        evidence = tuple(sorted(self.tables & {
            "person",
            "person_content",
            "external_ids",
            "person_topic",
            "identity_claim",
            "person_search",
        }))
        gaps = [
            "source snapshots, terms revisions, rights, and deletion obligations are absent from v2 rows",
            "legacy person keys may contain mutable handles and are exposed only as source locators",
            "identifier scope/stability/uniqueness are inferred by a conservative compatibility registry",
        ]
        return AdapterCapabilities(
            adapter=self.__class__.__name__,
            schema_family="people-graph-v2",
            observations="compatibility projection",
            identities=(
                "separate decision stream" if "identity_claim" in self.tables else "missing"
            ),
            works_roles="present" if "person_content" in self.tables else "missing",
            topics="present" if "person_topic" in self.tables else "missing",
            rights="pending unless caller supplies exact SourcePolicy",
            claims="identity claims only; generic evidence claims missing",
            evidence=evidence,
            gaps=tuple(gaps),
        )


