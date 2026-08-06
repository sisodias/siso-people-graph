"""Hugging Face Hub model, dataset, Space, and account observations."""
from __future__ import annotations

from typing import Any, Mapping

from sources.software.envelope import make_envelope


def _identifier(
    scheme: str,
    value: Any,
    *,
    stability: str,
    evidence: str,
    uniqueness: str = "unique",
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


def adapt_huggingface_fixture(
    fixture: Mapping[str, Any],
    *,
    raw_pointer: str = "tests/sources_software_ai/fixtures/huggingface.json",
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

    for account in fixture.get("accounts", []):
        kind = "organisation" if account.get("kind") == "organisation" else "account"
        identifiers = [
            _identifier(
                "huggingface_handle",
                account["handle"],
                stability="mutable",
                evidence="Hugging Face Hub account handle",
            )
        ]
        for literal in account.get("identifiers", []):
            identifiers.append(dict(literal))
        records.append(
            make_envelope(
                **meta,
                record_native_id=f"account:{account['handle']}",
                raw_record=account,
                subject_kind=kind,
                subject_native_id=f"huggingface:account:{account['handle']}",
                subject_label=account.get("display_name") or account["handle"],
                attributes={
                    "account_type": account.get("kind", "account"),
                    "handle": account["handle"],
                    "display_name": account.get("display_name"),
                    "metrics": [
                        {"name": key, "value": value, "observed_at": meta["observed_at"]}
                        for key, value in account.get("metrics", {}).items()
                    ],
                },
                identifiers=identifiers,
                evidence=[
                    {
                        "kind": "source_field",
                        "locator": f"https://huggingface.co/{account['handle']}",
                        "observed_at": meta["observed_at"],
                    }
                ],
                raw_pointer=f"{raw_pointer}#/accounts/{account['handle']}",
            )
        )

    for repo in fixture.get("repositories", []):
        repo_type = repo["repo_type"]
        repo_id = repo["id"]
        native_id = f"huggingface:{repo_type}:{repo_id}"
        owner_handle = repo["owner"]["handle"]
        owner_kind = "organisation" if repo["owner"].get("kind") == "organisation" else "account"
        relationships = []
        for link in repo.get("links", []):
            relationships.append(
                {
                    "predicate": link["predicate"],
                    "object": {
                        "kind": "work",
                        "source_native_id": f"huggingface:{link['repo_type']}:{link['id']}",
                        "label": link["id"],
                    },
                    "observed_at": meta["observed_at"],
                    "evidence": link.get("evidence", "literal Hub card metadata"),
                }
            )
        contributions = [
            {
                "role": repo["owner"].get("role", "repository_owner"),
                "order": 1,
                "agent": {
                    "kind": owner_kind,
                    "source_native_id": f"huggingface:account:{owner_handle}",
                    "label": owner_handle,
                    "identifiers": [
                        _identifier(
                            "huggingface_handle",
                            owner_handle,
                            stability="mutable",
                            evidence="Hugging Face repo namespace",
                        )
                    ],
                },
                "observed_at": meta["observed_at"],
            }
        ]
        for order, contributor in enumerate(repo.get("contributors", []), start=2):
            contributions.append(
                {
                    "role": contributor.get("role", "contributor"),
                    "order": order,
                    "agent": {
                        "kind": "account",
                        "source_native_id": f"huggingface:account:{contributor['handle']}",
                        "label": contributor["handle"],
                        "identifiers": [
                            _identifier(
                                "huggingface_handle",
                                contributor["handle"],
                                stability="mutable",
                                evidence="Hugging Face commit contributor handle",
                            )
                        ],
                    },
                    "observed_at": meta["observed_at"],
                }
            )
        identifiers = [
            _identifier(
                "huggingface_repo_id",
                repo_id,
                stability="mutable",
                evidence="Hugging Face Hub repository id/namespace",
            )
        ]
        if repo.get("sha"):
            identifiers.append(
                _identifier(
                    "git_commit_sha",
                    repo["sha"],
                    stability="stable",
                    scope="global",
                    evidence="Hugging Face Hub repository sha",
                )
            )
        records.append(
            make_envelope(
                **{**meta, "observed_at": repo.get("last_modified", meta["observed_at"])},
                record_native_id=f"{repo_type}:{repo_id}:{repo.get('sha', 'head')}",
                raw_record=repo,
                subject_kind="work",
                subject_native_id=native_id,
                subject_label=repo_id,
                attributes={
                    "work_type": f"ai_{repo_type}",
                    "repo_type": repo_type,
                    "license": repo.get("license"),
                    "private": bool(repo.get("private", False)),
                    "gated": repo.get("gated", False),
                    "pipeline_tag": repo.get("pipeline_tag"),
                    "sdk": repo.get("sdk"),
                    "created_at": repo.get("created_at"),
                    "last_modified": repo.get("last_modified"),
                    "metrics": [
                        {"name": key, "value": value, "observed_at": meta["observed_at"]}
                        for key, value in repo.get("metrics", {}).items()
                    ],
                },
                identifiers=identifiers,
                contributions=contributions,
                relationships=relationships,
                evidence=[
                    {
                        "kind": "source_field",
                        "locator": f"https://huggingface.co/api/{repo_type}s/{repo_id}",
                        "observed_at": meta["observed_at"],
                    }
                ],
                raw_pointer=f"{raw_pointer}#/repositories/{repo_type}/{repo_id}",
            )
        )

        for revision in repo.get("revisions", []):
            revision_id = revision["sha"]
            records.append(
                make_envelope(
                    **{**meta, "observed_at": revision["created_at"]},
                    record_native_id=f"{repo_type}:{repo_id}:revision:{revision_id}",
                    raw_record={"repo": repo_id, "revision": revision},
                    subject_kind="work",
                    subject_native_id=f"huggingface:{repo_type}-revision:{repo_id}@{revision_id}",
                    subject_label=f"{repo_id}@{revision_id[:8]}",
                    attributes={
                        "work_type": f"ai_{repo_type}_revision",
                        "repo_type": repo_type,
                        "created_at": revision["created_at"],
                        "license": repo.get("license"),
                        "metrics": [],
                    },
                    identifiers=[
                        _identifier(
                            "git_commit_sha",
                            revision_id,
                            stability="stable",
                            scope="global",
                            evidence="Hugging Face repository revision sha",
                        )
                    ],
                    relationships=[
                        {
                            "predicate": "version_of",
                            "object": {
                                "kind": "work",
                                "source_native_id": native_id,
                                "label": repo_id,
                            },
                            "observed_at": revision["created_at"],
                            "evidence": "Hugging Face revision belongs to repository",
                        }
                    ],
                    contributions=contributions,
                    evidence=[
                        {
                            "kind": "source_field",
                            "locator": f"https://huggingface.co/{repo_id}/commit/{revision_id}",
                            "observed_at": revision["created_at"],
                        }
                    ],
                    raw_pointer=f"{raw_pointer}#/repositories/{repo_type}/{repo_id}/revisions/{revision_id}",
                )
            )

    return records
