#!/usr/bin/env python3
"""SAP SuccessFactors (classic) RSS job-feed scanner — cracked 2026-10-16.

Every classic SuccessFactors career site exposes an RSS feed at
  https://<career-site>/services/rss/job/?locale=en_US&keywords=(<query>)
with per-item <title> (job + location), <link>, <pubDate> and the full JD in
<description>. That makes ZF / Lear / Nexteer / etc. directly queryable without a browser.

Usage:
  python skills/job-search/scripts/sf_rss_scan.py --site zf --keywords validation
  python skills/job-search/scripts/sf_rss_scan.py --url https://jobs.lear.com --keywords test --days 7
  python skills/job-search/scripts/sf_rss_scan.py --site zf --keywords "" --all-us
"""
from __future__ import annotations

import argparse
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
)

SITES = {
    "zf": "https://jobs.zf.com",
    "lear": "https://jobs.lear.com",
    "nexteer": "https://jobs.nexteer.com",
    "tenneco": "https://jobs.tenneco.com",
    "dana": "https://jobs.dana.com",
    "paccar": "https://jobs.paccar.com",
    "bmw": "https://jobs.bmwgroup.com",
    "marelli": "https://jobs.marelli.com",
}

TESTER_RE = re.compile(
    r"test|validat|verif|integrat|hil|sil|mil|qualit|reliab|adas|autonom|embedded|"
    r"ecu|diagnos|dvp|systems engineer",
    re.I,
)
MANAGER_RE = re.compile(r"manager|director|head of|supervisor|vp |vice president|chief", re.I)


def fetch_rss(base: str, keywords: str) -> str:
    url = (
        f"{base}/services/rss/job/?locale=en_US&keywords=({urllib.parse.quote(keywords)})"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml,*/*"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def parse(xml: str) -> list[dict]:
    items = []
    for chunk in re.split(r"<item>", xml)[1:]:
        chunk = chunk.split("</item>")[0]
        tmatch = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", chunk, re.S)
        link = re.search(r"<link>(.*?)</link>", chunk, re.S)
        pub = re.search(r"<pubDate>(.*?)</pubDate>", chunk, re.S)
        desc = re.search(r"<description><!\[CDATA\[(.*?)\]\]></description>", chunk, re.S)
        if not tmatch:
            continue
        t = tmatch.group(1).strip()
        title = t
        loc = ""
        m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", t)
        if m:
            title = m.group(1)
            loc = m.group(2)
        try:
            dt = parsedate_to_datetime(pub.group(1)) if pub else None
        except Exception:  # noqa: BLE001
            dt = None
        items.append(
            {
                "title": title.strip(),
                "loc": loc,
                "link": (link.group(1).split("?")[0] if link else ""),
                "pub": pub.group(1) if pub else "",
                "dt": dt,
                "desc": (chunk[chunk.find("<description>") :])[:1500],
            }
        )
    # the first item is the feed/channel title - drop items with no link
    return [i for i in items if i["link"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--url", help="career-site base URL instead of --site")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--days", type=int, default=0)
    ap.add_argument("--all", action="store_true", help="no tester-title filter")
    ap.add_argument("--us-only", action="store_true", default=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    base = args.url or SITES.get(args.site or "")
    if not base:
        print("need --site or --url")
        return 2

    items = parse(fetch_rss(base, args.keywords))
    cut = datetime.now(timezone.utc) - timedelta(days=args.days) if args.days else None
    rows = []
    for i in items:
        t = (i["title"] or "") + " (" + (i["loc"] or "") + ")"
        if args.us_only and not re.search(r",\s*US\b|United States", i["loc"] or t):
            continue
        if cut:
            try:
                dt = parsedate_to_datetime(i["pub"])
                if dt < cut:
                    continue
            except Exception:
                pass
        if not args.all:
            if not TESTER_RE.search(t) or MANAGER_RE.search(t):
                continue
        rows.append(i)

    rows.sort(key=lambda x: x.get("pub") or "", reverse=True)
    print(f"{base}: {len(items)} items in feed, {len(rows)} matched (us_only={args.us_only}, days={args.days})")
    for i in rows:
        print(f"  {i['pub'][:25]:26} | {i['link'][:95]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
