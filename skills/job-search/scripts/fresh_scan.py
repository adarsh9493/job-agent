"""Discover fresh candidate postings on a single company's public career board.

This scanner is not an eligibility or domain gate. The agent must inspect the full
job description and company evidence before a role is queued.

Usage:
    python skills/job-search/scripts/fresh_scan.py --company motional
    python skills/job-search/scripts/fresh_scan.py --company motional --verbose
    python skills/job-search/scripts/fresh_scan.py --probe
"""
from __future__ import annotations

import argparse
from email.utils import parsedate_to_datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# company key -> list of board specs. Multiple candidates = probe until one works.
BOARDS: dict[str, list[dict]] = {
    "motional": [{"type": "greenhouse", "token": "motional"}],
    "nuro": [{"type": "greenhouse", "token": "nuro"}],
    # custom site APIs cracked via browser sniff 2026-10-17
    "aurora": [{"type": "aurora_api"}],
    "rivian": [{"type": "rivian_api"}],
    "lucid": [{"type": "greenhouse", "token": "lucid"},
              {"type": "greenhouse", "token": "lucidmotors"}],
    "nvidia": [{"type": "workday", "host": "nvidia.wd5.myworkdayjobs.com",
                "tenant": "nvidia", "site": "NVIDIAExternalCareerSite"}],
    "mobileye": [],
    "applied": [{"type": "ashby", "token": "applied"}],
    "woven": [{"type": "lever", "token": "woven-by-toyota"}],
    "kodiak": [{"type": "greenhouse", "token": "kodiakrobotics"},
               {"type": "greenhouse", "token": "kodiak"}],
    "gatik": [{"type": "greenhouse", "token": "gatikaiinc"}],
    "maymobility": [{"type": "greenhouse", "token": "maymobility"}],
    "torc": [{"type": "greenhouse", "token": "torcrobotics"},
             {"type": "greenhouse", "token": "torc"}],
    # HawkSearch API cracked via browser sniff 2026-10-17 (ClientGuid is public, stable)
    "aptiv": [{"type": "hawksearch", "host": "aptivcareers.searchapi-na.hawksearch.com",
               "guid": "28fad22cfe584b879917858203dd97ce"}],
    # server-rendered Umbraco listing pages (cracked 2026-10-17 via browser sniff;
    # JSON API is cookie-gated, HTML scrape works plain)
    "generalmotors": [{"type": "gm_html", "base": "https://search-careers.gm.com"}],
    # CWS/m-cloud talent-cloud API cracked via browser sniff 2026-10-17
    # (careers.stellantis.com JSONP -> jobsapi-google.m-cloud.io/api/job/search)
    "stellantis": [{"type": "mcloud", "host": "jobsapi-google.m-cloud.io",
                    "org": "companies/16115603-6c1b-4c45-b544-238a4e6c51b3",
                    "base": "https://careers.stellantis.com"}],
    "toyota": [{"type": "greenhouse", "token": "toyotaresearchinstitute"}],
    "honda": [],
    "hyundai": [],
    "kia": [],
    "nissan": [],
    "bmw": [{"type": "successfactors_rss", "base": "https://jobs.bmwgroup.com"}],
    "mercedes": [],
    "vw": [],
    "volvo": [{"type": "greenhouse", "token": "volvocars"}],
    "polestar": [{"type": "greenhouse", "token": "polestar"}],
    "paccar": [{"type": "successfactors_rss", "base": "https://jobs.paccar.com"}],
    "navistar": [],
    "cummins": [{"type": "greenhouse", "token": "cummins"}],
    "bosch": [{"type": "smartrecruiters", "token": "BoschGroup"}],
    "continental": [{"type": "smartrecruiters", "token": "Continental"}],
    "zf": [{"type": "successfactors_rss", "base": "https://jobs.zf.com"}],
    "valeo": [],
    "lear": [{"type": "successfactors_rss", "base": "https://jobs.lear.com"}],
    "visteon": [],
    "harman": [],
    "panasonic": [],
    "denso": [],
    "borgwarner": [{"type": "greenhouse", "token": "borgwarner"}],
    "qualcomm": [],
    "harbinger": [{"type": "greenhouse", "token": "harbingermotors"}],
    "chargepoint": [{"type": "greenhouse", "token": "chargepoint"}],
    "geotab": [{"type": "greenhouse", "token": "geotab"}],
    "scout": [{"type": "greenhouse", "token": "scoutmotors"}],
    "gentex": [{"type": "workday", "host": "gentex.wd5.myworkdayjobs.com",
                "tenant": "gentex", "site": "Gentex"}],
    "adient": [{"type": "workday", "host": "adient.wd3.myworkdayjobs.com",
                "tenant": "adient", "site": "External"}],
    "redwood": [{"type": "greenhouse", "token": "redwoodmaterials"}],
    "waymo": [{"type": "greenhouse", "token": "waymo"}],
    "zoox": [{"type": "lever", "token": "zoox"}],
    "caterpillar": [{"type": "smartrecruiters", "token": "Caterpillar"}],
    "wayve": [{"type": "greenhouse", "token": "wayve"}],
    "stackav": [{"type": "greenhouse", "token": "stackav"}],
    "waabi": [{"type": "greenhouse", "token": "waabi"}],
    "sonatus": [{"type": "greenhouse", "token": "sonatus"}],
    "botauto": [{"type": "greenhouse", "token": "botauto"}],
    "tula": [{"type": "greenhouse", "token": "tulainternational"}],
    "nexteer": [{"type": "successfactors_rss", "base": "https://jobs.nexteer.com"}],
}

# candidates tried in order when the primary token is unreachable (probe order matters)
BOARD_FIXES: dict[str, list[dict]] = {
    "aurora": [{"type": "greenhouse", "token": "aurorainnovation"}],
    "rivian": [{"type": "workday", "host": "rivian.wd1.myworkdayjobs.com",
                "tenant": "rivian", "site": "Rivian"}],
    "nvidia": [{"type": "workday", "host": "nvidia.wd1.myworkdayjobs.com",
                "tenant": "nvidia", "site": "NVIDIA"},
               {"type": "workday", "host": "nvidia.wd5.myworkdayjobs.com",
                "tenant": "nvidia", "site": "NVIDIA"}],
    "applied": [{"type": "ashby", "token": "applied-intuition"}],
    "gatik": [{"type": "greenhouse", "token": "gatikai"}],
    "toyota": [{"type": "greenhouse", "token": "toyotaresearchinstitute"}],
    "volvo": [{"type": "greenhouse", "token": "volvocars"}],
    "polestar": [{"type": "greenhouse", "token": "polestar"}],
    "cummins": [{"type": "workday", "host": "cummins.wd5.myworkdayjobs.com",
                 "tenant": "cummins", "site": "External"}],
    "borgwarner": [{"type": "workday", "host": "borgwarner.wd1.myworkdayjobs.com",
                    "tenant": "borgwarner", "site": "External"}],
    "gentex": [{"type": "workday", "host": "gentex.wd5.myworkdayjobs.com",
                "tenant": "gentex", "site": "Gentex"}],
    "adient": [{"type": "workday", "host": "adient.wd3.myworkdayjobs.com",
                "tenant": "adient", "site": "External"}],
    "caterpillar": [{"type": "workday", "host": "caterpillar.wd5.myworkdayjobs.com",
                     "tenant": "caterpillar", "site": "External"}],
    "wayve": [{"type": "lever", "token": "wayve"}],
    "waabi": [{"type": "lever", "token": "waabi"}],
    "tula": [{"type": "lever", "token": "tula"}],
}

# ---- title filters -------------------------------------------------------
# Candidate-title filter only; the full JD determines ADAS/AD scope.
TESTER = re.compile(
    r"\b(test|testing|validation|verif|integration|hils?|sils?|mils?|"
    r"simulation|sensor validation|test automation|reliability\s+(test|validation))\b", re.I)

# Exclude all development/design/manufacturing/process/quality/supplier/calibration/controls/hardware roles
# Also exclude operator, technician, student, co-op, intern, contract roles
# KEEP: "test engineer", "validation engineer", "verification engineer", "integration test engineer", "integration validation engineer"
DEV_OUT = re.compile(
    r"(software (engineer|developer|intern)|\bswe\b|full.?stack|backend|frontend|"
    r"web ?\d|android|ios\b|machine learning|\bml\b|data (engineer|scientist)|"
    r"research scientist|algorithms?|platform engineer|sre|devops|cloud|"
    r"developer|firmware engineer|application engineer|cloud|"
    r"software engineer|"
    r"hardware engineer|controls engineer|calibration engineer|"
    r"design engineer|development engineer|development.*validation|development.*test|"
    r"project engineer|manufacturing engineer|process engineer|quality engineer|"
    r"hardware reliability|supplier.*engineer|manufacturing.*engineer|"
    r"production engineer|test.*developer|"
    r"embedded.*engineer|ecu.*engineer|diagnostic.*engineer|"
    r"firmware.*engineer|application.*engineer|operator|technician|"
    r"student|co-?op|intern|contract)", re.I)

MGR_OUT = re.compile(r"(\bmanager\b|director|head of|\bvp\b|chief |supervisor)", re.I)
JUNK_OUT = re.compile(
    r"(intern|co-?op|apprentice|sales|marketing|finance|accounting|\bhr\b|human resources|"
    r"legal|recruiter|talent|procurement|supply chain|buyer|driver|technician|"
    r"product manager|program manager|project manager|customer|field service|"
    r"security engineer|privacy|environmental|health & safety|esg|"
    r"hardware reliability|hw reliability)", re.I)
NON_US = re.compile(
    r"(india|bangalore|bengaluru|pune|hyderabad|chennai|noida|gurgaon|beijing|shanghai|"
    r"germany|munich|berlin|stuttgart|india|japan|tokyo|korea|seoul|china|uk\b|london|"
    r"france|paris|italy|madrid|sweden|gothenburg|netherlands|amsterdam|israel|"
    r"toronto|ontario|quebec|canada|mexico|brazil|poland|czech|romania|hungary|"
    r"austria|spain|portugal|finland|denmark|norway|belgium|taiwan|singapore|"
    r"vietnam|thailand|malaysia|indonesia|australia|korea)", re.I)
US_OK = re.compile(
    r"(united states|\busa?\b|remote|california|texas|michigan|arizona|nevada|georgia|"
    r"illinois|washington|colorado|oregon|massachusetts|pennsylvania|new york|ohio|"
    r"virginia|florida|north carolina|wisconsin|indiana|tenennessee|tennessee|minnesota|"
    r"maryland|missouri|utah|new jersey|connecticut|district of columbia|d\.?c\.?|"
    r"sunnyvale|palo alto|san francisco|los angeles|san diego|irvine|seattle|austin|"
    r"detroit|ann arbor|troy|warren|farmington|plymouth|zeeland|gorham|portland|"
    r"boston|pittsburgh|atlanta|chicago|dallas|houston|denver|phoenix|orlando|"
    r"madison|indianapolis|columbus|nashville|raleigh|charlotte|buffalo|rochester)", re.I)


def http_json(url: str, payload: dict | None = None) -> dict | None:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def http_text(url: str) -> str | None:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def parse_successfactors_rss(xml_text: str) -> list[dict]:
    """Normalize a SuccessFactors RSS feed into scanner postings."""
    root = ET.fromstring(xml_text)
    jobs = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip().split("?", 1)[0]
        pub_date = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        location = ""
        match = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", title)
        if match:
            title, location = match.group(1).strip(), match.group(2).strip()
        posted = ""
        if pub_date:
            try:
                published = parsedate_to_datetime(pub_date)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                posted = published.astimezone(timezone.utc).date().isoformat()
            except (TypeError, ValueError, OverflowError):
                pass
        jobs.append({"title": title, "location": location, "posted": posted, "url": link})
    return jobs


def _workday_posted(text: str) -> str:
    """Normalize Workday 'postedOn' to YYYY-MM-DD. Tenants mix ISO dates with
    relative text ('Posted Today', 'Posted 3 Days Ago', 'Posted 30+ Days Ago')."""
    s = (text or "").strip()
    m = re.match(r"^\d{4}-\d{2}-\d{2}", s)
    if m:
        return m.group(0)
    t = re.sub(r"^posted\s*", "", s, flags=re.I).strip().lower()
    today = date.today()
    if t.startswith("today"):
        return today.isoformat()
    for pat, delta in ((r"^(\d+)\s+day", lambda n: timedelta(days=n)),
                       (r"^(\d+)\s+week", lambda n: timedelta(weeks=n)),
                       (r"^(\d+)\s+month", lambda n: timedelta(days=30 * n))):
        m = re.match(pat, t)
        if m:
            return (today - delta(int(m.group(1)))).isoformat()
    return ""  # '30+ Days Ago' etc. -> unparsable -> skipped by the freshness filter


def fetch_board(spec: dict) -> list[dict] | None:
    """Return normalized jobs [{title, location, posted: date, url}] or None if board unreachable."""
    t = spec["type"]
    if t == "greenhouse":
        d = http_json(f"https://boards-api.greenhouse.io/v1/boards/{spec['token']}/jobs?content=false")
        if d is None or "jobs" not in d:
            return None
        out = []
        for j in d["jobs"]:
            posted = (j.get("first_published") or j.get("updated_at") or "")[:10]
            out.append({"title": j.get("title", ""), "location": (j.get("location") or {}).get("name", ""),
                        "posted": posted, "url": j.get("absolute_url", "")})
        return out
    if t == "lever":
        d = http_json(f"https://api.lever.co/v0/postings/{spec['token']}?mode=json")
        if not isinstance(d, list):
            return None
        return [{"title": j.get("text", ""), "location": (j.get("categories") or {}).get("location", ""),
                 "posted": datetime.utcfromtimestamp(j["createdAt"] / 1000).strftime("%Y-%m-%d"),
                 "url": j.get("hostedUrl", "")} for j in d]
    if t == "ashby":
        d = http_json(f"https://api.ashbyhq.com/posting-api/job-board/{spec['token']}")
        if not d or not d.get("jobs"):
            return None
        return [{"title": j.get("title", ""), "location": j.get("location", ""),
                 "posted": (j.get("publishedAt") or "")[:10], "url": j.get("jobUrl", "")}
                for j in d["jobs"]]
    if t == "smartrecruiters":
        d = http_json(f"https://api.smartrecruiters.com/v1/companies/{spec['token']}/postings?limit=250")
        if not d or not d.get("content"):
            return None
        out = []
        for j in d["content"]:
            loc = j.get("location") or {}
            out.append({"title": j.get("name", ""),
                        "location": f"{loc.get('city','')}, {loc.get('country','')}",
                        "posted": (j.get("releasedDate") or "")[:10], "url": j.get("jobUrl", "")})
        return out
    if t == "workday":
        url = f"https://{spec['host']}/wday/cxs/{spec['tenant']}/{spec['site']}/jobs"
        d = None
        # some tenants reject large pages with HTTP 400 (NVIDIA caps at 20)
        for lim in (40, 20):
            d = http_json(url, {"limit": lim, "offset": 0, "appliedFacets": {}, "searchText": ""})
            if d is not None:
                break
        # tenants differ: some return jobsWithPostings, others jobPostings (NVIDIA)
        postings = (d or {}).get("jobsWithPostings") or (d or {}).get("jobPostings")
        if not postings:
            return None
        out = []
        for j in postings:
            loc = j.get("locationsText", "")
            # NVIDIA collapses multi-site postings to '5 Locations' — the real
            # location is the first externalPath segment ('/job/US-CA-Remote/…_JR…')
            if not loc or re.fullmatch(r"\d+\s+Locations?", loc, re.I):
                seg = (j.get("externalPath") or "").split("/")
                loc = seg[2].replace("-", " ") if len(seg) > 2 else ""
            ep = j.get("externalPath", "")
            out.append({"title": j.get("title", ""), "location": loc,
                        "posted": _workday_posted(j.get("postedOn", "")),
                        # externalPath already starts with '/job/' on most tenants
                        "url": f"https://{spec['host']}{ep if ep.startswith('/job/') else '/job' + ep}"})
        return out
    if t == "rivian_api":
        # careers.rivian.com custom API (cracked 2026-10-17); 10 jobs/page, caps at 600
        out = []
        for page in range(1, 61):
            d = http_json(f"https://careers.rivian.com/api/jobs?page={page}"
                          "&sortBy=relevance&descending=false&internal=false&tags2=Rivian%20Automotive")
            if not d or not d.get("jobs"):
                break
            for j in d["jobs"]:
                j = j.get("data") or j
                out.append({"title": j.get("title", ""), "location": j.get("full_location", ""),
                            "posted": (j.get("posted_date") or j.get("create_date") or "")[:10],
                            "url": f"https://careers.rivian.com/jobs/{j.get('req_id','')}"})
            if len(out) >= min(d.get("totalCount") or 10**9, 600):
                break
        return out or None
    if t == "mcloud":
        # CWS/m-cloud talent-cloud API (Stellantis); GET, plain JSON, US-filtered
        out, off, total = [], 0, 10**9
        while off < min(total, 1000):
            q = urllib.parse.urlencode({
                "pageSize": 100, "offset": off, "companyName": spec["org"],
                "customAttributeFilter": 'primary_country="US"',
                "orderBy": "posting_publish_time desc", "queryLanguageCode": "en-US",
                "disableSpellCheck": "true", "enableBroadening": "true"})
            d = http_json(f"https://{spec['host']}/api/job/search?{q}")
            if not d or not d.get("searchResults"):
                break
            total = d.get("totalHits") or total
            for r in d["searchResults"]:
                j = r.get("job") or r
                out.append({"title": j.get("title", ""),
                            "location": (f"{j.get('primary_city','')}, {j.get('primary_state','')}, "
                                         "United States"),
                            "posted": (j.get("open_date") or "")[:10],
                            "url": j.get("url") or f"{spec.get('base','')}/job/{j.get('id','')}/"})
            off += len(d["searchResults"])
        return out or None
    if t == "gm_html":
        # search-careers.gm.com (Umbraco, cracked 2026-10-17): server-rendered listing
        # pages (20/page, ?page=N, ?search=<kw> works); the umbraco JSON API is
        # cookie+x-ph gated, so scrape HTML. Posted dates live in each detail
        # page's JSON-LD (datePosted) — fetched only for tester-title matches.
        base = spec["base"]
        out, seen = [], set()
        for page in range(1, 51):
            h = http_text(f"{base}/en/jobs/" + (f"?page={page}" if page > 1 else ""))
            if not h:
                break
            n = 0
            for card in re.split(r'<div class="card card-job', h)[1:]:
                m = re.search(
                    r'<a class="stretched-link" href="(/en/jobs/(jr-[\w-]+)/[^"]+)"[^>]*>([^<]+)</a>',
                    card)
                if not m or m.group(2) in seen:
                    continue
                seen.add(m.group(2))
                loc = re.search(r'sprite\.svg#map-marker"></use></svg>([^<]+)', card)
                out.append({"title": m.group(3).strip(),
                            "location": (loc.group(1).strip() if loc else "") + ", United States",
                            "posted": "", "url": base + m.group(1)})
                n += 1
            if n == 0:
                break
        for j in out:
            if TESTER.search(j["title"]):
                d = http_text(j["url"]) or ""
                m = re.search(r'"datePosted":\s*"(\d{4}-\d{2}-\d{2})', d)
                j["posted"] = m.group(1) if m else ""
        return out or None
    if t == "aurora_api":
        # aurora.tech /api/jobs-index (Ashby-backed, cracked 2026-10-17); board caps at 100
        d = http_json("https://aurora.tech/api/jobs-index")
        if not d or not d.get("jobs"):
            return None
        return [{"title": j.get("title", ""), "location": "; ".join(j.get("locations") or []),
                 "posted": j.get("publishedDate", ""), "url": j.get("applyLink", "")}
                for j in d["jobs"]]
    if t == "hawksearch":
        # HawkSearch v2 POST API (Aptiv careers, cracked 2026-10-17); 16/page, ~40 pages
        out = []
        for page in range(1, 41):
            payload = {"ClientData": {"UserAgent": UA["User-Agent"], "VisitId": "0", "VisitorId": "0",
                                      "Custom": {"custom": None}},
                       "Keyword": "", "FacetSelections": {}, "PageNo": page, "IndexName": "",
                       "IgnoreSpellcheck": False, "ClientGuid": spec["guid"],
                       "Is100CoverageTurnedOn": False}
            d = http_json(f"https://{spec['host']}/api/v2/search/", payload)
            if not d or not d.get("Results"):
                break
            for j in d["Results"]:
                doc = j.get("Document") or {}
                out.append({"title": (doc.get("title") or [""])[0],
                            "location": (doc.get("primarylocation") or [""])[0],
                            "posted": ((doc.get("created_moment") or [""])[0])[:10],
                            "url": (doc.get("link") or [""])[0]})
            pag = d.get("Pagination") or {}
            if page >= (pag.get("NofPages") or 1):
                break
        return out or None
    if t == "successfactors_rss":
        url = (f"{spec['base']}/services/rss/job/?locale=en_US"
               f"&keywords={urllib.parse.quote('')}")
        xml_text = http_text(url)
        if xml_text is None:
            return None
        try:
            return parse_successfactors_rss(xml_text)
        except ET.ParseError:
            return None
    return None


def in_scope(title: str) -> str | None:
    if not TESTER.search(title):
        return "no-tester-keyword"
    if MGR_OUT.search(title):
        return "manager"
    if JUNK_OUT.search(title):
        return "junk"
    # Exclude all development/design/hardware/manufacturing/process/quality/supplier/calibration/controls roles
    # even if they have "validation" or "test" in the title (e.g., "Hardware Development and Validation Engineer")
    # Only allow titles where PRIMARY role is explicitly test/validation/verification/HIL/SIL/MIL
    if DEV_OUT.search(title):
        return "dev"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=7)
    ap.add_argument("--company", choices=sorted(BOARDS), help="scan one approved company board")
    ap.add_argument("--probe", action="store_true", help="only report reachable boards")
    ap.add_argument("--verbose", action="store_true", help="show filtered-out fresh roles too")
    args = ap.parse_args()

    if not args.company and not args.probe:
        ap.error("--company is required for a job scan; use --probe only to check board availability")

    today = date.today()
    cutoff = today - timedelta(days=args.max_days)
    keys = [args.company] if args.company else list(BOARDS)
    print(f"fresh_scan — {today} (<= {args.max_days}d, US, tester-only)\n")
    for k in keys:
        specs = BOARDS.get(k, []) + BOARD_FIXES.get(k, [])
        if not specs:
            print(f"  {k:<14} NO AUTOMATED SCAN ADAPTER — search official career portal directly")
            continue
        jobs = None
        for spec in specs:
            jobs = fetch_board(spec)
            if jobs is not None:
                if args.probe:
                    print(f"  {k:<14} OK via {spec['type']}:{spec.get('token', spec.get('host'))} ({len(jobs)} jobs)")
                break
        if jobs is None:
            print(f"  {k:<14} UNREACHABLE ({', '.join(s['type'] for s in specs)})")
            continue
        if args.probe:
            continue
        hits, shown = [], 0
        for j in jobs:
            try:
                posted = date.fromisoformat(str(j["posted"])[:10])
            except ValueError:
                continue
            if posted < cutoff:
                continue
            age = (today - posted).days
            loc = j["location"] or ""
            if NON_US.search(loc):
                reason = "non-US"
            else:
                reason = in_scope(j["title"])
            if reason and not args.verbose:
                continue
            flag = "CANDIDATE" if reason is None else f"out({reason})"
            hits.append((age, f"    {flag} [{age:>2}d] {j['title'][:78]} | {loc[:40]} | {j['url']}"))
        hits.sort()
        if not hits:
            if args.verbose:
                print(f"  --- {k} --- 0 fresh in-scope US jobs")
            continue
        printed = False
        for age, line in hits:
            if not args.verbose and age > args.max_days:
                continue
            if not printed:
                print(f"  --- {k} ---")
                printed = True
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
