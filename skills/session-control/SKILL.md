---
name: Session Control
description: Handle start, stop, and resume - load and save state in data/state/state.json so work resumes exactly where it left off.
---

# Session Control

**Goal:** implement the run lifecycle: start, stop, resume.

## Inputs / files

- `data/state/state.json` — company, job, step, queue, session stats.

## Steps

- **start** — load `state.json` and the tracker, then loop: search → tailor → login → apply → log. If
  a saved job/step exists, resume exactly there.
- **stop** — finish or safely abort the current form, save state (company, job, step, queue), halt.
- **I found a job** — stop permanently, summarize stats, ask whether to keep the setup for later.

## Rules

- Work **only** between start and stop; no unattended 24/7 running (`AGENTS.md` rule 7).
- **30–90 s pause** between applications; brief progress summary every ~5 applications.
- At every stop / session end remind: *"No daily application cap is set. Want to set one?"*

## Outputs

- `data/state/state.json` kept current.
