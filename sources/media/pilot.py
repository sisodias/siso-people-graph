"""Offline runner for the living-creators/media pilot.

No subcommand performs network I/O.  Production collectors are expected to save
source snapshots under the applicable terms, then pass those payloads through
these deterministic adapters.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from sources.creators.bridges import propose_bridges
from sources.creators.cohort import build_manifest, observation_metrics, read_seeds
from sources.creators.envelope import (
    canonical_json,
    payload_sha256,
    read_ndjson,
    validate_envelope,
    write_ndjson,
)
from sources.creators.public_web import parse_jsonld_page
from sources.media.conference import adapt_pretalx_schedule
from sources.media.open_library import adapt_author, adapt_edition, adapt_work
from sources.media.policies import SOURCE_POLICIES, policy_registry
from sources.media.podcast_index import adapt_response as adapt_podcast_index
from sources.media.rss import adapt_rss
from sources.media.scholarly import (
    adapt_crossref_work,
    adapt_openalex_author,
    adapt_openalex_work,
    adapt_openreview_note,
)
from sources.media.youtube import adapt_channels, adapt_videos


def _json(path: Path) -> Mapping[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def fixture_observations(fixture_dir: Path, retrieved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    rss_path = fixture_dir / "podcast.xml"
    rss_text = rss_path.read_text(encoding="utf-8")
    records.extend(
        adapt_rss(
            xml_text=rss_text,
            feed_url="https://feeds.example.test/bounded-show.xml",
            retrieved_at=retrieved_at,
            observed_at="2026-08-05T12:00:00Z",
            terms_revision="fixture publisher terms: public metadata only",
        )
    )

    podcast_path = fixture_dir / "podcast_index.json"
    records.extend(
        adapt_podcast_index(
            payload=_json(podcast_path),
            endpoint="https://api.podcastindex.org/api/1.0/episodes/byfeedid?id=9001",
            retrieved_at=retrieved_at,
        )
    )

    youtube = _json(fixture_dir / "youtube.json")
    records.extend(
        adapt_channels(
            payload=youtube["channels"],
            endpoint="https://www.googleapis.com/youtube/v3/channels?id=UCfixture001",
            retrieved_at=retrieved_at,
        )
    )
    records.extend(
        adapt_videos(
            payload=youtube["videos"],
            endpoint="https://www.googleapis.com/youtube/v3/videos?id=vid-fixture-001",
            retrieved_at=retrieved_at,
        )
    )

    open_library = _json(fixture_dir / "open_library.json")
    records.append(
        adapt_author(
            payload=open_library["author"],
            endpoint="https://openlibrary.org/authors/OLFIXTUREA.json",
            retrieved_at=retrieved_at,
        )
    )
    records.append(
        adapt_work(
            payload=open_library["work"],
            endpoint="https://openlibrary.org/works/OLFIXTUREW.json",
            retrieved_at=retrieved_at,
        )
    )
    records.append(
        adapt_edition(
            payload=open_library["edition"],
            endpoint="https://openlibrary.org/books/OLFIXTUREM.json",
            retrieved_at=retrieved_at,
        )
    )

    scholarly = _json(fixture_dir / "scholarly.json")
    records.append(
        adapt_crossref_work(
            item=scholarly["crossref"],
            endpoint="https://api.crossref.org/works/10.5555/fixture.2026.1",
            retrieved_at=retrieved_at,
        )
    )
    records.append(
        adapt_openalex_author(
            payload=scholarly["openalex_author"],
            endpoint="https://api.openalex.org/authors/A5000000001",
            retrieved_at=retrieved_at,
        )
    )
    records.append(
        adapt_openalex_work(
            payload=scholarly["openalex_work"],
            endpoint="https://api.openalex.org/works/W5000000001",
            retrieved_at=retrieved_at,
        )
    )
    records.append(
        adapt_openreview_note(
            payload=scholarly["openreview"],
            endpoint="https://api2.openreview.net/notes?id=fixture-note-1",
            retrieved_at=retrieved_at,
        )
    )

    conference = _json(fixture_dir / "conference.json")
    records.extend(
        adapt_pretalx_schedule(
            payload=conference,
            endpoint="https://conference.example.test/schedule/export/schedule.json",
            retrieved_at=retrieved_at,
        )
    )

    site_path = fixture_dir / "personal_site.html"
    records.extend(
        parse_jsonld_page(
            html=site_path.read_text(encoding="utf-8"),
            page_url="https://alex.example.test/",
            retrieved_at=retrieved_at,
            observed_at="2026-08-04T08:00:00Z",
            terms_revision="fixture page terms: discovery only",
        )
    )
    return records


def fixture_receipts(fixture_dir: Path) -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    for path in sorted(fixture_dir.iterdir()):
        if not path.is_file():
            continue
        receipts.append(
            {
                "path": path.name,
                "sha256": payload_sha256(path.read_bytes()),
            }
        )
    return receipts


def export_fixtures(args: argparse.Namespace) -> int:
    fixture_dir = Path(args.fixture_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records = fixture_observations(fixture_dir, args.retrieved_at)
    observations_path = out_dir / "observations.ndjson"
    write_ndjson(records, observations_path)

    seeds = read_seeds(fixture_dir / "seeds.ndjson")
    manifest = build_manifest(
        seeds,
        target_size=args.target_size,
        source_targets={"github_seed": args.target_size // 2, "modern_author_seed": args.target_size // 2},
        generated_at=args.retrieved_at,
        snapshot_receipts=fixture_receipts(fixture_dir),
    )
    reviews_path = fixture_dir / "reviews.json"
    reviews = _json(reviews_path).get("reviews", []) if reviews_path.exists() else []
    candidates = propose_bridges(records)
    metrics = observation_metrics(
        records,
        manifest=manifest,
        reviewed_candidates=reviews if isinstance(reviews, list) else [],
    )
    metrics["quota_and_cost"] = {
        "network_requests_made": 0,
        "fixture_bytes": sum(path.stat().st_size for path in fixture_dir.iterdir() if path.is_file()),
        "credential_required_sources": ["podcast_index_api", "youtube_data_api", "openalex_api"],
        "source_constraints": {
            source_id: SOURCE_POLICIES[source_id]["quota_or_rate_limit"]
            for source_id in sorted(metrics["source_counts"])
        },
    }
    metrics["freshness"] = {
        "youtube_refresh_days": 30,
        "podcast_index": "cache-header bounded; prefer publisher RSS for durable replay",
        "open_sources": "replay from timestamped snapshot receipt",
        "per_source_refresh_rule": {
            source_id: SOURCE_POLICIES[source_id]["refresh_rule"]
            for source_id in sorted(metrics["source_counts"])
        },
    }
    fixture_sources = set(metrics["source_counts"])
    policy_sources = fixture_sources.intersection(SOURCE_POLICIES)
    missing_policies = sorted(fixture_sources.difference(SOURCE_POLICIES))
    metrics["removal_coverage"] = {
        "sources_with_documented_workflow": len(policy_sources),
        "sources_in_fixture": len(fixture_sources),
        "missing_source_policies": missing_policies,
        "coverage": (
            len(policy_sources) / len(fixture_sources) if fixture_sources else None
        ),
    }

    _write_json(out_dir / "bridge-candidates.json", candidates)
    _write_json(out_dir / "cohort-manifest.json", manifest)
    _write_json(out_dir / "pilot-metrics.json", metrics)
    print(
        canonical_json(
            {
                "observations": len(records),
                "bridge_candidates": len(candidates),
                "cohort_actual": manifest["actual_size"],
                "cohort_target": manifest["target_size"],
                "output": str(out_dir),
            }
        )
    )
    return 0


def validate_command(args: argparse.Namespace) -> int:
    records = read_ndjson(args.path)
    for record in records:
        validate_envelope(record)
    print(canonical_json({"valid": len(records), "path": str(args.path)}))
    return 0


def cohort_command(args: argparse.Namespace) -> int:
    seeds = read_seeds(args.seeds)
    manifest = build_manifest(
        seeds,
        target_size=args.target_size,
        generated_at=args.generated_at,
    )
    _write_json(Path(args.out), manifest)
    print(canonical_json({"actual_size": manifest["actual_size"], "status": manifest["status"]}))
    return 0


def policies_command(args: argparse.Namespace) -> int:
    registry = policy_registry()
    _write_json(Path(args.out), registry)
    print(canonical_json({"sources": len(registry["sources"]), "out": args.out}))
    return 0


def metrics_command(args: argparse.Namespace) -> int:
    records = read_ndjson(args.observations)
    manifest = _json(Path(args.manifest)) if args.manifest else None
    metrics = observation_metrics(records, manifest=manifest)
    _write_json(Path(args.out), metrics)
    print(canonical_json({"records": metrics["records"], "out": args.out}))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export-fixtures", help="run every adapter over offline fixtures")
    export.add_argument("--fixture-dir", required=True)
    export.add_argument("--out-dir", required=True)
    export.add_argument("--retrieved-at", required=True)
    export.add_argument("--target-size", type=int, default=250)
    export.set_defaults(func=export_fixtures)

    validate = sub.add_parser("validate", help="validate an observation NDJSON file")
    validate.add_argument("path")
    validate.set_defaults(func=validate_command)

    cohort = sub.add_parser("cohort", help="build a deterministic cohort manifest")
    cohort.add_argument("--seeds", required=True)
    cohort.add_argument("--target-size", type=int, default=250)
    cohort.add_argument("--generated-at", required=True)
    cohort.add_argument("--out", required=True)
    cohort.set_defaults(func=cohort_command)

    policies = sub.add_parser("policies", help="write the source policy registry")
    policies.add_argument("--out", required=True)
    policies.set_defaults(func=policies_command)

    metrics = sub.add_parser("metrics", help="measure existing observation NDJSON")
    metrics.add_argument("--observations", required=True)
    metrics.add_argument("--manifest")
    metrics.add_argument("--out", required=True)
    metrics.set_defaults(func=metrics_command)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
