#!/usr/bin/env python3
"""Source manifests: what went into a build, precisely enough to rebuild it.

A build is reproducible only if its INPUTS are identified exactly. "We loaded
the GitHub corpus" is not an input identification -- it does not say which
snapshot, whether the file changed underneath, what we were permitted to do with
it, or what the loader expected to find inside.

A manifest answers all of that for one source:

  source_id        stable name for the source, e.g. 'github_identity'
  snapshot         the exact revision/snapshot identifier of that source
  uri_class        the CLASS of acquisition URI, never the URI itself
  digest           sha256 of the source artifact as acquired
  rights_revision  which terms/licence revision governed this acquisition
  acquired_at      when we obtained it
  loader_version   which loader consumed it
  schema_version   which target schema it was loaded into
  row_contract     what the loader expects to find: tables, and count bounds

uri_class deserves its reason. A manifest is a PUBLIC artifact in a public
repository; a literal acquisition URI would publish vault topology -- the exact
thing the spec forbids. So we record that a source arrived as, say, a
'local_sqlite_snapshot' or an 'https_api_export', which is what a reader needs
in order to reproduce the KIND of acquisition, and we record the digest, which
is what proves they got the same bytes. Where the file actually sits on a given
machine is an environment override (see build_v3/paths.py), not a published fact.

row_contract is the guard against a silent input swap. If a loader expects
repo_card to exist with at least one row and it arrives empty, the build must
fail loudly at validation rather than emit a technically-valid empty graph and
call it a successful reproduction.
"""
import dataclasses
import hashlib
import json
import pathlib
import typing

MANIFEST_VERSION = "pg-source-manifest-0.1"

# Acquisition classes. Deliberately coarse -- this describes HOW a source was
# obtained, not WHERE it lives.
URI_CLASSES = (
    "local_sqlite_snapshot",   # a SQLite file taken from a local corpus store
    "https_api_export",        # pulled from a documented HTTP API
    "https_bulk_download",     # a published bulk file
    "fixture",                 # a tiny synthetic input, for tests and CI
)


def sha256_file(path, chunk=1 << 20):
    """Digest a file. Streaming, because corpus snapshots run to hundreds of MB."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


@dataclasses.dataclass
class RowContract:
    """What a loader requires of a source before it will trust it.

    min_rows defaults to 1 rather than 0 on purpose: an empty table is nearly
    always a broken acquisition rather than a real state of the world, and the
    failure we are guarding against is a build that succeeds on no data.
    """
    table: str
    min_rows: int = 1
    max_rows: typing.Optional[int] = None
    required_columns: typing.List[str] = dataclasses.field(default_factory=list)

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(
            table=d["table"],
            min_rows=d.get("min_rows", 1),
            max_rows=d.get("max_rows"),
            required_columns=list(d.get("required_columns", [])),
        )


@dataclasses.dataclass
class SourceManifest:
    source_id: str
    snapshot: str
    uri_class: str
    digest: str
    rights_revision: str
    acquired_at: str
    loader_version: str
    schema_version: str
    row_contracts: typing.List[RowContract] = dataclasses.field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        if self.uri_class not in URI_CLASSES:
            raise ValueError(
                f"uri_class {self.uri_class!r} not one of {URI_CLASSES}. "
                "Add a class rather than recording a literal URI."
            )

    def to_dict(self):
        d = dataclasses.asdict(self)
        d["manifest_version"] = MANIFEST_VERSION
        d["row_contracts"] = [c.to_dict() for c in self.row_contracts]
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(
            source_id=d["source_id"],
            snapshot=d["snapshot"],
            uri_class=d["uri_class"],
            digest=d["digest"],
            rights_revision=d["rights_revision"],
            acquired_at=d["acquired_at"],
            loader_version=d["loader_version"],
            schema_version=d["schema_version"],
            row_contracts=[RowContract.from_dict(c) for c in d.get("row_contracts", [])],
            notes=d.get("notes", ""),
        )

    def write(self, directory):
        directory = pathlib.Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.source_id}.manifest.json"
        # sort_keys so a manifest is itself byte-stable -- a manifest that
        # reordered between writes would defeat the digest it is meant to support.
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")
        return path

    @classmethod
    def read(cls, path):
        return cls.from_dict(json.loads(pathlib.Path(path).read_text()))


def load_all(directory):
    """Every manifest in a directory, ordered by source_id for determinism."""
    directory = pathlib.Path(directory)
    if not directory.exists():
        return []
    return sorted(
        (SourceManifest.read(p) for p in directory.glob("*.manifest.json")),
        key=lambda m: m.source_id,
    )


def verify_digest(manifest, actual_path):
    """Confirm the artifact on disk is the one the manifest describes.

    Returns (ok, actual_digest). The caller decides whether a mismatch is fatal;
    for a release build it must be, for an exploratory run it may not be.
    """
    actual = sha256_file(actual_path)
    return actual == manifest.digest, actual
