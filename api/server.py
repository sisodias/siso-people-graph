"""Read-only HTTP API over QueryEngine.

THIS MODULE CONTAINS ZERO SQL. It is a thin projection of query_v3.engine.QueryEngine
-- every route delegates to the engine and serialises its dict envelope. Adding
SQL here would re-introduce the read-layer/identity-layer drift this lane is
designed to prevent; if a new query is needed, add it to query_v3 and bind it
here.

Safety properties (held by construction):
  * GET and HEAD only. There are no write endpoints. There is no arbitrary-SQL
    endpoint. The query library is the single read surface.
  * The server binds 127.0.0.1 by default -- not 0.0.0.0 -- so it does not
    become a public read of the corpus without an explicit choice.
  * Bad ints produce a 400, never a traceback.
  * Missing required parameters produce a 400 naming the param, never a 500.
"""
from __future__ import annotations

import argparse
import http.server
import json
import socketserver
import sys
import urllib.parse
from typing import Any

from query_v3.engine import QueryEngine

ROUTES = {
    "GET": {
        "/health": "_route_health",
        "/inventory": "_route_inventory",
        "/source": "_route_source",
        "/who": "_route_who",
        "/works": "_route_works",
        "/relationships": "_route_relationships",
        "/path": "_route_path",
        "/claims": "_route_claims",
    },
}


def _parse_int(name: str, raw: str | None, default: int | None = None) -> int:
    """Strict int parser. Raises ValueError on anything that is not a base-10 int."""
    if raw is None or raw == "":
        if default is None:
            raise ValueError(name)
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValueError(name)


def _missing(msg: str, status: int = 400) -> dict:
    return {"error": msg, "status": status}


def _dump(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class _Handler(http.server.BaseHTTPRequestHandler):
    """One handler class. `server` attribute is the owning APIServer."""

    server_version = "PeopleGraphReadOnly/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401, A003
        # Quiet by default; tests can replace log_message if they want verbose.
        pass

    def do_HEAD(self) -> None:  # noqa: N802
        self._serve(method="HEAD")

    def do_GET(self) -> None:  # noqa: N802
        self._serve(method="GET")

    # Every mutating verb is refused explicitly with 405. Relying on
    # BaseHTTPRequestHandler's default gives 501 "Unsupported method", which
    # reads as "not implemented yet" rather than "this API does not write" --
    # a read-only guarantee should be stated, not inferred from an omission.
    def _reject(self) -> None:
        self.send_response(405)
        self.send_header("Allow", "GET, HEAD")
        body = _dump(
            {
                "error": f"{self.command} is not allowed: this API is read-only "
                         "by design and exposes no write endpoint.",
                "status": 405,
                "allowed_methods": ["GET", "HEAD"],
            }
        )
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_POST = do_PUT = do_DELETE = do_PATCH = _reject  # noqa: N815
    do_OPTIONS = do_TRACE = do_CONNECT = _reject  # noqa: N815

    def _serve(self, method: str) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"
        methods = ROUTES.get(method, {})
        qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        factory = self.server.engine_factory  # type: ignore[attr-defined]

        if path not in methods:
            self._json(
                404,
                _missing(
                    f"unknown path {path!r}; valid routes: {sorted(methods) or sorted(ROUTES['GET'])}",
                    status=404,
                ),
            )
            return
        # Construct the engine inside this thread: sqlite3.Connection is bound
        # to the thread that opened it, and the handler thread is not the
        # factory's thread. The engine is read-only and the open is cheap.
        engine = factory()
        try:
            if method == "HEAD":
                # HEAD mirrors GET but with no body. Run the route to validate
                # the path/params, then discard the body.
                handler_name = methods[path]
                handler = getattr(self, handler_name)
                try:
                    handler(engine, qs)
                except ValueError as exc:
                    self._json(400, _missing(
                        f"missing or non-integer parameter: {exc}", status=400))
                    return
                except Exception as exc:  # noqa: BLE001
                    self._json(500, _missing(f"engine error: {exc}", status=500))
                    return
                self._json(200, {"status": "ok"}, write_body=False)
                return
            self._dispatch(methods[path], engine, qs, write_body=True)
        finally:
            engine.close()

    def _dispatch(self, handler_name: str, engine: QueryEngine, qs: dict, write_body: bool) -> None:
        handler = getattr(self, handler_name)
        try:
            payload = handler(engine, qs)
        except ValueError as exc:
            missing = str(exc)
            self._json(400, _missing(f"missing or non-integer parameter: {missing}", status=400))
            return
        except Exception as exc:  # noqa: BLE001
            self._json(500, _missing(f"engine error: {exc}", status=500))
            return
        self._json(200, payload, write_body=write_body)

    # ---------------------------------------------------------- helpers

    def _json(self, status: int, payload: dict, write_body: bool = True) -> None:
        body = _dump(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if write_body:
            self.wfile.write(body)

    # ------------------------------------------------------------ routes

    @staticmethod
    def _route_health(engine: QueryEngine, _qs: dict) -> dict:
        return {"status": "ok"}

    @staticmethod
    def _route_inventory(engine: QueryEngine, _qs: dict) -> dict:
        return engine.inventory()

    @staticmethod
    def _route_source(engine: QueryEngine, _qs: dict) -> dict:
        return engine.source()

    @staticmethod
    def _route_who(engine: QueryEngine, qs: dict) -> dict:
        name = (qs.get("name") or [""])[0]
        if not name:
            raise ValueError("name")
        limit = _parse_int("limit", (qs.get("limit") or [None])[0], default=8)
        offset = _parse_int("offset", (qs.get("offset") or [None])[0], default=0)
        return engine.who(name, limit=limit, offset=offset)

    @staticmethod
    def _route_works(engine: QueryEngine, qs: dict) -> dict:
        name = (qs.get("name") or [""])[0]
        if not name:
            raise ValueError("name")
        limit = _parse_int("limit", (qs.get("limit") or [None])[0], default=100)
        offset = _parse_int("offset", (qs.get("offset") or [None])[0], default=0)
        return engine.works(name, limit=limit, offset=offset)

    @staticmethod
    def _route_relationships(engine: QueryEngine, qs: dict) -> dict:
        name = (qs.get("name") or [""])[0]
        if not name:
            raise ValueError("name")
        limit = _parse_int("limit", (qs.get("limit") or [None])[0], default=25)
        return engine.relationships(name, limit=limit)

    @staticmethod
    def _route_path(engine: QueryEngine, qs: dict) -> dict:
        frm = (qs.get("from") or [""])[0]
        to = (qs.get("to") or [""])[0]
        if not frm:
            raise ValueError("from")
        if not to:
            raise ValueError("to")
        max_hops = _parse_int("max_hops", (qs.get("max_hops") or [None])[0], default=3)
        return engine.path(frm, to, max_hops=max_hops)

    @staticmethod
    def _route_claims(engine: QueryEngine, qs: dict) -> dict:
        name = (qs.get("name") or [""])[0]
        if not name:
            raise ValueError("name")
        limit = _parse_int("limit", (qs.get("limit") or [None])[0], default=25)
        return engine.claims(name, limit=limit)


class _ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Per-connection threads; daemonised so it doesn't block process exit."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr: tuple[str, int], handler: type,
                 engine_factory: "callable[[], QueryEngine]") -> None:
        super().__init__(addr, handler)
        self.engine_factory = engine_factory


def build_server(engine: QueryEngine, host: str = "127.0.0.1", port: int = 0) -> _ThreadingServer:
    """Construct the HTTP server. Tests can pass port=0 for an ephemeral bind.

    The engine is wrapped in a factory so a fresh connection is opened on the
    thread that handles each request; sqlite3 connections are bound to the
    thread that created them, and the request thread is not this thread.
    """
    def factory() -> QueryEngine:
        return QueryEngine(config=engine.config, root=engine.config.root)
    return _ThreadingServer((host, port), _Handler, factory)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="people-graph-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    engine = QueryEngine(root=args.root)
    server = build_server(engine, host=args.host, port=args.port)
    host, port = server.server_address[:2]
    print(f"PeopleGraph read-only API listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.close()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
