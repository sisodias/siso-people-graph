"""Observation projection methods shared by the v2 compatibility adapter."""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterator
from urllib.parse import quote

from .contract import ENVELOPE_VERSION, assert_valid
from .adapter_common import (
    _coerce_time,
    _identifier_semantics,
    _legacy_person_locator,
    _row_hash,
)


class V2ProjectionMixin:
    def _policy(self, source_id: str) -> SourcePolicy:
        return self.source_policies.get(source_id, self.default_policy)

    def _source_block(
        self,
        *,
        source_id: str,
        record_native_id: str,
        observed_at: Any,
        payload_sha256: str,
        fallback_time: str | None = None,
    ) -> dict[str, str]:
        policy = self._policy(source_id)
        observed = _coerce_time(observed_at, fallback_time)
        retrieved = _coerce_time(policy.retrieved_at, observed)
        return {
            "source_id": source_id,
            "snapshot_id": policy.snapshot_id,
            "record_native_id": record_native_id,
            "observed_at": observed,
            "retrieved_at": retrieved,
            "terms_revision": policy.terms_revision,
            "rights_state": policy.rights_state,
            "payload_sha256": payload_sha256,
        }

    def _external_rows(
        self, con: sqlite3.Connection
    ) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
        """Partition v2 ``external_ids`` into identifiers and observed attributes.

        The legacy table can contain values such as ``real_name``, ``company``,
        ``location``, or biography text.  Those values are retained verbatim but
        never promoted into identifier semantics.
        """

        by_person: dict[str, list[dict[str, Any]]] = {}
        attributes_by_person: dict[str, list[dict[str, Any]]] = {}
        attribute_only = {
            "name",
            "full_name",
            "display_name",
            "real_name",
            "company",
            "employer",
            "organisation_name",
            "location",
            "city",
            "country",
            "biography",
            "bio",
            "topic",
            "subject",
        }
        for row in con.execute(
            "SELECT person_id, platform, value, confidence, source "
            "FROM external_ids ORDER BY person_id, platform, value"
        ):
            person_key = str(row["person_id"])
            platform = str(row["platform"])
            platform_key = platform.strip().lower().replace("-", "_")
            literal = {
                "field": platform,
                "value": str(row["value"]),
                "source": row["source"] or "unknown",
                "confidence": row["confidence"],
            }
            if platform_key in attribute_only:
                attributes_by_person.setdefault(person_key, []).append(literal)
                continue
            scope, stability, uniqueness = _identifier_semantics(platform)
            by_person.setdefault(person_key, []).append(
                {
                    "scheme": platform,
                    "value": str(row["value"]),
                    "scope": scope,
                    "stability": stability,
                    "uniqueness": uniqueness,
                    "evidence": (
                        f"legacy-v2 external_ids literal; source={row['source'] or 'unknown'}; "
                        f"confidence={row['confidence']}"
                    ),
                }
            )
        return by_person, attributes_by_person

    def _topic_rows(self, con: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
        if "person_topic" not in self.tables:
            return {}
        by_person: dict[str, list[dict[str, Any]]] = {}
        for row in con.execute(
            "SELECT person_id, topic, scheme, weight, source "
            "FROM person_topic ORDER BY person_id, scheme, topic"
        ):
            by_person.setdefault(str(row["person_id"]), []).append(
                {
                    "type": "topic_assignment",
                    "target_source_native_id": f"{row['scheme']}:{row['topic']}",
                    "label": str(row["topic"]),
                    "scheme": str(row["scheme"]),
                    "weight": row["weight"],
                    "source": row["source"],
                    "review_state": "observed",
                }
            )
        return by_person

    def _iter_people(self, con: sqlite3.Connection) -> Iterator[dict[str, Any]]:
        identifiers, external_attributes = self._external_rows(con)
        topics = self._topic_rows(con)
        columns = [
            "person_id",
            "name",
            "sort_name",
            "kind",
            "state",
            "merged_into",
            "birth_year",
            "death_year",
            "primary_tier",
            "rank_score",
            "origin",
            "topics_json",
            "built_at",
        ]
        query = "SELECT " + ",".join(columns) + " FROM person ORDER BY person_id"
        for row in con.execute(query):
            raw = {column: row[column] for column in columns}
            legacy_key = str(row["person_id"])
            record_native_id = _legacy_person_locator(legacy_key)
            attributes = {
                "legacy_record_key": legacy_key,
                "legacy_kind": row["kind"],
                "sort_name": row["sort_name"],
                "legacy_state": row["state"],
                "birth_year": row["birth_year"],
                "death_year": row["death_year"],
                "legacy_primary_tier": row["primary_tier"],
                "legacy_rank_score": row["rank_score"],
                "origin": row["origin"],
                "legacy_topics_json": row["topics_json"],
                "built_at": row["built_at"],
                "legacy_external_attributes": external_attributes.get(legacy_key, []),
            }
            attributes = {key: value for key, value in attributes.items() if value is not None}
            kind = str(row["kind"])
            if kind not in {"person", "organisation", "account", "work", "event", "venue", "place", "concept", "claim"}:
                kind = "organisation" if kind == "organisation" else "person"
            evidence: list[dict[str, Any]] = [
                {
                    "kind": "compatibility_projection",
                    "source_table": "person",
                    "legacy_source": row["origin"],
                    "limitations": [
                        "v2 does not record an exact source snapshot on person rows",
                        "v2 does not record rights or deletion obligations on person rows",
                        "legacy row keys are locators, not new canonical IDs",
                    ],
                }
            ]
            if row["merged_into"]:
                evidence.append(
                    {
                        "kind": "legacy_identity_state",
                        "state": "merged",
                        "target_source_locator": _legacy_person_locator(str(row["merged_into"])),
                        "note": "reported separately from source facts; no merge is executed",
                    }
                )
            payload_hash = _row_hash(
                "person",
                {
                    **raw,
                    "external_ids": identifiers.get(legacy_key, []),
                    "external_attributes": external_attributes.get(legacy_key, []),
                    "topics": topics.get(legacy_key, []),
                },
            )
            record = {
                "envelope_version": ENVELOPE_VERSION,
                "source": self._source_block(
                    source_id="legacy-v2",
                    record_native_id=record_native_id,
                    observed_at=row["built_at"],
                    payload_sha256=payload_hash,
                ),
                "subject": {
                    "kind": kind,
                    "source_native_id": record_native_id,
                    "label": str(row["name"]),
                    "attributes": attributes,
                },
                "identifiers": identifiers.get(legacy_key, []),
                "contributions": [],
                "relationships": topics.get(legacy_key, []),
                "evidence": evidence,
                "raw_pointer": f"sqlite://{self.path.name}#person/{quote(legacy_key, safe='')}",
            }
            assert_valid(record)
            yield record

    def _iter_works(self, con: sqlite3.Connection) -> Iterator[dict[str, Any]]:
        query = (
            "SELECT pc.person_id, pc.domain, pc.content_ref, pc.role, pc.score, "
            "pc.title, pc.source, pc.observed_at, pc.meta_json, p.built_at "
            "FROM person_content pc JOIN person p ON p.person_id=pc.person_id "
            "ORDER BY pc.domain, pc.content_ref, pc.person_id, pc.role"
        )
        for row in con.execute(query):
            raw = {key: row[key] for key in row.keys()}
            domain = str(row["domain"])
            content_ref = str(row["content_ref"])
            role = str(row["role"])
            source_id = str(row["source"] or domain or "legacy-v2")
            record_native_id = (
                f"person_content/{quote(str(row['person_id']), safe='')}/"
                f"{quote(domain, safe='')}/{quote(content_ref, safe='')}/{quote(role, safe='')}"
            )
            try:
                meta = json.loads(row["meta_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                meta = {"legacy_literal": row["meta_json"]}
            payload_hash = _row_hash("person_content", raw)
            record = {
                "envelope_version": ENVELOPE_VERSION,
                "source": self._source_block(
                    source_id=source_id,
                    record_native_id=record_native_id,
                    observed_at=row["observed_at"],
                    fallback_time=row["built_at"],
                    payload_sha256=payload_hash,
                ),
                "subject": {
                    "kind": "work",
                    "source_native_id": f"{domain}:{content_ref}",
                    "label": str(row["title"] or content_ref),
                    "attributes": {
                        "domain": domain,
                        "score_observation": row["score"],
                        "legacy_meta": meta,
                    },
                },
                "identifiers": [],
                "contributions": [
                    {
                        "contributor_source_native_id": _legacy_person_locator(
                            str(row["person_id"])
                        ),
                        "role": role,
                        "order": None,
                        "observed_at": _coerce_time(row["observed_at"], row["built_at"]),
                        "source_table": "person_content",
                    }
                ],
                "relationships": [],
                "evidence": [
                    {
                        "kind": "literal_row",
                        "source_table": "person_content",
                        "provenance_source": source_id,
                        "limitations": [
                            "v2 work rows do not carry source snapshot, terms revision, or rights state",
                            "score is preserved as a timestamped legacy observation, not a universal canonical rank",
                        ],
                    }
                ],
                "raw_pointer": (
                    f"sqlite://{self.path.name}#person_content/"
                    f"{quote(record_native_id, safe='')}"
                ),
            }
            # Remove null score instead of writing a misleading observed value.
            if row["score"] is None:
                record["subject"]["attributes"].pop("score_observation")
            assert_valid(record)
            yield record

    def _iter_topics(self, con: sqlite3.Connection) -> Iterator[dict[str, Any]]:
        if "person_topic" not in self.tables:
            return
        for row in con.execute(
            "SELECT person_id, topic, scheme, weight, source "
            "FROM person_topic ORDER BY scheme, topic, person_id"
        ):
            raw = {key: row[key] for key in row.keys()}
            scheme = str(row["scheme"])
            topic = str(row["topic"])
            source_id = str(row["source"] or "legacy-v2")
            record_native_id = (
                f"person_topic/{quote(str(row['person_id']), safe='')}/"
                f"{quote(scheme, safe='')}/{quote(topic, safe='')}"
            )
            record = {
                "envelope_version": ENVELOPE_VERSION,
                "source": self._source_block(
                    source_id=source_id,
                    record_native_id=record_native_id,
                    observed_at=None,
                    payload_sha256=_row_hash("person_topic", raw),
                ),
                "subject": {
                    "kind": "concept",
                    "source_native_id": f"{scheme}:{topic}",
                    "label": topic,
                    "attributes": {"scheme": scheme},
                },
                "identifiers": [],
                "contributions": [],
                "relationships": [
                    {
                        "type": "topic_assignment",
                        "source_subject_native_id": _legacy_person_locator(
                            str(row["person_id"])
                        ),
                        "weight": row["weight"],
                        "review_state": "observed",
                    }
                ],
                "evidence": [
                    {
                        "kind": "legacy_derived_edge",
                        "source_table": "person_topic",
                        "provenance_source": source_id,
                        "note": "source vocabulary remains namespaced by scheme",
                    }
                ],
                "raw_pointer": (
                    f"sqlite://{self.path.name}#person_topic/"
                    f"{quote(record_native_id, safe='')}"
                ),
            }
            assert_valid(record)
            yield record

