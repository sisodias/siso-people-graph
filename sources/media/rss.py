"""Open RSS/Atom and Podcasting 2.0 observation adapter."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from sources.creators.envelope import evidence, identifier, make_envelope, payload_sha256
from sources.media.common import SourceContext, agent, contribution, first_text, relationship
from sources.media.policies import SOURCE_POLICIES

_POLICY = SOURCE_POLICIES["podcast_rss"]

PODCAST_NS = "https://podcastindex.org/namespace/1.0"
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"


def _text(parent: ET.Element, *tags: str) -> str:
    for tag in tags:
        node = parent.find(tag)
        if node is not None and node.text and node.text.strip():
            return node.text.strip()
    return ""


def _link(parent: ET.Element) -> str:
    value = _text(parent, "link", f"{{{ATOM_NS}}}link")
    if value:
        return value
    for node in parent.findall(f"{{{ATOM_NS}}}link"):
        href = node.attrib.get("href", "").strip()
        if href:
            return href
    return ""


def _persons(parent: ET.Element, locator: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, node in enumerate(parent.findall(f"{{{PODCAST_NS}}}person")):
        label = (node.text or "").strip()
        if not label:
            continue
        role = node.attrib.get("role", "host").strip().lower() or "host"
        href = node.attrib.get("href", "").strip()
        person_id = href or f"label:{label}"
        identifiers: list[dict[str, Any]] = []
        if href:
            identifiers.append(
                identifier(
                    scheme="official_website",
                    value=href,
                    scope="global",
                    stability="unknown",
                    uniqueness="unknown",
                    evidence=f"{locator} podcast:person[{index}]@href",
                )
            )
        results.append(
            contribution(
                role=role,
                agent_record=agent(
                    source_native_id=person_id,
                    label=label,
                    identifiers=identifiers,
                ),
                evidence=f"{locator} podcast:person[{index}]",
                order=index + 1,
                identity_evidence="explicit_link" if href else "name_only",
            )
        )
    return results


def _fallback_author(parent: ET.Element, locator: str, role: str) -> list[dict[str, Any]]:
    label = _text(parent, f"{{{ITUNES_NS}}}author", "author", "managingEditor")
    if not label:
        return []
    return [
        contribution(
            role=role,
            agent_record=agent(source_native_id=f"label:{label}", label=label),
            evidence=f"{locator} author field",
            identity_evidence="name_only",
        )
    ]


def _transcript_relationships(item: ET.Element, locator: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, node in enumerate(item.findall(f"{{{PODCAST_NS}}}transcript")):
        url = node.attrib.get("url", "").strip()
        if not url:
            continue
        results.append(
            {
                "predicate": "has_transcript_pointer",
                "object": {
                    "kind": "work",
                    "source_native_id": url,
                    "label": node.attrib.get("type", "transcript"),
                    "attributes": {
                        "media_type": node.attrib.get("type"),
                        "language": node.attrib.get("language"),
                        "rel": node.attrib.get("rel"),
                        "rights_gate": "not_acquired",
                    },
                },
                "evidence": f"{locator} podcast:transcript[{index}]",
            }
        )
    return results


def adapt_rss(
    *,
    xml_text: str,
    feed_url: str,
    retrieved_at: str,
    observed_at: str | None = None,
    terms_revision: str = _POLICY["terms_revision"],
    rights_state: str = _POLICY["rights_state_default"],
) -> list[dict[str, Any]]:
    """Emit show and episode observations from one supplied RSS/Atom payload."""

    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None and root.tag.endswith("feed"):
        channel = root
    if channel is None:
        raise ValueError("RSS/Atom payload has no channel/feed element")

    digest = payload_sha256(xml_text)
    context = SourceContext(
        source_id="podcast_rss",
        snapshot_id=f"sha256:{digest}",
        observed_at=observed_at or retrieved_at,
        retrieved_at=retrieved_at,
        terms_revision=terms_revision,
        rights_state=rights_state,
        raw_pointer=f"sha256:{digest}",
    )
    show_guid = _text(channel, f"{{{PODCAST_NS}}}guid")
    show_native_id = show_guid or feed_url
    show_title = first_text(_text(channel, "title"), default=show_native_id)
    show_identifiers = [
        identifier(
            scheme="rss_feed_url",
            value=feed_url,
            scope="source",
            stability="mutable",
            uniqueness="unique",
            evidence=f"feed locator {feed_url}",
        )
    ]
    if show_guid:
        show_identifiers.append(
            identifier(
                scheme="podcast_guid",
                value=show_guid,
                scope="global",
                stability="stable",
                uniqueness="unique",
                evidence=f"{feed_url} channel podcast:guid",
            )
        )
    show_link = _link(channel)
    if show_link:
        show_identifiers.append(
            identifier(
                scheme="official_website",
                value=show_link,
                scope="global",
                stability="unknown",
                uniqueness="unknown",
                evidence=f"{feed_url} channel link",
            )
        )
    show_contributions = _persons(channel, f"{feed_url}#channel")
    if not show_contributions:
        show_contributions = _fallback_author(channel, f"{feed_url}#channel", "host")

    records: list[dict[str, Any]] = [
        make_envelope(
            source=context.block(show_native_id, xml_text),
            subject_kind="work",
            subject_native_id=show_native_id,
            label=show_title,
            attributes={
                "work_type": "podcast_show",
                "language": _text(channel, "language") or None,
                "publisher_description_present": bool(_text(channel, "description")),
                "feed_url": feed_url,
            },
            identifiers=show_identifiers,
            contributions=show_contributions,
            relationships=[],
            evidence_items=[
                evidence(
                    kind="literal_source_field",
                    locator=f"{feed_url}#channel/title",
                    literal=show_title,
                    source_field="channel/title",
                )
            ],
            raw_pointer=context.raw_pointer,
        )
    ]

    items = channel.findall("item")
    if not items and root.tag.endswith("feed"):
        items = channel.findall(f"{{{ATOM_NS}}}entry")
    for index, item in enumerate(items):
        item_locator = f"{feed_url}#item-{index}"
        episode_guid = _text(item, f"{{{PODCAST_NS}}}guid", "guid", f"{{{ATOM_NS}}}id")
        episode_link = _link(item)
        enclosure = item.find("enclosure")
        enclosure_url = enclosure.attrib.get("url", "").strip() if enclosure is not None else ""
        native_id = first_text(episode_guid, episode_link, enclosure_url, default=f"{show_native_id}:item:{index}")
        title = first_text(_text(item, "title", f"{{{ATOM_NS}}}title"), default=native_id)
        identifiers = []
        if episode_guid:
            identifiers.append(
                identifier(
                    scheme="rss_item_guid",
                    value=episode_guid,
                    scope="source",
                    stability="stable",
                    uniqueness="unique",
                    evidence=f"{item_locator} guid",
                )
            )
        if episode_link:
            identifiers.append(
                identifier(
                    scheme="episode_url",
                    value=episode_link,
                    scope="global",
                    stability="unknown",
                    uniqueness="unknown",
                    evidence=f"{item_locator} link",
                )
            )
        episode_people = _persons(item, item_locator)
        if not episode_people:
            # Per Podcasting 2.0, item-level person rows replace channel people;
            # absent rows fall back to regular show contributors, still with the
            # source evidence retained.
            episode_people = [dict(value) for value in show_contributions]
        relationships = [
            relationship(
                predicate="part_of",
                object_kind="work",
                object_native_id=show_native_id,
                object_label=show_title,
                evidence=f"{item_locator} parent channel",
            )
        ]
        relationships.extend(_transcript_relationships(item, item_locator))
        if enclosure_url:
            relationships.append(
                {
                    "predicate": "has_media_pointer",
                    "object": {
                        "kind": "work",
                        "source_native_id": enclosure_url,
                        "label": enclosure.attrib.get("type", "media") if enclosure is not None else "media",
                        "attributes": {
                            "length": enclosure.attrib.get("length") if enclosure is not None else None,
                            "rights_gate": "not_acquired",
                        },
                    },
                    "evidence": f"{item_locator} enclosure",
                }
            )
        published = _text(item, "pubDate", f"{{{ATOM_NS}}}published", f"{{{ATOM_NS}}}updated")
        records.append(
            make_envelope(
                source=context.block(native_id, xml_text),
                subject_kind="work",
                subject_native_id=native_id,
                label=title,
                attributes={
                    "work_type": "podcast_episode",
                    "published": published or None,
                    "episode_type": _text(item, f"{{{PODCAST_NS}}}episode") or None,
                    "description_present": bool(
                        _text(item, "description", f"{{{CONTENT_NS}}}encoded")
                    ),
                },
                identifiers=identifiers,
                contributions=episode_people,
                relationships=relationships,
                evidence_items=[
                    evidence(
                        kind="literal_source_field",
                        locator=f"{item_locator}/title",
                        literal=title,
                        source_field="item/title",
                    )
                ],
                raw_pointer=context.raw_pointer,
            )
        )
    return records
