"""CLI, HTTP API, MCP and viewer are projections -- never a second implementation.

The defect this lane fixes was caused by a read path that had drifted away from
the identity layer. Four surfaces each carrying their own SQL is that same defect
with four times the surface area, so `test_no_surface_contains_sql` is a
structural guard, not a style check: it fails the build if any surface starts
talking to the database directly.

Everything else here asserts that the surfaces preserve the truth contract
rather than flattening it away on the way out.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from query_v3 import QueryEngine  # noqa: E402
from api import build_server  # noqa: E402
from mcp import handle  # noqa: E402
from viewer import render  # noqa: E402
from tests.query_v3.fixtures import build_people_db  # noqa: E402


class NoDuplicateSqlTest(unittest.TestCase):
    """The structural guard: only the query library may touch the database."""

    SURFACES = ("api", "mcp", "viewer")
    SQL = re.compile(
        r"\b(SELECT\s+\w|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|"
        r"ATTACH\s+DATABASE|CREATE\s+TABLE)\b", re.IGNORECASE)

    def test_no_surface_contains_sql(self):
        offenders = []
        for pkg in self.SURFACES:
            for root, _dirs, files in os.walk(os.path.join(REPO, pkg)):
                if "__pycache__" in root:
                    continue
                for fn in files:
                    if not fn.endswith(".py"):
                        continue
                    path = os.path.join(root, fn)
                    with open(path, encoding="utf-8") as fh:
                        for i, line in enumerate(fh, 1):
                            code = line.split("#", 1)[0]
                            if self.SQL.search(code):
                                offenders.append(f"{pkg}/{fn}:{i}: {line.strip()}")
        self.assertEqual(offenders, [],
                         "surfaces must call the query library, never SQL")

    def test_no_surface_imports_sqlite(self):
        offenders = []
        for pkg in self.SURFACES:
            for root, _dirs, files in os.walk(os.path.join(REPO, pkg)):
                if "__pycache__" in root:
                    continue
                for fn in files:
                    if not fn.endswith(".py"):
                        continue
                    with open(os.path.join(root, fn), encoding="utf-8") as fh:
                        for i, line in enumerate(fh, 1):
                            code = line.split("#", 1)[0]
                            if re.match(r"\s*(import|from)\s+sqlite3", code):
                                offenders.append(f"{pkg}/{fn}:{i}")
        self.assertEqual(offenders, [])


class _FixtureCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        build_people_db(os.path.join(cls.tmp.name, "people_v2.sqlite"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class HttpApiTest(_FixtureCase):
    def setUp(self):
        self.engine = QueryEngine(root=self.tmp.name)
        self.srv = build_server(self.engine, "127.0.0.1", 0)
        self.port = self.srv.server_address[1]
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.engine.close()

    def get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            with exc:  # close the error body, else ResourceWarning noise
                return exc.code, json.loads(exc.read())

    def test_who_applies_identity_over_http(self):
        status, body = self.get("/who?name=Kant")
        self.assertEqual(status, 200)
        kant = [m for m in body["result"]["matches"]
                if m["person_id"] in ("bk:kant", "gh:kant")]
        self.assertEqual(len(kant), 1)
        self.assertTrue(body["identity_resolution"]["applied"])

    def test_truth_contract_survives_serialisation(self):
        _s, body = self.get("/works?name=Prolific+Author&limit=5")
        self.assertEqual(body["page"]["total_matched"], 250)
        self.assertTrue(body["page"]["truncated"])
        for field in ("capabilities", "coverage_gaps", "identity_resolution",
                      "sources"):
            self.assertIn(field, body)

    def test_bad_input_is_a_json_error_not_a_traceback(self):
        for path in ("/who", "/who?name=x&limit=abc", "/path?from=a"):
            status, body = self.get(path)
            self.assertEqual(status, 400, path)
            self.assertIn("error", body)

    def test_unknown_route_lists_valid_routes(self):
        status, body = self.get("/definitely-not-a-route")
        self.assertEqual(status, 404)
        self.assertIn("error", body)
        # The error must name the alternatives, so a caller can self-correct.
        self.assertIn("/who", body["error"])
        self.assertIn("/works", body["error"])

    def test_no_write_or_sql_endpoints_exist(self):
        for path in ("/query", "/sql", "/execute", "/write", "/admin"):
            status, _b = self.get(path)
            self.assertEqual(status, 404, f"{path} must not exist")

    def test_write_methods_are_rejected(self):
        url = f"http://127.0.0.1:{self.port}/who?name=Kant"
        for method in ("POST", "PUT", "DELETE", "PATCH"):
            req = urllib.request.Request(url, method=method, data=b"{}")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=15)
            with ctx.exception as err:
                self.assertEqual(err.code, 405, method)
                body = json.loads(err.read())
            self.assertEqual(body["allowed_methods"], ["GET", "HEAD"])
            self.assertIn("read-only", body["error"])


class McpTest(_FixtureCase):
    def setUp(self):
        self.engine = QueryEngine(root=self.tmp.name)

    def tearDown(self):
        self.engine.close()

    def test_tools_are_listed_with_schemas(self):
        resp = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                      self.engine)
        tools = resp["result"]["tools"]
        names = {t["name"] for t in tools}
        self.assertIn("people_who", names)
        self.assertIn("people_works", names)
        for t in tools:
            self.assertIn("inputSchema", t)
            self.assertEqual(t["inputSchema"]["type"], "object")

    def test_call_returns_the_engine_envelope(self):
        resp = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                       "params": {"name": "people_who",
                                  "arguments": {"name": "Kant"}}}, self.engine)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertIn("identity_resolution", payload)
        kant = [m for m in payload["result"]["matches"]
                if m["person_id"] in ("bk:kant", "gh:kant")]
        self.assertEqual(len(kant), 1)

    def test_unknown_tool_is_an_error_object_not_a_crash(self):
        resp = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                       "params": {"name": "people_drop_table",
                                  "arguments": {}}}, self.engine)
        self.assertIn("error", resp)

    def test_unknown_method_is_an_error_object(self):
        resp = handle({"jsonrpc": "2.0", "id": 4, "method": "nonsense"},
                      self.engine)
        self.assertIn("error", resp)

    def test_no_write_tool_is_exposed(self):
        resp = handle({"jsonrpc": "2.0", "id": 5, "method": "tools/list"},
                      self.engine)
        for t in resp["result"]["tools"]:
            for banned in ("write", "insert", "update", "delete", "sql",
                           "execute", "merge", "accept"):
                self.assertNotIn(banned, t["name"].lower())


class ViewerTest(_FixtureCase):
    def setUp(self):
        self.engine = QueryEngine(root=self.tmp.name)

    def tearDown(self):
        self.engine.close()

    def test_renders_the_truth_contract_not_just_rows(self):
        html = render(self.engine.who("Kant"))
        low = html.lower()
        self.assertIn("identity", low)
        self.assertIn("kant", low)

    def test_truncation_is_visible_to_a_human(self):
        html = render(self.engine.works("Prolific Author", limit=5)).lower()
        self.assertIn("250", html)
        self.assertTrue("truncat" in html or "of 250" in html)

    def test_database_values_are_escaped(self):
        """Titles and names are source data; they must never become markup.

        The hostile value has to be reachable by the query, or this test escapes
        nothing and passes vacuously -- so the row is indexed under a findable
        token and the assertion first proves the row actually came back.
        """
        hostile = "Malory <script>alert(1)</script>"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "people_v2.sqlite")
            build_people_db(path)
            import sqlite3
            con = sqlite3.connect(path)
            con.execute(
                "INSERT INTO person(person_id,name,kind,state,origin,built_at) "
                "VALUES('bk:xss',?,'human','linked','book','2026-08-06')",
                (hostile,))
            con.execute(
                "INSERT INTO person_search(person_id,name,aliases) VALUES(?,?,?)",
                ("bk:xss", hostile, "Malory"))
            con.commit()
            con.close()
            with QueryEngine(root=tmp) as e:
                result = e.who("Malory")
                html = render(result)

        self.assertTrue(result["result"]["matches"],
                        "the hostile row must be returned, or nothing is escaped")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)


class CliTest(_FixtureCase):
    """loaders/ask.py must be a projection too -- same answers, same contract."""

    def run_cli(self, *args):
        out = subprocess.run(
            [sys.executable, os.path.join(REPO, "loaders", "ask.py"), *args],
            cwd=self.tmp.name, capture_output=True, text=True, timeout=60,
            env={**os.environ, "PYTHONPATH": REPO},
        )
        self.assertTrue(out.stdout.strip(), f"no output: {out.stderr[:500]}")
        return json.loads(out.stdout)

    def test_cli_applies_identity_decisions(self):
        data = self.run_cli("--who", "Kant")
        kant = [m for m in data["result"]["matches"]
                if m["person_id"] in ("bk:kant", "gh:kant")]
        self.assertEqual(len(kant), 1)

    def test_cli_reports_truncation(self):
        data = self.run_cli("--works", "Prolific Author", "--limit", "10")
        self.assertEqual(data["page"]["total_matched"], 250)
        self.assertTrue(data["page"]["truncated"])

    def test_cli_declares_search_path(self):
        data = self.run_cli("--who", "Kant")
        self.assertEqual(data["execution"]["search_path"], "fts5")

    def test_cli_on_empty_estate_is_explicit(self):
        with tempfile.TemporaryDirectory() as empty:
            out = subprocess.run(
                [sys.executable, os.path.join(REPO, "loaders", "ask.py"),
                 "--who", "Kant"],
                cwd=empty, capture_output=True, text=True, timeout=60,
                env={**os.environ, "PYTHONPATH": REPO},
            )
            data = json.loads(out.stdout)
        self.assertTrue(any("no people database" in w.lower()
                            for w in data["warnings"]))


if __name__ == "__main__":
    unittest.main()
