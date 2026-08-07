#!/usr/bin/env python3
"""One-command graph build: fixtures or declared sources, validated and digested.

    python3 build_v3/build.py --fixture --out-dir ./build-a

That single command generates fixtures, runs every loader in order, computes the
projections, validates the result, writes the manifests and emits a logical
digest -- with no network, no vault, and no path that exists only on one machine.
Running it twice in two directories and comparing digests is the reproducibility
proof the spec asks for; `verify_reproducible.py` automates exactly that.

WHAT MAKES THE OUTPUT REPRODUCIBLE

Three sources of non-determinism had to be removed, and it is worth naming them
because each was silent:

  1. WALL-CLOCK TIMESTAMPS. Every loader stamped time.gmtime() into observed_at
     and built_at, so two builds differed in every single row. --observed-at
     pins one value for the whole build; the real clock time is recorded in
     build_run, which the digest excludes.
  2. NON-IDEMPOTENT ACCUMULATION. `rank_score = rank_score + x` meant the output
     depended on run count. Observations are keyed and REPLACEd instead.
  3. TIE-BREAKING BY DICT ORDER. A top-25 cut sorted only by count silently
     depended on source row order. Ties now break by name.

What remains non-reproducible is documented honestly in
docs/handoffs/reproducible-builds.md rather than papered over.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_v3 import digest as digest_mod  # noqa: E402
from build_v3 import fixtures as fixtures_mod  # noqa: E402
from build_v3 import manifest as manifest_mod  # noqa: E402
from build_v3 import paths  # noqa: E402
from build_v3 import project as project_mod  # noqa: E402
from build_v3 import validate as validate_mod  # noqa: E402

BUILDER_VERSION = "build_v3/1"
SCHEMA_VERSION = "people_schema_v2"

# A fixed timestamp for fixture builds. Any constant works; what matters is that
# it is the SAME constant across runs, which is what makes rows comparable.
FIXTURE_OBSERVED_AT = "2026-08-06T00:00:00Z"
FIXTURE_RIGHTS = "fixture-synthetic-no-rights-encumbrance"


def _run(cmd, label):
    """Run a loader as a subprocess so the CLI contract is what gets tested.

    Importing the loaders would test the functions; invoking them tests the
    command line the README documents and CI runs, which is the surface that
    actually broke.
    """
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"{label} failed (exit {proc.returncode})\n"
            f"  cmd: {' '.join(cmd)}\n"
            f"  stderr: {proc.stderr[-2000:]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"raw_stdout": proc.stdout[-2000:]}


def build_fixture(out_dir, observed_at=FIXTURE_OBSERVED_AT, run_id=None):
    """Full offline build from generated fixtures."""
    out = pathlib.Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    src_dir = out / "sources"
    graph = out / "people_v2.sqlite"
    repo = paths.REPO_ROOT
    run_id = run_id or f"fixture-{hashlib.sha256(str(out).encode()).hexdigest()[:12]}"

    steps = {}
    fx = fixtures_mod.write_all(src_dir)
    steps["fixtures"] = fx

    steps["build_v2"] = _run([
        sys.executable, str(repo / "loaders" / "build_people_graph_v2.py"),
        "--v1", fx["v1"], "--people", fx["books_people"], "--books", fx["books"],
        "--out", str(graph), "--observed-at", observed_at,
        "--books-snapshot", fixtures_mod.FIXTURE_SNAPSHOT, "--run-id", run_id,
    ], "build_people_graph_v2")

    steps["load_owners"] = _run([
        sys.executable, str(repo / "loaders" / "load_owners_into_people_graph.py"),
        "--identity", fx["identity"], "--graph", str(graph),
        "--min-stars", "100", "--apply", "--observed-at", observed_at,
        "--snapshot", fixtures_mod.FIXTURE_SNAPSHOT,
    ], "load_owners_into_people_graph")

    steps["load_topics"] = _run([
        sys.executable, str(repo / "loaders" / "load_owner_topics.py"),
        "--identity", fx["identity"], "--graph", str(graph),
        "--min-stars", "100", "--apply", "--observed-at", observed_at,
        "--snapshot", fixtures_mod.FIXTURE_SNAPSHOT,
    ], "load_owner_topics")

    # The crates load must run AFTER load_owners: person_person has FK
    # references into person, and a dependency edge can only be written once
    # both owners exist as rows.
    steps["load_crates"] = _run([
        sys.executable, str(repo / "loaders" / "load_crates_into_people_graph.py"),
        "--crates", fx["crates"], "--graph", str(graph),
        "--apply", "--observed-at", observed_at,
        "--snapshot", fixtures_mod.FIXTURE_SNAPSHOT,
    ], "load_crates_into_people_graph")

    steps["projections"] = project_mod.compute_all(
        str(graph), computed_at=observed_at, apply_changes=True)

    # Source manifests describing exactly what went in.
    man_dir = out / "manifests"
    manifests = []
    for source_id, artifact, contracts in (
        ("v1_migration", fx["v1"],
         [manifest_mod.RowContract("person", 1, None, ["person_id", "name"])]),
        ("books", fx["books"],
         [manifest_mod.RowContract("book", 1, None, ["gid", "title"])]),
        ("gutenberg", fx["books_people"],
         [manifest_mod.RowContract("person", 1, None, ["person_key"])]),
        ("github_identity", fx["identity"],
         [manifest_mod.RowContract("repo_card", 1, None, ["full_name", "stars"])]),
        ("repo_card", fx["identity"],
         [manifest_mod.RowContract("repo_card", 1, None, ["full_name", "topics_json"])]),
        ("repo_category", fx["identity"],
         [manifest_mod.RowContract("repo_category", 1, None, ["full_name", "overall_value"])]),
        ("crates_io", fx["crates"],
         [manifest_mod.RowContract("crate", 1, None, ["name", "owner_login"])]),
        ("crates_io_dependencies", fx["crates"],
         [manifest_mod.RowContract("crate_dependency", 1, None, ["crate", "depends_on"])]),
        ("crates_io_teams", fx["crates"],
         [manifest_mod.RowContract("crate_team", 1, None, ["team_login", "crate"])]),
    ):
        m = manifest_mod.SourceManifest(
            source_id=source_id,
            snapshot=fixtures_mod.FIXTURE_SNAPSHOT,
            uri_class="fixture",
            digest=manifest_mod.sha256_file(artifact),
            rights_revision=FIXTURE_RIGHTS,
            acquired_at=observed_at,
            loader_version=BUILDER_VERSION,
            schema_version=SCHEMA_VERSION,
            row_contracts=contracts,
            notes="Synthetic fixture. Contains no real personal data.",
        )
        m.write(man_dir)
        manifests.append(m)
    steps["manifests"] = [m.source_id for m in manifests]

    report = validate_mod.validate(str(graph), man_dir)
    (out / "validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    steps["validation"] = {
        "status": report["status"],
        "failed": report["failed_stages"],
        "warned": report["warned_stages"],
    }

    dig = digest_mod.logical_digest(str(graph))
    (out / "digest.json").write_text(json.dumps(dig, indent=2, sort_keys=True) + "\n")

    result = {
        "out_dir": str(out),
        "graph": str(graph),
        "run_id": run_id,
        "observed_at": observed_at,
        "builder": BUILDER_VERSION,
        "steps": steps,
        "digest": dig["overall"],
        "counts": dig["counts"],
        "validation_status": report["status"],
    }
    (out / "build.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture", action="store_true",
                    help="build from generated fixtures (offline, no real data)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--observed-at", default=FIXTURE_OBSERVED_AT)
    ap.add_argument("--run-id")
    a = ap.parse_args()
    if not a.fixture:
        ap.error(
            "only --fixture builds are supported from a clean checkout. "
            "A full build needs declared source snapshots; see "
            "docs/handoffs/reproducible-builds.md for the documented command."
        )
    t = time.time()
    res = build_fixture(a.out_dir, a.observed_at, a.run_id)
    res["elapsed_s"] = round(time.time() - t, 2)
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0 if res["validation_status"] != "fail" else 1


if __name__ == "__main__":
    sys.exit(main())
