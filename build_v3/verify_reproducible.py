#!/usr/bin/env python3
"""Two clean builds in separate directories, compared. The acceptance test.

    python3 build_v3/verify_reproducible.py

Both specs set the same bar: "Run two clean fixture builds in separate
directories and show equal logical digest and row counts." This does exactly
that and reports the answer as a measurement, including the binary question,
which it does NOT assume.

Exit code 0 means the logical digests and per-table counts matched. Anything
else means they did not, and the report names the differing tables so the cause
is locatable rather than merely known to exist.
"""
import argparse
import json
import pathlib
import shutil
import sys
import tempfile
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_v3 import build as build_mod  # noqa: E402
from build_v3 import digest as digest_mod  # noqa: E402


def verify(base_dir=None, keep=False):
    tmp = pathlib.Path(base_dir) if base_dir else pathlib.Path(tempfile.mkdtemp(
        prefix="pg-repro-"))
    tmp.mkdir(parents=True, exist_ok=True)
    dir_a, dir_b = tmp / "build-a", tmp / "build-b"

    # Distinct run_ids on purpose. If run metadata leaked into canonical facts,
    # these two builds would differ -- so passing with different run_ids is what
    # proves the separation actually holds, rather than being merely intended.
    res_a = build_mod.build_fixture(dir_a, run_id="run-a")
    res_b = build_mod.build_fixture(dir_b, run_id="run-b")

    dig_a = digest_mod.logical_digest(res_a["graph"])
    dig_b = digest_mod.logical_digest(res_b["graph"])
    cmp = digest_mod.compare(dig_a, dig_b)
    binary = digest_mod.measure_binary_stability(res_a["graph"], res_b["graph"])

    report = {
        "logically_equal": cmp["equal"],
        "counts_equal": cmp["counts_equal"],
        "digest_a": cmp["overall_a"],
        "digest_b": cmp["overall_b"],
        "differing_tables": cmp["differing_tables"],
        "row_counts": dig_a["counts"],
        "total_rows": dig_a["total_rows"],
        "binary_reproducibility": binary,
        "validation_a": res_a["validation_status"],
        "validation_b": res_b["validation_status"],
        "dir_a": str(dir_a),
        "dir_b": str(dir_b),
        "note": (
            "Byte identity of a SQLite file is not the invariant. Page "
            "allocation, freelist state, the header change counter and WAL "
            "checkpoint timing all vary independently of content. Logical "
            "equivalence -- equal per-table digests over sorted rows plus equal "
            "counts -- is the required and asserted property."
        ),
    }
    if not keep and not base_dir:
        shutil.rmtree(tmp, ignore_errors=True)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", help="where to build; default a temp dir")
    ap.add_argument("--keep", action="store_true", help="keep build directories")
    a = ap.parse_args()
    rep = verify(a.dir, a.keep)
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0 if (rep["logically_equal"] and rep["counts_equal"]) else 1


if __name__ == "__main__":
    sys.exit(main())
