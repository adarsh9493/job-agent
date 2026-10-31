#!/usr/bin/env python
"""One-screen session briefing - the first thing a run reads.

    python scripts/runtime/boot.py            # compact JSON briefing (<= 2048 bytes)
    python scripts/runtime/boot.py --measure  # same payload, used by the context budget gate

The briefing answers only what the next decision needs: mode, current job/step, queue head,
rotating cursor, the next approved company, interview blocks, legal blockers, and whether a run
lock is held. It never prints or reads a large data file. Missing files are reported, not fatal,
so a brand-new clone can still boot.
"""
from __future__ import annotations

import argparse
import json
from datetime import date

from _common import DATA, STATE_PATH, read_json
import checkpoint
import state as state_module

LEGAL_BLOCKERS = DATA / "profile" / "legal-blockers.json"
LOCK = DATA / "state" / "run.lock"
BRIEF_LIMIT = 2048


def next_company(state_payload: dict):
    """First non-blocked approved company from the saved rotating cursor."""
    try:
        import sweep
        cursor = (state_payload.get("sweep") or {}).get("cursor")
        for entry in sweep.plan(date.today(), cursor=cursor):
            if not entry.get("interview_blocked"):
                return entry["company"]
    except Exception:
        return None
    return None


def _blocker_count(payload) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("blockers", "pending", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
    return 0


def _compact(payload: dict) -> dict:
    return {
        key: value for key, value in payload.items()
        if value not in (None, "", [], {}, 0, False) or key == "mode"
    }


def build(state_payload: dict | None = None) -> dict:
    if state_payload is None:
        state_payload = read_json(STATE_PATH, default={}) or {}
    hot = state_module.fit(state_module.hot_payload(state_payload))
    lock = checkpoint.lock_status(LOCK)
    counters = hot.get("session") or {}
    brief = {
        "mode": state_payload.get("mode") or "missing",
        "since": (state_payload.get("started_at") if state_payload.get("mode") == "running"
                  else state_payload.get("last_stop_at")),
        "session": {
            key: counters.get(key) for key in ("applied", "submitted", "skipped",
                                               "failed", "manual_needed")
            if counters.get(key)
        },
        "current": hot.get("current") or {},
        "queue": (hot.get("queue") or [])[:2],
        "queue_len": hot.get("queue_len"),
        "cursor": hot.get("cursor"),
        "next": next_company(state_payload),
        "blocked": hot.get("interview_blocked") or [],
        "needs_user": hot.get("needs_user"),
        "onboarding": bool(state_payload.get("onboarding_confirmed")),
        "companies": bool(state_payload.get("companies_approved")),
        "legal_blockers": _blocker_count(read_json(LEGAL_BLOCKERS, default=None)),
        "lock": "free" if not lock.get("held") else f"held:{lock.get('pid')}",
    }
    return _fit(_compact(brief))


def _fit(payload: dict) -> dict:
    """Drop the least important fields until the briefing fits its byte budget."""
    def size(item):
        return len(json.dumps(item, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    for field in ("since", "blocked", "cursor", "session", "legal_blockers"):
        if size(payload) <= BRIEF_LIMIT:
            break
        payload.pop(field, None)
    while size(payload) > BRIEF_LIMIT and payload.get("queue"):
        payload["queue"] = payload["queue"][:-1]
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--measure", action="store_true",
                        help="print the briefing only (context budget gate)")
    args = parser.parse_args(argv)

    payload = build()
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    print(text)
    return 0 if len(text.encode("utf-8")) <= BRIEF_LIMIT else 1


if __name__ == "__main__":
    raise SystemExit(main())
