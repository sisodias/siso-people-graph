import json
import sqlite3
import unittest

from support import connect, digest

class PeopleGraphV3WorkProjectionTests(unittest.TestCase):
    def test_work_subtypes_roles_versions_citations_and_dependencies(self) -> None:
        con = connect(sample=True)
        row = con.execute(
            """SELECT w.title,wv.version_type,wv.version_label,c.role,c.ordinal
               FROM contribution c
               JOIN work w ON w.work_id=c.work_id
               JOIN work_version wv ON wv.work_version_id=c.work_version_id
               WHERE c.contribution_id='contrib:zoe-work-a'"""
        ).fetchone()
        self.assertEqual(
            row,
            ("Evidence Graphs in Practice", "edition", "1", "author", 1),
        )
        self.assertEqual(con.execute("SELECT COUNT(*) FROM citation").fetchone()[0], 1)
        self.assertEqual(
            con.execute("SELECT COUNT(*) FROM work_dependency").fetchone()[0],
            1,
        )

        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO work
                   (work_id,work_type,title,original_language,
                    source_observation_id,rights_state,privacy_state,
                    publication_state,created_at)
                   VALUES ('pg:01H-ORG-A','article','Not a Work','en',
                           'obs:fixture-a:org-1','open_data','public','public',
                           '2026-08-06')"""
            )
        con.close()


    def test_vocabularies_remain_namespaced_and_crosswalks_explicit(self) -> None:
        con = connect(sample=True)
        # Same source-local token is legal in another namespace.
        con.execute(
            """INSERT INTO vocabulary_term
               (term_id,vocabulary_id,source_local_id,label,description,
                source_observation_id)
               VALUES ('term:curated:concept-1','vocab:curated-topics','concept-1',
                       'Different curated meaning','fixture',
                       'obs:fixture-a:concept-1')"""
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO vocabulary_term
                   (term_id,vocabulary_id,source_local_id,label,description,
                    source_observation_id)
                   VALUES ('term:fixture:duplicate','vocab:fixture-topics',
                           'concept-1','Duplicate','fixture',
                           'obs:fixture-a:concept-1')"""
            )
        self.assertEqual(
            con.execute("SELECT COUNT(*) FROM term_crosswalk").fetchone()[0],
            1,
        )
        con.close()


    def test_model_output_is_explicit_and_not_source_evidence(self) -> None:
        con = connect(sample=True)
        row = con.execute(
            """SELECT a.status,e.evidence_kind,e.generated_by_model,
                      e.model_name,e.model_version
               FROM assertion a
               JOIN evidence e ON e.evidence_id=a.primary_evidence_id
               WHERE a.assertion_id='assertion:zoe-topic-model'"""
        ).fetchone()
        self.assertEqual(row, ("proposed", "model_output", 1, "fixture-classifier", "0.1"))

        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO evidence
                   (evidence_id,observation_id,evidence_kind,locator,excerpt,
                    excerpt_sha256,observed_at,extraction_method,model_name,
                    model_version,input_sha256,generated_by_model,rights_state,
                    privacy_state,publication_state)
                   VALUES ('ev:bad-model','obs:fixture-a:author-1',
                           'source_record','fixture://bad',NULL,NULL,'2026-08-06',
                           'model','bad','1',?,1,'open_data','public','internal')""",
                (digest("bad-model-input"),),
            )
        con.close()


    def test_projections_are_named_versioned_scoped_and_uncertain(self) -> None:
        con = connect(sample=True)
        row = con.execute(
            """SELECT d.name,d.version,r.as_of,r.source_scope_json,
                      v.metric_name,v.value_json,v.uncertainty_json
               FROM projection_value v
               JOIN projection_run r
                 ON r.projection_run_id=v.projection_run_id
               JOIN projection_definition d
                 ON d.projection_definition_id=r.projection_definition_id"""
        ).fetchone()
        self.assertEqual(row[0:3], ("fixture-topic-affinity", "0.1", "2026-08-06T00:00:00Z"))
        self.assertIn("snapshots", json.loads(row[3]))
        self.assertEqual(row[4], "topic_affinity")
        self.assertIn("value", json.loads(row[5]))
        self.assertIn("low", json.loads(row[6]))

        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """INSERT INTO projection_definition
                   (projection_definition_id,name,version,purpose,
                    output_semantics,method_card_uri,method_sha256,created_at)
                   VALUES ('projection:def:duplicate','fixture-topic-affinity',
                           '0.1','duplicate','duplicate','fixture://method',?,
                           '2026-08-06')""",
                (digest("duplicate-method"),),
            )
        con.close()
