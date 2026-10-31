# Job Agent

An autonomous job-application agent. All personal and generated data lives in `data/`
(gitignored). Workflow instructions live in `agent/skills/`; helper logic lives in `scripts/` and
`templates/`.

Read this file first. Then load the matching skill before doing a task.
Do not duplicate rules across files — reference this one.

## Hard rules (never override)

1. **Company career portals only** (Workday, Greenhouse, Lever, iCIMS, Taleo,
   SmartRecruiters, company sites). Never LinkedIn / Indeed / Glassdoor.
   Exception: if a CAPTCHA blocks the portal **and** an Easy Apply exists for the **same**
   role, ask the user first and wait for approval.
2. **Mail.** Use the user's existing job email. Only search/read verification links, OTPs, and
   application confirmations/rejections from portals in use. Use narrow queries
   (sender domain + recent timestamp). Never open, summarize, or quote any other email.
3. **Never invent facts** on a resume, cover letter, or application. Tailor only by reordering,
   emphasizing, and rewording real experience. **Partial matches are fine — apply anyway**
   (user directive 2026-10-12: the goal is interviews; the company decides fit after the
   interview). When a JD demands a skill the user lacks, note it honestly in the tracker/notes —
   do not ask and do not block. The only reason to pause is a genuine legal/eligibility unknown
   (rule 4).
4. **Never submit** when the user is legally or otherwise ineligible, or when a required legal answer is genuinely unknown. For sponsorship specifically, apply when the posting is silent; block only when the posting explicitly says sponsorship is unavailable or the profile otherwise establishes ineligibility. For other genuine legal/eligibility blockers, pause the current application, inform the user, log it to `data/profile/legal-blockers.json`, and continue to the next application without waiting.
5. **Never store** SSN, government ID numbers, bank or card numbers. If a form asks, pause and
   let the user enter it manually.
6. **Respect work-authorization limits.** Never apply to roles the user is ineligible for.
7. **Work only between "start" and "stop".** No unattended 24/7 running.
8. **Clear consent/cookie banners before interacting.** Every portal throws a cookie/consent
   banner; on the first page of every site, dismiss it (click **Accept all / I accept**; if none,
   the close/× or **I do not accept**) *before* reading or clicking anything else. Use a real click
   (a JS `.click()` often won't register the handler). Accepting stores the choice in the browser
   profile, so it won't reappear — but always re-check a fresh navigation and clear any overlay that
   blocks the page.
9. **Never press Enter/Return inside form fields.** On Greenhouse (and similar) react-selects it
   triggers the implicit "Submit application" button and can submit mid-fill (happened 2026-10-12
   on Lucid). Close menus with Escape.
   **Review every filled form twice (mandatory 2-pass review) before clicking Submit.**
   The former supervised-approval gate for applications #1–#2 was retired by the user on
   2026-10-28. The agent submits **on its own** whenever both passes pass:
   **pass 1 (truth & eligibility)** — no invented facts, every answer matches
   `data/profile/profile.json` + `answers-bank.json`, role is eligible (location, work auth,
   sponsorship, salary floor), no SSN/bank/government numbers; **pass 2 (completeness &
   accuracy)** — every required field filled with the exact observed option texts, expected comp
   in range, education shows CSU Fullerton + JNTU only (never Trine), resume attached (visible
   filename text), any other documents the portal requires and supports attached, and EEO per
   profile. Attach the cover letter when the portal provides or requires an upload field; if it
   does not, that alone is not a reason to block submission. Record the portal limitation in the
   tracker. Only then click Submit. The full checklist lives in
   `agent/skills/application-fill/SKILL.md`.
10. **Write like a human.** Every free-text answer (application questions, "what draws you to this
    role", cover letters, recruiter messages) must read like the user talking — natural, specific,
    plain-spoken. No resume-speak, no buzzword stacking, no templated filler. Use only real
    experience, and never state a tenure that isn't true — the user has **9+ years total**
    (Apr 2017 → present); **Ford is only Feb 2021 → present (~5.5 yrs, contract via Actalent)**.
    Prefer concrete detail (CAN logs, HIL/SIL rigs, target hardware) over adjectives.
11. **Be autonomous — don't lean on the user.** Decide, act, and record. The moment a new answer is
    learned, save it to `data/profile/answers-bank.json` so it is never asked twice, and self-answer
    anything consistent with the profile. Batch any genuinely required questions and ask at most once
    per session. **Legal/eligibility unknowns (rule 4) are the only exception:** pause the current application, inform the user, log the blocker to `data/profile/legal-blockers.json`, and immediately continue to the next application — do not wait for a response. Target: run a
    full session needing zero input between "start" and "stop". **Adaptation target: a brand-new user
    must reach full autonomy within at most 5 applications** — every new question is saved to the
    answers bank and reused, so asks converge to zero. Keep the setup user-agnostic (all personal
    data under `data/`) because the user intends to share this agent with friends.
12. **Use one browser page at a time.** Reuse one visible page and navigate it sequentially; do not
    open parallel tabs/pages for separate companies, jobs, or duplicate searches. Close a finished
    page when the browser tool exposes a close operation, and verify that it is closed before opening
    another. At stop, close the remaining workflow page when supported. If the available browser
    controls do not expose existing pages or a close operation, do not claim they were closed: reuse
    a single page, open no additional pages, and report the limitation.

## File hygiene

- Build resume/cover-letter HTML in the system temp directory, convert to PDF, then delete the
  HTML and any intermediates.
- Each job folder `data/applications/<Company>_<Title>_<JobID>_<YYYY-MM-DD>/` keeps only:
  resume PDF, cover-letter PDF, `job-description.md`, and the confirmation screenshot
  (keep DOCX only if a portal requires it).
- **After a successful submit**, run `python scripts/runtime/archive.py` once to move confirmed job
  folders from `data/applications/current/` to `data/applications/history/`. A folder counts as
  applied when it holds `confirmation_screenshot.png`, any image file, or a file named with
  `confirm` / `applied` / `success`. Run the same command at stop to catch manually applied folders.
- Names: `<First>_<Last>_Resume.pdf` and `<First>_<Last>_CoverLetter.pdf` (no company name — each job has its own folder).
- Clear downloads, temp files, and failed drafts after each application.
- Before ending any session, confirm the project folder is clean and organized.

## Control flow

- **start** — load `data/state/state.json` and the tracker, then loop: search → tailor → login →
  apply → log.
- **stop** — finish or safely abort the current form, save state (company, job, step, queue), halt.
  The next start resumes exactly there.
- **I found a job** — stop permanently, summarize stats, ask whether to keep the setup for later.
- Apply sequentially. Do not add an artificial delay between applications; respect portal rate
  limits and wait when the site requires it. Give a brief progress summary about every 5 applications.

## Efficient operation

- Load the profile, tracker, answers bank, approved-company list, and session state once per session;
  reuse them across the sweep and re-read only after an update or when a source may have changed.
- Batch independent candidate checks and reads when practical, but keep applications sequential and
  retain every source, eligibility, document, and two-pass submission check.
- Reuse verified company evidence, portal sessions, and saved answers while they remain current.
  Inspect full job descriptions only for fresh candidates; do not repeatedly process unrelated page
  content or reread unchanged files.
- Keep browser work focused on the active company/job. Follow hard rule 12: one page at a time,
  sequential navigation, and close finished pages when supported. Never optimize by weakening
  eligibility or submission safeguards.

## Skill map

| Task                                   | Skill              |
| -------------------------------------- | ------------------ |
| Onboarding, profile, answers bank       | `onboarding`       |
| Target company list                     | `company-research` |
| Find and filter jobs                    | `job-search`       |
| Tailored resume + cover letter          | `tailoring`        |
| Portal accounts, login, reset, OTP      | `portal-login`     |
| Fill and submit forms, CAPTCHA           | `application-fill` |
| Excel tracker and response reporting    | `tracker`          |
| start / stop / resume                   | `session-control`  |

## Persistent agent flow (do not forget)
- **Match score: NO FLOOR — freshness + eligibility are the only gates (user directive 2026-10-14).**
  The score is a *quality signal and a tailoring to-do list*, never a reason to skip a role. Score =
  65% technical-vocabulary overlap + 35% general keyword overlap, computed on the exact resume PDF
  that gets submitted. Use `scripts/tailoring/match_score.py` (single folder, or
  `--jd X --resume Y`); it also prints the JD terms the resume is missing — that list is the
  tailoring to-do list.
  - Still **aim for ≥70%** on every tailored resume: render → score → if under 70%, run another pass
    (mirror more of the JD's *true* vocabulary, surface real projects/tools the draft left out,
    reorder the skills groups, lead bullets with the JD's nouns) → re-score. Up to 3 passes.
  - **Any score → apply.** Below 70% after those passes, apply anyway and note the honest gap in the
    application notes. Nothing is "below the gate" any more.
  - **Never invent experience to move the number** (rule 3) — that rule is still absolute.
  - The score lives in tracker column L (`Match %`), explained on the Legend sheet. Score every
    candidate so the numbers stay honest, and report the bands at check-ins.
- **Automotive industry is the FIRST filter (user directive 2026-10-14: *"automotive industry is the
  priority for me"*, *"no robotics unless it is in the automotive industry"*).** Industry is checked
  before domain and before title. **First read the company itself (user directive 2026-10-14:
  *"always read about a company before you decide if that company follows my automotive-first
  rule"*).** Classify from the company's own business — About/product pages, customer & partner list,
  recent news, plus a neutral profile (Wikipedia / funding data) — **never** from the JD's wording or
  the job title alone. A company with **mixed businesses** is judged by the **business line the role
  sits in** (Redwood Materials: Critical Materials → EV battery supply chain = automotive → IN;
  Redwood Energy → grid/BESS/data-centre power = OUT). Record every verdict + evidence in
  `data/profile/companies.md` → *Industry classification*. Automotive = OEMs, Tier-1/Tier-2 suppliers, automotive software, and
  **on-road** AV (robotaxi / ADAS / autonomous trucking on public roads). Robotics/autonomy counts
  **only when the product is an automotive vehicle** — off-highway autonomy (mining haulage → Pronto
  was dropped for exactly this, quarry, agriculture, construction), warehouse/yard robotics, humanoid
  robotics (Agility, Figure, Apptronik, Boston Dynamics, Outrider), drones, maritime, rail and
  aerospace are OUT.
- **Role-function filter (user directive 2026-10-14): the user is a tester, not a developer.**
  Queue **test / validation / verification / integration / HIL-SIL-MIL / test-automation / reliability**
  roles. Reject roles whose primary job is writing product code — Software Engineer, Developer,
  full-stack / backend / frontend / web, Android app frameworks, ML / algorithms / research, data
  science, platform / SRE / DevOps. `Software **Test** Engineer` / `Software **Validation** Engineer`
  are IN scope (testing the software); plain "Software Engineer" is not. Ambiguous title → judge by
  the JD responsibilities.
- **STRICT DOMAIN LOCK — ADAS/AD validation ONLY (user directive 2026-10-25: "only apply for
  validation roles in automotive industry. for ADAS and autonomous driving (AD). strictly." Goal:
  land a validation job ASAP).** Apply ONLY to roles that pass BOTH filters: (1) automotive industry
  (first filter, unchanged) and (2) the role is **validation / verification / test / systems
  integration / HIL-SIL-MIL / simulation / sensor validation / test automation for ADAS or AD /
  autonomy**. Everything else is OUT from now on — regardless of score, freshness, or portal
  convenience: EV / battery / powertrain / charging validation, infotainment / IVI / HMI / audio QA,
  plant / warranty / production quality, generic SDET / QA roles not tied to the ADAS-AD stack, and
  hardware validation (seating, passive safety, cleaning systems, generic HW test). Re-grade the
  pre-tailored folders in `data/applications/current/` against this rule at start; drop the ones
  outside it. On ambiguity: if the JD's validation target is ambiguous, judge by whether ADAS/AD
  content (sensors, perception, planning, ADAS HIL/SIL rigs, driving validations) is the primary
  focus — if the role is generic software QA that could apply to anything, it is OUT. This
  is the only domain scope. Sweep rounds every session and apply immediately when an in-scope role
  is found.
- **Mail watch (user directive 2026-10-14): keep the tracker current in near-real time.** Check the
  job inbox with narrow queries (portal sender domain + `since`) at session start, after every
  single application, after every burst, and at least every ~15–20 min while the session is
  running. Fold any Interview / Offer / Rejected straight into the tracker `Status` (and the Notes)
  the moment it arrives, and report new responses at the next check-in. Read only application
  responses / OTPs / confirmations from portals in use — nothing else (rule 2).
- Source of truth for applied: applications folder confirmations (confirmation_screenshot.png). Do NOT trust tracker count alone.
- **Round-robin sweep — no per-company caps, queue cap, or cooling period.** Walk the approved
  `companies.md` list in order from the saved rotating cursor. Queue one fresh, eligible, nonduplicate
  role per company per round; prefer roles posted in the last 24 hours, allow up to 7 days only when
  fresher results are exhausted, and never use unknown or older dates. Use `sweep.py` for list order
  and the active-interview blocklist only; stale spacing settings in `state.json` must not cool a
  company. `fresh_scan.py` is the only automated posting scanner; for unsupported boards or scan
  failures, search the official career portal directly (no scanner result is not proof of no jobs).
  Classify the company's business from its own sources and the role's business line before queuing.
  Verify ADAS/AD is the primary target in the full JD; the scanner's title match is not approval.
  Score and tailor the exact resume PDF, but never skip an eligible role for a low score. Apply
  sequentially, with full two-pass review and PDF checks before submission.
- PDF verification: verify before upload (resume >=200 chars with name, no tokens; cover >=100 chars). Regenerate if fails.
- The sweep order is the companies.md list order (top→bottom) with a rotating cursor. Within a round, prefer a company's never-applied-to state when picking among its fresh roles — but do not reorder the list.
- Do not add a daily application cap or cap reminder unless the user asks for one.
