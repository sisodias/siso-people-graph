"""Pretalx-compatible public conference schedule adapter."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from sources.creators.envelope import evidence, identifier, make_envelope, payload_sha256
from sources.media.common import SourceContext, agent, contribution, first_text, relationship
from sources.media.policies import SOURCE_POLICIES

_POLICY = SOURCE_POLICIES["pretalx_schedule"]
TERMS_REVISION = _POLICY["terms_revision"]


def _events(conference: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    days = conference.get("days", [])
    if not isinstance(days, list):
        return
    for day in days:
        if not isinstance(day, Mapping):
            continue
        rooms = day.get("rooms", {})
        if not isinstance(rooms, Mapping):
            continue
        for room_name, values in rooms.items():
            if not isinstance(values, list):
                continue
            for event in values:
                if isinstance(event, Mapping):
                    yield str(room_name), event


def adapt_pretalx_schedule(
    *,
    payload: Mapping[str, Any],
    endpoint: str,
    retrieved_at: str,
    rights_state: str = "discovery_only",
) -> list[dict[str, Any]]:
    schedule = payload.get("schedule") if isinstance(payload.get("schedule"), Mapping) else payload
    conference = schedule.get("conference") if isinstance(schedule.get("conference"), Mapping) else schedule
    conference_id = first_text(
        conference.get("acronym"),
        conference.get("slug"),
        conference.get("title"),
        default=endpoint,
    )
    conference_title = first_text(conference.get("title"), default=conference_id)
    digest = payload_sha256(payload)
    context = SourceContext(
        source_id="pretalx_schedule",
        snapshot_id=f"sha256:{digest}",
        observed_at=retrieved_at,
        retrieved_at=retrieved_at,
        terms_revision=TERMS_REVISION,
        rights_state=rights_state,
        raw_pointer=endpoint,
    )
    records: list[dict[str, Any]] = []
    for room_name, event in _events(conference):
        event_id = first_text(event.get("guid"), event.get("id"), event.get("slug"))
        if not event_id:
            continue
        title = first_text(event.get("title"), default=event_id)
        ids = [
            identifier(
                scheme="pretalx_event_id",
                value=event_id,
                scope="source",
                stability="stable",
                uniqueness="unique",
                evidence=f"{endpoint} event.guid|id",
            )
        ]
        event_url = first_text(event.get("url"))
        if event_url:
            ids.append(
                identifier(
                    scheme="event_url",
                    value=event_url,
                    scope="global",
                    stability="unknown",
                    uniqueness="unknown",
                    evidence=f"{endpoint} event.url",
                )
            )
        contributors: list[dict[str, Any]] = []
        persons = event.get("persons", [])
        if isinstance(persons, list):
            for index, person in enumerate(persons):
                if not isinstance(person, Mapping):
                    continue
                label = first_text(person.get("public_name"), person.get("name"))
                if not label:
                    continue
                person_id = first_text(person.get("code"), person.get("id"), default=f"{event_id}#speaker-{index}")
                person_ids = []
                if person.get("code") or person.get("id"):
                    person_ids.append(
                        identifier(
                            scheme="pretalx_speaker_id",
                            value=person_id,
                            scope="source",
                            stability="stable",
                            uniqueness="unique",
                            evidence=f"{endpoint} event.persons[{index}].code|id",
                        )
                    )
                links = person.get("links", [])
                if isinstance(links, list):
                    for link_index, link in enumerate(links):
                        url = link.get("url") if isinstance(link, Mapping) else None
                        if url:
                            person_ids.append(
                                identifier(
                                    scheme="same_as_url",
                                    value=str(url),
                                    scope="global",
                                    stability="unknown",
                                    uniqueness="unknown",
                                    evidence=f"{endpoint} event.persons[{index}].links[{link_index}]",
                                )
                            )
                contributors.append(
                    contribution(
                        role="speaker",
                        agent_record=agent(
                            source_native_id=person_id,
                            label=label,
                            identifiers=person_ids,
                        ),
                        evidence=f"{endpoint} event.persons[{index}]",
                        order=index + 1,
                        identity_evidence="explicit_link" if len(person_ids) > 1 else "source_native",
                    )
                )
        relationships = [
            relationship(
                predicate="part_of",
                object_kind="event",
                object_native_id=conference_id,
                object_label=conference_title,
                evidence=f"{endpoint} schedule.conference",
            )
        ]
        if room_name:
            relationships.append(
                relationship(
                    predicate="held_at",
                    object_kind="venue",
                    object_native_id=f"{conference_id}:room:{room_name}",
                    object_label=room_name,
                    evidence=f"{endpoint} day.rooms[{room_name!r}]",
                    valid_at=first_text(event.get("date"), event.get("start")) or None,
                )
            )
        records.append(
            make_envelope(
                source=context.block(event_id, event),
                subject_kind="event",
                subject_native_id=event_id,
                label=title,
                attributes={
                    "work_type": "conference_talk",
                    "conference": conference_title,
                    "date": event.get("date"),
                    "start": event.get("start"),
                    "duration": event.get("duration"),
                    "language": event.get("language"),
                    "track": event.get("track"),
                    "session_type": event.get("type"),
                    "abstract_persisted": False,
                    "description_persisted": False,
                    "recording_persisted": False,
                },
                identifiers=ids,
                contributions=contributors,
                relationships=relationships,
                evidence_items=[
                    evidence(
                        kind="literal_source_field",
                        locator=f"{endpoint}#event-{event_id}",
                        literal=title,
                        source_field="event.title",
                    )
                ],
                raw_pointer=endpoint,
            )
        )
    return records
