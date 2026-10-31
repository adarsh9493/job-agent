---
name: job-search
description: Use when searching approved company career portals for fresh ADAS/AD validation roles. Verify eligibility and duplicates, then queue eligible candidates.
---

# Job Search

Find fresh ADAS/AD validation roles on approved company career portals. This skill follows the
current policy in `AGENTS.md`; it does not define a separate search policy.

## Inputs

- `data/profile/companies.md` — approved companies, career URLs, ATS types, and industry evidence.
  Query it with `python scripts/runtime/companies.py show "<name>"` (cached verdict + stale flag).
- `data/profile/profile.json` — work authorization, locations, exclusions, and salary floor.
- `data/tracker/applications.xlsx` — check duplicates with
  `python scripts/runtime/tracker.py has-applied`; never read the sheet whole.
- `data/profile/prior-applications.md` — pre-existing applications; compare company + title + location.
- `data/state/state.json` — current queue and rotating sweep cursor; read it through
  `python scripts/runtime/state.py` / `sweep.py --next`.

**Full filter definitions (automotive-first, role function, strict ADAS/AD lock, freshness, sweep):
`reference/filters.md`.** Apply them exactly; this skill does not redefine them.

## Workflow

1. Load profile, tracker, prior applications, and state once for the sweep; reuse those loaded facts
   between companies and re-read only when a source changes. Re-grade folders in
   `data/applications/current/` against the strict ADAS/AD rule in `AGENTS.md`.
   Leave in-scope work intact; remove only out-of-scope generated drafts.
2. Walk the approved company list in order from the saved rotating cursor. Read the company’s own
   business sources and classify mixed-business roles by business line before searching. Record the
   verdict and evidence in `companies.md`.
3. Search company career portals only. Search ADAS / autonomous driving / on-road autonomy
   validation, test, verification, HIL/SIL/MIL, simulation, sensor validation, driving scenarios,
   perception, planning, and systems integration.
4. Inspect the complete job description. The primary validation target must be ADAS/AD/autonomy;
   a relevant title or a general automotive employer is not enough. Reject unrelated roles including
   EV/powertrain, infotainment, production quality, generic SDET/QA, and non-automotive robotics.
5. Apply the freshness rule: prefer postings from the last 24 hours; use up to 7 days only after
   fresher results are exhausted. Never queue unknown or older dates.
6. Check work authorization, sponsorship, location, salary floor, exclusions, manager status, and
   company ATS limits. An unknown legal/eligibility answer blocks this application; record it and
   continue to the next role.
7. Deduplicate against the tracker, prior applications, and current/history folders using company,
   job ID, URL, and title + location. Verify possible duplicates before queueing.
8. Use `scripts/scan/fresh_scan.py` as the only automated posting scanner, and only to
   discover candidates. A scanner hit is not an industry, ADAS/AD, eligibility, or duplicate
   approval; verify those from source pages. If a company has no scanner adapter or scanning fails,
   search its official career portal directly; no scan results do not mean no jobs exist.
9. Queue at most one role per company in each round, in company-list order. Choose the freshest
   eligible role, then the best match. Continue round-robin from the next company after each round.
   There is no agent-imposed cooling period or queue cap; obey only company-stated application limits
   and active interview blocks.
10. Save the observed job description in the job folder. Score against the exact tailored resume PDF
    after rendering. Match score is a tailoring signal, never an eligibility gate.

## Rules

- Never use LinkedIn, Indeed, or Glassdoor as a job source.
- Do not infer automotive industry or ADAS/AD relevance from a job title alone.
- Do not queue product-development roles, people-manager roles, or roles the user is ineligible for.
- Use `scripts/runtime/sweep.py` only for approved-company order and active interview
  blocking. It does not scan postings or enforce the freshness rule. There is no agent-imposed
  cooling period.
- Apply sequentially, not in parallel.

## Output

Eligible, nonduplicate ADAS/AD validation candidates with observed job descriptions and the queue
updated in `data/state/state.json`.
