<!-- GENERATED - do not edit. Source: agent/skills/job-search/reference/filters.md -->

# Search filters (user directives — do not relax)

## 1. Automotive industry is the FIRST filter (2026-10-14)

*"Automotive industry is the priority for me"*, *"no robotics unless it is in the automotive
industry"*. Industry is checked before domain and before title.

- **Read about the company itself first** (*"always read about a company before you decide if that
  company follows my automotive-first rule"*): its About/product pages, customer & partner list,
  recent news, plus a neutral profile (Wikipedia / funding data). **Never** classify from the JD's
  wording or the job title.
- A **mixed-business** company is judged by the **business line the role sits in** (Redwood
  Materials: Critical Materials → EV battery supply chain = automotive → IN; Redwood Energy →
  grid/BESS/data-centre power = OUT).
- **Automotive** = OEMs, Tier-1/Tier-2 suppliers, automotive software, and **on-road** AV (robotaxi
  / ADAS / autonomous trucking on public roads).
- Robotics/autonomy counts **only when the product is an automotive vehicle**. **OUT:** off-highway
  autonomy (mining haulage → Pronto was dropped for exactly this; quarry, agriculture,
  construction), warehouse/yard robotics, humanoid robotics (Agility, Figure, Apptronik, Boston
  Dynamics, Outrider), drones, maritime, rail, aerospace.
- Record every verdict **+ evidence** in `data/profile/companies.md` → *Industry classification*;
  `python scripts/runtime/companies.py show "<name>"` returns the cached verdict and flags a stale
  one (older than 180 days) for re-check.

## 2. Role function: the user is a tester, not a developer (2026-10-14)

Queue **test / validation / verification / integration / HIL-SIL-MIL / test-automation /
reliability** roles. Reject roles whose primary job is writing product code — Software Engineer,
Developer, full-stack / backend / frontend / web, Android app frameworks, ML / algorithms /
research, data science, platform / SRE / DevOps. `Software **Test** Engineer` / `Software
**Validation** Engineer` are IN scope; plain "Software Engineer" is not. Ambiguous title → judge by
the JD responsibilities.

## 3. STRICT DOMAIN LOCK — ADAS/AD validation only (2026-10-25)

*"Only apply for validation roles in automotive industry. For ADAS and autonomous driving (AD).
Strictly."* Goal: land a validation job ASAP.

Apply ONLY when **both** filters pass: (1) automotive industry (filter 1, unchanged) and (2) the
role is **validation / verification / test / systems integration / HIL-SIL-MIL / simulation /
sensor validation / test automation for ADAS or AD / autonomy**.

**OUT regardless of score, freshness, or portal convenience:** EV / battery / powertrain / charging
validation, infotainment / IVI / HMI / audio QA, plant / warranty / production quality, generic
SDET / QA roles not tied to the ADAS-AD stack, hardware validation (seating, passive safety,
cleaning systems, generic HW test).

On ambiguity: if the JD's validation target is ambiguous, judge by whether ADAS/AD content
(sensors, perception, planning, ADAS HIL/SIL rigs, driving validations) is the primary focus. A
generic software QA role that could apply to anything is OUT. Re-grade folders in
`data/applications/current/` against this rule at start and drop the ones outside it.

## 4. Freshness and round-robin sweep

- Prefer postings from the **last 24 hours**; allow up to **7 days** only when fresher results are
  exhausted. Never queue unknown or older dates.
- **One fresh, eligible, nonduplicate role per company per round**, in `companies.md` list order
  from the saved rotating cursor (`python scripts/runtime/sweep.py --next`).
- **No per-company caps, no queue cap, no cooling period.** Only company-stated application limits
  and the active-interview blocklist apply. Stale spacing settings in `state.json` must not cool a
  company.
- Within a round, prefer a company's never-applied-to state when picking among its fresh roles, but
  do not reorder the list.
- `fresh_scan.py` is the only automated posting scanner. For unsupported boards or scan failures,
  search the official career portal directly — **no scanner result is not proof of no jobs**.
- Sweep every session and apply immediately when an in-scope role is found.
- Never add a daily application cap or cap reminder unless the user asks for one.

## 5. Dedupe and source of truth

- Deduplicate against the tracker (`python scripts/runtime/tracker.py has-applied`), prior
  applications, and current/history folders using company, job ID, URL, and title + location.
- **Source of truth for "applied" is the job folder confirmation screenshot**
  (`confirmation_screenshot.png`), not the tracker count alone.

## 6. Cadence

- Apply sequentially, never in parallel. No artificial delay between applications; respect portal
  rate limits and wait when the site requires it.
- Give a brief progress summary about every 5 applications.
