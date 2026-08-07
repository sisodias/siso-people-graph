from __future__ import annotations

import json
import unittest
from pathlib import Path

from sources.creators.bridges import propose_bridges
from sources.creators.envelope import validate_envelope
from sources.media.pilot import fixture_observations
from sources.media.podcast_index import auth_headers
from sources.media.policies import SOURCE_POLICIES, validate_source_policy

FIXTURES = Path(__file__).parent / "fixtures"
RETRIEVED_AT = "2026-08-06T15:00:00Z"


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = fixture_observations(FIXTURES, RETRIEVED_AT)

    def test_all_fixture_adapters_emit_valid_envelopes(self) -> None:
        self.assertEqual(16, len(self.records))
        for record in self.records:
            validate_envelope(record)

    def test_distinct_work_and_event_types_survive(self) -> None:
        types = {
            record["subject"]["attributes"].get("work_type")
            for record in self.records
        }
        self.assertTrue(
            {
                "podcast_show",
                "podcast_episode",
                "youtube_video",
                "book",
                "book_edition",
                "conference_talk",
                "article",
                "openreview_article",
            }.issubset(types)
        )

    def test_unlicensed_payloads_are_not_persisted(self) -> None:
        serialized = json.dumps(self.records).lower()
        self.assertNotIn("not persisted by the adapter", serialized)
        self.assertNotIn("abstract_inverted_index", serialized)
        self.assertNotIn("subscribercount", serialized)
        self.assertNotIn("viewcount", serialized)
        transcript_edges = [
            edge
            for record in self.records
            for edge in record["relationships"]
            if edge["predicate"] == "has_transcript_pointer"
        ]
        self.assertGreaterEqual(len(transcript_edges), 2)
        self.assertTrue(
            all(edge["object"]["attributes"]["rights_gate"] == "not_acquired" for edge in transcript_edges)
        )

    def test_jsonld_contributor_same_as_is_bridge_evidence(self) -> None:
        article = next(
            record
            for record in self.records
            if record["subject"]["label"] == "Evidence before identity"
        )
        actor = article["contributions"][0]["agent"]
        self.assertEqual(
            "https://profiles.example.test/alex-rivera",
            actor["identifiers"][0]["value"],
        )
        self.assertEqual("same_as_url", actor["identifiers"][0]["scheme"])

    def test_youtube_channel_is_an_account_not_a_person(self) -> None:
        channels = [
            record
            for record in self.records
            if record["subject"]["attributes"].get("account_type") == "youtube_channel"
        ]
        self.assertEqual(1, len(channels))
        self.assertEqual("account", channels[0]["subject"]["kind"])
        handle = next(item for item in channels[0]["identifiers"] if item["scheme"] == "youtube_handle")
        self.assertEqual("source", handle["scope"])
        self.assertEqual("mutable", handle["stability"])

    def test_bridge_queue_uses_authority_or_explicit_links_only(self) -> None:
        candidates = propose_bridges(self.records)
        self.assertEqual(4, len(candidates))
        self.assertEqual(1, sum(item["strength"] == "strong" for item in candidates))
        self.assertTrue(all(not item["automatic_acceptance"] for item in candidates))
        signal_types = {item["signal"]["type"] for item in candidates}
        self.assertEqual(
            {"shared_authority_identifier", "shared_explicit_link"},
            signal_types,
        )
        serialized = json.dumps(candidates)
        self.assertNotIn('"scheme": "name"', serialized)
        for candidate in candidates:
            for receipt in candidate["positive_evidence"]:
                self.assertTrue(receipt["source_record"])
                self.assertTrue(receipt["identifier"]["evidence"])

    def test_every_fixture_source_has_refresh_and_removal_policy(self) -> None:
        fixture_sources = {record["source"]["source_id"] for record in self.records}
        self.assertEqual(set(), fixture_sources.difference(SOURCE_POLICIES))
        for source_id in fixture_sources:
            policy = SOURCE_POLICIES[source_id]
            validate_source_policy(policy)
            self.assertTrue(policy["refresh_rule"])
            self.assertTrue(policy["deletion_update_method"])
            self.assertTrue(policy["retention_boundary"])

    def test_podcast_index_auth_matches_documented_sha1_recipe(self) -> None:
        headers = auth_headers(
            api_key="key",
            api_secret="secret",
            unix_time=1700000000,
            user_agent="siso-people-graph-test/0.1",
        )
        self.assertEqual("key", headers["X-Auth-Key"])
        self.assertEqual("1700000000", headers["X-Auth-Date"])
        self.assertEqual(40, len(headers["Authorization"]))


if __name__ == "__main__":
    unittest.main()
