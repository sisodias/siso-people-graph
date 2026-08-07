import contextlib
import io
import json
import os
import tempfile
import unittest

from identity_v3.cli import main
from identity_v3.engine import IdentityEngine


class CliTests(unittest.TestCase):
    def _run(self, argv):
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = main(argv)
        return code, json.loads(output.getvalue()) if output.getvalue() else None, error.getvalue()

    def test_full_review_accept_resolve_undo_audit_flow(self):
        handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        handle.close()
        try:
            with IdentityEngine(handle.name) as engine:
                engine.upsert_entity("registry:one", label="One Person", kind="human", origin="registry")
                engine.upsert_entity("github:one", label="one-person", kind="human", origin="github")
                for entity_id in ("registry:one", "github:one"):
                    engine.record_identifier(
                        entity_id, "orcid", "0000-0001-1111-1111",
                        source="fixture", observed_at="2026-08-06T00:00:00Z",
                    )

            code, proposed, _ = self._run(["propose", "--db", handle.name, "--no-sync-v2"])
            self.assertEqual(code, 0)
            self.assertEqual(proposed["auto_eligible"], 1)
            candidate_id = proposed["samples"][0]["candidate_id"]

            code, accepted, _ = self._run([
                "accept", "--db", handle.name, "--candidate", candidate_id,
                "--decided-by", "test:auto", "--automatic",
            ])
            self.assertEqual(code, 0)
            decision_id = accepted["decision_id"]

            code, resolved, _ = self._run([
                "resolve", "--db", handle.name, "--entity", "github:one",
            ])
            self.assertEqual(code, 0)
            self.assertEqual(resolved["canonical_entity_id"], "registry:one")

            # Repeating acceptance is an idempotent no-op, not a second active
            # decision that would require multiple undo commands.
            code, repeated, _ = self._run([
                "accept", "--db", handle.name, "--candidate", candidate_id,
                "--decided-by", "test:auto", "--automatic",
            ])
            self.assertEqual(code, 0)
            self.assertTrue(repeated["idempotent"])
            self.assertEqual(repeated["decision_id"], decision_id)

            code, undone, _ = self._run([
                "undo", "--db", handle.name, "--decision", decision_id,
            ])
            self.assertEqual(code, 0)
            self.assertEqual(undone["undone_decision_id"], decision_id)

            code, audit, _ = self._run(["audit", "--db", handle.name])
            self.assertEqual(code, 0)
            self.assertTrue(audit["invariants_ok"])
            self.assertEqual(audit["counts"]["active_acceptances"], 0)
        finally:
            os.unlink(handle.name)


if __name__ == "__main__":
    unittest.main()
