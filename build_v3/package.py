#!/usr/bin/env python3
"""Release packaging: compressed asset, checksums, manifest, provenance receipt.

The graph ships as a RELEASE ASSET, never in git -- the repository's own
.gitignore explains why: "a 688MB database committed once is 688MB forever".
This module produces the things that make such an asset trustworthy once it
leaves the repo, and deliberately does NOT upload anything. Both specs are
explicit: "Do not upload a production asset."

A release consists of four artifacts:

  <name>.sqlite.gz      the compressed database
  <name>.sha256         checksums of both the raw and compressed forms
  <name>.manifest.json  what was built, from which sources, under which rights
  <name>.receipt.json   the provenance receipt -- digests, counts, validation

The receipt is the important one. A consumer who has the asset and the receipt
can verify that the database they hold is logically the one that was built and
validated, without trusting the publisher's description of it.

gzip is written with mtime=0. Without that, the compressed bytes embed the
current time and two packagings of an identical database differ -- which would
reintroduce, at the packaging layer, exactly the non-determinism the build layer
just removed.
"""
import argparse
import gzip
import hashlib
import json
import os
import pathlib
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_v3 import digest as digest_mod  # noqa: E402
from build_v3 import manifest as manifest_mod  # noqa: E402
from build_v3 import validate as validate_mod  # noqa: E402

PACKAGE_VERSION = "pg-release-package-0.1"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def compress(src, dest):
    """gzip with a zeroed mtime, so packaging is itself reproducible."""
    with open(src, "rb") as fin, open(dest, "wb") as fout:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fout, mtime=0) as gz:
            shutil.copyfileobj(fin, gz)
    return dest


def package(graph_db, out_dir, name="people-graph-v2", manifests_dir=None,
            built_at=None):
    graph_db = pathlib.Path(graph_db)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    built_at = built_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    dig = digest_mod.logical_digest(str(graph_db))
    report = validate_mod.validate(str(graph_db), manifests_dir)

    # A failing validation must not be silently packaged. Refusing here is the
    # difference between a release process and a copy command.
    if report["status"] == "fail":
        raise RuntimeError(
            f"refusing to package a database that fails validation: "
            f"{report['failed_stages']}")

    gz_path = out / f"{name}.sqlite.gz"
    compress(graph_db, gz_path)

    raw_sha = _sha256(graph_db)
    gz_sha = _sha256(gz_path)
    (out / f"{name}.sha256").write_text(
        f"{raw_sha}  {name}.sqlite\n{gz_sha}  {name}.sqlite.gz\n")

    sources = [m.to_dict() for m in manifest_mod.load_all(manifests_dir)] \
        if manifests_dir else []
    (out / f"{name}.manifest.json").write_text(
        json.dumps({"package_version": PACKAGE_VERSION, "name": name,
                    "built_at": built_at, "sources": sources},
                   indent=2, sort_keys=True) + "\n")

    receipt = {
        "package_version": PACKAGE_VERSION,
        "name": name,
        "built_at": built_at,
        "logical_digest": dig["overall"],
        "digest_version": dig["digest_version"],
        "table_digests": dig["tables"],
        "row_counts": dig["counts"],
        "total_rows": dig["total_rows"],
        "sha256_raw": raw_sha,
        "sha256_gz": gz_sha,
        "bytes_raw": graph_db.stat().st_size,
        "bytes_gz": gz_path.stat().st_size,
        "validation_status": report["status"],
        "validation_warnings": report["warned_stages"],
        "source_count": len(sources),
        "verify_command": (
            f"gunzip -c {name}.sqlite.gz > {name}.sqlite && "
            f"python3 build_v3/digest.py {name}.sqlite  "
            f"# 'overall' must equal logical_digest above"),
        "note": "Byte identity of the .sqlite file is NOT a release invariant; "
                "logical_digest is. See docs/handoffs/reproducible-builds.md.",
    }
    (out / f"{name}.receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    return {
        "out_dir": str(out),
        "artifacts": sorted(p.name for p in out.iterdir()),
        "logical_digest": dig["overall"],
        "validation_status": report["status"],
        "uploaded": False,
        "upload_note": "This tool never uploads. Publishing is a separate, "
                       "deliberate human step.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", default="people-graph-v2")
    ap.add_argument("--manifests")
    ap.add_argument("--built-at")
    a = ap.parse_args()
    print(json.dumps(package(a.graph, a.out_dir, a.name, a.manifests, a.built_at),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
