"""Evidence-only cross-source identity candidate generation.

The output is a review queue, never a merge.  Labels and names are intentionally
ignored so adapters cannot recreate the current graph's name-only stitch bug.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .envelope import canonical_json, validate_envelope

AUTHORITY_SCHEMES = {"orcid", "viaf", "isni", "wikidata"}
EXPLICIT_LINK_SCHEMES = {"same_as_url", "official_website"}
SOURCE_ACCOUNT_SCHEMES = {
    "github_account_id",
    "youtube_channel_id",
    "podcast_index_person_id",
    "openreview_profile_id",
    "open_library_author_id",
    "openalex_author_id",
}


def normalize_url(value: str) -> str:
    """Normalize only syntax that does not alter the linked resource's identity."""

    parts = urlsplit(value.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if not scheme or not host:
        return value.strip()
    port = parts.port
    netloc = host
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        netloc = f"{host}:{port}"
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    # Tracking parameters are not identity-bearing.  Preserve every other query
    # parameter because profile paths can legitimately use them.
    query = urlencode(
        sorted(
            (key, val)
            for key, val in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
        )
    )
    return urlunsplit((scheme, netloc, path, query, ""))


def _subject_ref(envelope: Mapping[str, Any]) -> dict[str, str]:
    source = envelope["source"]
    subject = envelope["subject"]
    return {
        "source_id": source["source_id"],
        "source_native_id": subject["source_native_id"],
        "kind": subject["kind"],
        "label": subject["label"],
    }


def _iter_entities(envelope: Mapping[str, Any]):
    """Yield the observed subject and contribution agents with their identifiers."""

    yield _subject_ref(envelope), envelope["identifiers"], "subject"
    for index, edge in enumerate(envelope["contributions"]):
        actor = edge.get("agent", {})
        if not isinstance(actor, Mapping):
            continue
        native_id = actor.get("source_native_id")
        label = actor.get("label")
        if not native_id or label is None:
            continue
        identifiers = actor.get("identifiers", [])
        if not isinstance(identifiers, list):
            continue
        yield (
            {
                "source_id": envelope["source"]["source_id"],
                "source_native_id": str(native_id),
                "kind": str(actor.get("kind") or "unknown"),
                "label": str(label),
                "role_context": str(edge.get("role") or "unknown"),
            },
            identifiers,
            f"contribution[{index}]",
        )


def _dedupe_subjects(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for receipt in receipts:
        subject = receipt["subject"]
        by_key[(subject["source_id"], subject["source_native_id"])] = subject
    return sorted(
        by_key.values(), key=lambda item: (item["source_id"], item["source_native_id"])
    )


def _candidate_id(signal: Mapping[str, Any], subjects: list[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256(
        canonical_json({"signal": signal, "subjects": subjects}).encode("utf-8")
    ).hexdigest()[:20]
    return f"bridge:{digest}"


def propose_bridges(envelopes: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return deterministic review candidates from literal, inspectable evidence.

    Authority identifiers may be high-confidence cross-source signals.  Explicit
    ``sameAs``/official-site links are strong evidence but remain review-only.
    Source account IDs identify an account in one source; sharing them across
    different sources is treated as a conflict rather than proof about a human.
    """

    authority_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    link_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    account_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for envelope in envelopes:
        validate_envelope(envelope)
        for ref, identifiers, context in _iter_entities(envelope):
            for item in identifiers:
                scheme = item["scheme"].lower()
                value = item["value"].strip()
                receipt = {
                    "subject": ref,
                    "identifier": dict(item),
                    "source_record": envelope["source"]["record_native_id"],
                    "record_context": context,
                }
                if (
                    scheme in AUTHORITY_SCHEMES
                    and item["stability"] == "stable"
                    and item["uniqueness"] == "unique"
                ):
                    authority_groups[(scheme, value.lower())].append(receipt)
                elif scheme in EXPLICIT_LINK_SCHEMES:
                    link_groups[normalize_url(value)].append(receipt)
                elif scheme in SOURCE_ACCOUNT_SCHEMES:
                    account_groups[(scheme, value)].append(receipt)

    candidates: list[dict[str, Any]] = []
    for (scheme, value), receipts in sorted(authority_groups.items()):
        sources = {item["subject"]["source_id"] for item in receipts}
        if len(receipts) < 2 or len(sources) < 2:
            continue
        subjects = _dedupe_subjects(receipts)
        signal = {"type": "shared_authority_identifier", "scheme": scheme, "value": value}
        candidates.append(
            {
                "candidate_id": _candidate_id(signal, subjects),
                "status": "proposed",
                "strength": "strong",
                "automatic_acceptance": False,
                "subjects": subjects,
                "positive_evidence": receipts,
                "negative_evidence": [],
                "conflicts": [],
                "signal": signal,
                "note": "High-confidence candidate; still requires identity-lane review.",
            }
        )

    for value, receipts in sorted(link_groups.items()):
        sources = {item["subject"]["source_id"] for item in receipts}
        if len(receipts) < 2 or len(sources) < 2:
            continue
        subjects = _dedupe_subjects(receipts)
        signal = {"type": "shared_explicit_link", "scheme": "same_as_url", "value": value}
        candidates.append(
            {
                "candidate_id": _candidate_id(signal, subjects),
                "status": "proposed",
                "strength": "review_only",
                "automatic_acceptance": False,
                "subjects": subjects,
                "positive_evidence": receipts,
                "negative_evidence": [],
                "conflicts": [],
                "signal": signal,
                "note": "Literal publisher/author link; site ownership and direction must be reviewed.",
            }
        )

    # A source account identifier appearing under more than one source is not a
    # bridge.  Preserve it as an audit conflict so a mapping bug cannot be read as
    # identity evidence.
    for (scheme, value), receipts in sorted(account_groups.items()):
        sources = {item["subject"]["source_id"] for item in receipts}
        if len(receipts) < 2 or len(sources) < 2:
            continue
        subjects = _dedupe_subjects(receipts)
        signal = {"type": "source_scope_collision", "scheme": scheme, "value": value}
        candidates.append(
            {
                "candidate_id": _candidate_id(signal, subjects),
                "status": "conflicted",
                "strength": "invalid",
                "automatic_acceptance": False,
                "subjects": subjects,
                "positive_evidence": [],
                "negative_evidence": receipts,
                "conflicts": ["source-scoped identifier reused across sources"],
                "signal": signal,
                "note": "Do not resolve; inspect adapter scope or source data.",
            }
        )

    return sorted(candidates, key=lambda item: item["candidate_id"])


def reviewed_precision(reviews: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Calculate transparent precision over a manually labelled candidate sample."""

    reviewed = [dict(item) for item in reviews if item.get("reviewed")]
    eligible = [item for item in reviewed if item.get("decision") == "accept"]
    true_positive = sum(bool(item.get("same_entity")) for item in eligible)
    false_positive = len(eligible) - true_positive
    precision = true_positive / len(eligible) if eligible else None
    return {
        "reviewed_candidates": len(reviewed),
        "accepted_candidates": len(eligible),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "precision": precision,
        "scope": "manual labels supplied to this function; no extrapolation",
    }
