#!/usr/bin/env python
"""Run every maintenance gate in order and print one line of JSON.

    python scripts/maintenance/validate_all.py
    python scripts/maintenance/validate_all.py --verbose

Gates: unit tests, adapter sync, context budgets, deterministic dry run.
Exit code 0 only when every gate passes - this is the MAINTAIN-mode gate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GATES = (
    ("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
    ("adapters", [sys.executable, "scripts/maintenance/sync_adapters.py", "--check"]),
    ("context", [sys.executable, "scripts/maintenance/context_report.py"]),
    ("dry_run", [sys.executable, "scripts/maintenance/dry_run.py"]),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="show each gate's output")
    args = parser.parse_args(argv)

    results = {}
    for name, command in GATES:
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False
        )
        results[name] = completed.returncode == 0
        if args.verbose or completed.returncode != 0:
            tail = (completed.stdout + completed.stderr).strip().splitlines()[-8:]
            for line in tail:
                print(f"[{name}] {line}", file=sys.stderr)

    payload = {"ok": all(results.values()), "gates": results}
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
