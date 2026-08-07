"""Public compatibility-adapter facade for independent parallel lanes."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .adapter_common import (
    AdapterCapabilities,
    AdapterError,
    BookLibraryObservationAdapter,
    IdentityDecision,
    NDJSONObservationAdapter,
    SourcePolicy,
    UnsupportedAdapterError,
    sqlite_tables,
)
from .adapter_v2 import V2SQLiteAdapter
from .adapter_v3 import V3SQLiteAdapter

def open_sqlite_adapter(
    path: str | Path,
    *,
    source_policies: Mapping[str, SourcePolicy] | None = None,
) -> V2SQLiteAdapter | V3SQLiteAdapter:
    """Select a supported adapter without silently treating v3 as v2."""

    tables = sqlite_tables(path)
    if V2SQLiteAdapter.REQUIRED_TABLES.issubset(tables):
        return V2SQLiteAdapter(path, source_policies=source_policies)
    if tables.intersection(V3SQLiteAdapter.OBSERVATION_TABLE_CANDIDATES):
        return V3SQLiteAdapter(path)
    raise UnsupportedAdapterError(
        "no current-v2 or future-v3 observation compatibility seam detected"
    )


__all__ = [
    "AdapterCapabilities", "AdapterError", "BookLibraryObservationAdapter",
    "IdentityDecision", "NDJSONObservationAdapter", "SourcePolicy",
    "UnsupportedAdapterError", "V2SQLiteAdapter", "V3SQLiteAdapter",
    "open_sqlite_adapter", "sqlite_tables",
]
