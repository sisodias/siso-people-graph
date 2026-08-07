"""Adapters for the current v2 database and pg-observation-0.1 records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterable, Mapping, TextIO

from .engine import IdentityEngine, IdentityError, stable_id, stable_json, utc_now
from .registry import is_auto_resolvable, normalize_identifier, rule_for

LEGACY_METHOD_VERSION = "v2-legacy.1"
ENVELOPE_VERSION = "pg-observation-0.1"
_FORBIDDEN_CANONICAL_KEYS = {
    "canonical_id", "canonical_person_id", "people_graph_id", "canonical_entity_id",
}


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def _parse_legacy_scheme(evidence: str) -> str | None:
    text = (evidence or "").strip()
    try:
        decoded = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        decoded = None
    if isinstance(decoded, dict):
        scheme = decoded.get("scheme") or decoded.get("platform")
        if scheme:
            return str(scheme).casefold()
        # identity_v3 writes structured evidence with the literal identifier
        # match nested under ``positive``. Reading it here keeps a safe v2 claim
        # safe across rebuilds and adapters without trusting arbitrary strings.
        positive = decoded.get("positive")
        if isinstance(positive, list):
            schemes = {
                str(item.get("scheme")).casefold()
                for item in positive
                if isinstance(item, Mapping) and item.get("scheme")
            }
            if len(schemes) == 1:
                return next(iter(schemes))
        return None
    match = re.match(r"^([A-Za-z0-9_.:-]+)=", text)
    return match.group(1).casefold() if match else None


def import_v2(connection: sqlite3.Connection, *, observed_at: str | None = None) -> dict[str, int]:
    """Import current v2 entities, external fields, and review state additively.

    Legacy `external_ids` rows are reclassified through the explicit registry.
    Unsafe legacy accepted `shared_external_id` claims without a named reviewer
    are quarantined rather than silently creating canonical clusters.
    """
    engine = IdentityEngine(connection)
    when = observed_at or utc_now()
    stats = {
        "entities": 0,
        "identifiers": 0,
        "aliases": 0,
        "attributes": 0,
        "claims": 0,
        "decisions": 0,
        "quarantined_claims": 0,
    }
    if not engine.table_exists("person"):
        return stats

    person_columns = _table_columns(connection, "person")
    select = ["person_id", "name"]
    for optional in ("kind", "origin", "birth_year", "death_year", "state"):
        select.append(optional if optional in person_columns else f"NULL AS {optional}")
    for row in connection.execute(f"SELECT {','.join(select)} FROM person"):
        engine.upsert_entity(
            row[0], label=row[1], kind=row[2] or "unknown", origin=row[3],
            source_native_id=row[0], birth_year=row[4], death_year=row[5],
            source_state=row[6], created_at=when,
        )
        stats["entities"] += 1

    external_rows: list[sqlite3.Row] = []
    if engine.table_exists("external_ids"):
        external_rows = connection.execute(
            "SELECT person_id,platform,value,confidence,source FROM external_ids"
        ).fetchall()

    # Identifiers first so mutable aliases can point at their stable account id.
    stable_by_entity: dict[str, dict[str, str]] = {}
    for row in external_rows:
        person_id, platform, value, confidence, source = row
        rule = rule_for(platform)
        if rule.category != "identifier":
            continue
        if engine.record_identifier(
            person_id, platform, value, source=source or "v2_external_ids",
            observed_at=when,
            evidence={"legacy_confidence": confidence, "table": "external_ids"},
        ):
            stats["identifiers"] += 1
            stable_by_entity.setdefault(person_id, {})[platform] = normalize_identifier(platform, value)

    for row in external_rows:
        person_id, platform, value, confidence, source = row
        rule = rule_for(platform)
        evidence = {"legacy_confidence": confidence, "table": "external_ids", "platform": platform}
        if rule.category == "identifier":
            continue
        if rule.category == "alias":
            stable_scheme = None
            stable_value = None
            if platform == "github_login" and "github_id" in stable_by_entity.get(person_id, {}):
                stable_scheme = "github_id"
                stable_value = stable_by_entity[person_id]["github_id"]
            engine.record_alias(
                person_id, platform, value, source=source or "v2_external_ids",
                observed_at=when, stable_identifier_scheme=stable_scheme,
                stable_identifier_value=stable_value, evidence=evidence,
            )
            stats["aliases"] += 1
        else:
            attribute = platform if rule.category in {"attribute", "metric"} else f"legacy_external_id:{platform}"
            engine.record_attribute(
                person_id, attribute, value, source=source or "v2_external_ids",
                observed_at=when, evidence=evidence,
            )
            stats["attributes"] += 1

    if not engine.table_exists("identity_claim"):
        connection.commit()
        return stats

    claim_columns = _table_columns(connection, "identity_claim")
    decided_expr = "decided_by" if "decided_by" in claim_columns else "NULL AS decided_by"
    claim_id_expr = "claim_id" if "claim_id" in claim_columns else "rowid AS claim_id"
    rows = connection.execute(
        f"""SELECT {claim_id_expr},person_a,person_b,method,confidence,evidence,status,
                    {decided_expr},created_at
             FROM identity_claim"""
    ).fetchall()
    accepted_any = False
    for row in rows:
        claim_id, entity_a, entity_b, method, confidence, evidence, status, decided_by, created_at = row
        if entity_a == entity_b:
            continue
        entity_a, entity_b = sorted((entity_a, entity_b))
        scheme = _parse_legacy_scheme(evidence) if method == "shared_external_id" else None
        safe_shared = bool(scheme and is_auto_resolvable(scheme))
        conflicts: list[str] = []
        if method == "shared_external_id" and not safe_shared:
            conflicts.append("legacy_noneligible_external_id")
        candidate_id = stable_id("legacy-cand", entity_a, entity_b, method, LEGACY_METHOD_VERSION)
        review_state = status if status in {"proposed", "accepted", "rejected"} else "proposed"
        import_as_decision = False
        if review_state == "accepted":
            # A named reviewer may accept a weak *candidate*, but an old claim
            # whose method literally says shared_external_id is unsafe when the
            # underlying scheme is company/location/name/etc. Quarantine those
            # regardless of the old decided_by value; they can be re-reviewed
            # with positive and negative evidence in this lane.
            unsafe_shared = method == "shared_external_id" and not safe_shared
            import_as_decision = (not unsafe_shared) and (bool(decided_by) or safe_shared)
            if not import_as_decision:
                review_state = "proposed"
                stats["quarantined_claims"] += 1
        connection.execute(
            """
            INSERT INTO identity_v3_candidate
              (candidate_id,entity_a,entity_b,method,method_version,confidence,
               auto_eligible,positive_evidence_json,negative_evidence_json,
               conflict_reasons_json,review_state,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(entity_a,entity_b,method,method_version) DO UPDATE SET
              confidence=excluded.confidence,
              auto_eligible=excluded.auto_eligible,
              positive_evidence_json=excluded.positive_evidence_json,
              conflict_reasons_json=excluded.conflict_reasons_json,
              review_state=CASE
                WHEN identity_v3_candidate.review_state IN ('accepted','rejected')
                  THEN identity_v3_candidate.review_state
                ELSE excluded.review_state END,
              updated_at=excluded.updated_at
            """,
            (
                candidate_id, entity_a, entity_b, method, LEGACY_METHOD_VERSION,
                float(confidence), int(safe_shared),
                stable_json([{"type": "legacy_v2_claim", "evidence": evidence, "scheme": scheme}]),
                "[]", stable_json(conflicts), review_state,
                created_at or when, when,
            ),
        )
        stats["claims"] += 1
        if review_state == "rejected" or import_as_decision:
            outcome = "rejected" if review_state == "rejected" else "accepted"
            if outcome == "accepted":
                prospective = engine._prospective_members(entity_a, entity_b)
                cluster_conflicts = engine._component_identifier_conflicts(prospective)
                if cluster_conflicts:
                    # Do not recreate an impossible transitive cluster while
                    # importing legacy review state. Preserve the candidate and
                    # an audit receipt so a human can adjudicate it explicitly.
                    connection.execute(
                        """UPDATE identity_v3_candidate
                           SET review_state='proposed',
                               conflict_reasons_json=?,updated_at=?
                           WHERE candidate_id=?""",
                        (
                            stable_json(["legacy_transitive_identifier_conflict"]),
                            when,
                            candidate_id,
                        ),
                    )
                    stats["quarantined_claims"] += 1
                    event_id = stable_id("audit", "legacy_cluster_conflict", claim_id, candidate_id)
                    connection.execute(
                        """INSERT OR IGNORE INTO identity_v3_audit_event
                           (event_id,event_type,severity,candidate_id,details_json,created_at)
                           VALUES (?,?,?,?,?,?)""",
                        (
                            event_id, "legacy_cluster_conflict", "error", candidate_id,
                            stable_json({"claim_id": claim_id, "conflicts": cluster_conflicts}),
                            when,
                        ),
                    )
                    continue
            decision_id = stable_id("legacy-decision", claim_id, candidate_id, outcome)
            connection.execute(
                """INSERT OR IGNORE INTO identity_v3_decision
                   (decision_id,candidate_id,entity_a,entity_b,outcome,active,
                    decided_by,decided_at,rationale)
                   VALUES (?,?,?,?,?,1,?,?,?)""",
                (
                    decision_id, candidate_id, entity_a, entity_b, outcome,
                    decided_by or ("legacy-safe-auto" if safe_shared else "legacy-review"),
                    created_at or when, "Imported from v2 identity_claim",
                ),
            )
            stats["decisions"] += 1
            accepted_any = accepted_any or outcome == "accepted"
        elif conflicts:
            event_id = stable_id("audit", "legacy_claim_quarantined", claim_id, candidate_id)
            connection.execute(
                """INSERT OR IGNORE INTO identity_v3_audit_event
                   (event_id,event_type,severity,candidate_id,details_json,created_at)
                   VALUES (?,?,?,?,?,?)""",
                (
                    event_id, "legacy_claim_quarantined", "warning", candidate_id,
                    stable_json({"claim_id": claim_id, "evidence": evidence, "conflicts": conflicts}),
                    when,
                ),
            )
    if accepted_any:
        engine.recompute_clusters(reason="import-v2", created_at=when)
    connection.commit()
    return stats


def _walk_forbidden_keys(value: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}"
            if str(key) in _FORBIDDEN_CANONICAL_KEYS:
                found.append(child)
            found.extend(_walk_forbidden_keys(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk_forbidden_keys(item, f"{path}[{index}]"))
    return found


def import_observation(connection: sqlite3.Connection, record: Mapping[str, object]) -> dict[str, object]:
    """Import one pg-observation-0.1 record without assigning canonical identity."""
    if record.get("envelope_version") != ENVELOPE_VERSION:
        raise IdentityError(f"unsupported envelope_version: {record.get('envelope_version')!r}")
    forbidden = _walk_forbidden_keys(record)
    if forbidden:
        raise IdentityError(f"observation envelope contains canonical id fields: {forbidden}")
    source = record.get("source")
    subject = record.get("subject")
    if not isinstance(source, Mapping) or not isinstance(subject, Mapping):
        raise IdentityError("source and subject objects are required")
    source_id = str(source.get("source_id") or "").strip()
    record_native_id = str(source.get("record_native_id") or "").strip()
    subject_native_id = str(subject.get("source_native_id") or record_native_id).strip()
    kind = str(subject.get("kind") or "unknown").strip()
    if not source_id or not subject_native_id:
        raise IdentityError("source_id and subject source_native_id are required")
    native_digest = hashlib.sha256(
        f"{source_id}\x1f{kind}\x1f{subject_native_id}".encode("utf-8")
    ).hexdigest()[:24]
    entity_id = f"obs:{source_id}:{kind}:{native_digest}"
    observed_at = str(source.get("observed_at") or source.get("retrieved_at") or utc_now())
    payload_sha256 = str(source.get("payload_sha256") or "")
    engine = IdentityEngine(connection)
    engine.upsert_entity(
        entity_id,
        label=str(subject.get("label") or "") or None,
        kind=kind,
        origin=source_id,
        source_native_id=subject_native_id,
        created_at=observed_at,
    )

    imported = {"entity_id": entity_id, "identifiers": 0, "aliases": 0, "attributes": 0}
    identifiers = record.get("identifiers") or []
    if not isinstance(identifiers, list):
        raise IdentityError("identifiers must be a list")
    for item in identifiers:
        if not isinstance(item, Mapping):
            raise IdentityError("identifier entries must be objects")
        scheme = str(item.get("scheme") or "").casefold()
        value = item.get("value")
        rule = rule_for(scheme)
        evidence = {
            "literal_evidence": item.get("evidence"),
            "declared_scope": item.get("scope"),
            "declared_stability": item.get("stability"),
            "declared_uniqueness": item.get("uniqueness"),
            "record_native_id": record_native_id,
        }
        if rule.category == "identifier":
            if engine.record_identifier(
                entity_id, scheme, value, source=source_id, observed_at=observed_at,
                evidence=evidence,
            ):
                imported["identifiers"] += 1
        elif rule.category == "alias":
            if engine.record_alias(
                entity_id, scheme, value, source=source_id, observed_at=observed_at,
                evidence=evidence,
            ):
                imported["aliases"] += 1
        else:
            # Unknown or non-unique fields remain source attributes even when an
            # envelope declares them unique. The local registry is the policy.
            engine.record_attribute(
                entity_id, f"observed_identifier:{scheme or 'unknown'}", value,
                source=source_id, observed_at=observed_at,
                payload_sha256=payload_sha256, evidence=evidence,
            )
            imported["attributes"] += 1

    attributes = subject.get("attributes") or {}
    if not isinstance(attributes, Mapping):
        raise IdentityError("subject.attributes must be an object")
    for key, value in attributes.items():
        engine.record_attribute(
            entity_id, str(key), value, source=source_id, observed_at=observed_at,
            payload_sha256=payload_sha256,
            evidence={"record_native_id": record_native_id, "raw_pointer": record.get("raw_pointer")},
        )
        imported["attributes"] += 1

    for field in ("contributions", "relationships", "evidence"):
        value = record.get(field) or []
        if value:
            engine.record_attribute(
                entity_id, f"envelope:{field}", value, source=source_id,
                observed_at=observed_at, payload_sha256=payload_sha256,
                evidence={"record_native_id": record_native_id, "raw_pointer": record.get("raw_pointer")},
            )
            imported["attributes"] += 1
    if record.get("raw_pointer"):
        engine.record_attribute(
            entity_id, "raw_pointer", record.get("raw_pointer"), source=source_id,
            observed_at=observed_at, payload_sha256=payload_sha256,
            evidence={"record_native_id": record_native_id},
        )
        imported["attributes"] += 1
    connection.commit()
    return imported


def import_observation_ndjson(connection: sqlite3.Connection, source: str | Path | TextIO) -> dict[str, object]:
    close = False
    if hasattr(source, "read"):
        handle = source  # type: ignore[assignment]
    else:
        handle = Path(source).open("r", encoding="utf-8")
        close = True
    records: list[dict[str, object]] = []
    try:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise IdentityError(f"invalid NDJSON at line {line_number}: {exc}") from exc
            records.append(import_observation(connection, record))
    finally:
        if close:
            handle.close()
    return {"records": len(records), "imports": records}
