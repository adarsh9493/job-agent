#!/usr/bin/env python
"""Preflight guard: refuse a role that breaks a hard rule.

    python scripts/runtime/guard.py --company "Lucid Motors" --title "ADAS Validation Engineer" \
        --job-id 4009378007 --url https://boards.greenhouse.io/lucid/jobs/4009378007

Checks, in order: session is running, the run lock is held, the company is on the approved list,
the title is not a manager/director role, the role is not already in the tracker, no legal blocker
is pending, and the job folder exists when one is given. Prints one JSON line; exit 1 means stop
this application and move on.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import DATA, STATE_PATH, emit, norm, read_json
import checkpoint
import companies
import tracker

SCAN_DIR = Path(__file__).resolve().parents[1] / "scan"
if str(SCAN_DIR) not in sys.path:
    sys.path.insert(0, str(SCAN_DIR))
from fresh_scan import MGR_OUT

LEGAL_BLOCKERS = DATA / "profile" / "legal-blockers.json"
LOCK = DATA / "state" / "run.lock"


def _legal_blocker(company: str, job_id=None, title=None):
    payload = read_json(LEGAL_BLOCKERS, default={}) or {}
    blockers = payload.get("blockers") if isinstance(payload, dict) else payload
    for blocker in blockers or []:
        if not isinstance(blocker, dict):
            continue
        if norm(blocker.get("company")) != norm(company):
            continue
        blocker_id = blocker.get("job_id")
        blocker_title = blocker.get("job_title") or blocker.get("title")
        if job_id and blocker_id and norm(blocker_id) != norm(job_id):
            continue
        if not job_id and title and blocker_title and norm(blocker_title) != norm(title):
            continue
        return blocker
    return None


def _duplicate(company: str, job_id=None, url=None, title=None) -> dict:
    try:
        result = tracker.has_applied(company, job_id=job_id, url=url, title=title)
        if not isinstance(result, dict) or not isinstance(result.get("applied"), bool):
            return {"applied": False, "error": "tracker returned an invalid duplicate-check result"}
        return result
    except Exception as error:
        return {"applied": False, "error": f"tracker unavailable: {error}"}


def evaluate(company: str, title=None, job_id=None, url=None, folder=None,
             require_lock: bool = True) -> dict:
    if not company or not company.strip():
        return {"ok": False, "check": "company", "reason": "company is required"}

    state = read_json(STATE_PATH, default=None)
    if not isinstance(state, dict):
        return {"ok": False, "check": "state",
                "reason": "session state is missing; run checkpoint.py init"}
    if state.get("mode") != "running":
        return {"ok": False, "check": "mode",
                "reason": f"session mode is {state.get('mode')!r}, not 'running'"}

    if require_lock:
        status = checkpoint.lock_status(LOCK)
        if not status.get("held"):
            return {"ok": False, "check": "lock",
                    "reason": "run lock is not held; start with checkpoint.py set-mode running"}

    try:
        found = companies.show(company)
    except Exception as error:
        return {"ok": False, "check": "company",
                "reason": f"approved-company list unavailable: {error}"}
    if not found:
        return {"ok": False, "check": "company",
                "reason": f"{company} is not on the approved company list"}

    if title and MGR_OUT.search(title):
        return {"ok": False, "check": "title",
                "reason": f"manager/director title is excluded: {title}"}

    duplicate = _duplicate(company, job_id, url, title)
    if duplicate.get("error"):
        return {"ok": False, "check": "duplicate", "reason": duplicate["error"]}
    if duplicate.get("applied"):
        return {"ok": False, "check": "duplicate",
                "reason": (f"already applied on {duplicate.get('date')} "
                           f"({duplicate.get('status')})")}

    blocker = _legal_blocker(company, job_id, title)
    if blocker:
        question = str(blocker.get("question_text") or "").strip()
        return {"ok": False, "check": "legal",
                "reason": "legal blocker pending: " + (question[:160] or "see legal-blockers.json")}

    if folder and not Path(folder).is_dir():
        return {"ok": False, "check": "folder", "reason": f"job folder does not exist: {folder}"}

    classification = found.get("classification") or {}
    result = {
        "ok": True,
        "company": found.get("name") or company,
        "industry": classification.get("verdict"),
        "stale": found.get("stale"),
        "checks": {"mode": "running", "lock": "held", "approved": True,
                   "title": "ok", "duplicate": "none", "legal": "clear"},
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--company", required=True)
    parser.add_argument("--title")
    parser.add_argument("--job-id")
    parser.add_argument("--url")
    parser.add_argument("--folder")
    parser.add_argument("--allow-unlocked", action="store_true",
                        help="skip the run-lock check (recovery/debug only)")
    args = parser.parse_args(argv)

    result = evaluate(args.company, args.title, args.job_id, args.url, args.folder,
                      require_lock=not args.allow_unlocked)
    emit(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
