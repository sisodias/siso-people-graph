"""Replayable GitHub profile observation handling."""
from __future__ import annotations

import hashlib
from typing import Mapping

from .engine import IdentityEngine, stable_json, utc_now

GITHUB_PROFILE_FIELDS = (
    "id",
    "node_id",
    "login",
    "name",
    "twitter_username",
    "blog",
    "company",
    "location",
    "bio",
    "type",
    "followers",
    "created_at",
)


def payload_digest(profile: Mapping[str, object]) -> str:
    return hashlib.sha256(stable_json(profile).encode("utf-8")).hexdigest()


def record_github_profile(
    engine: IdentityEngine,
    entity_id: str,
    requested_login: str,
    profile: Mapping[str, object],
    *,
    observed_at: str | None = None,
    source: str = "github_api",
) -> dict[str, object]:
    """Record profile fields as identifiers, aliases, attributes, and receipts.

    No canonical name, rank, or build metadata is updated here. Null fields still
    receive an observation receipt so a resumable job does not refetch forever.
    """
    when = observed_at or utc_now()
    digest = payload_digest(profile)
    stable_id = profile.get("id")
    stable_id_text = str(stable_id) if stable_id not in (None, "") else None
    engine.upsert_entity(entity_id)

    identifiers: list[tuple[str, str]] = []
    aliases: list[tuple[str, str]] = []
    attributes: list[tuple[str, object]] = []

    if stable_id_text:
        engine.record_identifier(
            entity_id, "github_id", stable_id_text, source=source,
            observed_at=when, evidence={"field": "id", "payload_sha256": digest},
        )
        identifiers.append(("github_id", stable_id_text))
    if profile.get("node_id"):
        engine.record_identifier(
            entity_id, "github_node_id", profile["node_id"], source=source,
            observed_at=when, evidence={"field": "node_id", "payload_sha256": digest},
        )
        identifiers.append(("github_node_id", str(profile["node_id"])))

    response_login = str(profile.get("login") or requested_login).strip()
    login_values = []
    if requested_login.strip():
        login_values.append(requested_login.strip())
    if response_login and response_login.casefold() not in {value.casefold() for value in login_values}:
        login_values.append(response_login)
    for login in login_values:
        if stable_id_text:
            engine.record_account_alias(
                entity_id, "github_login", login,
                stable_identifier_scheme="github_id",
                stable_identifier_value=stable_id_text,
                source=source, observed_at=when,
                evidence={"requested_login": requested_login, "response_login": response_login,
                          "payload_sha256": digest},
            )
        else:
            engine.record_alias(
                entity_id, "github_login", login, source=source, observed_at=when,
                evidence={"requested_login": requested_login, "response_login": response_login,
                          "payload_sha256": digest},
            )
        aliases.append(("github_login", login))

    if profile.get("twitter_username"):
        engine.record_alias(
            entity_id, "x_handle", profile["twitter_username"], source=source,
            observed_at=when, evidence={"field": "twitter_username", "payload_sha256": digest},
        )
        aliases.append(("x_handle", str(profile["twitter_username"])))

    attribute_map = {
        "real_name": profile.get("name"),
        "website": profile.get("blog"),
        "company": profile.get("company"),
        "location": profile.get("location"),
        "biography": profile.get("bio"),
        "profile_type": profile.get("type"),
        "followers": profile.get("followers"),
        "account_created_at": profile.get("created_at"),
    }
    for attribute, value in attribute_map.items():
        # Null observations are retained; they are evidence that the field was
        # checked, not a reason to block the other independent fields.
        engine.record_attribute(
            entity_id, attribute, value, source=source, observed_at=when,
            payload_sha256=digest, evidence={"payload_sha256": digest},
        )
        attributes.append((attribute, value))

    for field in GITHUB_PROFILE_FIELDS:
        value = profile.get(field)
        engine.record_enrichment_receipt(
            entity_id, field, source=source, observed_at=when,
            payload_sha256=digest, present=value not in (None, ""),
        )

    return {
        "entity_id": entity_id,
        "payload_sha256": digest,
        "requested_login": requested_login,
        "response_login": response_login,
        "identifiers": identifiers,
        "aliases": aliases,
        "attributes": attributes,
    }
