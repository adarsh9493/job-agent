#!/usr/bin/env python
"""Render the working queue from `state.json` into a tiny `queue.md` the agent can read whole.

    python scripts/runtime/queue.py view          # rebuild data/state/queue.md and print it
    python scripts/runtime/queue.py view --json   # same data as one JSON line

The queue lives in `state.queue` (array of objects with company, title, url, job_id, status,
notes). Markdown is capped at 2048 bytes; older entries are summarised as a count.
"""
from __future__ import annotations

import argparse

from _common import QUEUE_MD, STATE_PATH, emit, read_json, write_json

QUEUE_LIMIT = 2048


def rows() -> list[dict]:
    state = read_json(STATE_PATH, default={}) or {}
    queue = state.get("queue") or []
    return [row for row in queue if isinstance(row, dict)]


def render(items: list[dict], limit: int = QUEUE_LIMIT) -> str:
    header = f"# Queue ({len(items)})\n\n"
    lines = []
    for index, item in enumerate(items, start=1):
        title = item.get("title") or "?"
        company = item.get("company") or "?"
        status = item.get("status") or "queued"
        job_id = item.get("job_id") or "-"
        lines.append(f"{index}. **{company}** - {title} ({job_id}) [{status}]\n")
    text = header + "".join(lines)
    while len(text.encode("utf-8")) > limit and lines:
        lines.pop()
        text = header + "".join(lines) + f"\n... {len(items) - len(lines)} more\n"
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    view = sub.add_parser("view")
    view.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    items = rows()
    text = render(items)
    QUEUE_MD.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_MD.write_text(text, encoding="utf-8", newline="\n")
    if args.json:
        emit({"queue": items, "bytes": len(text.encode("utf-8"))})
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
