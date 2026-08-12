#!/usr/bin/env python3
"""Repository path resolution, and the environment overrides that replace it.

This module exists because of one concrete failure. `build_people_graph_v2.py`
computed its schema location as `dirname(__file__)/people_schema_v2.sql` -- that
is `loaders/people_schema_v2.sql`, but the tracked file is `schema/people_schema_v2.sql`.
The build therefore worked only on a machine where an untracked copy happened to
sit beside the loader. On a clean checkout it raised FileNotFoundError before
reading a single byte of input:

    FileNotFoundError: .../loaders/people_schema_v2.sql

That is the whole class of bug this file is meant to close: a path that is
correct in one person's working directory and nowhere else. The rules here are

  1. Locate the repository root by walking up from THIS file, not from the
     caller's cwd, so a loader invoked from anywhere resolves identically.
  2. Resolve every well-known artifact through a named function, so a moved file
     is one edit here rather than a grep across loaders.
  3. Allow an environment override for each one, so an operator can point a
     build at a vault, a scratch copy or a fixture WITHOUT that topology being
     hard-coded in public source. The default is the repository layout; the
     override is the private deployment.

No path in this file names a machine, a user, a mount point or a vault.
"""
import os
import pathlib

# The repo root is two levels up from build_v3/paths.py. Anchoring on __file__
# rather than cwd is the point: `cd /tmp && python3 /repo/loaders/x.py` must
# resolve exactly as `cd /repo && python3 loaders/x.py` does.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _env_path(var, default):
    """An override wins, otherwise the in-repo default.

    Overrides are absolute-or-relative-to-cwd by design: the operator supplying
    one knows where their data is, and we must not silently reinterpret it.
    """
    raw = os.environ.get(var)
    if raw:
        return pathlib.Path(raw).expanduser().resolve()
    return default


def schema_v2():
    """The v2 SQL schema. Override: PG_SCHEMA_V2.

    This is the path that was broken. It lives in schema/, not loaders/.
    """
    return _env_path("PG_SCHEMA_V2", REPO_ROOT / "schema" / "people_schema_v2.sql")


def manifests_dir():
    """Where source manifests live. Override: PG_MANIFESTS_DIR."""
    return _env_path("PG_MANIFESTS_DIR", REPO_ROOT / "manifests")


def build_dir():
    """Working directory for build outputs. Override: PG_BUILD_DIR.

    Defaults OUTSIDE the repo tree is wrong (surprising); defaults inside it is
    also wrong (gitignored churn). We default to ./build-out relative to cwd so
    two builds in two directories are naturally independent -- which is exactly
    what the two-run reproducibility proof needs.
    """
    return _env_path("PG_BUILD_DIR", pathlib.Path.cwd() / "build-out")


def require(path, what):
    """Fail with a message that says what to do, not merely what went wrong.

    A clean-checkout failure should never again be a bare FileNotFoundError with
    a path the reader cannot place.
    """
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{what} not found at {p}.\n"
            f"  repo root resolved to: {REPO_ROOT}\n"
            f"  set an override if this artifact lives elsewhere."
        )
    return p
