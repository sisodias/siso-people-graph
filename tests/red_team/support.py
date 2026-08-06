"""Shared standard-library helpers for the People Graph red-team fixtures."""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable

BASELINE_COMMIT = "de048bb3b34bf931b56fd741cb46c1334acdfb98"

BOOK_BASELINE_COMMIT = "be9ab0831b9ea8802d6898f3a3dfa8a61c63e80b"

@dataclass(frozen=True)
class Case:
    case_id: str
    title: str
    expectation: str  # PASS or EXPECTED_FAILURE
    invariant: str
    finding_ids: tuple[str, ...]
    run: Callable[["Context"], tuple[bool, dict[str, Any]]]

@dataclass
class Result:
    case_id: str
    title: str
    status: str
    expectation: str
    invariant: str
    finding_ids: list[str]
    evidence: dict[str, Any]
    elapsed_ms: int

class Context:
    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()
        self.fixture_dir = self.repo / "tests" / "red_team" / "fixtures"
        self._module_counter = 0

    def production(self, relative: str) -> Path:
        path = self.repo / relative
        if not path.is_file():
            raise FileNotFoundError(f"required production file is missing: {path}")
        return path

    def fixture(self, name: str) -> Path:
        path = self.fixture_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"required fixture is missing: {path}")
        return path

    def module(self, relative: str) -> Any:
        path = self.production(relative)
        self._module_counter += 1
        name = f"pg_red_team_{path.stem}_{self._module_counter}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def schema_text(self) -> str:
        return self.production("schema/people_schema_v2.sql").read_text(encoding="utf-8")

@contextlib.contextmanager
def quiet_stdio() -> Iterable[None]:
    """Silence production progress output while preserving fixture evidence."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield

def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def make_graph(ctx: Context, path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        con.executescript(ctx.schema_text())
        con.commit()
    finally:
        con.close()

def add_person(
    con: sqlite3.Connection,
    person_id: str,
    name: str,
    *,
    kind: str = "human",
    state: str = "linked",
    origin: str = "registry",
    rank_score: float | None = None,
    birth_year: int | None = None,
    death_year: int | None = None,
    built_at: str = "2026-08-01T00:00:00Z",
) -> None:
    con.execute(
        """INSERT INTO person
           (person_id,name,kind,state,origin,rank_score,birth_year,death_year,built_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            person_id,
            name,
            kind,
            state,
            origin,
            rank_score,
            birth_year,
            death_year,
            built_at,
        ),
    )

def make_v1(path: Path, people: list[tuple[str, str, str, str | None, float | None]]) -> None:
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            CREATE TABLE person (
              person_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              origin TEXT NOT NULL,
              primary_tier TEXT,
              rank_score REAL
            );
            CREATE TABLE person_content (
              person_id TEXT NOT NULL,
              domain TEXT NOT NULL,
              content_ref TEXT NOT NULL,
              score REAL,
              title TEXT,
              meta_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE external_ids (
              person_id TEXT NOT NULL,
              platform TEXT NOT NULL,
              value TEXT NOT NULL
            );
            """
        )
        con.executemany("INSERT INTO person VALUES (?,?,?,?,?)", people)
        con.commit()
    finally:
        con.close()

def make_book_people(
    path: Path,
    people: list[tuple[str, str, int | None, int | None, int, int, str]],
    edges: list[tuple[str, int, str]],
) -> None:
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            CREATE TABLE person (
              person_key TEXT PRIMARY KEY,
              display_name TEXT NOT NULL,
              birth_year INTEGER,
              death_year INTEGER,
              work_count INTEGER NOT NULL,
              is_corporate INTEGER NOT NULL DEFAULT 0,
              raw_variants TEXT NOT NULL DEFAULT '[]'
            );
            CREATE TABLE person_work (
              person_key TEXT NOT NULL,
              gid INTEGER NOT NULL,
              role TEXT NOT NULL
            );
            """
        )
        con.executemany("INSERT INTO person VALUES (?,?,?,?,?,?,?)", people)
        con.executemany("INSERT INTO person_work VALUES (?,?,?)", edges)
        con.commit()
    finally:
        con.close()

def make_books(
    path: Path,
    books: list[tuple[int, str]],
    subjects: list[tuple[int, str]] | None = None,
) -> None:
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            CREATE TABLE book (gid INTEGER PRIMARY KEY, title TEXT NOT NULL);
            CREATE TABLE book_subject (gid INTEGER NOT NULL, subject TEXT NOT NULL);
            """
        )
        con.executemany("INSERT INTO book VALUES (?,?)", books)
        con.executemany("INSERT INTO book_subject VALUES (?,?)", subjects or [])
        con.commit()
    finally:
        con.close()

def build_v2_with_tracked_schema(
    ctx: Context,
    v1: Path,
    people: Path,
    books: Path,
    out: Path,
) -> dict[str, Any]:
    module = ctx.module("loaders/build_people_graph_v2.py")
    module.SCHEMA = str(ctx.production("schema/people_schema_v2.sql"))
    with quiet_stdio():
        return module.build(str(v1), str(people), str(books), str(out))

def make_identity_source(path: Path, rows: list[tuple[Any, ...]]) -> None:
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            CREATE TABLE repo_card (
              full_name TEXT NOT NULL,
              stars INTEGER,
              language TEXT,
              description TEXT,
              topics_json TEXT,
              url TEXT,
              fork INTEGER
            );
            CREATE TABLE repo_category (
              full_name TEXT NOT NULL,
              overall_value REAL,
              reuse_value REAL
            );
            """
        )
        if rows:
            con.executemany("INSERT INTO repo_card VALUES (?,?,?,?,?,?,?)", rows)
        con.commit()
    finally:
        con.close()
