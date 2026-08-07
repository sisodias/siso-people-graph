"""YouTube Data API channel/video metadata mapper.

The adapter is intentionally source-separated.  Channel IDs identify YouTube
accounts, not humans; channel titles, custom URLs and handles are aliases.  No
cross-platform score, inferred demographic, transcript, media file or canonical
person identity is produced.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from sources.creators.envelope import evidence, identifier, make_envelope, payload_sha256
from sources.media.common import SourceContext, agent, contribution, first_text, relationship
from sources.media.policies import SOURCE_POLICIES

_POLICY = SOURCE_POLICIES["youtube_data_api"]
TERMS_REVISION = _POLICY["terms_revision"]


def _context(payload: Mapping[str, Any], endpoint: str, retrieved_at: str) -> SourceContext:
    digest = payload_sha256(payload)
    return SourceContext(
        source_id="youtube_data_api",
        snapshot_id=f"sha256:{digest}",
        observed_at=retrieved_at,
        retrieved_at=retrieved_at,
        terms_revision=TERMS_REVISION,
        rights_state=_POLICY["rights_state_default"],
        raw_pointer=endpoint,
    )


def _items(payload: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    value = payload.get("items", [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def adapt_channels(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> list[dict[str, Any]]:
    context = _context(payload, endpoint, retrieved_at)
    records: list[dict[str, Any]] = []
    for item in _items(payload):
        channel_id = str(item.get("id") or "")
        if not channel_id:
            continue
        snippet = item.get("snippet") if isinstance(item.get("snippet"), Mapping) else {}
        title = first_text(snippet.get("title"), default=channel_id)
        ids = [
            identifier(
                scheme="youtube_channel_id",
                value=channel_id,
                scope="source",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} items[].id",
            )
        ]
        custom_url = first_text(snippet.get("customUrl"))
        if custom_url:
            ids.append(
                identifier(
                    scheme="youtube_handle",
                    value=custom_url,
                    scope="source",
                    stability="mutable",
                    uniqueness="unique",
                    evidence=f"{endpoint} items[{channel_id}].snippet.customUrl",
                )
            )
        records.append(
            make_envelope(
                source=context.block(channel_id, item),
                subject_kind="account",
                subject_native_id=channel_id,
                label=title,
                attributes={
                    "account_type": "youtube_channel",
                    "published_at": snippet.get("publishedAt"),
                    "country": snippet.get("country"),
                    "etag": item.get("etag"),
                    "refresh_required_days": 30,
                    "description_persisted": False,
                    "statistics_persisted": False,
                    "identity_boundary": "channel account; not asserted as a human",
                },
                identifiers=ids,
                contributions=[],
                relationships=[],
                evidence_items=[
                    evidence(
                        kind="literal_source_field",
                        locator=f"{endpoint}#channel-{channel_id}",
                        literal=title,
                        source_field="snippet.title",
                    )
                ],
                raw_pointer=endpoint,
            )
        )
    return records


def adapt_videos(
    *, payload: Mapping[str, Any], endpoint: str, retrieved_at: str
) -> list[dict[str, Any]]:
    context = _context(payload, endpoint, retrieved_at)
    records: list[dict[str, Any]] = []
    for item in _items(payload):
        video_id = str(item.get("id") or "")
        if not video_id:
            continue
        snippet = item.get("snippet") if isinstance(item.get("snippet"), Mapping) else {}
        content = item.get("contentDetails") if isinstance(item.get("contentDetails"), Mapping) else {}
        status = item.get("status") if isinstance(item.get("status"), Mapping) else {}
        title = first_text(snippet.get("title"), default=video_id)
        channel_id = first_text(snippet.get("channelId"))
        channel_title = first_text(snippet.get("channelTitle"), default=channel_id)
        contributions = []
        relationships = []
        if channel_id:
            account_record = agent(
                source_native_id=channel_id,
                label=channel_title or channel_id,
                kind="account",
                identifiers=[
                    identifier(
                        scheme="youtube_channel_id",
                        value=channel_id,
                        scope="source",
                        stability="stable",
                        uniqueness="unique",
                        evidence=f"{endpoint} items[{video_id}].snippet.channelId",
                    )
                ],
            )
            contributions.append(
                contribution(
                    role="publisher_account",
                    agent_record=account_record,
                    evidence=f"{endpoint} items[{video_id}].snippet.channelId",
                    identity_evidence="source_native_account",
                )
            )
            relationships.append(
                relationship(
                    predicate="published_by",
                    object_kind="account",
                    object_native_id=channel_id,
                    object_label=channel_title or channel_id,
                    evidence=f"{endpoint} items[{video_id}].snippet.channelId",
                )
            )
        records.append(
            make_envelope(
                source=context.block(video_id, item),
                subject_kind="work",
                subject_native_id=video_id,
                label=title,
                attributes={
                    "work_type": "youtube_video",
                    "published_at": snippet.get("publishedAt"),
                    "duration": content.get("duration"),
                    "category_id": snippet.get("categoryId"),
                    "default_language": snippet.get("defaultLanguage"),
                    "privacy_status": status.get("privacyStatus"),
                    "contains_synthetic_media": status.get("containsSyntheticMedia"),
                    "etag": item.get("etag"),
                    "refresh_required_days": 30,
                    "description_persisted": False,
                    "tags_persisted": False,
                    "statistics_persisted": False,
                    "transcript_persisted": False,
                    "media_persisted": False,
                },
                identifiers=[
                    identifier(
                        scheme="youtube_video_id",
                        value=video_id,
                        scope="source",
                        stability="stable",
                        uniqueness="unique",
                        evidence=f"{endpoint} items[].id",
                    )
                ],
                contributions=contributions,
                relationships=relationships,
                evidence_items=[
                    evidence(
                        kind="literal_source_field",
                        locator=f"{endpoint}#video-{video_id}",
                        literal=title,
                        source_field="snippet.title",
                    )
                ],
                raw_pointer=endpoint,
            )
        )
    return records
