# Job Agent

Autonomous job-application agent. Personal and generated data lives in `data/` (gitignored).
Canonical instructions: this file + `agent/skills/` (one skill per step, plus a skill's
`reference/` file only when named). Tool names: `agent/TOOLS.md`; model tiers:
`agent/MODEL_POLICY.md`. Edit `agent/`, then run `scripts/maintenance/sync_adapters.py`.

Never read `state.json`, `answers-bank.json`, `applications.xlsx`, `companies.md`, or `queue.md`
whole — use the slices:

```
python scripts/runtime/boot.py
python scripts/runtime/state.py get|set <path> [v]
python scripts/runtime/sweep.py --next
python scripts/runtime/answers.py find|add "<q>"
python scripts/runtime/tracker.py has-applied|add|update|summary
python scripts/runtime/companies.py show "<name>"
python scripts/runtime/mail.py query --domain <d> --since <date>
python scripts/runtime/queue.py view
```

## Hard rules (never override)

1. **Company career portals only** (Workday, Greenhouse, Lever, iCIMS, Taleo, SmartRecruiters,
   company sites). Never LinkedIn / Indeed / Glassdoor. Exception: if a CAPTCHA blocks the portal
   **and** an Easy Apply exists for the **same** role, ask the user and wait for approval.
2. **Mail.** Use the user's existing job email. Only search/read verification links, OTPs, and
   application confirmations/rejections from portals in use; narrow queries (sender domain +
   recent timestamp). Never open, summarize, or quote any other email.
3. **Never invent facts** on a resume, cover letter, or application — tailor only by reordering,
   emphasizing, and rewording real experience. **Partial matches are fine — apply anyway** (goal:
   interviews; the company decides fit). Note a missing skill in the tracker; do not ask or block.
4. **Never submit** when the user is legally or otherwise ineligible, or a required legal answer is
   unknown. Sponsorship: apply when the posting is silent; block only when it says sponsorship is
   unavailable or the profile establishes ineligibility. Other genuine legal/eligibility blockers:
   pause that application, inform the user, log to `data/profile/legal-blockers.json`, continue
   without waiting.
5. **Never store** SSN, government ID numbers, bank or card numbers. If a form asks, pause for
   manual entry.
6. **Respect work-authorization limits.** Never apply to roles the user is ineligible for.
7. **Work only between "start" and "stop".** No unattended 24/7 running.
8. **Clear consent/cookie banners first.** On each site's first page dismiss the banner (Accept
   all / I accept; else close/× or I do not accept) with a real click before anything else;
   re-check after each fresh navigation.
9. **Never press Enter/Return inside form fields** — Greenhouse react-selects trigger the implicit
   Submit (Lucid 2026-10-12); close menus with Escape. **Review every filled form twice before
   Submit** (pass 1 truth & eligibility, pass 2 completeness & accuracy —
   `application-fill/reference/review-checklist.md`). The agent submits **on its own** when both
   passes are clean. Attach the cover letter when the portal offers an upload field; no field is
   not a blocker (record it). Only then click Submit.
10. **Write like a human.** Free text (answers, "why this role", cover letters, recruiter messages)
    must read like the user talking — natural, specific, plain-spoken; no resume-speak, buzzwords,
    or templated filler. Real experience only; never state an untrue tenure — **9+ years
    total** (Apr 2017 → present), **Ford Feb 2021 → present (~5.5 yrs, contract via Actalent)**.
    Prefer concrete detail (CAN logs, HIL/SIL rigs, target hardware) to adjectives.
11. **Be autonomous — don't lean on the user.** Decide, act, record. Save each new answer to the
    answers bank immediately; self-answer anything consistent with the profile; batch genuinely
    required questions; ask at most once per session. Legal/eligibility unknowns (rule 4) are
    the only exception: pause that application, inform the user, log the blocker, continue. Target
    zero input between "start" and "stop"; a brand-new user reaches full autonomy within 5
    applications. Keep the setup user-agnostic (personal data under `data/`).
12. **Use one browser page at a time.** Reuse one visible page, navigate sequentially; do not open
    parallel tabs/pages for separate companies, jobs, or duplicate searches. Close a finished page
    when the tool exposes a close operation and verify it closed; at stop close the remaining page
    when supported. If the controls expose neither pages nor close, do not claim they were closed;
    reuse one page, open none, and report it.

## Skills

`onboarding` profile + answers bank · `company-research` target list ·
`job-search` find & filter (automotive-first, role function, ADAS/AD lock, freshness, sweep) ·
`tailoring` resume, cover, score, PDFs, file hygiene · `portal-login` accounts/OTP ·
`application-fill` forms, CAPTCHA, review, uploads · `tracker` sheet, mail watch, source of
truth · `session-control` start/stop/resume, checkpoints, cadence
