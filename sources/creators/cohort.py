"""Deterministic cohort selection and pilot metrics for living creators.

The selector operates on source-native seed rows.  It never joins by label and
never assigns a People Graph canonical ID.  Production runs can feed it current
GitHub/Book Library exports; tests use tiny public-safe fixtures.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .bridges import propose_bridges
from .envelope import canonical_json, read_ndjson, validate_envelope

SEED_VERSION = "living-creator-seed-0.1"
MANIFEST_VERSION = "living-creators-cohort-0.1"


class CohortError(ValueError):
    pass


def validate_seed(seed: Mapping[str, Any]) -> None:
    required = {
        "seed_version",
        "seed_id",
        "source_id",
        "source_native_id",
        "label",
        "domains",
        "stable_identifiers",
        "explicit_links",
        "living_evidence",
    }
    missing = sorted(required.difference(seed))
    if missing:
        raise CohortError(f"seed missing required fields: {', '.join(missing)}")
    if seed["seed_version"] != SEED_VERSION:
        raise CohortError(f"unsupported seed_version: {seed['seed_version']!r}")
    if not isinstance(seed["domains"], list) or not seed["domains"]:
        raise CohortError("seed domains must be a non-empty list")
    if not isinstance(seed["stable_identifiers"], list):
        raise CohortError("stable_identifiers must be a list")
    if not seed["stable_identifiers"]:
        raise CohortError("name-only seeds are forbidden; provide a source-native stable ID")
    for item in seed["stable_identifiers"]:
        if not isinstance(item, Mapping) or not item.get("scheme") or not item.get("value"):
            raise CohortError("stable identifier rows need scheme and value")
        if item.get("scheme") in {"name", "real_name", "company", "location", "handle"}:
            raise CohortError(f"unsafe seed identifier scheme: {item.get('scheme')}")
    living = seed["living_evidence"]
    if not isinstance(living, Mapping) or living.get("state") not in {
        "living",
        "likely_living",
        "unknown",
    }:
        raise CohortError("living_evidence.state must be living|likely_living|unknown")


def _seed_sort_key(seed: Mapping[str, Any]) -> tuple[str, str, str]:
    digest = hashlib.sha256(canonical_json(seed).encode("utf-8")).hexdigest()
    return str(seed["source_id"]), digest, str(seed["seed_id"])


def _source_queues(seeds: Iterable[Mapping[str, Any]]) -> dict[str, deque[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for raw in seeds:
        seed = dict(raw)
        validate_seed(seed)
        seed_id = str(seed["seed_id"])
        if seed_id in seen:
            raise CohortError(f"duplicate seed_id: {seed_id}")
        seen.add(seed_id)
        grouped[str(seed["source_id"])].append(seed)
    return {
        source: deque(sorted(items, key=_seed_sort_key))
        for source, items in sorted(grouped.items())
    }


def build_manifest(
    seeds: Iterable[Mapping[str, Any]],
    *,
    target_size: int = 250,
    source_targets: Mapping[str, int] | None = None,
    generated_at: str,
    snapshot_receipts: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, source-balanced cohort manifest.

    ``source_targets`` is a soft cap.  Remaining slots are filled round-robin so
    a sparse source does not block the run.  Rows stay source-native and can be
    linked only later through explicit review candidates.
    """

    if target_size <= 0:
        raise CohortError("target_size must be positive")
    queues = _source_queues(seeds)
    selected: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    caps = {key: int(value) for key, value in (source_targets or {}).items()}

    # First satisfy requested source cohorts.
    for source, cap in sorted(caps.items()):
        queue = queues.get(source, deque())
        while queue and counts[source] < cap and len(selected) < target_size:
            seed = queue.popleft()
            selected.append(seed)
            counts[source] += 1

    # Fill any remaining slots round-robin across all sources.
    sources = list(queues)
    while len(selected) < target_size and any(queues[source] for source in sources):
        for source in sources:
            if len(selected) >= target_size:
                break
            if queues[source]:
                seed = queues[source].popleft()
                selected.append(seed)
                counts[source] += 1

    status = "ready" if len(selected) >= target_size else "fixture_only"
    return {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": generated_at,
        "target_size": target_size,
        "actual_size": len(selected),
        "status": status,
        "selection_policy": {
            "identity": "source-native seeds only; no label/name merge",
            "living_rule": "living or likely_living preferred; unknown retained for review",
            "balancing": "source targets followed by deterministic round-robin",
            "source_targets": dict(sorted(caps.items())),
        },
        "snapshot_receipts": [dict(item) for item in (snapshot_receipts or [])],
        "members": selected,
        "source_counts": dict(sorted(counts.items())),
        "unfilled_slots": max(0, target_size - len(selected)),
        "production_gate": (
            "ready for adapter collection" if status == "ready" else
            "supply current People Graph and modern-author source snapshots"
        ),
    }


def read_seeds(path: Path | str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                seed = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CohortError(f"{path}:{line_number}: {exc}") from exc
            validate_seed(seed)
            records.append(seed)
    return records


def observation_metrics(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    manifest: Mapping[str, Any] | None = None,
    reviewed_candidates: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Measure the pilot without converting candidates into accepted identity."""

    for envelope in envelopes:
        validate_envelope(envelope)
    rights = Counter(record["source"]["rights_state"] for record in envelopes)
    sources = Counter(record["source"]["source_id"] for record in envelopes)
    work_types = Counter(
        str(record["subject"]["attributes"].get("work_type", record["subject"]["kind"]))
        for record in envelopes
    )
    roles = Counter(
        str(contribution.get("role", "unknown"))
        for record in envelopes
        for contribution in record["contributions"]
    )
    all_candidates = propose_bridges(envelopes)
    strong_candidates = [item for item in all_candidates if item["strength"] == "strong"]
    review_candidates = [item for item in all_candidates if item["strength"] == "review_only"]
    subject_refs = {
        (record["source"]["source_id"], record["subject"]["source_native_id"])
        for record in envelopes
    }
    observed_entity_refs = set(subject_refs)
    for record in envelopes:
        source_id = str(record["source"]["source_id"])
        for contribution in record["contributions"]:
            agent = contribution.get("agent", {})
            if isinstance(agent, Mapping) and agent.get("source_native_id"):
                observed_entity_refs.add((source_id, str(agent["source_native_id"])))

    subjects_with_bridge = {
        (subject["source_id"], subject["source_native_id"])
        for candidate in all_candidates
        if candidate["strength"] in {"strong", "review_only"}
        for subject in candidate["subjects"]
    }
    candidate_domain_counts = [
        len({subject["source_id"] for subject in candidate["subjects"]})
        for candidate in all_candidates
        if candidate["strength"] in {"strong", "review_only"}
    ]
    work_or_event_records = sum(
        record["subject"]["kind"] in {"work", "event", "venue"}
        for record in envelopes
    )
    contribution_edges = sum(len(record["contributions"]) for record in envelopes)
    rights_complete = sum(rights.values()) == len(envelopes)

    reviewed = [dict(item) for item in (reviewed_candidates or []) if item.get("reviewed")]
    accepted = [item for item in reviewed if item.get("decision") == "accept"]
    true_positive = sum(bool(item.get("same_entity")) for item in accepted)
    precision = true_positive / len(accepted) if accepted else None

    return {
        "metric_version": "living-creators-pilot-metrics-0.1",
        "scope": "offline fixture/replay observations; candidates are not canonical identities",
        "cohort": {
            "target_size": manifest.get("target_size") if manifest else None,
            "actual_size": manifest.get("actual_size") if manifest else None,
            "status": manifest.get("status") if manifest else None,
        },
        "baseline_comparison": {
            "documented_current_cross_domain_stitch_people": 3,
            "pilot_candidate_signals": len(all_candidates),
            "accepted_identity_added_by_this_lane": 0,
            "comparability_note": "pilot candidates are review hypotheses, not accepted identities",
        },
        "records": len(envelopes),
        "unique_source_subjects": len(subject_refs),
        "unique_observed_entities": len(observed_entity_refs),
        "source_counts": dict(sorted(sources.items())),
        "work_type_counts": dict(sorted(work_types.items())),
        "role_counts": dict(sorted(roles.items())),
        "works_and_appearances": {
            "work_event_or_venue_records": work_or_event_records,
            "contribution_edges": contribution_edges,
            "works_or_appearances_per_manifest_member": (
                contribution_edges / manifest["actual_size"]
                if manifest and manifest.get("actual_size")
                else None
            ),
        },
        "bridge_candidates": {
            "all": len(all_candidates),
            "strong_authority": len(strong_candidates),
            "review_only_explicit_link": len(review_candidates),
            "subjects_with_bridge_signal": len(subjects_with_bridge),
            "strong_or_review_bridge_rate": (
                len(subjects_with_bridge) / len(observed_entity_refs)
                if observed_entity_refs else None
            ),
            "source_domain_count_distribution": dict(
                sorted(Counter(candidate_domain_counts).items())
            ),
            "mean_source_domains_per_candidate": (
                sum(candidate_domain_counts) / len(candidate_domain_counts)
                if candidate_domain_counts else None
            ),
            "automatic_acceptance": 0,
        },
        "reviewed_precision": {
            "reviewed": len(reviewed),
            "accepted": len(accepted),
            "true_positive": true_positive,
            "false_positive": len(accepted) - true_positive,
            "precision": precision,
            "warning": "fixture-labelled precision is not a production estimate",
        },
        "rights": {
            "state_counts": dict(sorted(rights.items())),
            "completeness": 1.0 if rights_complete else 0.0,
            "unknown_or_pending": rights.get("pending", 0),
        },
        "retention": {
            "transcript_or_media_payloads_persisted": 0,
            "raw_pointers_only": True,
        },
    }


def load_observations(paths: Iterable[Path | str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(read_ndjson(path))
    return records
