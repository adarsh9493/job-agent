#!/usr/bin/env python3
"""Aptiv job-board scan (HawkSearch / Sitecore integration, cracked 2026-10-16).

Discovery method: loaded https://www.aptiv.com/en/jobs/search/open-positions in the
browser and read the network log. The page posts to
  POST https://aptivcareers.searchapi-na.hawksearch.com/api/v2/search/
(header x-hawksearch-clientguid: 28fad22cfe584b879917858203dd97ce, ACAO *) and returns
the whole index (631 jobs, 123 United States) with title / link / location /
created_moment / jobdescription.

Usage:
  python skills/job-search/scripts/aptiv_scan.py                # US + tester-title filter
  python skills/job-search/scripts/aptiv_scan.py --all          # all US jobs
  python skills/job-search/scripts/aptiv_scan.py --days 30 --all
  python skills/job-search/scripts/aptiv_scan.py --all --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

GUID = "28fad22cfe584b879917858203dd97ce"
URL = "https://aptivcareers.searchapi-na.hawksearch.com/api/v2/search/"

TESTER_RE = re.compile(
    r"test|validat|verif|integrat|hil|sil|mil|qualit|reliab|adas|autonom|embedded|"
    r"ecu|can |diagnos|harness|systems engineer",
    re.I,
)


def fetch_page(page_no: int, page_size: int) -> dict:
    body = {
        "ClientData": {
            "UserAgent": "job-agent/1.0",
            "VisitId": "11111111-1111-1111-1111-111111111111",
            "VisitorId": "22222222-2222-2222-2222-222222222222",
            "Custom": {"custom": None},
        },
        "Keyword": "",
        "FacetSelections": {},
        "PageNo": page_no,
        "IndexName": "",
        "IgnoreSpellcheck": False,
        "IsInPreview": False,
        "ClientGuid": GUID,
        "Is100CoverageTurnedOn": False,
        "PageSize": page_size,
        "MaxPerPage": page_size,
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json; charset=utf-8",
            "x-hawksearch-clientguid": GUID,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def harvest(page_size: int = 96) -> list[dict]:
    out: list[dict] = []
    page = 0
    total_pages = 1
    while page < total_pages and page < 60:
        j = fetch_page(page, page_size)
        pag = j.get("Pagination") or {}
        total_pages = pag.get("NofPages") or 1
        for res in j.get("Results") or []:
            d = res.get("Document") or {}
            out.append(
                {
                    "id": (d.get("jobrequisitionid") or [""])[0] or res.get("DocId"),
                    "title": (d.get("title") or [""])[0],
                    "loc": (d.get("primarylocation") or [""])[0],
                    "state": (d.get("primarystate") or [""])[0],
                    "city": (d.get("primarycity") or [""])[0],
                    "country": (d.get("primarycountry") or [""])[0],
                    "fam": (d.get("jobfamily") or [""])[0],
                    "grp": (d.get("jobfamilygroup") or [""])[0],
                    "created": (d.get("created_moment") or [""])[0],
                    "url": (d.get("link") or [""])[0],
                }
            )
        page += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="no tester-title filter")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--days", type=int, default=0, help="only created within N days (0 = any)")
    args = ap.parse_args()

    jobs = harvest()
    us = [j for j in jobs if "united states" in (j["country"] or "").lower()]
    rows = us if args.all else [j for j in us if TESTER_RE.search(j["title"] or "")]
    if args.days:
        from datetime import datetime, timedelta, timezone

        cut = datetime.now(timezone.utc) - timedelta(days=args.days)
        keep = []
        for j in rows:
            try:
                dt = datetime.fromisoformat((j["created"] or "").replace("Z", "+00:00"))
            except Exception:
                keep.append(j)
                continue
            if dt >= cut:
                keep.append(j)
        rows = keep

    if args.json:
        print(json.dumps(rows, indent=1))
        return 0

    print(f"Aptiv: {len(jobs)} total postings, {len(us)} US, {len(rows)} matched")
    for j in sorted(rows, key=lambda x: (x["created"] or ""), reverse=True):
        print(f"{j['created'][:10]:10} | {j['id']:<12} | {j['loc'][:38]:38} | {j['title'][:75]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
