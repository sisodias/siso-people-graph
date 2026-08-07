"""Minimal MCP surface over QueryEngine -- stdio JSON-RPC 2.0, stdlib only.

Like the HTTP API, this module contains ZERO SQL. It is a thin dispatcher onto
the query library; one tool per engine method. Tests can drive `handle()` directly
with a synthetic request dict, so the protocol loop in `_serve_stdio` is the only
piece that touches streams.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from query_v3.engine import QueryEngine

TOOLS: list[dict] = [
    {
        "name": "people_who",
        "description": (
            "Find candidate people matching a name. Returns the full response "
            "envelope including identity_resolution, page.truncated and "
            "coverage_gaps."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name to search for."},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 500},
                "offset": {"type": "integer", "default": 0, "minimum": 0},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "people_works",
        "description": (
            "Everything a person produced, with honest counts and fetch routes. "
            "Returns the full envelope."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "limit": {"type": "integer", "default": 100, "minimum": 1, "maximum": 500},
                "offset": {"type": "integer", "default": 0, "minimum": 0},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "people_relationships",
        "description": (
            "Typed, evidenced neighbours of a person. Co-contribution is derived "
            "from shared works; typed relations require the person_relation table."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "limit": {"type": "integer", "default": 25, "minimum": 1, "maximum": 500},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "people_path",
        "description": (
            "Bounded BFS route between two people over co-contribution edges. "
            "max_hops is clamped by the engine (1..4)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from": {"type": "string", "description": "Start person name."},
                "to": {"type": "string", "description": "End person name."},
                "max_hops": {"type": "integer", "default": 3, "minimum": 1, "maximum": 4},
            },
            "required": ["from", "to"],
            "additionalProperties": False,
        },
    },
    {
        "name": "people_claims",
        "description": "Evidence-backed assertions about a person, with review state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "limit": {"type": "integer", "default": 25, "minimum": 1, "maximum": 500},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "people_inventory",
        "description": (
            "What data exists at all, and what is missing. Always call this first "
            "if a tool returns coverage_gaps you do not expect."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "people_source",
        "description": (
            "Source snapshots: paths, rights_state, retrieval time. Reports the "
            "actual files this engine attached on this machine."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def _call(tool_name: str, arguments: dict, engine: QueryEngine) -> dict:
    if tool_name == "people_who":
        return engine.who(
            arguments["name"],
            limit=int(arguments.get("limit", 8)),
            offset=int(arguments.get("offset", 0)),
        )
    if tool_name == "people_works":
        return engine.works(
            arguments["name"],
            limit=int(arguments.get("limit", 100)),
            offset=int(arguments.get("offset", 0)),
        )
    if tool_name == "people_relationships":
        return engine.relationships(arguments["name"], limit=int(arguments.get("limit", 25)))
    if tool_name == "people_path":
        return engine.path(
            arguments["from"],
            arguments["to"],
            max_hops=int(arguments.get("max_hops", 3)),
        )
    if tool_name == "people_claims":
        return engine.claims(arguments["name"], limit=int(arguments.get("limit", 25)))
    if tool_name == "people_inventory":
        return engine.inventory()
    if tool_name == "people_source":
        return engine.source()
    raise ValueError(f"unknown tool: {tool_name}")


def handle(request: dict, engine: QueryEngine) -> dict:
    """Dispatch a single JSON-RPC 2.0 request to the engine.

    Returns a JSON-RPC response dict. Never touches stdio; callers wire it up.
    """
    rid = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    def err(code: int, message: str, data: Any = None) -> dict:
        e: dict = {"code": code, "message": message}
        if data is not None:
            e["data"] = data
        out: dict = {"jsonrpc": "2.0", "id": rid, "error": e}
        return out

    if not isinstance(request, dict):
        return err(-32600, "invalid request (not an object)")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "people-graph", "version": "0.1"},
                "capabilities": {"tools": {"listChanged": False}},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str):
            return err(-32602, "params.name must be a string")
        if not isinstance(arguments, dict):
            return err(-32602, "params.arguments must be an object")
        try:
            payload = _call(name, arguments, engine)
        except KeyError as exc:
            return err(-32602, f"missing required argument: {exc.args[0]}")
        except ValueError as exc:
            return err(-32602, f"invalid argument: {exc}")
        except Exception as exc:  # noqa: BLE001
            return err(-32603, f"engine error: {exc}")
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(payload, ensure_ascii=False)}
                ],
                "isError": False,
            },
        }
    if method == "notifications/initialized":
        # Notifications have no id; we still echo a benign response if id was provided.
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    return err(-32601, f"method not found: {method!r}")


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _serve_stdio(engine: QueryEngine) -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except ValueError as exc:
            _send({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"parse error: {exc}"},
            })
            continue
        try:
            response = handle(request, engine)
        except Exception as exc:  # noqa: BLE001
            _send({
                "jsonrpc": "2.0",
                "id": request.get("id") if isinstance(request, dict) else None,
                "error": {"code": -32603, "message": f"internal error: {exc}"},
            })
            continue
        # Notifications (no id) do not get a response per JSON-RPC.
        if isinstance(request, dict) and "id" in request:
            _send(response)
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="people-graph-mcp")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    engine = QueryEngine(root=args.root)
    try:
        return _serve_stdio(engine)
    finally:
        engine.close()


if __name__ == "__main__":
    sys.exit(main())
