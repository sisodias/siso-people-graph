"""Read-only HTML projection of a QueryEngine response.

Every value that originated from the database is escaped -- this is the one
non-negotiable property of the viewer. If the corpus contains a name with a
`<script>` tag in it, the viewer renders it as text, not as a script.

The viewer renders the truth contract alongside the rows:
  * identity_resolution.mode + applied decisions
  * page.truncated (loud when true)
  * coverage_gaps
  * warnings
  * every item's evidence.grade

No external assets, no CDN, no JS framework.
"""
from __future__ import annotations

import html
import json
from typing import Any

from query_v3.response import SCHEMA_VERSION

_BASE_CSS = """
:root { color-scheme: light dark; }
body { font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
       margin: 0; padding: 1.5rem; max-width: 1100px; }
header { border-bottom: 1px solid currentColor; padding-bottom: 0.75rem; margin-bottom: 1rem; }
h1 { font-size: 1.25rem; margin: 0 0 0.25rem 0; }
h2 { font-size: 1rem; margin: 1.5rem 0 0.5rem 0; }
.meta { color: #666; font-size: 0.85rem; }
.badge { display: inline-block; padding: 2px 6px; border-radius: 4px;
         font-size: 0.8rem; font-weight: 600; }
.badge.ok { background: #e6f4ea; color: #1a7f37; }
.badge.warn { background: #fff8c5; color: #9a6700; }
.badge.gap { background: #ffebe9; color: #cf222e; }
.badge.truncated { background: #ffd8b5; color: #b15b00; }
ul { padding-left: 1.25rem; }
li.item { padding: 0.5rem 0; border-bottom: 1px solid #eee; }
li.item:last-child { border-bottom: none; }
.evidence { color: #555; font-size: 0.85rem; }
pre { background: rgba(0,0,0,0.05); padding: 0.5rem; overflow-x: auto;
      border-radius: 4px; font-size: 0.85rem; }
.section { margin-bottom: 1rem; }
table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid #eee; }
"""


def _esc(value: Any) -> str:
    """Escape ANYTHING that could carry a `<` or `&` from the database."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _section(title: str, body: str, klass: str = "") -> str:
    return f'<section class="section {klass}"><h2>{_esc(title)}</h2>{body}</section>'


def _render_truth_contract(result: dict) -> str:
    """Render the truth contract fields that distinguish a page from a corpus."""
    page = result.get("page") or {}
    identity = result.get("identity_resolution") or {}
    caps = result.get("capabilities") or {}
    out: list[str] = []

    truncated = bool(page.get("truncated"))
    badge = '<span class="badge truncated">TRUNCATED</span>' if truncated else \
            '<span class="badge ok">complete</span>'
    out.append(
        "<p>"
        f"{badge} returned <strong>{_esc(page.get('returned'))}</strong> of "
        f"<strong>{_esc(page.get('total_matched'))}</strong> "
        f"(limit={_esc(page.get('limit'))}, offset={_esc(page.get('offset'))})"
        "</p>"
    )
    counts_exact = page.get("counts_are_exact")
    if counts_exact is False:
        out.append(
            '<p class="badge gap">total_matched unknown: counts are NOT exact</p>'
        )

    mode = identity.get("mode") or caps.get("identity_mode")
    if mode:
        out.append(f"<p>identity_resolution.mode: <strong>{_esc(mode)}</strong></p>")

    applied = identity.get("applied") or []
    if applied:
        items = "".join(f"<li>{_esc(d)}</li>" for d in applied)
        out.append(f"<p>applied decisions:</p><ul>{items}</ul>")

    unresolved = identity.get("unresolved") or []
    if unresolved:
        items = "".join(f"<li>{_esc(u)}</li>" for u in unresolved)
        out.append(
            f'<p class="badge gap">unresolved candidates:</p><ul>{items}</ul>'
        )

    gaps = result.get("coverage_gaps") or []
    if gaps:
        items = "".join(f'<li><span class="badge gap">gap</span> {_esc(g)}</li>' for g in gaps)
        out.append(f"<p>coverage_gaps:</p><ul>{items}</ul>")

    warnings = result.get("warnings") or []
    if warnings:
        items = "".join(f'<li><span class="badge warn">warn</span> {_esc(w)}</li>' for w in warnings)
        out.append(f"<p>warnings:</p><ul>{items}</ul>")

    return _section("Truth contract", "".join(out))


def _render_evidence(item: dict) -> str:
    """Render an item's evidence block -- grade included."""
    ev = item.get("evidence") or {}
    grade = ev.get("grade") or "unknown"
    badge_cls = "ok" if grade in ("observed", "primary") else "warn"
    source = ev.get("source")
    detail = ev.get("detail")
    observed_at = ev.get("observed_at")
    bits = [
        f'<span class="badge {badge_cls}">{_esc(grade)}</span>',
        f"source: {_esc(source)}" if source else "",
        f"observed_at: {_esc(observed_at)}" if observed_at else "",
        f"<div class='evidence'>{_esc(detail)}</div>" if detail else "",
    ]
    return " ".join(b for b in bits if b)


def _list_items(items: list[dict]) -> str:
    if not items:
        return "<p><em>no items</em></p>"
    out: list[str] = []
    for item in items:
        title = (
            item.get("title") or item.get("name") or item.get("statement")
            or item.get("ref") or item.get("person_id") or "(item)"
        )
        extras = []
        for key in ("domain", "ref", "role", "review_state", "relation",
                    "person_id", "claim_id"):
            val = item.get(key)
            if val is not None:
                extras.append(f"<strong>{_esc(key)}</strong>: {_esc(val)}")
        ev_html = _render_evidence(item)
        out.append(
            f"<li class='item'><div><strong>{_esc(title)}</strong></div>"
            f"<div class='evidence'>{' | '.join(extras)}</div>"
            f"<div class='evidence'>{ev_html}</div></li>"
        )
    return "<ul>" + "".join(out) + "</ul>"


def _render_result(result: dict) -> str:
    out: list[str] = []
    if "matches" in result:
        out.append(_section(f"matches ({len(result['matches'])})",
                            _list_items(result["matches"])))
    if "works" in result:
        person = result.get("person")
        head = ""
        if person:
            head = (f"<p>person: {_esc(person.get('name'))} "
                    f"(person_id={_esc(person.get('person_id'))})</p>")
        out.append(_section(f"works ({len(result['works'])})", head +
                            _list_items(result["works"])))
    if "neighbours" in result:
        person = result.get("person")
        head = ""
        if person:
            head = (f"<p>person: {_esc(person.get('name'))} "
                    f"(person_id={_esc(person.get('person_id'))})</p>")
        out.append(_section(f"neighbours ({len(result['neighbours'])})", head +
                            _list_items(result["neighbours"])))
    if "claims" in result:
        out.append(_section(f"claims ({len(result['claims'])})",
                            _list_items(result["claims"])))
    if "path" in result:
        path = result.get("path")
        if path is None:
            out.append(_section("path", "<p><em>no path</em></p>"))
        else:
            out.append(_section("path", _list_items(path)))
    if "domains" in result:
        rows = "".join(
            f"<tr><td>{_esc(d)}</td><td>{_esc(info.get('path'))}</td>"
            f"<td>{_esc(json.dumps(info.get('tables') or {}, ensure_ascii=False))}</td></tr>"
            for d, info in (result["domains"] or {}).items()
        )
        out.append(_section("domains", f"<table><thead><tr>"
                              "<th>domain</th><th>path</th><th>tables (counts)</th>"
                              "</tr></thead><tbody>" + rows + "</tbody></table>"))
    if "sources" in result:
        rows = "".join(
            f"<tr><td>{_esc(d)}</td><td>{_esc(info.get('path'))}</td>"
            f"<td>{_esc(info.get('attached'))}</td>"
            f"<td>{_esc(json.dumps(info.get('rights'), ensure_ascii=False))}</td></tr>"
            for d, info in (result["sources"] or {}).items()
        )
        out.append(_section("sources", f"<table><thead><tr>"
                              "<th>domain</th><th>path</th><th>attached</th>"
                              "<th>rights</th></tr></thead><tbody>" + rows +
                              "</tbody></table>"))
    return "".join(out)


def render(result: dict) -> str:
    """Render an engine response dict as a self-contained HTML document."""
    qt = result.get("query_type") or "result"
    q = result.get("query") or {}
    head = (
        f"<header><h1>{_esc(qt)}</h1>"
        f"<div class='meta'>schema_version={_esc(SCHEMA_VERSION)} | "
        f"query={_esc(json.dumps(q, ensure_ascii=False))}</div></header>"
    )
    body = _render_truth_contract(result) + _render_result(result.get("result") or {})
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{_esc(qt)}</title><style>{_BASE_CSS}</style></head>"
        f"<body>{head}{body}</body></html>"
    )
