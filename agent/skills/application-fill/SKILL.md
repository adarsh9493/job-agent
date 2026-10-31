---
name: application-fill
description: Use when completing job applications in a visible browser. Submit autonomously after two-pass review, attach required and supported documents, reuse the answers bank, handle CAPTCHAs, and never guess on legal eligibility.
---

# Application Fill

**Goal:** complete and submit one application accurately, or hand it off safely.

## Inputs

- Job folder PDFs (resume + cover letter).
- `data/profile/profile.json`, `data/profile/answers-bank.json`.
- `data/vault/credentials.txt`.

## Steps

1. Fill from `profile.json` and the answers bank (`python scripts/runtime/answers.py find "<q>"`).
   Always attach the resume. Attach the cover letter when the portal provides or requires an
   upload field; a portal with no cover-letter field is not by itself a reason to stop or withhold
   submission. Confirm the visible attachment filenames.
2. Use one browser page at a time (`AGENTS.md` rule 12). Reuse the authenticated portal session
   while it remains valid; navigate the same page rather than opening a new tab for another
   company or job. Save each newly learned non-legal answer with
   `python scripts/runtime/answers.py add "<q>" "<a>"` immediately.
3. Never guess a required field. Legal/eligibility unknowns: log to
   `data/profile/legal-blockers.json`, stop this application, and continue to the next one
   (`AGENTS.md` rule 4) — do not wait for a response.
4. CAPTCHA → `reference/captcha.md`.
5. Portal quirks (Greenhouse, Ashby, embedded forms) → `reference/portals.md`. Workday →
   `reference/workday.md`.
6. Document checks before upload → `reference/documents.md`.
7. **Two-pass review → `reference/review-checklist.md`.** Submit autonomously only when both
   passes are clean; do not seek per-application approval.
8. Save the confirmation screenshot in the job folder, run
   `python scripts/runtime/archive.py` once, and update the tracker
   (`python scripts/runtime/tracker.py add ...`) before moving to the next role. Close the finished
   page when supported; otherwise reuse it and report at stop if it cannot be closed.

## Never

- Submit with an unknown legal/eligibility answer (`AGENTS.md` rule 4).
- Store SSN, government ID numbers, bank or card numbers; pause for manual entry (rule 5).
- Fall back to LinkedIn / Indeed / Glassdoor without the approved exception (rule 1).
- Press Enter/Return inside a form field (rule 9).
- Claim a page was closed when the browser tool exposes no close operation (rule 12).

## Outputs

- Submitted application and confirmation screenshot; applied folder archived to `history/`; answers
  bank updated; tracker row written.
