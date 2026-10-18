# Job Agent

An autonomous job-application agent. All personal and generated data lives in `data/`
(gitignored). Logic lives here, in `skills/`, and in `templates/`.

Read this file first. Then load the matching skill with the `skill` tool before doing a task.
Do not duplicate rules across files — reference this one.

## Hard rules (never override)

1. **Company career portals only** (Workday, Greenhouse, Lever, iCIMS, Taleo,
   SmartRecruiters, company sites). Never LinkedIn / Indeed / Glassdoor.
   Exception: if a CAPTCHA blocks the portal **and** an Easy Apply exists for the **same**
   role, ask the user first and wait for approval.
2. **Gmail.** Use the user's existing job email. Only search/read verification links, OTPs, and
   application confirmations/rejections from portals in use. Use narrow queries
   (sender domain + recent timestamp). Never open, summarize, or quote any other email.
3. **Never invent facts** on a resume, cover letter, or application. Tailor only by reordering,
   emphasizing, and rewording real experience. **Partial matches are fine — apply anyway**
   (user directive 2026-10-12: the goal is interviews; the company decides fit after the
   interview). When a JD demands a skill the user lacks, note it honestly in the tracker/notes —
   do not ask and do not block. The only reason to pause is a genuine legal/eligibility unknown
   (rule 4).
4. **Never submit** if a legal/eligibility answer is unknown. Ask the user.
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
   Applications #1–#2 were a supervised test run (explicit user approval each time, granted
   2026-10-12). From application #3 on, the agent submits **on its own** but only after both passes
   pass: **pass 1 (truth & eligibility)** — no invented facts, every answer matches
   `data/profile/profile.json` + `answers-bank.json`, role is eligible (location, work auth,
   sponsorship, salary floor), no SSN/bank/government numbers; **pass 2 (completeness &
   accuracy)** — every required field filled with the exact observed option texts, expected comp
   in range, education shows CSU Fullerton + JNTU only (never Trine), resume + cover letter
   attached (visible filename text), EEO per profile. Only then click Submit. The full checklist
   lives in `skills/application-fill/SKILL.md`.
10. **Write like a human.** Every free-text answer (application questions, "what draws you to this
    role", cover letters, recruiter messages) must read like the user talking — natural, specific,
    plain-spoken. No resume-speak, no buzzword stacking, no templated filler. Use only real
    experience, and never state a tenure that isn't true — the user has **9+ years total**
    (Apr 2017 → present); **Ford is only Feb 2021 → present (~5.5 yrs, contract via Actalent)**.
    Prefer concrete detail (CAN logs, HIL/SIL rigs, target hardware) over adjectives.
11. **Be autonomous — don't lean on the user.** Decide, act, and record. The moment a new answer is
    learned, save it to `data/profile/answers-bank.json` so it is never asked twice, and self-answer
    anything consistent with the profile. Batch any genuinely required questions and ask at most once
    per session. Only a legal/eligibility unknown (rule 4) may pause an application. Target: run a
    full session needing zero input between "start" and "stop". **Adaptation target: a brand-new user
    must reach full autonomy within at most 5 applications** — every new question is saved to the
    answers bank and reused, so asks converge to zero. Keep the setup user-agnostic (all personal
    data under `data/`) because the user intends to share this agent with friends.

## File hygiene

- Build resume/cover-letter HTML in the system temp directory, convert to PDF, then delete the
  HTML and any intermediates.
- Each job folder `data/applications/<Company>_<Title>_<JobID>_<YYYY-MM-DD>/` keeps only:
  resume PDF, cover-letter PDF, `job-description.md`, and the confirmation screenshot
  (keep DOCX only if a portal requires it).
- **After a successful submit**, move the job folder from `data/applications/current/` to
  `data/applications/history/` — a folder counts as *applied* once it holds
  a confirmation screenshot — `confirmation_screenshot.png`, any image file, or any file named with `confirm`/`applied`/`success` (a manual apply may save it under any name). Running `python skills/documentation.py` archives every applied
  folder left in `current/`; `python skills/archive_hook.py` watches `current/` and archives automatically (or `--once` for a single pass).
- Names: `<First>_<Last>_Resume.pdf` and `<First>_<Last>_CoverLetter.pdf` (no company name — each job has its own folder).
- Clear downloads, temp files, and failed drafts after each application.
- Before ending any session, confirm the project folder is clean and organized.

## Control flow

- **start** — load `data/state/state.json` and the tracker, then loop: search → tailor → login →
  apply → log.
- **stop** — finish or safely abort the current form, save state (company, job, step, queue), halt.
  The next start resumes exactly there.
- **I found a job** — stop permanently, summarize stats, ask whether to keep the setup for later.
- **Archive hook.** Start `python skills/archive_hook.py` (background watcher) at **start** and let it
  run for the session; it moves any `current/` folder that gains a confirmation screenshot (any image file, or any file named with confirm/applied/success — so a manual apply works too) into
  `history/`. `python skills/archive_hook.py --once` is an idempotent one-shot archive — safe to run
  after any submit and at **stop**.
- Keep a **30–90 s pause between applications**. Every ~5 applications give a brief progress summary. **Stop after ~12 applications** (session budget) and report.
- At every stop / session end, remind: *"No daily application cap is set. Want to set one?"*

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
  that gets submitted. Use `skills/tailoring/scripts/match_score.py` (single folder, or
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
  aerospace are OUT. **Priority order per role: 1) automotive industry → 2) position name (the
  logic's role names: ADAS, AV, integration, validation, HIL/SIL, test automation, reliability,
  verification, systems integration, quality-validation, embedded/ECU, EV/powertrain, infotainment)
  → 3) domain breadth.**
- **Role-function filter (user directive 2026-10-14): the user is a tester, not a developer.**
  Queue **test / validation / verification / integration / HIL-SIL-MIL / test-automation / reliability**
  roles. Reject roles whose primary job is writing product code — Software Engineer, Developer,
  full-stack / backend / frontend / web, Android app frameworks, ML / algorithms / research, data
  science, platform / SRE / DevOps. `Software **Test** Engineer` / `Software **Validation** Engineer`
  are IN scope (testing the software); plain "Software Engineer" is not. Ambiguous title → judge by
  the JD responsibilities.
- **Domain focus (user directive 2026-10-14, revised): autonomous-vehicle testing/validation is the
  lead domain — then equal breadth.** Search **AV test / AV validation / AV systems integration & test
  / AV vehicle-level, simulation and behaviour validation / AV test operations & test infrastructure**
  — plus anything adjacent to AV validation — **first**, and give AV-validation roles the first queue
  slots. Then one query set each for infotainment / IVI / HMI / connected-vehicle, HIL-SIL test,
  systems integration & test, ADAS/AD validation, EV / battery / powertrain / charging, embedded / ECU
  / CAN diagnostics, quality / reliability / DVP&R, test automation and software validation.
  **Chassis / thermal / NVH is dropped** (user directive 2026-10-14). Never over-weight infotainment.
  Still tester-only: AV roles that write product code stay out; AV test/validation/integration roles
  are in.
- **Gmail watch (user directive 2026-10-14): keep the tracker current in near-real time.** Check the
  job inbox with narrow queries (portal sender domain + `since`) at session start, after every
  single application, after every burst, and at least every ~15–20 min while the session is
  running. Fold any Interview / Offer / Rejected straight into the tracker `Status` (and the Notes)
  the moment it arrives, and report new responses at the next check-in. Read only application
  responses / OTPs / confirmations from portals in use — nothing else (rule 2).
- Source of truth for applied: applications folder confirmations (confirmation_screenshot.png). Do NOT trust tracker count alone.
- **Round-robin sweep — no per-company caps, no max-5 queue (user-approved 2026-10-17).** Walk the company list **one role per company, in companies.md list order (top→bottom)**, starting at a **rotating cursor** (each round resumes where the last one stopped; the cursor comes from `sweep.cursor` in `state.json` when set, else it is derived from the most recently applied company) — get the order + spacing check from `python skills/job-search/scripts/sweep.py` (`... --company "Lucid Motors"` exits 1 when the company is cooling). Queue one role per company (24h preferred / 7d fallback, >7d never, manager filter, dedupe vs tracker+prior-apps). A company applied to within the last **3 days** is COOLING — skip it this round (`min_days_between` in `state.json`; `--min-days 0` disables the guard). A company with no role posted in the last 24 h is skipped that round. A company with several fresh roles queues its best (newest <24h, then highest match); the rest wait for the next round. Obey a company's **own** ATS-stated limit (e.g. Waymo 5/60d) — that is not our cap. Then apply **sequentially, one by one through the list**: tailor+fill+submit with PDF content verification (no {{tokens}}, >=200 chars, contains name). When the round ends, continue from the cursor (the next round starts where the last one left off). **Never apply one-by-one in parallel** — apply in order. Session budget: **~12 applications per session**, then stop and report.
- PDF verification: verify before upload (resume >=200 chars with name, no tokens; cover >=100 chars). Regenerate if fails.
- The sweep order is the companies.md list order (top→bottom) with a rotating cursor. Within a round, prefer a company's never-applied-to state when picking among its fresh roles — but do not reorder the list.
- Daily cap reminder: suppressed unless explicitly asked.
