"""Capability-detecting adapter seam for additive v3 observation tables."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from .contract import assert_valid, write_ndjson
from .adapter_common import (
    AdapterCapabilities,
    AdapterError,
    IdentityDecision,
    UnsupportedAdapterError,
    _connect_read_only,
    sqlite_tables,
)

class V3SQLiteAdapter:
    """Capability-detecting seam for additive v3 databases.

    Until a normalized v3 schema is merged, the stable integration point is a
    table containing the full envelope in one JSON column.  The detector reports
    normalized canonical/claim tables when present but never guesses their join
    semantics.
    """

    OBSERVATION_TABLE_CANDIDATES = (
        "source_observation",
        "source_observations",
        "observation",
        "observations",
        "source_record",
    )
    JSON_COLUMN_CANDIDATES = (
        "envelope_json",
        "observation_json",
        "record_json",
        "payload_json",
    )
    CANONICAL_TABLE_CANDIDATES = {
        "canonical_entity",
        "canonical_cluster",
        "entity_redirect",
        "identity_decision",
    }
    CLAIM_TABLE_CANDIDATES = {"claim", "claims", "assertion", "assertions"}
    WORK_TABLE_CANDIDATES = {"work", "works", "contribution", "contributions"}

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.tables = sqlite_tables(self.path)
        self.observation_table, self.json_column = self._detect_json_seam()
        if self.observation_table is None or self.json_column is None:
            raise UnsupportedAdapterError(
                "v3-like tables were detected but no full-envelope JSON compatibility seam exists"
            )

    def _detect_json_seam(self) -> tuple[str | None, str | None]:
        with _connect_read_only(self.path) as con:
            for table in self.OBSERVATION_TABLE_CANDIDATES:
                if table not in self.tables:
                    continue
                columns = {
                    str(row[1])
                    for row in con.execute(f'PRAGMA table_info("{table}")')
                }
                for column in self.JSON_COLUMN_CANDIDATES:
                    if column in columns:
                        return table, column
        return None, None

    def iter_observations(self) -> Iterator[dict[str, Any]]:
        assert self.observation_table is not None
        assert self.json_column is not None
        with _connect_read_only(self.path) as con:
            query = (
                f'SELECT rowid, "{self.json_column}" AS envelope '
                f'FROM "{self.observation_table}" ORDER BY rowid'
            )
            for row in con.execute(query):
                try:
                    record = json.loads(row["envelope"])
                except (TypeError, json.JSONDecodeError) as exc:
                    raise AdapterError(
                        f"{self.observation_table} row {row['rowid']} contains invalid envelope JSON"
                    ) from exc
                assert_valid(record)
                yield record

    def iter_identity_decisions(self) -> Iterator[IdentityDecision]:
        # Normalized v3 decision schemas are intentionally not guessed.  A later
        # lane registers an explicit mapper without altering observation import.
        return iter(())

    def export(self, path: str | Path) -> int:
        return write_ndjson(path, self.iter_observations())

    def capabilities(self) -> AdapterCapabilities:
        canonical = sorted(self.tables & self.CANONICAL_TABLE_CANDIDATES)
        claims = sorted(self.tables & self.CLAIM_TABLE_CANDIDATES)
        works = sorted(self.tables & self.WORK_TABLE_CANDIDATES)
        gaps: list[str] = []
        if canonical:
            gaps.append(
                "canonical tables detected but decision mapping remains explicit and separate"
            )
        if claims:
            gaps.append(
                "claim tables detected but normalized claim mapping requires a versioned mapper"
            )
        return AdapterCapabilities(
            adapter=self.__class__.__name__,
            schema_family="people-graph-v3-detected",
            observations="present via full-envelope JSON seam",
            identities=("detected/separate" if canonical else "missing or not detected"),
            works_roles=("detected" if works else "inside envelopes only"),
            topics="inside envelopes or schema-specific",
            rights="required by envelope validator",
            claims=("detected/separate" if claims else "missing or not detected"),
            evidence=(
                f"{self.observation_table}.{self.json_column}",
                *canonical,
                *claims,
                *works,
            ),
            gaps=tuple(gaps),
        )


