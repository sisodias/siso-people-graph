#!/usr/bin/env python3
"""Deterministic LOGICAL digests over a built graph.

WHY LOGICAL AND NOT BINARY

The obvious way to check that two builds agree is `sha256 a.sqlite b.sqlite`.
That does not work, and claiming it does would be dishonest. A SQLite file is
not a deterministic function of its logical content: page allocation depends on
insertion order, freelist state carries the ghosts of deleted rows, the header
holds a change counter, WAL checkpointing timing affects layout, and the
`sqlite_sequence` value for an AUTOINCREMENT table advances even across
identical logical outcomes.

So this module computes a digest over what the database MEANS rather than how it
is laid out:

  * every canonical table, in a fixed table order
  * every row within a table, sorted by its full tuple
  * every value rendered through one explicit, typed rule
  * excluding tables that legitimately differ between runs (build_run)

Two builds are "logically equivalent" when these digests match and per-table
counts match. That is the invariant the spec requires when byte identity is not
stable, and `measure_binary_stability` below reports the byte question honestly
rather than assuming an answer.

The digest is per-table as well as overall, because a single mismatching hash
tells you only that something differs; a per-table breakdown tells you where.
"""
import hashlib
import json
import sqlite3

DIGEST_VERSION = "pg-logical-digest-0.1"

# Tables that MUST NOT enter the digest, with the reason each is excluded.
# An exclusion is a claim about reproducibility, so each one is justified here
# rather than being an unexplained skip.
EXCLUDED_TABLES = {
    # Run metadata is expected to differ between runs -- that is its purpose.
    "build_run",
    # SQLite internals, not content.
    "sqlite_sequence",
    "sqlite_stat1",
    "sqlite_stat4",
}

# FTS5 creates shadow tables whose contents depend on internal segment merging.
# The logical content they index is already digested via the base table, so
# digesting the shadows would add non-determinism without adding coverage.
FTS_SHADOW_SUFFIXES = (
    "_data", "_idx", "_content", "_docsize", "_config", "_row",
)


def _is_fts_shadow(name, all_tables):
    for suffix in FTS_SHADOW_SUFFIXES:
        if name.endswith(suffix):
            base = name[: -len(suffix)]
            if base in all_tables:
                return True
    return False


def _render(value):
    """One explicit rule per type, so rendering never depends on locale or repr.

    Floats are the subtle case. repr(float) varies in trailing-digit behaviour
    across contexts, and a value that arrives as 3.0 in one run and 3 in another
    is the SAME measurement. We normalise via repr of the float, which in Python
    3 round-trips exactly, and normalise integral floats to a single form so
    3 and 3.0 do not produce different digests.
    """
    if value is None:
        return "\x00NULL"
    if isinstance(value, bool):
        return "\x00B" + ("1" if value else "0")
    if isinstance(value, int):
        return "\x00I" + str(value)
    if isinstance(value, float):
        if value == int(value) and abs(value) < 2**53:
            return "\x00I" + str(int(value))
        return "\x00F" + repr(value)
    if isinstance(value, bytes):
        return "\x00X" + value.hex()
    return "\x00S" + str(value)


def _table_names(conn):
    rows = conn.execute(
        "SELECT name, type FROM sqlite_master "
        "WHERE type IN ('table') ORDER BY name"
    ).fetchall()
    names = {r[0] for r in rows}
    keep = []
    for name in sorted(names):
        if name in EXCLUDED_TABLES:
            continue
        if name.startswith("sqlite_"):
            continue
        if _is_fts_shadow(name, names):
            continue
        keep.append(name)
    return keep


def _column_names(conn, table):
    # Sorted so a column added in a different position does not reorder the
    # digest input for unrelated columns.
    return sorted(r[1] for r in conn.execute(f"PRAGMA table_info({table})"))


def table_digest(conn, table):
    """(digest, row_count) for one table.

    Rows are sorted by their rendered tuple rather than by a primary key,
    because not every table has a usable one and ORDER BY over all columns is
    the only ordering guaranteed to be total.
    """
    cols = _column_names(conn, table)
    if not cols:
        return hashlib.sha256(b"").hexdigest(), 0
    col_sql = ", ".join(f'"{c}"' for c in cols)
    rows = conn.execute(f'SELECT {col_sql} FROM "{table}"').fetchall()
    rendered = sorted("\x01".join(_render(v) for v in row) for row in rows)
    h = hashlib.sha256()
    # The header binds the digest to the column set: two tables with identical
    # values under different column names must not collide.
    h.update(("\x02".join(cols) + "\x03").encode("utf-8"))
    for line in rendered:
        h.update(line.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest(), len(rows)


def logical_digest(db_path):
    """Full logical fingerprint of a built graph.

    Returns a dict carrying the overall digest, per-table digests and per-table
    row counts -- the three things the acceptance criterion asks to compare.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        tables = _table_names(conn)
        per_table = {}
        counts = {}
        for t in tables:
            d, n = table_digest(conn, t)
            per_table[t] = d
            counts[t] = n
        overall = hashlib.sha256()
        overall.update((DIGEST_VERSION + "\n").encode("utf-8"))
        for t in tables:
            overall.update(f"{t}\x01{per_table[t]}\x01{counts[t]}\n".encode("utf-8"))
        return {
            "digest_version": DIGEST_VERSION,
            "overall": overall.hexdigest(),
            "tables": per_table,
            "counts": counts,
            "total_rows": sum(counts.values()),
        }
    finally:
        conn.close()


def compare(a, b):
    """Diff two digest reports into something a human can act on."""
    tables = sorted(set(a["tables"]) | set(b["tables"]))
    differing = []
    for t in tables:
        da, db_ = a["tables"].get(t), b["tables"].get(t)
        if da != db_:
            differing.append({
                "table": t,
                "digest_a": da,
                "digest_b": db_,
                "count_a": a["counts"].get(t),
                "count_b": b["counts"].get(t),
            })
    return {
        "equal": a["overall"] == b["overall"],
        "overall_a": a["overall"],
        "overall_b": b["overall"],
        "counts_equal": a["counts"] == b["counts"],
        "differing_tables": differing,
    }


def measure_binary_stability(path_a, path_b):
    """Report byte identity as a MEASUREMENT, never as an assumption.

    The spec asks to "measure binary SQLite reproducibility honestly". This
    returns what is actually true of these two files, so the answer in the
    handoff is observed rather than asserted.
    """
    def sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()

    import os
    sa, sb = sha(path_a), sha(path_b)
    return {
        "byte_identical": sa == sb,
        "sha256_a": sa,
        "sha256_b": sb,
        "size_a": os.path.getsize(path_a),
        "size_b": os.path.getsize(path_b),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Compute a logical digest of a graph.")
    ap.add_argument("db")
    ap.add_argument("--compare-to", help="second database; prints a comparison")
    a = ap.parse_args()
    rep = logical_digest(a.db)
    if a.compare_to:
        other = logical_digest(a.compare_to)
        out = {
            "a": rep,
            "b": other,
            "comparison": compare(rep, other),
            "binary": measure_binary_stability(a.db, a.compare_to),
        }
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out["comparison"]["equal"] else 1
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
