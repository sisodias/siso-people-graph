"""Schema.org/JSON-LD observations from explicitly supplied public web pages.

The adapter does not crawl.  A caller provides one page payload and its URL.  By
default the result is ``discovery_only`` because public visibility is not a
blanket reuse licence.  Only compact metadata and evidence pointers are emitted.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any, Iterable, Mapping

from .envelope import evidence, identifier, make_envelope, payload_sha256, source_block
from sources.media.policies import SOURCE_POLICIES

_POLICY = SOURCE_POLICIES["public_web_schema_org"]

SCHEMA_TYPE_TO_SUBJECT = {
    "Person": ("person", None),
    "Organization": ("organisation", None),
    "Corporation": ("organisation", None),
    "Article": ("work", "article"),
    "BlogPosting": ("work", "article"),
    "NewsArticle": ("work", "article"),
    "Book": ("work", "book"),
    "Course": ("work", "course"),
    "PodcastSeries": ("work", "podcast_show"),
    "PodcastEpisode": ("work", "podcast_episode"),
    "VideoObject": ("work", "video"),
    "CreativeWork": ("work", "creative_work"),
    "Event": ("event", "event"),
    "EducationEvent": ("event", "course_event"),
    "PublicationEvent": ("event", "publication_event"),
    "Place": ("place", None),
}


class _JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture = False
        self._parts: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        attributes = {key.lower(): value for key, value in attrs}
        media_type = (attributes.get("type") or "").lower()
        if media_type in {"application/ld+json", "application/json+ld"}:
            self._capture = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._capture:
            self.blocks.append("".join(self._parts))
            self._capture = False
            self._parts = []


def _iter_nodes(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, list):
        for item in value:
            yield from _iter_nodes(item)
    elif isinstance(value, Mapping):
        graph = value.get("@graph")
        if graph is not None:
            yield from _iter_nodes(graph)
        else:
            yield value


def _types(node: Mapping[str, Any]) -> list[str]:
    raw = node.get("@type", [])
    if isinstance(raw, str):
        return [raw.rsplit("/", 1)[-1]]
    if isinstance(raw, list):
        return [str(item).rsplit("/", 1)[-1] for item in raw]
    return []


def _first_type(node: Mapping[str, Any]) -> tuple[str, str | None] | None:
    for schema_type in _types(node):
        if schema_type in SCHEMA_TYPE_TO_SUBJECT:
            return SCHEMA_TYPE_TO_SUBJECT[schema_type]
    return None


def _as_objects(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    if isinstance(value, str):
        return [{"name": value}]
    return []


def _node_id(node: Mapping[str, Any], page_url: str, index: int) -> str:
    for key in ("@id", "url", "identifier"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"{page_url}#jsonld-node-{index}"


def _label(node: Mapping[str, Any], native_id: str) -> str:
    for key in ("name", "headline", "title"):
        value = node.get(key)
        if isinstance(value, str):
            return value
    return native_id


def _compact_attributes(node: Mapping[str, Any], work_type: str | None) -> dict[str, Any]:
    allowed = {
        "datePublished",
        "dateModified",
        "startDate",
        "endDate",
        "inLanguage",
        "isPartOf",
        "location",
        "jobTitle",
        "affiliation",
    }
    attributes = {key: node[key] for key in sorted(allowed) if key in node}
    attributes["schema_types"] = _types(node)
    if work_type:
        attributes["work_type"] = work_type
    return attributes


def _same_as_identifiers(node: Mapping[str, Any], page_url: str) -> list[dict[str, str]]:
    values = node.get("sameAs", [])
    if isinstance(values, str):
        values = [values]
    results: list[dict[str, str]] = []
    if isinstance(values, list):
        for index, value in enumerate(values):
            if not isinstance(value, str) or not value.strip():
                continue
            results.append(
                identifier(
                    scheme="same_as_url",
                    value=value.strip(),
                    scope="global",
                    stability="unknown",
                    uniqueness="unknown",
                    evidence=f"{page_url} JSON-LD sameAs[{index}]",
                )
            )
    return results


def _contributors(node: Mapping[str, Any], page_url: str) -> list[dict[str, Any]]:
    role_fields = {
        "author": "author",
        "creator": "creator",
        "editor": "editor",
        "performer": "performer",
        "actor": "speaker",
        "contributor": "contributor",
        "organizer": "organizer",
    }
    contributions: list[dict[str, Any]] = []
    for field, role in role_fields.items():
        for index, actor in enumerate(_as_objects(node.get(field))):
            label = str(actor.get("name") or actor.get("@id") or "")
            native_id = str(actor.get("@id") or actor.get("url") or f"label:{label}")
            if not label:
                continue
            receipt = f"{page_url} JSON-LD {field}[{index}]"
            actor_identifiers: list[dict[str, str]] = []
            same_as_values = actor.get("sameAs", [])
            if isinstance(same_as_values, str):
                same_as_values = [same_as_values]
            if isinstance(same_as_values, list):
                for same_as_index, same_as in enumerate(same_as_values):
                    if not isinstance(same_as, str) or not same_as.strip():
                        continue
                    actor_identifiers.append(
                        identifier(
                            scheme="same_as_url",
                            value=same_as.strip(),
                            scope="global",
                            stability="unknown",
                            uniqueness="unknown",
                            evidence=f"{receipt} sameAs[{same_as_index}]",
                        )
                    )
            elif actor.get("@id") or actor.get("url"):
                actor_identifiers.append(
                    identifier(
                        scheme="official_website",
                        value=native_id,
                        scope="global",
                        stability="unknown",
                        uniqueness="unknown",
                        evidence=f"{receipt} @id|url",
                    )
                )

            actor_record: dict[str, Any] = {
                "source_native_id": native_id,
                "label": label,
                "kind": "organisation"
                if "Organization" in _types(actor)
                else "unknown",
            }
            if actor_identifiers:
                actor_record["identifiers"] = actor_identifiers
            contribution: dict[str, Any] = {
                "role": role,
                "agent": actor_record,
                "evidence": receipt,
                "identity_evidence": "explicit_link"
                if actor_identifiers or actor.get("@id") or actor.get("url")
                else "name_only",
            }
            contributions.append(contribution)
    return contributions


def parse_jsonld_page(
    *,
    html: str,
    page_url: str,
    retrieved_at: str,
    observed_at: str | None = None,
    terms_revision: str = _POLICY["terms_revision"],
    rights_state: str = _POLICY["rights_state_default"],
) -> list[dict[str, Any]]:
    """Parse one supplied page and emit source-native observations.

    The HTML itself is not copied into the envelope.  Callers should keep a
    content-addressed receipt outside Git when retention is permitted.
    """

    parser = _JsonLdParser()
    parser.feed(html)
    digest = payload_sha256(html)
    snapshot_id = f"sha256:{digest}"
    records: list[dict[str, Any]] = []
    node_index = 0
    for block_index, block in enumerate(parser.blocks):
        try:
            decoded = json.loads(block)
        except json.JSONDecodeError:
            continue
        for node in _iter_nodes(decoded):
            mapping = _first_type(node)
            if mapping is None:
                continue
            subject_kind, work_type = mapping
            native_id = _node_id(node, page_url, node_index)
            label = _label(node, native_id)
            source = source_block(
                source_id="public_web_schema_org",
                snapshot_id=snapshot_id,
                record_native_id=native_id,
                observed_at=observed_at or retrieved_at,
                retrieved_at=retrieved_at,
                terms_revision=terms_revision,
                rights_state=rights_state,
                payload=html,
            )
            identifiers = [
                identifier(
                    scheme="page_url",
                    value=native_id if native_id.startswith("http") else page_url,
                    scope="source",
                    stability="unknown",
                    uniqueness="unknown",
                    evidence=f"{page_url} JSON-LD node identity",
                )
            ]
            identifiers.extend(_same_as_identifiers(node, page_url))
            records.append(
                make_envelope(
                    source=source,
                    subject_kind=subject_kind,
                    subject_native_id=native_id,
                    label=label,
                    attributes=_compact_attributes(node, work_type),
                    identifiers=identifiers,
                    contributions=_contributors(node, page_url),
                    relationships=[],
                    evidence_items=[
                        evidence(
                            kind="literal_source_field",
                            locator=f"{page_url}#jsonld-{block_index}-{node_index}",
                            literal=label,
                            source_field="name|headline|title",
                        )
                    ],
                    raw_pointer=f"sha256:{digest}",
                )
            )
            node_index += 1
    return records
