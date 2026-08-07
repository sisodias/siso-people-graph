#!/usr/bin/env python3
"""Run the isolated parallel-integration suite and contract self-check."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    suite = unittest.defaultTestLoader.discover(
        str(root / "tests/integration_parallel"), pattern="test_*.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    completed = subprocess.run(
        [sys.executable, "-m", "integration", "--compact", "check", "--repo-root", str(root)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.stdout:
        try:
            report = json.loads(completed.stdout)
        except json.JSONDecodeError:
            print(completed.stdout, end="")
        else:
            print(
                json.dumps(
                    {
                        "contract_check": report.get("valid"),
                        "records": report.get("contract_fixture", {}).get("record_count"),
                        "lanes": report.get("lane_registry", {}).get("lane_count"),
                        "blocking_risks": report.get("blocking_risk_count"),
                        "rerun_command": report.get("rerun_command"),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
