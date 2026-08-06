"""Software Heritage observation adapter.

Software Heritage identifiers are retained as intrinsic identifiers for archived
source objects. The pilot stores metadata and locators only; it does not clone or
proxy archived source payloads.
"""
from __future__ import annotations

from typing import Any, Mapping

from .envelope import make_envelope


def adapt_software_heritage_fixture(
    fixture: Mapping[str, Any],
    *,
    raw_pointer: str = "tests/sources_software_ai/fixtures/software_heritage.json",
) -> list[dict[str, Any]]:
    meta = {
        "source_id": fixture["source_id"],
        "snapshot_id": fixture["snapshot_id"],
        "observed_at": fixture["observed_at"],
        "retrieved_at": fixture["retrieved_at"],
        "terms_revision": fixture["terms_revision"],
        "rights_state": fixture["rights_state"],
    }
    records: list[dict[str, Any]] = []
    for item in fixture.get("objects", []):
        relationships = []
        if item.get("origin"):
            relationships.append(
                {
                    "predicate": "archives",
                    "object": {
                        "kind": "work",
                        "source_native_id": item["origin"]["native_id"],
                        "label": item["origin"]["label"],
                    },
                    "observed_at": item.get("visit_date", meta["observed_at"]),
                    "evidence": item["origin"].get("evidence", "Software Heritage origin URL"),
                }
            )
        if item.get("parent_swhid"):
            relationships.append(
                {
                    "predicate": "contained_in",
                    "object": {
                        "kind": "work",
                        "source_native_id": item["parent_swhid"],
                        "label": item["parent_swhid"],
                    },
                    "observed_at": item.get("visit_date", meta["observed_at"]),
                    "evidence": "Software Heritage object graph",
                }
            )
        records.append(
            make_envelope(
                **{**meta, "observed_at": item.get("visit_date", meta["observed_at"])},
                record_native_id=item["swhid"],
                raw_record=item,
                subject_kind="work",
                subject_native_id=item["swhid"],
                subject_label=item.get("label", item["swhid"]),
                attributes={
                    "work_type": f"software_archive_{item['object_type']}",
                    "object_type": item["object_type"],
                    "visit_date": item.get("visit_date"),
                    "license": item.get("license"),
                    "metrics": [],
                },
                identifiers=[
                    {
                        "scheme": "swhid",
                        "value": item["swhid"],
                        "scope": "global",
                        "stability": "stable",
                        "uniqueness": "unique",
                        "evidence": "Software Heritage intrinsic identifier",
                    }
                ],
                relationships=relationships,
                evidence=[
                    {
                        "kind": "source_locator",
                        "locator": item.get("api_url", f"softwareheritage:{item['swhid']}"),
                        "observed_at": item.get("visit_date", meta["observed_at"]),
                    }
                ],
                raw_pointer=f"{raw_pointer}#/objects/{item['swhid']}",
            )
        )
    return records
