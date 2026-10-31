#!/usr/bin/env python
"""Turn the approved-company markdown into a queryable JSON index, and show one company.

    python scripts/runtime/companies.py build          # refresh data/profile/companies.json
    python scripts/runtime/companies.py show "Waymo"
    python scripts/runtime/companies.py list
    python scripts/runtime/companies.py stale          # classifications needing a re-check

`show` returns the company row plus its cached industry classification, so the agent reads a few
hundred bytes instead of the whole 113-row markdown table. A verdict older than 180 days (or
missing) is flagged `stale: true` and must be re-verified from the company's own sources.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date

from _common import COMPANIES_JSON, COMPANIES_MD, emit, read_json, today, write_json

STALE_DAYS = 180
VERSION = 1


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _numbered_rows(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip().startswith("|"):
                continue
            cells = _cells(line)
            if len(cells) >= 2 and re.fullmatch(r"\d+", cells[0]) and cells[1]:
                rows.append({
                    "index": int(cells[0]),
                    "name": cells[1],
                    "sector": cells[2] if len(cells) > 2 else "",
                    "careers_url": cells[3] if len(cells) > 3 else "",
                    "ats": cells[4] if len(cells) > 4 else "",
                })
    return rows


def _classification_rows(path: str) -> dict[str, dict]:
    """Verdict table: | Company | evidence | business line | Verdict | Checked |"""
    found: dict[str, dict] = {}
    in_section = False
    with open(path, encoding="utf-8-sig") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("## "):
                in_section = "industry classification" in stripped.lower()
                continue
            if not in_section or not stripped.startswith("|"):
                continue
            cells = _cells(stripped)
            if len(cells) < 5 or cells[0].lower() == "company":
                continue
            found[cells[0]] = {
                "evidence": cells[1],
                "business_line": cells[2],
                "verdict": cells[3],
                "checked": cells[4],
            }
    return found


def build(path=None, out=None) -> dict:
    from sweep import key as company_key

    path = str(COMPANIES_MD) if path is None else path
    out = str(COMPANIES_JSON) if out is None else out
    classifications = _classification_rows(path)
    companies = []
    for row in _numbered_rows(path):
        verdict = classifications.get(row["name"])
        companies.append({**row, "key": company_key(row["name"]), "classification": verdict})
    payload = {"version": VERSION, "updated_at": today(), "companies": companies}
    write_json(out, payload)
    return {"ok": True, "companies": len(companies),
            "classified": sum(1 for c in companies if c["classification"]), "out": out}


def load(auto_build: bool = True) -> dict:
    data = read_json(COMPANIES_JSON, default=None)
    if not isinstance(data, dict) or not data.get("companies"):
        if not auto_build:
            return {"version": VERSION, "updated_at": today(), "companies": []}
        build()
        data = read_json(COMPANIES_JSON, default={"companies": []})
    return data


def _age_days(checked: str):
    try:
        return (date.today() - date.fromisoformat(checked[:10])).days
    except (ValueError, TypeError):
        return None


def show(name: str) -> dict | None:
    from sweep import key as company_key

    wanted = company_key(name)
    for company in load()["companies"]:
        if company["key"] == wanted or company["name"].lower() == name.lower():
            classification = company.get("classification")
            age = _age_days(classification["checked"]) if classification else None
            return {
                **company,
                "age_days": age,
                "stale": classification is None or age is None or age > STALE_DAYS,
            }
    return None


def stale() -> list[dict]:
    out = []
    for company in load()["companies"]:
        classification = company.get("classification")
        age = _age_days(classification["checked"]) if classification else None
        if classification is None or age is None or age > STALE_DAYS:
            out.append({"name": company["name"], "checked": (classification or {}).get("checked"),
                        "age_days": age})
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("list")
    sub.add_parser("stale")
    shower = sub.add_parser("show")
    shower.add_argument("name")
    args = parser.parse_args(argv)

    if args.command == "build":
        emit(build())
        return 0
    if args.command == "list":
        emit([{"index": c["index"], "name": c["name"], "key": c["key"]}
              for c in load()["companies"]])
        return 0
    if args.command == "stale":
        emit({"stale": stale()})
        return 0
    found = show(args.name)
    if not found:
        print(f"not in the approved list: {args.name}", file=sys.stderr)
        return 2
    emit(found)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
