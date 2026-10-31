"""Round-robin planner for approved-company order and active interview blocking.

User-approved policy (2026-10-20) — this REPLACES the old tiered per-company caps:
  * NO per-company caps (no 3/2 per 30 days, no 30-day window, no title-family cap).
  * NO cooling period — apply to any company any time.
  * One role per company per round.
  * Sweep order = the companies.md list order (top to bottom), starting at a
    rotating cursor — each round resumes where the last round stopped. The cursor
    is taken from `sweep.cursor` in state.json when set, otherwise it is derived
    from the most recently applied company.
  * Posting freshness is checked by the job-search workflow, not by this planner.
  * ATS-stated limits (a company's OWN rule, e.g. Waymo 5/60d) are still obeyed —
    those are not our cap.
  * **Interview blocklist**: If any interview (recruiter screen, phone screen,
    technical, on-site) is scheduled or in progress for a company, skip that
    company until the process completes (offer or rejection). Loaded from
    `interview_blocklist.active_interviews` in state.json.

The tracker Excel is the source of truth for applications (folder confirmation
screenshots are the source of truth for "did it go out"). Company names in the
tracker are free text, so matching is done on a normalised alias key.

Usage:
    python skills/job-search/scripts/sweep.py                   # print approved-company order
    python skills/job-search/scripts/sweep.py --company Lucid    # check active interview block
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TRACKER = os.path.join(PROJ, "data", "tracker", "applications.xlsx")
COMPANIES = os.path.join(PROJ, "data", "profile", "companies.md")
STATE = os.path.join(PROJ, "data", "state", "state.json")
# statuses that represent a real application (used to derive the rotating cursor)
APPLIED_STATUS = (
    "applied", "application", "interview", "offer", "rejected",
    "in process", "under consideration", "assessment", "screening",
)

# tracker free-text name -> canonical key (first match wins, checked on the normalised name)
ALIASES = {
    "lucid": "lucid",
    "motional": "motional",
    "appliedintuition": "applied",
    "applied": "applied",
    "generalmotors": "generalmotors",
    "gm": "generalmotors",
    "robertbosch": "bosch",
    "bosch": "bosch",
    "rivian": "rivian",
    "torc": "torc",
    "nuro": "nuro",
    "harbinger": "harbinger",
    "kodiak": "kodiak",
    "chargepoint": "chargepoint",
    "geotab": "geotab",
    "scout": "scout",
    "zoox": "zoox",
    "wayve": "wayve",
    "waymo": "waymo",
    "caterpillar": "caterpillar",
    "woven": "woven",
    "ford": "ford",
    "redwood": "redwood",
    "continental": "continental",
    "valeo": "valeo",
    "samsara": "samsara",
    "gatik": "gatik",
    "waabi": "waabi",
    "stackav": "stackav",
    "maymobility": "maymobility",
    "sonatus": "sonatus",
    "ghost": "ghost",
    "tula": "tula",
    "slate": "slate",
    "indigo": "indigo",
    "weride": "weride",
    "aurora": "aurora",
    "aeva": "aeva",
    "hyliion": "hyliion",
    "pronto": "pronto",
    # added 2026-10-17 so target-list names link to tracker names
    "magna": "magna",
    "adient": "adient",
    "gentex": "gentex",
    "aptiv": "aptiv",
    "visteon": "visteon",
    "nexteer": "nexteer",
    "borgwarner": "borgwarner",
    "lear": "lear",
    "denso": "denso",
    "harman": "harman",
    "qualcomm": "qualcomm",
    "nvidia": "nvidia",
    "mobileye": "mobileye",
    "stellantis": "stellantis",
    "toyota": "toyota",
    "honda": "honda",
    "hyundai": "hyundai",
    "kia": "kia",
    "nissan": "nissan",
    "volvo": "volvo",
    "polestar": "polestar",
    "cummins": "cummins",
    "paccar": "paccar",
    "navistar": "navistar",
    "panasonic": "panasonic",
    "bmw": "bmw",
    "zf": "zf",
}


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def key(name: str) -> str:
    """Canonical company key for a tracker company name or a board slug."""
    n = norm(name)
    if n in ALIASES:
        return ALIASES[n]
    matches = []
    for alias, canonical in ALIASES.items():
        match = re.search(
            rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])",
            (name or "").lower(),
        )
        if match:
            matches.append((match.start(), -len(alias), canonical))
    if matches:
        return min(matches)[2]
    return n


def _rows():
    import openpyxl

    ws = openpyxl.load_workbook(TRACKER, data_only=True)["Applications"]
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[1]:
            continue
        d = row[0]
        if hasattr(d, "date"):
            d = d.date()
        elif isinstance(d, (int, float)):  # raw Excel serial
            d = date(1899, 12, 30) + timedelta(days=int(d))
        elif isinstance(d, str):
            try:
                d = date.fromisoformat(d[:10])
            except ValueError:
                d = None
        out.append({"date": d, "company": str(row[1]), "title": str(row[2] or ""), "status": str(row[9] or "")})
    return out


def last_applied() -> dict[str, date]:
    """key -> most recent real application date (all time)."""
    out: dict[str, date] = {}
    for r in _rows():
        if not r["date"]:
            continue
        if not any(s in r["status"].lower() for s in APPLIED_STATUS):
            continue
        k = key(r["company"])
        if k not in out or r["date"] > out[k]:
            out[k] = r["date"]
    return out


def applied_keys() -> set[str]:
    return {key(r["company"]) for r in _rows() if r["company"]}


def company_list(path: str = COMPANIES) -> list[str]:
    """Ordered target companies parsed from the numbered tier tables of companies.md."""
    names: list[str] = []
    if not os.path.exists(path):
        return names
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 2 and re.fullmatch(r"\d+", cells[0]) and cells[1] and set(cells[1]) != {"-"}:
                names.append(cells[1])
    seen, out = set(), []
    for n in names:
        k = key(n)
        if k and k not in seen:
            seen.add(k)
            out.append(n)
    return out


def _link(tk: str, keys: set[str]) -> str | None:
    """Link a target key to a tracker key (exact, then containment)."""
    if tk in keys:
        return tk
    for u in keys:
        if u and len(u) >= 4 and (u in tk or tk in u):
            return u
    return None


def _state_sweep() -> dict:
    try:
        with open(STATE, encoding="utf-8-sig") as fh:
            return json.load(fh).get("sweep", {}) or {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def _state_interview_blocklist() -> list[dict]:
    """Load active interviews from state.json interview_blocklist."""
    try:
        with open(STATE, encoding="utf-8-sig") as fh:
            data = json.load(fh)
            blocklist = data.get("interview_blocklist", {})
            if blocklist.get("enabled", False):
                return blocklist.get("active_interviews", [])
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return []


def is_interview_blocked(company_key: str) -> tuple[bool, str]:
    """Check if a company has an active interview. Returns (blocked, reason)."""
    interviews = _state_interview_blocklist()
    for interview in interviews:
        # Match by company key
        if company_key.lower() in interview.get("company", "").lower():
            stage = interview.get("stage", "unknown")
            return True, f"active interview ({stage})"
    return False, ""


def _resolve_rows(companies_file: str, la: dict, keys: set) -> list[dict]:
    """One row per company-list entry, in list order, with its last-applied date."""
    rows = []
    for i, name in enumerate(company_list(companies_file)):
        tk = key(name)
        linked = _link(tk, keys)
        rows.append({"company": name, "key": linked or tk, "idx": i,
                     "last": la.get(linked) if linked else None})
    return rows


def _auto_cursor(rows: list[dict]) -> int:
    """Resume right after the most recently applied company (list order = where we left off)."""
    dated = [(r["idx"], r["last"]) for r in rows if r["last"]]
    if not dated:
        return 0
    newest = max(d for _, d in dated)
    return (max(i for i, d in dated if d == newest) + 1) % len(rows)


def plan(today: date | None = None, companies_file: str = COMPANIES,
         cursor: str | None = None) -> list[dict]:
    """Return approved companies in list order, rotated to start at the cursor.

    `cursor` may be a company name/key. When omitted, the saved `sweep.cursor` from
    state.json is used; when that is absent too, the cursor is derived from the most
    recently applied company so each round resumes where the last round stopped.
    """
    today = today or date.today()
    la = last_applied()
    keys = applied_keys() | set(la)
    rows = _resolve_rows(companies_file, la, keys)

    start = 0
    explicit = cursor if cursor is not None else _state_sweep().get("cursor")
    if explicit:
        ck = key(str(explicit))
        for r in rows:
            if r["key"] == ck or key(r["company"]) == ck:
                start = r["idx"]
                break
    else:
        start = _auto_cursor(rows)

    ordered = rows[start:] + rows[:start]

    entries = []
    for i, r in enumerate(ordered):
        days = (today - r["last"]).days if r["last"] else None
        interview_blocked, interview_reason = is_interview_blocked(r["key"])
        entries.append({"company": r["company"], "last": r["last"], "days": days,
                        "interview_blocked": interview_blocked,
                        "interview_reason": interview_reason,
                        "idx": r["idx"], "start": i == 0})
    return entries


def status(company: str, today: date | None = None) -> dict:
    """Return the most recent application and active-interview status."""
    today = today or date.today()
    la = last_applied()
    k = key(company)
    linked = _link(k, set(la) | applied_keys()) or k
    last = la.get(linked)
    days = (today - last).days if last else None
    interview_blocked, interview_reason = is_interview_blocked(linked)
    if interview_blocked:
        reason = f"interview block: {interview_reason}"
    elif last is None:
        reason = "free (never applied)"
    else:
        reason = "free"
    return {"company": company, "last": last, "days": days,
            "interview_blocked": interview_blocked, "reason": reason}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--company")
    ap.add_argument("--today")
    ap.add_argument("--cursor", help="start the sweep at this company (name or tracker key)")
    ap.add_argument("--companies-file", default=COMPANIES)
    args = ap.parse_args()
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()

    if args.company:
        s = status(args.company, today)
        flags = []
        if s.get("interview_blocked"):
            flags.append(f"INTERVIEW_BLOCKED({s.get('interview_reason','')})")
        flag = ", ".join(flags) if flags else "OK"
        print(f"{s['company']}: last={s['last']} -> {flag} ({s['reason']})")
        return 1 if s.get("interview_blocked") else 0

    entries = plan(today, args.companies_file, args.cursor)
    start = next((e["company"] for e in entries if e.get("start")), "?")
    print(f"approved-company order (rotating cursor) — {today}\n"
          f"round starts at: {start}\n")
    for e in entries:
        last = e["last"] or "never"
        days = "-" if e["days"] is None else f"{e['days']}d"
        flag = (f"INTERVIEW_BLOCKED({e.get('interview_reason','')})"
                if e.get("interview_blocked") else "ok")
        mark = "->" if e.get("start") else "  "
        print(f"  {mark} {e['company']:<26} last {str(last):<12} ({days:>5})  {flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
