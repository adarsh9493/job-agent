#!/usr/bin/env python
"""Build the narrow mail query the agent is allowed to run (hard rule 2).

    python scripts/runtime/mail.py query --domain lucidmotors.com
    python scripts/runtime/mail.py query --domain myworkday.com --since 2026-10-29 --subject applied

The script never touches the mailbox. It prints the exact query string to hand to the harness's
mail tool: one portal sender domain plus a date window, optionally a subject hint. Anything wider
is out of policy.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

from _common import emit


def build_query(domain: str, since: str | None = None, days: int = 3,
                subject: str | None = None) -> dict:
    domain = domain.strip().lower()
    if not domain or " " in domain:
        raise ValueError("one sender domain is required, e.g. lucidmotors.com")
    start = since or (date.today() - timedelta(days=days)).isoformat()
    try:
        date.fromisoformat(start)
    except ValueError as exc:
        raise ValueError(f"invalid since date: {start}") from exc
    parts = [f"from:(@{domain})", f"after:{start.replace('-', '/')}"]
    if subject:
        parts.append(f'subject:("{subject.strip()}")')
    return {
        "query": " ".join(parts),
        "since": start,
        "scope": "OTPs, verification links, application confirmations and rejections only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    query = sub.add_parser("query")
    query.add_argument("--domain", required=True)
    query.add_argument("--since")
    query.add_argument("--days", type=int, default=3)
    query.add_argument("--subject")
    args = parser.parse_args(argv)

    try:
        emit(build_query(args.domain, args.since, args.days, args.subject))
    except ValueError as error:
        print(str(error), file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
