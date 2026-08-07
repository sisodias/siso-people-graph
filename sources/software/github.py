"""GitHub REST and GH Archive fixture adapters.

The adapter treats GitHub numeric account/repository IDs and GraphQL node IDs as
source-scoped stable identifiers. Logins, full names, and repository full names
remain mutable aliases. No record receives a canonical People Graph identifier.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .envelope import make_envelope


def _identifier(
    scheme: str,
    value: Any,
    *,
    stability: str,
    uniqueness: str = "unique",
    evidence: str,
    scope: str = "source",
) -> dict[str, Any]:
    return {
        "scheme": scheme,
        "value": str(value),
        "scope": scope,
        "stability": stability,
        "uniqueness": uniqueness,
        "evidence": evidence,
    }


def _metrics(item: Mapping[str, Any], observed_at: str) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for key in ("followers", "following", "public_repos", "stars", "forks", "watchers"):
        if key in item and item[key] is not None:
            metrics.append({"name": key, "value": item[key], "observed_at": observed_at})
    return metrics


def _source(meta: Mapping[str, Any], source_id: str) -> dict[str, Any]:
    source_meta = meta["sources"][source_id]
    return {
        "source_id": source_id,
        "snapshot_id": source_meta["snapshot_id"],
        "observed_at": source_meta["observed_at"],
        "retrieved_at": source_meta["retrieved_at"],
        "terms_revision": source_meta["terms_revision"],
        "rights_state": source_meta["rights_state"],
    }


def adapt_github_fixture(
    fixture: Mapping[str, Any], *, raw_pointer: str = "tests/sources_software_ai/fixtures/github.json"
) -> list[dict[str, Any]]:
    """Convert a bounded GitHub/GH Archive fixture to observation envelopes."""

    records: list[dict[str, Any]] = []
    rest_source = _source(fixture, "github_rest")

    for item in fixture.get("accounts", []):
        native_id = f"github:account:{item['id']}"
        identifiers = [
            _identifier(
                "github_account_id",
                item["id"],
                stability="stable",
                evidence="GitHub REST account.id",
            ),
            _identifier(
                "github_node_id",
                item["node_id"],
                stability="stable",
                evidence="GitHub REST account.node_id",
            ),
            _identifier(
                "github_login",
                item["login"],
                stability="mutable",
                evidence="GitHub REST account.login",
            ),
        ]
        relationships = []
        for alias in item.get("previous_logins", []):
            relationships.append(
                {
                    "predicate": "renamed_from",
                    "object": {
                        "kind": "account",
                        "source_native_id": f"github:login:{alias['login']}",
                        "label": alias["login"],
                    },
                    "valid_time": {
                        "from": alias.get("valid_from"),
                        "to": alias.get("valid_to"),
                    },
                    "observed_at": rest_source["observed_at"],
                    "evidence": "GitHub REST login history fixture",
                }
            )
        account_kind = "organisation" if item.get("type") == "Organization" else "account"
        attributes = {
            "account_type": item.get("type", "Unknown"),
            "login": item["login"],
            "display_name": item.get("name"),
            "company": item.get("company"),
            "location": item.get("location"),
            "bio": item.get("bio"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "metrics": _metrics(item, rest_source["observed_at"]),
        }
        records.append(
            make_envelope(
                **rest_source,
                record_native_id=f"account:{item['id']}:{rest_source['snapshot_id']}",
                raw_record=item,
                subject_kind=account_kind,
                subject_native_id=native_id,
                subject_label=item["login"],
                attributes=attributes,
                identifiers=identifiers,
                relationships=relationships,
                evidence=[
                    {
                        "kind": "source_field",
                        "locator": f"GET /users/{item['login']}",
                        "observed_at": rest_source["observed_at"],
                    }
                ],
                raw_pointer=f"{raw_pointer}#/accounts/{item['id']}",
            )
        )

    for item in fixture.get("repositories", []):
        native_id = f"github:repository:{item['id']}"
        identifiers = [
            _identifier(
                "github_repository_id",
                item["id"],
                stability="stable",
                evidence="GitHub REST repository.id",
            ),
            _identifier(
                "github_node_id",
                item["node_id"],
                stability="stable",
                evidence="GitHub REST repository.node_id",
            ),
            _identifier(
                "github_full_name",
                item["full_name"],
                stability="mutable",
                evidence="GitHub REST repository.full_name",
            ),
        ]
        contributions: list[dict[str, Any]] = [
            {
                "role": "repository_owner",
                "order": 1,
                "agent": {
                    "kind": "organisation"
                    if item["owner"].get("type") == "Organization"
                    else "account",
                    "source_native_id": f"github:account:{item['owner']['id']}",
                    "label": item["owner"]["login"],
                    "identifiers": [
                        _identifier(
                            "github_account_id",
                            item["owner"]["id"],
                            stability="stable",
                            evidence="GitHub REST repository.owner.id",
                        )
                    ],
                },
                "observed_at": item.get("observed_at", rest_source["observed_at"]),
            }
        ]
        for order, contributor in enumerate(item.get("contributors", []), start=1):
            contributions.append(
                {
                    "role": contributor.get("role", "contributor"),
                    "order": order,
                    "agent": {
                        "kind": "account",
                        "source_native_id": f"github:account:{contributor['id']}",
                        "label": contributor["login"],
                        "identifiers": [
                            _identifier(
                                "github_account_id",
                                contributor["id"],
                                stability="stable",
                                evidence="GitHub REST contributor.id",
                            )
                        ],
                    },
                    "observed_at": item.get("observed_at", rest_source["observed_at"]),
                }
            )

        relationships: list[dict[str, Any]] = []
        for transfer in item.get("transfers", []):
            relationships.append(
                {
                    "predicate": "transferred_from",
                    "object": {
                        "kind": "account",
                        "source_native_id": f"github:account:{transfer['from_owner_id']}",
                        "label": transfer["from_owner_login"],
                    },
                    "valid_time": {"at": transfer["at"]},
                    "observed_at": item.get("observed_at", rest_source["observed_at"]),
                    "evidence": transfer.get("evidence", "repository full-name history"),
                }
            )
        for dependency in item.get("dependencies", []):
            relationships.append(
                {
                    "predicate": "depends_on",
                    "object": {
                        "kind": "work",
                        "source_native_id": dependency["purl"],
                        "label": dependency.get("name", dependency["purl"]),
                    },
                    "attributes": {
                        "requirement": dependency.get("requirement"),
                        "environment": dependency.get("environment", "runtime"),
                    },
                    "observed_at": item.get("observed_at", rest_source["observed_at"]),
                    "evidence": dependency.get("evidence", "dependency manifest fixture"),
                }
            )
        for swhid in item.get("swhids", []):
            relationships.append(
                {
                    "predicate": "archived_as",
                    "object": {
                        "kind": "work",
                        "source_native_id": swhid,
                        "label": swhid,
                    },
                    "observed_at": item.get("observed_at", rest_source["observed_at"]),
                    "evidence": "Software Heritage archival identifier exposed by source fixture",
                }
            )

        attributes = {
            "work_type": "software_repository",
            "full_name": item["full_name"],
            "description": item.get("description"),
            "default_branch": item.get("default_branch"),
            "license": item.get("license"),
            "archived": bool(item.get("archived", False)),
            "abandoned": bool(item.get("abandoned", False)),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "pushed_at": item.get("pushed_at"),
            "metrics": _metrics(item, item.get("observed_at", rest_source["observed_at"])),
        }
        records.append(
            make_envelope(
                **{**rest_source, "observed_at": item.get("observed_at", rest_source["observed_at"])},
                record_native_id=f"repository:{item['id']}:{item.get('observed_at', rest_source['snapshot_id'])}",
                raw_record=item,
                subject_kind="work",
                subject_native_id=native_id,
                subject_label=item["full_name"],
                attributes=attributes,
                identifiers=identifiers,
                contributions=contributions,
                relationships=relationships,
                evidence=[
                    {
                        "kind": "source_field",
                        "locator": f"GET /repositories/{item['id']}",
                        "observed_at": item.get("observed_at", rest_source["observed_at"]),
                    }
                ],
                raw_pointer=f"{raw_pointer}#/repositories/{item['id']}",
            )
        )

    for item in fixture.get("releases", []):
        relationships = [
            {
                "predicate": "version_of",
                "object": {
                    "kind": "work",
                    "source_native_id": f"github:repository:{item['repository_id']}",
                    "label": item["repository_full_name"],
                },
                "observed_at": rest_source["observed_at"],
                "evidence": "GitHub REST release.repository_url",
            }
        ]
        records.append(
            make_envelope(
                **{**rest_source, "observed_at": item["published_at"]},
                record_native_id=f"release:{item['id']}",
                raw_record=item,
                subject_kind="work",
                subject_native_id=f"github:release:{item['id']}",
                subject_label=f"{item['repository_full_name']} {item['tag_name']}",
                attributes={
                    "work_type": "software_release",
                    "tag_name": item["tag_name"],
                    "name": item.get("name"),
                    "draft": bool(item.get("draft", False)),
                    "prerelease": bool(item.get("prerelease", False)),
                    "published_at": item["published_at"],
                    "license": item.get("license"),
                    "metrics": [],
                },
                identifiers=[
                    _identifier(
                        "github_release_id",
                        item["id"],
                        stability="stable",
                        evidence="GitHub REST release.id",
                    ),
                    _identifier(
                        "git_tag",
                        item["tag_name"],
                        stability="mutable",
                        uniqueness="unknown",
                        evidence="GitHub REST release.tag_name",
                    ),
                ],
                contributions=[
                    {
                        "role": "release_publisher",
                        "order": 1,
                        "agent": {
                            "kind": "account",
                            "source_native_id": f"github:account:{item['author']['id']}",
                            "label": item["author"]["login"],
                            "identifiers": [
                                _identifier(
                                    "github_account_id",
                                    item["author"]["id"],
                                    stability="stable",
                                    evidence="GitHub REST release.author.id",
                                )
                            ],
                        },
                        "observed_at": item["published_at"],
                    }
                ],
                relationships=relationships,
                evidence=[
                    {
                        "kind": "source_field",
                        "locator": f"GET /repos/{item['repository_full_name']}/releases/{item['id']}",
                        "observed_at": rest_source["observed_at"],
                    }
                ],
                raw_pointer=f"{raw_pointer}#/releases/{item['id']}",
            )
        )

    archive_source = _source(fixture, "gh_archive")
    for item in fixture.get("events", []):
        actor_id = item["actor"]["id"]
        repo_id = item["repo"]["id"]
        records.append(
            make_envelope(
                **{**archive_source, "observed_at": item["created_at"]},
                record_native_id=str(item["id"]),
                raw_record=item,
                subject_kind="event",
                subject_native_id=f"gharchive:event:{item['id']}",
                subject_label=item["type"],
                attributes={
                    "event_type": item["type"],
                    "public": item.get("public", True),
                    "created_at": item["created_at"],
                    "payload_summary": item.get("payload_summary", {}),
                    "metrics": [],
                },
                identifiers=[
                    _identifier(
                        "github_event_id",
                        item["id"],
                        stability="stable",
                        evidence="GH Archive event.id",
                    )
                ],
                relationships=[
                    {
                        "predicate": "performed_by",
                        "object": {
                            "kind": "account",
                            "source_native_id": f"github:account:{actor_id}",
                            "label": item["actor"]["login"],
                        },
                        "observed_at": item["created_at"],
                        "evidence": "GH Archive event.actor",
                    },
                    {
                        "predicate": "occurred_on",
                        "object": {
                            "kind": "work",
                            "source_native_id": f"github:repository:{repo_id}",
                            "label": item["repo"]["name"],
                        },
                        "observed_at": item["created_at"],
                        "evidence": "GH Archive event.repo",
                    },
                ],
                evidence=[
                    {
                        "kind": "source_record",
                        "locator": f"gharchive:{archive_source['snapshot_id']}#{item['id']}",
                        "observed_at": item["created_at"],
                    }
                ],
                raw_pointer=f"{raw_pointer}#/events/{item['id']}",
            )
        )

    return records


def iter_account_ids(records: Iterable[Mapping[str, Any]]) -> set[str]:
    """Return stable GitHub account IDs present in envelopes or contributions."""

    found: set[str] = set()
    for record in records:
        for identifier in record.get("identifiers", []):
            if identifier.get("scheme") == "github_account_id":
                found.add(str(identifier["value"]))
        for contribution in record.get("contributions", []):
            for identifier in contribution.get("agent", {}).get("identifiers", []):
                if identifier.get("scheme") == "github_account_id":
                    found.add(str(identifier["value"]))
    return found
