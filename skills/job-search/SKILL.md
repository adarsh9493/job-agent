---
name: Job Search
description: Search company career portals in a hidden background browser, apply freshness and eligibility filters plus a duplicate check, and queue scored job candidates.
---

# Job Search

**Goal:** find fresh, eligible roles on target companies' own portals and queue the good ones.

## Inputs

- `data/profile/companies.md` — target companies and portals.
- `data/profile/profile.json` — work authorization, locations, seniority, exclusions.
- `data/tracker/applications.xlsx` — read before every search to prevent duplicates.
- `data/profile/prior-applications.md` — pre-existing/old-agent applications (OCR-derived, no job
  IDs) — also check for duplicates (match by company + title [+ location]).
- `data/state/state.json` — current queue.

## Steps

1. For each target company portal, search by **function × domain keyword pairs**, not fixed titles:
   - **Function words (required):** test, testing, validation, verification, integration, HIL, SIL,
     MIL, test automation, reliability, systems integration, quality (validation side), lab.
   - **Domain words (priority):** autonomous vehicle, AV test, AV validation, autonomy, self-driving,
     robotaxi, ADAS, simulation validation, scenario validation, vehicle-level validation, test
     operations, test infrastructure, infotainment, IVI, HMI, connected vehicle, connectivity,
     telematics, Android Automotive, QNX, cluster, OTA, vehicle software, cabin, EV, powertrain,
     sensors, ECU, CAN.
   - **Role-function filter (hard — user directive 2026-10-14): the user is a tester, not a
     developer.** Reject titles whose job is writing product code — Software Engineer, Developer,
     full-stack / backend / frontend / web, Android app frameworks, ML / algorithms / research, data
     science, platform / SRE / DevOps. `Software Test Engineer` / `Software Validation Engineer` are
     in scope. Ambiguous → read the responsibilities; if it is building product code, skip.
   - **Domain focus (user directive 2026-10-14, revised): autonomous-vehicle testing/validation
     first, then breadth.** Lead every sweep with **AV test / AV validation / AV systems integration &
     test / AV vehicle-level, simulation and behaviour validation / AV test operations & test
     infrastructure** — plus anything adjacent to AV validation — and give AV-validation roles the
     first queue slots. Then run one query set each for HIL/SIL, systems integration, ADAS/AD,
     EV/battery/powertrain, embedded/ECU/CAN, infotainment/IVI/HMI/connected-vehicle,
     quality/reliability and test automation. **Chassis / thermal / NVH is no longer searched.**
     Never over-weight infotainment; the goal is a job.
2. **Freshness filter:**
   - PRIMARY: posted within the **last 24 hours**.
   - FALLBACK: up to **7 days**, only when 24h results are exhausted.
   - HARD CEILING: **never** anything older than 7 days. Record the posting date; **skip if unknown**.
3. **Eligibility filters:** work authorization / sponsorship, location / remote, seniority, exclusions
   (contract/C2C, defense/govt, security clearance, **and manager roles**).
   - **INDUSTRY FILTER — FIRST (user directive 2026-10-14: *"automotive industry is the priority for
     me"*).** **Read about the company before deciding whether it passes** (user directive 2026-10-14:
     *"always read about a company before you decide if that company follows my automotive-first
     rule"*): the corporate site / About + product pages, its customer & partner list, recent news,
     plus a neutral profile (Wikipedia / funding data). Never classify from the JD's wording or the
     title alone. A **mixed-business** company is judged by the **business line the role sits in**
     (Redwood Materials → Critical Materials = automotive IN, Redwood Energy = grid/BESS OUT). Record
     the verdict + evidence in `data/profile/companies.md` → *Industry classification*.
     Automotive = OEMs, Tier-1/Tier-2 suppliers, automotive software, and **on-road** AV
     (robotaxi / ADAS / autonomous trucking on public roads). **Robotics/autonomy is in scope only
     when the product is an automotive vehicle** — so off-highway autonomy (mining haulage → Pronto,
     quarry, agriculture, construction), warehouse/yard robotics, humanoid robotics (Agility, Figure,
     Apptronik, Boston Dynamics, Outrider), drones, maritime, rail and aerospace are all OUT.
     Priority order per role: **1) automotive industry → 2) position name → 3) domain breadth.**
   - **Position-name filter (user directive 2026-10-14: *"then comes position names … like ADAS, AV,
     integration, validation, HIL and the rest of the names part of your agent logic"*).** Search and
     rank by the role names in the logic: ADAS/AD, AV / autonomous vehicle, integration, validation,
     verification, HIL/SIL/MIL, test automation, reliability, systems integration, quality
     (validation side), embedded/ECU, EV/powertrain, infotainment.
   - **Manager-role filter (user rule 2026-10-12):** skip any posting whose title contains
     **Manager, Director, Head of, VP, Vice President, Chief,** or **Supervisor** (people-manager
     roles). Individual-contributor titles (**Senior / Lead / Staff / Principal Engineer**) are fine.
     If a title is ambiguous (e.g., "Technical Lead Manager"), treat it as a manager role → skip.
4. **Duplicate check** against the tracker **and `data/profile/prior-applications.md`**
   (company + job ID / URL / title+location). Never queue a role already applied to, including
   duplicate postings of the same role. When company+title match a pre-existing entry whose ID is
   unknown, treat as a **possible duplicate** and verify (portal login) before applying.
5. **Match score 0–100 — a quality signal and tailoring to-do list, NOT a gate.** There is **no
   score floor** (user directive 2026-10-14): freshness + eligibility are the only gates, and every
   eligible fresh role is queued and applied. Score = 65% technical-vocabulary overlap + 35% general
   keyword overlap, computed on the resume PDF that will be submitted
   (`skills/tailoring/scripts/match_score.py`). It also prints the JD terms the resume is missing —
   that list *is* the tailoring to-do list. Target ≥70% when tailoring (75%+ = priority band); a low
   score never blocks an application — record it in tracker column L and note the honest gap.
6. **Round-robin sweep — one role per company, NO per-company caps (user-approved 2026-10-17).**
   Walk the company list **one role per company, in companies.md list order (top→bottom)**, starting
   at a **rotating cursor** — each round resumes where the last one stopped. The cursor comes from
   `sweep.cursor` in `state.json` when set, else it is derived from the most recently applied
   company. Get the order and the spacing check from
   `python skills/job-search/scripts/sweep.py`
   (`... --company "Lucid Motors"` exits 1 when the company is cooling). A company applied to within
   the last **3 days** is cooling — skip it this round (`min_days_between` in `state.json`;
   `--min-days 0` disables the guard). A company with no role posted in the last 24 h is skipped that
   round. A company with several fresh eligible roles queues its **best** (newest <24h, then highest
   match) and the rest wait for the next round. The old tiered caps (3 default / 2 small per 30 days,
   1 per title family) are **removed**. Still obey a company's **own** ATS-stated limit (e.g. Waymo
   5/60d) — that is not our cap.
7. Save each queued candidate's job description to its job folder as `job-description.md`.
8. Add approved candidates to the queue in `data/state/state.json` — **one per company per round**.

## Rules

- Run in a **background, hidden browser**.
- Clear any cookie/consent banner on first load before reading the list (`AGENTS.md` rule 8).
- Skip any posting whose date cannot be determined.
- Never apply to a role the user is ineligible for (`AGENTS.md` rule 6).
- **Never skip a role because of a low match score** — no floor; only freshness + eligibility gate.
- **One role per company per round; there are no per-company caps.** Use
  `python skills/job-search/scripts/sweep.py` for the sweep order and the 3-day spacing check before
  queueing or applying (a cooling company — applied within the last 3 days — is skipped this round).
- **Session budget: ~12 applications**, then stop and report (no daily cap is set).
- **Always read the company before an industry verdict** (user rule 2026-10-14: *"always read about a
  company before you decide if that company follows my automotive-first rule"*) — the company's own
  business, not the JD's wording or the title alone; record the verdict + evidence in
  `data/profile/companies.md`.
- Never queue a **manager/people-manager role** (Manager / Director / Head of / VP / Chief /
  Supervisor in the title) — user rule 2026-10-12.
- **Never queue a non-automotive company or role** — automotive industry is the first filter
  (Pronto, mining/off-highway autonomy, warehouse/humanoid robotics, drones, aerospace are OUT).

## Outputs

- Scored candidates; JD saved per job; queue updated in `data/state/state.json`.
