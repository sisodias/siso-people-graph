"""Where the databases are -- explicit configuration, not machine guessing.

The old ask.py carried a hardcoded list of paths including one developer's home
directory and a specific external volume. That is invisible policy: the same
command answers differently on two machines and nothing in the output says why.

Resolution order, first hit wins:
  1. explicit paths passed by the caller
  2. PEOPLE_GRAPH_CONFIG -- a JSON file mapping domain -> path
  3. PEOPLE_GRAPH_<DOMAIN> environment variables
  4. ./<domain>.sqlite relative to the working directory (the fixture default)

The resolved path for every attached domain is reported in the response, so the
answer to "why did this machine say something different" is always in the output
rather than in someone's shell history.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

DOMAINS = ("people", "books", "github", "awesome", "locator")

# Filenames looked for under the working directory when nothing is configured.
# Kept deliberately small: this is the fixture path, not a corpus search.
DEFAULT_FILENAMES = {
    "people": ("people_v2.sqlite", "people.sqlite"),
    "books": ("books.sqlite",),
    "github": ("identity.sqlite",),
    "awesome": ("awesome_catalog.sqlite",),
    "locator": ("locator.sqlite",),
}


@dataclass
class Config:
    paths: dict[str, str] = field(default_factory=dict)
    origins: dict[str, str] = field(default_factory=dict)
    root: str = "."
    budget_rows: int = 500
    timeout_ms: int = 5000

    def as_dict(self) -> dict:
        return {
            "resolved_paths": dict(sorted(self.paths.items())),
            "path_origins": dict(sorted(self.origins.items())),
            "row_budget": self.budget_rows,
            "timeout_ms": self.timeout_ms,
        }


def load(explicit: dict[str, str] | None = None, root: str | None = None,
         env: dict[str, str] | None = None) -> Config:
    env = os.environ if env is None else env
    root = root or env.get("PEOPLE_GRAPH_ROOT") or "."
    cfg = Config(root=root)

    if explicit:
        for domain, path in explicit.items():
            if path and os.path.exists(path):
                cfg.paths[domain] = os.path.abspath(path)
                cfg.origins[domain] = "explicit"

    conf_file = env.get("PEOPLE_GRAPH_CONFIG")
    if conf_file and os.path.exists(conf_file):
        try:
            with open(conf_file, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            data = {}
        for domain, path in (data.get("domains") or {}).items():
            if domain in cfg.paths:
                continue
            full = os.path.expanduser(str(path))
            if os.path.exists(full):
                cfg.paths[domain] = os.path.abspath(full)
                cfg.origins[domain] = f"config:{conf_file}"

    for domain in DOMAINS:
        if domain in cfg.paths:
            continue
        val = env.get(f"PEOPLE_GRAPH_{domain.upper()}")
        if val:
            full = os.path.expanduser(val)
            if os.path.exists(full):
                cfg.paths[domain] = os.path.abspath(full)
                cfg.origins[domain] = "env"

    for domain in DOMAINS:
        if domain in cfg.paths:
            continue
        for fn in DEFAULT_FILENAMES.get(domain, ()):
            candidate = os.path.join(root, fn)
            if os.path.exists(candidate):
                cfg.paths[domain] = os.path.abspath(candidate)
                cfg.origins[domain] = "default_local"
                break

    budget = env.get("PEOPLE_GRAPH_ROW_BUDGET")
    if budget and budget.isdigit():
        cfg.budget_rows = int(budget)
    return cfg
