---
# GENERATED - do not edit. Source: agent/skills/session-control/SKILL.md
name: session-control
description: Use when the user says start, stop, resume, or I found a job. Control the supported job-application workflow using persisted state.
---

# Session Control

Follow the lifecycle and hard rules in `AGENTS.md`; this skill defines no parallel runner or state
machine.

## Start

1. Run `python scripts/runtime/boot.py` and read the briefing. If `lock` is `held:*`, another run
   is active - stop and report it. If `data/state/state.json` is missing, run
   `python scripts/runtime/checkpoint.py init`; otherwise run
   `python scripts/runtime/migrate_state.py --apply` (idempotent; creates a sibling backup), then
   `python scripts/runtime/checkpoint.py validate`; do not proceed with malformed state.
2. Read the tracker summary (`python scripts/runtime/tracker.py summary`), pending legal blockers,
   approved company list, application-folder evidence, and rotating sweep cursor. Complete
   onboarding when needed. Reconcile conflicts and initialize both cursor fields from the approved
   list before setting a non-empty cursor. Then run
   `python scripts/runtime/checkpoint.py set-mode running`.
3. Before browser work, keep to one visible browser page; reuse it sequentially and close any
   finished page when the available browser controls support closure (`AGENTS.md` rule 12).
4. Check for new application responses using narrow mail queries as described in `AGENTS.md`.
5. Re-grade current job folders against the strict ADAS/AD validation rule and safely remove only
   out-of-scope generated drafts.
6. Run the company round-robin in `companies.md` order. Use `fresh_scan.py` as the only automated
   posting scanner; search official career portals directly for unsupported boards or scan failures.
   Verify company and full-JD role scope, freshness, eligibility, and duplicates before tailoring,
   reviewing, and submitting when safe. Update the tracker and archive confirmed folders.
7. Continue to the next role after a legal/eligibility blocker or portal failure; save the blocker or
   incomplete status and resume at the next company.
8. After each application or safely skipped role, persist its tracker status, queue, cursor, current
   company/job/step, and session counters with one atomic
   `python scripts/runtime/checkpoint.py save --file <partial.json>` before proceeding. Run
   `python scripts/runtime/checkpoint.py validate --expected-mode running`; never begin another
   application until the checkpoint is valid and readable.

## Stop

Finish or safely abort the active form; persist its exact company/job/form step and remaining queue;
archive confirmed folders; update the tracker summary and session counters. Then run
`python scripts/runtime/checkpoint.py set-mode stopped` followed by
`python scripts/runtime/checkpoint.py validate --expected-mode stopped`. The helper atomically
updates `mode`, `last_stop_at`, and `last_updated`, releases the run lock, and appends a mode event
to `data/state/events.jsonl` (recent history: `python scripts/runtime/events.py tail --limit 5`).
Confirm the cursor and queue in its output. Do
not begin another application after stop is requested. Close the remaining browser page when the
available controls support it; otherwise leave only the reused page and report that it could not be
closed. A later `start` resumes from that verified checkpoint.

## Job found

When the user says **“I found a job”**, stop permanently, summarize application statistics, and ask
whether to keep the setup.

## Cadence

- Apply sequentially, never in parallel. No artificial delay between applications; respect portal
  rate limits and wait when the site requires it.
- Give a brief progress summary about every 5 applications (applied, skipped, blocked, queued).
- Keep one browser page for the whole run and navigate it between companies and jobs
  (`AGENTS.md` rule 12).
