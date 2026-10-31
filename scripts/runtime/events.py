#!/usr/bin/env python
"""Append-only session event log (`data/state/events.jsonl`).

    python scripts/runtime/events.py append applied --key lucid:4009378007 \
        --data '{"company":"Lucid Motors","title":"ADAS Validation Engineer"}'
    python scripts/runtime/events.py tail --limit 5
    python scripts/runtime/events.py count

One JSON object per line. `append` is idempotent when a `key` is given: an event whose key is
already in the recent window is skipped, so re-running a checkpoint after an interruption never
duplicates history. The log is never read whole by the agent - use `tail`.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from _common import EVENTS_PATH, emit

RECENT_WINDOW = 200


def _recent_keys(path, limit: int = RECENT_WINDOW) -> set[str]:
    """Keys from the last `limit` events, read backwards so the file is never loaded whole."""
    path = Path(path)
    if not path.is_file():
        return set()
    keys: set[str] = set()
    try:
        with open(path, "rb") as handle:
            handle.seek(0, 2)
            position = handle.tell()
            buffer = b""
            while position > 0 and len(keys) < limit:
                step = min(8192, position)
                position -= step
                handle.seek(position)
                buffer = handle.read(step) + buffer
                lines = buffer.split(b"\n")
                buffer = lines.pop(0)
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line.decode("utf-8"))
                    except ValueError:
                        continue
                    if isinstance(event, dict) and event.get("key"):
                        keys.add(event["key"])
                    if len(keys) >= limit:
                        break
            if buffer.strip():
                try:
                    event = json.loads(buffer.decode("utf-8"))
                    if isinstance(event, dict) and event.get("key"):
                        keys.add(event["key"])
                except ValueError:
                    pass
    except OSError:
        return set()
    return keys


def append(kind: str, key: str | None = None, path=None, **data) -> dict:
    path = Path(EVENTS_PATH if path is None else path)
    if not kind:
        raise ValueError("event kind is required")
    if key and key in _recent_keys(path):
        return {"ok": True, "appended": False, "key": key}
    event = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "kind": kind,
        "key": key or f"{kind}:{datetime.now().strftime('%Y%m%dT%H%M%S%f')}",
        "data": data,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {"ok": True, "appended": True, "key": event["key"]}


def tail(limit: int = 10, path=None) -> list[dict]:
    path = Path(EVENTS_PATH if path is None else path)
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            out.append(event)
    return out


def count(path=None) -> int:
    path = Path(EVENTS_PATH if path is None else path)
    if not path.is_file():
        return 0
    try:
        with open(path, encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    adder = sub.add_parser("append", help="record one event (idempotent when --key repeats)")
    adder.add_argument("kind")
    adder.add_argument("--key")
    adder.add_argument("--data", default="{}", help="JSON object with event details")

    reader = sub.add_parser("tail", help="last N events")
    reader.add_argument("--limit", type=int, default=10)

    sub.add_parser("count", help="number of recorded events")

    args = parser.parse_args(argv)
    if args.command == "count":
        emit({"events": count()})
        return 0
    if args.command == "tail":
        emit({"events": tail(args.limit)})
        return 0

    try:
        data = json.loads(args.data)
    except ValueError:
        print("--data must be a JSON object", file=__import__("sys").stderr)
        return 2
    if not isinstance(data, dict):
        print("--data must be a JSON object", file=__import__("sys").stderr)
        return 2
    emit(append(args.kind, args.key, **data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
