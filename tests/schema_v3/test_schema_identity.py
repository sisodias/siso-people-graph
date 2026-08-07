import sqlite3
import unittest

from support import add_person, connect

class PeopleGraphV3IdentityTests(unittest.TestCase):
    def test_unique_identifiers_are_enforced_within_scope(self) -> None:
        con = connect(sample=True)
        # The sample assigns this global ORCID to entity A. The same accepted,
        # globally unique identifier cannot also be assigned to entity B.
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO entity_identifier
                   (entity_identifier_id,entity_id,scheme_id,value,
                    normalized_value,scope_type,scope_ref,stability,uniqueness,
                    source_observation_id,status,valid_from,valid_to)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "eid:duplicate-orcid",
                    "pg:01H-PERSON-B",
                    "orcid",
                    "0000-0002-1825-0097",
                    "0000-0002-1825-0097",
                    "global",
                    "",
                    "stable",
                    "unique",
                    "obs:fixture-b:author-9",
                    "accepted",
                    "2026-08-05",
                    None,
                ),
            )

        # Mutable/non-unique aliases may collide and therefore cannot imply an
        # automatic merge.
        for suffix, entity_id, observation_id in (
            ("a", "pg:01H-PERSON-A", "obs:fixture-a:author-1"),
            ("b", "pg:01H-PERSON-B", "obs:fixture-b:author-9"),
        ):
            con.execute(
                """INSERT INTO entity_identifier
                   (entity_identifier_id,entity_id,scheme_id,value,
                    normalized_value,scope_type,scope_ref,stability,uniqueness,
                    source_observation_id,status,valid_from,valid_to)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    f"eid:login:{suffix}",
                    entity_id,
                    "github_login",
                    "shared-label",
                    "shared-label",
                    "source",
                    "github",
                    "mutable",
                    "non_unique",
                    observation_id,
                    "accepted",
                    "2026-08-05",
                    None,
                ),
            )
        self.assertEqual(
            con.execute(
                "SELECT COUNT(*) FROM entity_identifier "
                "WHERE scheme_id='github_login' AND normalized_value='shared-label'"
            ).fetchone()[0],
            2,
        )
        con.close()


    def test_conflicting_stable_ids_block_identity_acceptance(self) -> None:
        con = connect(sample=True)
        add_person(con, "pg:01H-PERSON-C", "obs:test:c", "person-c", "Case C")
        add_person(con, "pg:01H-PERSON-D", "obs:test:d", "person-d", "Case D")

        for suffix, entity_id, observation_id, value in (
            ("c", "pg:01H-PERSON-C", "obs:test:c", "0000-0001-0000-0001"),
            ("d", "pg:01H-PERSON-D", "obs:test:d", "0000-0001-0000-0002"),
        ):
            con.execute(
                """INSERT INTO entity_identifier
                   (entity_identifier_id,entity_id,scheme_id,value,
                    normalized_value,scope_type,scope_ref,stability,uniqueness,
                    source_observation_id,status,valid_from,valid_to)
                   VALUES (?,?,?,?,?,'global','','stable','unique',?,'accepted',
                           '2026-08-05',NULL)""",
                (f"eid:orcid:{suffix}", entity_id, "orcid", value, value, observation_id),
            )

        con.execute(
            """INSERT INTO identity_candidate
               (candidate_id,entity_a,entity_b,method_name,method_version,
                confidence,review_state,conflict_summary,created_at,created_by,
                rights_state,publication_state)
               VALUES ('candidate:c-d','pg:01H-PERSON-C','pg:01H-PERSON-D',
                       'name_only','1',0.4,'in_review','different ORCIDs',
                       '2026-08-06T02:10:00Z','schema-test',
                       'public_metadata','internal')"""
        )
        con.execute(
            """INSERT INTO identity_conflict
               (conflict_id,candidate_id,conflict_type,left_identifier_id,
                right_identifier_id,description,status,created_at)
               VALUES ('conflict:c-d','candidate:c-d','conflicting_unique_id',
                       'eid:orcid:c','eid:orcid:d','Distinct stable ORCIDs',
                       'open','2026-08-06T02:11:00Z')"""
        )

        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO identity_decision
                   (decision_id,candidate_id,decision,decision_evidence_id,
                    decided_by,decided_at,rationale,supersedes_decision_id,
                    rights_state,publication_state)
                   VALUES ('decision:c-d','candidate:c-d','accepted',
                           'ev:manual-identity','schema-test',
                           '2026-08-06T02:12:00Z','should be blocked',NULL,
                           'public_metadata','internal')"""
            )

        con.execute(
            "UPDATE identity_conflict SET status='resolved', "
            "resolved_at='2026-08-06T02:13:00Z', "
            "resolution_note='fixture conflict adjudicated' "
            "WHERE conflict_id='conflict:c-d'"
        )
        con.execute(
            """INSERT INTO identity_decision
               (decision_id,candidate_id,decision,decision_evidence_id,
                decided_by,decided_at,rationale,supersedes_decision_id,
                rights_state,publication_state)
               VALUES ('decision:c-d','candidate:c-d','accepted',
                       'ev:manual-identity','schema-test',
                       '2026-08-06T02:14:00Z','accepted after explicit resolution',
                       NULL,'public_metadata','internal')"""
        )
        self.assertEqual(
            con.execute(
                "SELECT decision FROM identity_decision WHERE decision_id='decision:c-d'"
            ).fetchone()[0],
            "accepted",
        )
        con.close()


    def test_identity_merge_can_be_reversed_without_losing_sources(self) -> None:
        con = connect(sample=True)
        source_count = con.execute("SELECT COUNT(*) FROM source_observation").fetchone()[0]
        self.assertEqual(
            con.execute(
                "SELECT COUNT(*) FROM entity_redirect WHERE valid_to IS NULL"
            ).fetchone()[0],
            1,
        )

        # Undo is a transaction: append a revocation decision, close derived
        # memberships/redirects, and reactivate the redirected entity.
        con.execute("BEGIN")
        con.execute(
            """INSERT INTO identity_decision
               (decision_id,candidate_id,decision,decision_evidence_id,
                decided_by,decided_at,rationale,supersedes_decision_id,
                rights_state,publication_state)
               VALUES ('identity-decision:zoe-revoke','identity-candidate:zoe',
                       'revoked','ev:manual-identity','fixture-reviewer',
                       '2026-08-06T03:00:00Z','fixture undo',
                       'identity-decision:zoe-accept','public_metadata','internal')"""
        )
        con.execute(
            "UPDATE identity_cluster_membership "
            "SET valid_to='2026-08-06T03:00:00Z' "
            "WHERE cluster_id='cluster:zoe' AND valid_to IS NULL"
        )
        con.execute(
            "UPDATE entity_redirect SET valid_to='2026-08-06T03:00:00Z' "
            "WHERE redirect_id='redirect:zoe-b-a' AND valid_to IS NULL"
        )
        con.execute("UPDATE identity_cluster SET status='revoked' WHERE cluster_id='cluster:zoe'")
        con.execute("UPDATE entity SET status='active' WHERE entity_id='pg:01H-PERSON-B'")
        con.commit()

        self.assertEqual(
            con.execute(
                "SELECT COUNT(*) FROM entity_redirect WHERE valid_to IS NULL"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            con.execute(
                "SELECT COUNT(*) FROM identity_cluster_membership WHERE valid_to IS NULL"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            con.execute("SELECT COUNT(*) FROM source_observation").fetchone()[0],
            source_count,
        )
        self.assertEqual(
            con.execute(
                "SELECT COUNT(*) FROM entity WHERE entity_id IN "
                "('pg:01H-PERSON-A','pg:01H-PERSON-B')"
            ).fetchone()[0],
            2,
        )
        con.close()
