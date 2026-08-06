"""Podcast Index API metadata mapper.

The API terms prohibit permanent database copies of returned third-party
content unless independently licensed.  This adapter therefore emits compact,
refreshable observations and points back to the API/feed; it never stores audio,
transcripts, descriptions, artwork or full response bodies in production.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from sources.creators.envelope import evidence, identifier, make_envelope, payload_sha256
from sources.media.common import SourceContext, agent, contribution, first_text, relationship
from sources.media.policies import SOURCE_POLICIES

_POLICY = SOURCE_POLICIES["podcast_index_api"]
TERMS_REVISION = _POLICY["terms_revision"]


def auth_headers(*, api_key: str, api_secret: str, unix_time: int, user_agent: str) -> dict[str, str]:
    """Build documented Podcast Index request headers without exposing credentials."""

    if not api_key or not api_secret or not user_agent:
        raise ValueError("api_key, api_secret and user_agent are required")
    stamp = str(int(unix_time))
    token = hashlib.sha1(f"{api_key}{api_secret}{stamp}".encode("utf-8")).hexdigest()
    return {
        "User-Agent": user_agent,
        "X-Auth-Key": api_key,
        "X-Auth-Date": stamp,
        "Authorization": token,
    }


def _context(payload: Mapping[str, Any], retrieved_at: str, endpoint: str) -> SourceContext:
    digest = payload_sha256(payload)
    observed = first_text(payload.get("status", {}).get("lastUpdate"), retrieved_at)
    return SourceContext(
        source_id="podcast_index_api",
        snapshot_id=f"sha256:{digest}",
        observed_at=observed,
        retrieved_at=retrieved_at,
        terms_revision=TERMS_REVISION,
        rights_state=_POLICY["rights_state_default"],
        raw_pointer=endpoint,
    )


def _feed_record(feed: Mapping[str, Any], context: SourceContext, endpoint: str) -> dict[str, Any]:
    feed_id = str(feed.get("id") or feed.get("podcastGuid") or feed.get("url") or "")
    if not feed_id:
        raise ValueError("Podcast Index feed row has no id/guid/url")
    title = first_text(feed.get("title"), feed.get("originalTitle"), default=feed_id)
    ids = [
        identifier(
            scheme="podcast_index_feed_id",
            value=feed_id,
            scope="source",
            stability="stable",
            uniqueness="unique",
            evidence=f"{endpoint} feed.id",
        )
    ]
    podcast_guid = first_text(feed.get("podcastGuid"), feed.get("guid"))
    if podcast_guid:
        ids.append(
            identifier(
                scheme="podcast_guid",
                value=podcast_guid,
                scope="global",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} feed.podcastGuid",
            )
        )
    feed_url = first_text(feed.get("url"), feed.get("newestItemPublishTime"))
    if feed.get("url"):
        ids.append(
            identifier(
                scheme="rss_feed_url",
                value=str(feed["url"]),
                scope="source",
                stability="mutable",
                uniqueness="unique",
                evidence=f"{endpoint} feed.url",
            )
        )
    website = first_text(feed.get("link"))
    if website:
        ids.append(
            identifier(
                scheme="official_website",
                value=website,
                scope="global",
                stability="unknown",
                uniqueness="unknown",
                evidence=f"{endpoint} feed.link",
            )
        )
    owner = first_text(feed.get("ownerName"), feed.get("author"))
    contributions = []
    if owner:
        contributions.append(
            contribution(
                role="publisher",
                agent_record=agent(source_native_id=f"label:{owner}", label=owner),
                evidence=f"{endpoint} ownerName/author",
                identity_evidence="name_only",
            )
        )
    return make_envelope(
        source=context.block(feed_id, feed),
        subject_kind="work",
        subject_native_id=feed_id,
        label=title,
        attributes={
            "work_type": "podcast_show",
            "language": feed.get("language"),
            "dead": bool(feed.get("dead")),
            "last_update_time": feed.get("lastUpdateTime"),
            "retention_boundary": "response cache headers / independent publisher feed",
            "descriptions_persisted": False,
        },
        identifiers=ids,
        contributions=contributions,
        relationships=[],
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#feed-{feed_id}",
                literal=title,
                source_field="feed.title",
            )
        ],
        raw_pointer=endpoint,
    )


def _episode_people(episode: Mapping[str, Any], endpoint: str) -> list[dict[str, Any]]:
    people = episode.get("persons") or episode.get("people") or []
    if not isinstance(people, list):
        return []
    rows: list[dict[str, Any]] = []
    for index, person in enumerate(people):
        if not isinstance(person, Mapping):
            continue
        label = first_text(person.get("name"))
        if not label:
            continue
        href = first_text(person.get("href"))
        person_id = first_text(person.get("id"), href, default=f"label:{label}")
        identifiers = []
        if href:
            identifiers.append(
                identifier(
                    scheme="official_website",
                    value=href,
                    scope="global",
                    stability="unknown",
                    uniqueness="unknown",
                    evidence=f"{endpoint} episode.persons[{index}].href",
                )
            )
        rows.append(
            contribution(
                role=first_text(person.get("role"), default="guest").lower(),
                agent_record=agent(
                    source_native_id=person_id,
                    label=label,
                    identifiers=identifiers,
                ),
                evidence=f"{endpoint} episode.persons[{index}]",
                order=index + 1,
                identity_evidence="explicit_link" if href else "name_only",
            )
        )
    return rows


def _episode_record(
    episode: Mapping[str, Any], context: SourceContext, endpoint: str
) -> dict[str, Any]:
    episode_id = str(episode.get("id") or episode.get("guid") or episode.get("enclosureUrl") or "")
    if not episode_id:
        raise ValueError("Podcast Index episode row has no id/guid/enclosureUrl")
    title = first_text(episode.get("title"), default=episode_id)
    ids = [
        identifier(
            scheme="podcast_index_episode_id",
            value=episode_id,
            scope="source",
            stability="stable",
            uniqueness="unique",
            evidence=f"{endpoint} episode.id",
        )
    ]
    guid = first_text(episode.get("guid"))
    if guid and guid != episode_id:
        ids.append(
            identifier(
                scheme="rss_item_guid",
                value=guid,
                scope="source",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} episode.guid",
            )
        )
    feed_id = str(episode.get("feedId") or "")
    relationships = []
    if feed_id:
        relationships.append(
            relationship(
                predicate="part_of",
                object_kind="work",
                object_native_id=feed_id,
                object_label=first_text(episode.get("feedTitle"), default=feed_id),
                evidence=f"{endpoint} episode.feedId",
            )
        )
    transcript_url = first_text(episode.get("transcriptUrl"))
    if transcript_url:
        relationships.append(
            {
                "predicate": "has_transcript_pointer",
                "object": {
                    "kind": "work",
                    "source_native_id": transcript_url,
                    "label": "transcript",
                    "attributes": {"rights_gate": "not_acquired"},
                },
                "evidence": f"{endpoint} episode.transcriptUrl",
            }
        )
    return make_envelope(
        source=context.block(episode_id, episode),
        subject_kind="work",
        subject_native_id=episode_id,
        label=title,
        attributes={
            "work_type": "podcast_episode",
            "date_published": episode.get("datePublished"),
            "duration": episode.get("duration"),
            "explicit": episode.get("explicit"),
            "retention_boundary": "response cache headers / independent publisher feed",
            "descriptions_persisted": False,
            "media_persisted": False,
        },
        identifiers=ids,
        contributions=_episode_people(episode, endpoint),
        relationships=relationships,
        evidence_items=[
            evidence(
                kind="literal_source_field",
                locator=f"{endpoint}#episode-{episode_id}",
                literal=title,
                source_field="episode.title",
            )
        ],
        raw_pointer=endpoint,
    )


def adapt_response(
    *,
    payload: Mapping[str, Any],
    endpoint: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Map a previously fetched API response; no network access is performed."""

    context = _context(payload, retrieved_at, endpoint)
    records: list[dict[str, Any]] = []
    feeds: Sequence[Any] = payload.get("feeds") or payload.get("feed") or []
    if isinstance(feeds, Mapping):
        feeds = [feeds]
    for feed in feeds:
        if isinstance(feed, Mapping):
            records.append(_feed_record(feed, context, endpoint))
    episodes: Sequence[Any] = payload.get("items") or payload.get("episodes") or []
    if isinstance(episodes, Mapping):
        episodes = [episodes]
    for episode in episodes:
        if isinstance(episode, Mapping):
            records.append(_episode_record(episode, context, endpoint))
    return records
