#!/usr/bin/env python
"""Read or write one value in `data/state/state.json`, or get the compact session slice.

    python scripts/runtime/state.py get sweep.cursor
    python scripts/runtime/state.py set current.step "form"
    python scripts/runtime/state.py keys
    python scripts/runtime/state.py hot          # rebuild data/state/hot.json (<= 1024 bytes)

`hot` is the only state file the agent reads at session start. The full state.json keeps the
history; hot.json carries just what the next decision needs.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from _common import HOT_PATH, STATE_PATH, dot_get, dot_set, emit, read_json, write_json

HOT_LIMIT = 1024


def hot_payload(state: dict) -> dict:
    state = state or {}
    current = state.get("current") or {}
    queue = state.get("queue") or []
    blocklist = state.get("interview_blocklist") or {}
    blocked = [
        item.get("company") for item in (blocklist.get("active_interviews") or [])
        if isinstance(item, dict) and item.get("company")
    ]
    return {
        "mode": state.get("mode"),
        "updated": state.get("last_updated"),
        "session": state.get("session_stats") or {},
        "applied_session": state.get("applications_this_session"),
        "current": {
            key: current[key]
            for key in ("company", "title", "job_id", "step", "folder", "status")
            if current.get(key)
        },
        "queue": [
            {"company": row.get("company"), "title": row.get("title")}
            for row in queue[:3] if isinstance(row, dict)
        ],
        "queue_len": len(queue),
        "cursor": (state.get("sweep") or {}).get("cursor"),
        "interview_blocked": blocked,
        "needs_user": len(state.get("needs_user") or []),
    }


def fit(payload: dict, limit: int = HOT_LIMIT) -> dict:
    """Drop the least important parts until the projection fits the byte budget."""
    def size(item):
        return len(emit_text(item).encode("utf-8"))

    while size(payload) > limit and payload.get("queue"):
        payload["queue"] = payload["queue"][:-1]
    for field in ("updated", "cursor", "applied_session", "needs_user"):
        if size(payload) > limit and field in payload:
            payload.pop(field)
    while size(payload) > limit and payload.get("interview_blocked"):
        payload["interview_blocked"] = payload["interview_blocked"][:-1]
    return payload


def emit_text(payload) -> str:
    import json
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    get = sub.add_parser("get", help="print one value")
    get.add_argument("path")

    put = sub.add_parser("set", help="write one value (JSON, or plain text)")
    put.add_argument("path")
    put.add_argument("value")

    sub.add_parser("keys", help="print the top-level keys")
    sub.add_parser("hot", help="rebuild and print the compact session slice")

    args = parser.parse_args(argv)
    state = read_json(STATE_PATH, default={})

    if args.command == "get":
        try:
            emit(dot_get(state, args.path))
        except (KeyError, IndexError, TypeError, ValueError):
            print(f"missing path: {args.path}", file=sys.stderr)
            return 2
        return 0

    if args.command == "keys":
        emit(sorted(state) if isinstance(state, dict) else [])
        return 0

    if args.command == "set":
        import json
        try:
            value = json.loads(args.value)
        except ValueError:
            value = args.value
        dot_set(state, args.path, value)
        state["last_updated"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        write_json(STATE_PATH, state)
        emit({"ok": True, "path": args.path, "updated": state["last_updated"]})
        return 0

    payload = fit(hot_payload(state))
    write_json(HOT_PATH, payload)
    print(emit_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
