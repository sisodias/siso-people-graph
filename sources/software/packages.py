"""Package-registry adapters for PyPI, crates.io, and ecosyste.ms.

Package coordinates identify Works. Registry owners and maintainers are retained
as contribution relationships and are never promoted to aliases for people.
"""
from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import quote

from .envelope import make_envelope



def _purl(registry: str, coordinate: str, version: str | None = None) -> str:
    """Build the bounded Package-URL forms used by this pilot.

    npm scopes require the leading ``@`` to be percent-encoded while the scope
    separator remains a path separator. Other pilot registries use one name
    segment. A production collector should adopt ``packageurl-python`` rather
    than expand this deliberately small formatter.
    """

    if registry == "npm" and coordinate.startswith("@") and "/" in coordinate:
        scope, name = coordinate[1:].split("/", 1)
        path = f"%40{quote(scope, safe='')}/{quote(name, safe='')}"
    else:
        path = quote(coordinate, safe="._-")
    return f"pkg:{registry}/{path}" + (f"@{quote(version, safe='.+_-')}" if version else "")


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


def _meta(fixture: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": fixture["source_id"],
        "snapshot_id": fixture["snapshot_id"],
        "observed_at": fixture["observed_at"],
        "retrieved_at": fixture["retrieved_at"],
        "terms_revision": fixture["terms_revision"],
        "rights_state": fixture["rights_state"],
    }


def _agent(owner: Mapping[str, Any], scheme: str, evidence: str) -> dict[str, Any]:
    account_id = owner.get("id") or owner.get("login") or owner.get("name")
    agent = {
        "kind": "organisation" if owner.get("kind") == "organisation" else "account",
        "source_native_id": f"{scheme}:{account_id}",
        "label": owner.get("login") or owner.get("name") or str(account_id),
        "identifiers": [
            _identifier(
                scheme,
                account_id,
                stability=owner.get("stability", "unknown"),
                evidence=evidence,
            )
        ],
    }
    for identifier in owner.get("identifiers", []):
        agent["identifiers"].append(dict(identifier))
    return agent


def _package_record(
    *,
    meta: Mapping[str, Any],
    raw: Mapping[str, Any],
    registry: str,
    coordinate: str,
    label: str,
    package_id_scheme: str,
    package_id_value: str,
    package_id_evidence: str,
    attributes: Mapping[str, Any],
    contributions: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    raw_pointer: str,
) -> dict[str, Any]:
    purl = _purl(registry, coordinate)
    identifiers = [
        _identifier(
            package_id_scheme,
            package_id_value,
            stability="unknown",
            evidence=package_id_evidence,
        ),
        _identifier(
            "purl",
            purl,
            stability="stable",
            scope="global",
            evidence=f"Package URL derived from literal {registry} coordinate",
        ),
    ]
    return make_envelope(
        **meta,
        record_native_id=f"package:{coordinate}",
        raw_record=raw,
        subject_kind="work",
        subject_native_id=purl,
        subject_label=label,
        attributes={"work_type": "software_package", "registry": registry, **dict(attributes)},
        identifiers=identifiers,
        contributions=contributions,
        relationships=relationships,
        evidence=[
            {
                "kind": "source_record",
                "locator": raw_pointer,
                "observed_at": meta["observed_at"],
            }
        ],
        raw_pointer=raw_pointer,
    )


def _release_record(
    *,
    meta: Mapping[str, Any],
    raw: Mapping[str, Any],
    registry: str,
    coordinate: str,
    version: Mapping[str, Any],
    raw_pointer: str,
) -> dict[str, Any]:
    purl = _purl(registry, coordinate, str(version["version"]))
    relationships = [
        {
            "predicate": "version_of",
            "object": {
                "kind": "work",
                "source_native_id": _purl(registry, coordinate),
                "label": coordinate,
            },
            "observed_at": meta["observed_at"],
            "evidence": "registry version belongs to package coordinate",
        }
    ]
    for dependency in version.get("dependencies", []):
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
                    "environment": dependency.get("kind", "runtime"),
                    "optional": bool(dependency.get("optional", False)),
                },
                "observed_at": meta["observed_at"],
                "evidence": dependency.get("evidence", "literal registry dependency row"),
            }
        )
    identifiers = [
        _identifier(
            "purl",
            purl,
            stability="stable",
            scope="global",
            evidence="Package URL derived from registry coordinate and version",
        )
    ]
    if version.get("sha256"):
        identifiers.append(
            _identifier(
                "sha256",
                version["sha256"],
                stability="stable",
                scope="global",
                evidence="registry release artifact checksum",
            )
        )
    return make_envelope(
        **{**meta, "observed_at": version.get("published_at", meta["observed_at"])},
        record_native_id=f"release:{coordinate}:{version['version']}",
        raw_record={"package": raw.get("name"), "version": version},
        subject_kind="work",
        subject_native_id=purl,
        subject_label=f"{coordinate} {version['version']}",
        attributes={
            "work_type": "software_package_release",
            "registry": registry,
            "version": version["version"],
            "published_at": version.get("published_at"),
            "yanked": bool(version.get("yanked", False)),
            "license": version.get("license") or raw.get("license"),
            "metrics": [
                {
                    "name": name,
                    "value": value,
                    "observed_at": meta["observed_at"],
                }
                for name, value in version.get("metrics", {}).items()
            ],
        },
        identifiers=identifiers,
        relationships=relationships,
        evidence=[
            {
                "kind": "source_record",
                "locator": raw_pointer,
                "observed_at": meta["observed_at"],
            }
        ],
        raw_pointer=raw_pointer,
    )


def adapt_pypi_fixture(
    fixture: Mapping[str, Any], *, raw_pointer: str = "tests/sources_software_ai/fixtures/pypi.json"
) -> list[dict[str, Any]]:
    meta = _meta(fixture)
    records: list[dict[str, Any]] = []
    for package in fixture.get("packages", []):
        name = package["name"].lower().replace("_", "-")
        contributions = [
            {
                "role": owner.get("role", "maintainer"),
                "order": order,
                "agent": _agent(owner, "pypi_user", "PyPI project role user identifier"),
                "observed_at": meta["observed_at"],
            }
            for order, owner in enumerate(package.get("owners", []), 1)
        ]
        relationships = [
            {
                "predicate": "source_repository",
                "object": {
                    "kind": "work",
                    "source_native_id": repo["native_id"],
                    "label": repo["label"],
                },
                "observed_at": meta["observed_at"],
                "evidence": repo["evidence"],
            }
            for repo in package.get("source_repositories", [])
        ]
        records.append(
            _package_record(
                meta=meta,
                raw=package,
                registry="pypi",
                coordinate=name,
                label=package["name"],
                package_id_scheme="pypi_project",
                package_id_value=name,
                package_id_evidence="PyPI project name",
                attributes={
                    "summary": package.get("summary"),
                    "license": package.get("license"),
                    "requires_python": package.get("requires_python"),
                    "abandoned": bool(package.get("abandoned", False)),
                    "metrics": [
                        {"name": key, "value": value, "observed_at": meta["observed_at"]}
                        for key, value in package.get("metrics", {}).items()
                    ],
                },
                contributions=contributions,
                relationships=relationships,
                raw_pointer=f"{raw_pointer}#/packages/{name}",
            )
        )
        for version in package.get("versions", []):
            records.append(
                _release_record(
                    meta=meta,
                    raw=package,
                    registry="pypi",
                    coordinate=name,
                    version=version,
                    raw_pointer=f"{raw_pointer}#/packages/{name}/versions/{version['version']}",
                )
            )
    return records


def adapt_crates_fixture(
    fixture: Mapping[str, Any], *, raw_pointer: str = "tests/sources_software_ai/fixtures/crates.json"
) -> list[dict[str, Any]]:
    meta = _meta(fixture)
    records: list[dict[str, Any]] = []
    for package in fixture.get("crates", []):
        name = package["name"]
        contributions = [
            {
                "role": owner.get("role", "owner"),
                "order": order,
                "agent": _agent(owner, "crates_user_id", "crates.io owner.id"),
                "observed_at": meta["observed_at"],
            }
            for order, owner in enumerate(package.get("owners", []), 1)
        ]
        relationships = [
            {
                "predicate": "source_repository",
                "object": {
                    "kind": "work",
                    "source_native_id": package["repository"]["native_id"],
                    "label": package["repository"]["label"],
                },
                "observed_at": meta["observed_at"],
                "evidence": package["repository"]["evidence"],
            }
        ] if package.get("repository") else []
        records.append(
            _package_record(
                meta=meta,
                raw=package,
                registry="cargo",
                coordinate=name,
                label=name,
                package_id_scheme="crates_io_crate",
                package_id_value=name,
                package_id_evidence="crates.io crate.name",
                attributes={
                    "description": package.get("description"),
                    "license": package.get("license"),
                    "abandoned": bool(package.get("abandoned", False)),
                    "metrics": [
                        {"name": key, "value": value, "observed_at": meta["observed_at"]}
                        for key, value in package.get("metrics", {}).items()
                    ],
                },
                contributions=contributions,
                relationships=relationships,
                raw_pointer=f"{raw_pointer}#/crates/{name}",
            )
        )
        for version in package.get("versions", []):
            records.append(
                _release_record(
                    meta=meta,
                    raw=package,
                    registry="cargo",
                    coordinate=name,
                    version=version,
                    raw_pointer=f"{raw_pointer}#/crates/{name}/versions/{version['version']}",
                )
            )
    return records


def adapt_ecosystems_fixture(
    fixture: Mapping[str, Any], *, raw_pointer: str = "tests/sources_software_ai/fixtures/ecosystems.json"
) -> list[dict[str, Any]]:
    meta = _meta(fixture)
    records: list[dict[str, Any]] = []
    registry_map = {"npm": "npm", "pypi": "pypi", "crates": "cargo"}
    for package in fixture.get("packages", []):
        registry = registry_map.get(package["ecosystem"], package["ecosystem"])
        coordinate = package["name"]
        contributions = [
            {
                "role": owner.get("role", "maintainer"),
                "order": order,
                "agent": _agent(owner, f"{package['ecosystem']}_maintainer", "ecosyste.ms maintainer row"),
                "observed_at": meta["observed_at"],
            }
            for order, owner in enumerate(package.get("maintainers", []), 1)
        ]
        relationships: list[dict[str, Any]] = []
        for dependency in package.get("dependencies", []):
            relationships.append(
                {
                    "predicate": "depends_on",
                    "object": {
                        "kind": "work",
                        "source_native_id": dependency["purl"],
                        "label": dependency.get("name", dependency["purl"]),
                    },
                    "attributes": {"requirement": dependency.get("requirement")},
                    "observed_at": meta["observed_at"],
                    "evidence": "ecosyste.ms normalized dependency row",
                }
            )
        if package.get("repository"):
            relationships.append(
                {
                    "predicate": "source_repository",
                    "object": {
                        "kind": "work",
                        "source_native_id": package["repository"]["native_id"],
                        "label": package["repository"]["label"],
                    },
                    "observed_at": meta["observed_at"],
                    "evidence": package["repository"]["evidence"],
                }
            )
        records.append(
            _package_record(
                meta=meta,
                raw=package,
                registry=registry,
                coordinate=coordinate,
                label=package["name"],
                package_id_scheme="ecosystems_package_id",
                package_id_value=package["id"],
                package_id_evidence="ecosyste.ms package id",
                attributes={
                    "ecosystem": package["ecosystem"],
                    "latest_release": package.get("latest_release"),
                    "license": package.get("license"),
                    "abandoned": bool(package.get("abandoned", False)),
                    "metrics": [
                        {"name": key, "value": value, "observed_at": meta["observed_at"]}
                        for key, value in package.get("metrics", {}).items()
                    ],
                },
                contributions=contributions,
                relationships=relationships,
                raw_pointer=f"{raw_pointer}#/packages/{package['id']}",
            )
        )
    return records
