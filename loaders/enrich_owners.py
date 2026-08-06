#!/usr/bin/env python3
"""Record replayable GitHub profile observations for graph owners.

The loader remains compatible with the v2 CLI, but profile fields are no longer
promoted into canonical name, build timestamp, or rank. Each field is observed
independently, nulls receive receipts, mutable logins become time-bounded aliases,
and the stable numeric account id is the only GitHub value eligible for automatic
identity resolution.

Usage:
  enrich_owners.py --graph people_v2.sqlite --limit 500
  enrich_owners.py --graph people_v2.sqlite --limit 5000 --token "$GH_TOKEN"
  enrich_owners.py --graph fixture.sqlite --fixture tests/identity_v3/fixtures/github_profiles.json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from typing import Callable, Mapping
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from identity_v3.engine import IdentityEngine, utc_now  # noqa: E402
from identity_v3.enrichment import GITHUB_PROFILE_FIELDS, record_github_profile  # noqa: E402

API = "https://api.github.com/users/"
FetchResult = tuple[Mapping[str, object], int | None]
Fetcher = Callable[[str, str | None], FetchResult]


def fetch(login: str, token: str | None) -> FetchResult:
    req = urllib.request.Request(
        API + login,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "siso-people-graph-identity-v3/0.1",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        remaining = response.headers.get("X-RateLimit-Remaining")
        return json.load(response), (int(remaining) if remaining else None)


def fixture_fetcher(path: str | Path) -> Fetcher:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, list):
        profiles = {
            str(item.get("requested_login") or item.get("login")): item
            for item in raw if isinstance(item, dict)
        }
    elif isinstance(raw, dict):
        profiles = raw
    else:
        raise ValueError("fixture must be a JSON object or list")

    def replay(login: str, token: str | None = None) -> FetchResult:
        del token
        if login not in profiles:
            raise KeyError(f"fixture has no profile for {login}")
        profile = profiles[login]
        if not isinstance(profile, dict):
            raise ValueError(f"fixture profile for {login} must be an object")
        return profile, None

    return replay


def _existing_fields(connection: sqlite3.Connection, entity_id: str) -> set[str]:
    fields = {
        row[0] for row in connection.execute(
            """SELECT field FROM identity_v3_enrichment_receipt
               WHERE entity_id=? AND source='github_api'""",
            (entity_id,),
        )
    }
    legacy_map = {
        "github_id": "id",
        "github_node_id": "node_id",
        "github_login": "login",
        "real_name": "name",
        "x_handle": "twitter_username",
        "website": "blog",
        "company": "company",
        "location": "location",
        "biography": "bio",
    }
    for platform, in connection.execute(
        "SELECT DISTINCT platform FROM external_ids WHERE person_id=?",
        (entity_id,),
    ):
        mapped = legacy_map.get(platform)
        if mapped:
            fields.add(mapped)
    return fields


def _requested_login(connection: sqlite3.Connection, person_id: str, name: str) -> str:
    row = connection.execute(
        """SELECT value FROM external_ids
           WHERE person_id=? AND platform='github_login'
           ORDER BY rowid DESC LIMIT 1""",
        (person_id,),
    ).fetchone()
    if row and row[0]:
        return str(row[0])
    if person_id.startswith("gh:"):
        return person_id[3:]
    return name


def _write_legacy_compatibility(
    connection: sqlite3.Connection,
    person_id: str,
    requested_login: str,
    profile: Mapping[str, object],
) -> None:
    rows: list[tuple[str, str, float]] = []
    mapping = (
        ("github_id", profile.get("id"), 1.0),
        ("github_node_id", profile.get("node_id"), 1.0),
        ("github_login", profile.get("login") or requested_login, 1.0),
        ("real_name", profile.get("name"), 1.0),
        ("x_handle", profile.get("twitter_username"), 1.0),
        ("website", profile.get("blog"), 0.9),
        ("company", profile.get("company"), 0.7),
        ("location", profile.get("location"), 0.6),
        ("biography", profile.get("bio"), 0.5),
    )
    for platform, value, confidence in mapping:
        if value not in (None, ""):
            rows.append((platform, str(value).strip(), confidence))
    connection.executemany(
        """INSERT OR IGNORE INTO external_ids
           (person_id,platform,value,confidence,source) VALUES (?,?,?,?,?)""",
        [(person_id, platform, value, confidence, "github_api")
         for platform, value, confidence in rows],
    )
    # Source account type may safely refine an unknown kind, but every other
    # canonical field remains untouched.
    profile_type = profile.get("type")
    if profile_type in {"User", "Organization"}:
        kind = "organisation" if profile_type == "Organization" else "human"
        connection.execute(
            "UPDATE person SET kind=? WHERE person_id=? AND kind='unknown'",
            (kind, person_id),
        )


def enrich(
    graph_db: str,
    limit: int,
    token: str | None,
    sleep: float,
    *,
    fetcher: Fetcher | None = None,
    observed_at: str | None = None,
) -> dict[str, object]:
    connection = sqlite3.connect(graph_db)
    connection.row_factory = sqlite3.Row
    engine = IdentityEngine(connection)
    fetch_profile = fetcher or fetch
    when = observed_at or utc_now()

    rows = connection.execute(
        """SELECT person_id,name,kind,origin,rank_score,built_at
           FROM person WHERE origin='github'
           ORDER BY COALESCE(rank_score,0) DESC, person_id"""
    )
    selected: list[tuple[str, str, list[str]]] = []
    for row in rows:
        person_id, name = row["person_id"], row["name"]
        engine.upsert_entity(
            person_id, label=name, kind=row["kind"] or "unknown", origin=row["origin"],
            source_native_id=person_id, created_at=when,
        )
        existing = _existing_fields(connection, person_id)
        missing = [field for field in GITHUB_PROFILE_FIELDS if field not in existing]
        if not missing:
            continue
        selected.append((person_id, _requested_login(connection, person_id, name), missing))
        if limit and len(selected) >= limit:
            break

    stats: dict[str, object] = {
        "considered": len(selected),
        "fetched": 0,
        "users": 0,
        "orgs": 0,
        "errors": 0,
        "rate_limited": False,
        "renames": 0,
        "fields_observed": {field: 0 for field in GITHUB_PROFILE_FIELDS},
        "fields_absent": {field: 0 for field in GITHUB_PROFILE_FIELDS},
    }

    for person_id, login, missing in selected:
        try:
            profile, remaining = fetch_profile(login, token)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                stats["rate_limited"] = True
                break
            stats["errors"] = int(stats["errors"]) + 1
            continue
        except Exception:
            stats["errors"] = int(stats["errors"]) + 1
            continue

        result = record_github_profile(
            engine, person_id, login, profile, observed_at=when, source="github_api",
        )
        _write_legacy_compatibility(connection, person_id, login, profile)
        stats["fetched"] = int(stats["fetched"]) + 1
        profile_type = profile.get("type")
        if profile_type == "Organization":
            stats["orgs"] = int(stats["orgs"]) + 1
        else:
            stats["users"] = int(stats["users"]) + 1
        if str(result["response_login"]).casefold() != login.casefold():
            stats["renames"] = int(stats["renames"]) + 1
        for field in GITHUB_PROFILE_FIELDS:
            bucket = "fields_observed" if profile.get(field) not in (None, "") else "fields_absent"
            field_counts = stats[bucket]
            assert isinstance(field_counts, dict)
            field_counts[field] = int(field_counts[field]) + 1

        if int(stats["fetched"]) % 50 == 0:
            connection.commit()
            print(
                f"  {stats['fetched']}/{len(selected)} "
                f"(rate limit remaining: {remaining})",
                file=sys.stderr,
            )
        if remaining is not None and remaining < 10:
            stats["rate_limited"] = True
            break
        if sleep:
            time.sleep(sleep)

    connection.commit()
    stats["external_ids_total"] = connection.execute(
        "SELECT COUNT(*) FROM external_ids"
    ).fetchone()[0]
    stats["attribute_observations"] = connection.execute(
        "SELECT COUNT(*) FROM identity_v3_attribute WHERE source='github_api'"
    ).fetchone()[0]
    stats["alias_observations"] = connection.execute(
        "SELECT COUNT(*) FROM identity_v3_alias WHERE source='github_api'"
    ).fetchone()[0]
    connection.close()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--sleep", type=float, default=0.1)
    parser.add_argument("--fixture", help="replay profiles from a local JSON fixture")
    args = parser.parse_args()
    started = time.time()
    try:
        result = enrich(
            args.graph,
            args.limit,
            args.token,
            args.sleep,
            fetcher=fixture_fetcher(args.fixture) if args.fixture else None,
        )
    except (sqlite3.Error, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    result["elapsed_s"] = round(time.time() - started, 2)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
