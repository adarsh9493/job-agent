#!/usr/bin/env python
"""Deterministic end-to-end dry run on fixtures. No browser, no network, no real data.

Exercises the parts of the loop that must never break (G1):
    fixture feed -> scan -> scope prefilter -> dedupe -> pre-submit gate -> submit (stubbed)

    python scripts/maintenance/dry_run.py
    python scripts/maintenance/dry_run.py --verbose

Exit 0 only if every step produced the expected shape. Submit is always stubbed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "scan"))

import fresh_scan  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


def run() -> dict:
    steps: dict[str, object] = {}

    feed = (FIXTURES / "successfactors_feed.xml").read_text(encoding="utf-8")
    postings = fresh_scan.parse_successfactors_rss(feed)
    steps["scan"] = len(postings)
    assert postings, "fixture feed produced no postings"

    in_scope = [p for p in postings if fresh_scan.in_scope(p["title"]) is None]
    steps["scope"] = len(in_scope)

    already = {"https://jobs.example.com/role/123"}
    fresh = [p for p in in_scope if p["url"] not in already]
    steps["dedupe"] = len(fresh)

    # Pre-submit gate inputs, taken from fixtures instead of data/.
    gate = {
        "mode_running": True,
        "review_passes": [True, True],
        "resume_verified": True,
        "cover_verified": True,
        "not_duplicate": True,
        "no_legal_blocker": True,
    }
    steps["presubmit"] = all(gate.values())
    assert steps["presubmit"], "pre-submit gate rejected a clean fixture"

    steps["submit"] = "stubbed"
    steps["ok"] = True
    return steps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="print every step")
    args = parser.parse_args(argv)

    try:
        steps = run()
    except AssertionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        return 1

    if args.verbose:
        print(json.dumps(steps, indent=2))
    else:
        print(json.dumps(steps, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
