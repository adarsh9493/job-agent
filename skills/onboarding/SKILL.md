---
name: Onboarding
description: Ask the user profile and eligibility questions in small batches, read the master resume, and store everything in data/profile. Use on first run or when profile gaps appear.
---

# Onboarding

**Goal:** collect once everything needed to search, filter, and fill applications. Ask follow-ups
only for gaps. Never re-ask something already stored in `data/profile/`.

## Inputs

- `data/master/` — master resume and master cover letter (ask the user to add them if missing).
- `data/profile/profile.json`, `data/profile/answers-bank.json` — existing answers, if any.
- Hard rules in `AGENTS.md` (work authorization, no sensitive data).

## Steps

1. **Read `data/master/` first.** If empty, ask the user to drop in their master resume (and cover
   letter) before continuing. Extract name, contact, education, employment history, skills.
2. Ask in **small batches**, waiting for answers between batches:
   - **Work authorization** — US citizen / green card / visa type, expiry, sponsorship now or later.
     Drives eligibility filters: drop "no sponsorship", "US citizens only", and clearance roles when
     ineligible.
   - **Targets** — titles, seniority, industries. Stay in the user's domain or pivot. Their stated
     background: automotive validation / embedded, infotainment, HIL/SIL, data engineering. Ask about
     stretch domains (ADAS, autonomous vehicles, EV, others).
   - **Logistics** — locations, remote / hybrid / onsite, relocation, salary floor, notice period,
     start date, exclusions.
   - **Application basics** — legal name, phone, job email, full address, LinkedIn/portfolio,
     education, employment details, references, "how did you hear" answer.
   - **EEO / demographics** — including "decline to answer" as an option.
   - **Cover letter** — tone and any words/claims to avoid.
3. Write answers to `data/profile/profile.json` (structured) and `data/profile/answers-bank.json`
   (question → answer map used to fill portal forms).
4. **Summarize the whole profile back for confirmation** before continuing. Fix anything wrong.

## Rules

- Never store SSN, government ID numbers, bank or card numbers (`AGENTS.md` rule 5).
- Keep batches small; one topic at a time so answers stay clean.
- If the master resume is missing, do not invent one — ask.

## Outputs

- `data/profile/profile.json` and `data/profile/answers-bank.json`, populated and confirmed.
