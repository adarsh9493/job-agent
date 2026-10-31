# Changelog

All notable changes to this project. Maintenance sessions follow the phase plan in the
maintenance brief; every phase records its test state here.

## [Unreleased] - maintenance refactor (branch `refactor/harness-agnostic`)

### Phase 0 - Safety net (2026-10-31)

- Rollback point committed on branch `refactor/harness-agnostic` (`chore: checkpoint
  harness-agnostic refactor before maintenance pass`); `data/` excluded by `.gitignore`.
- Data backup: `data/backups/pre-refactor-2026-10-31.zip` (13.6 MB, 207 entries).
  Regenerable Chrome profile caches under `data/vault/` are excluded; `credentials.txt`,
  all JSON, tracker, applications and portal notes are included. Nothing deleted.
- Real Python 3.12.10 installed (`C:\Users\adars\AppData\Local\Programs\Python\Python312`),
  `.venv` created, Playwright Chromium installed.
- `requirements.txt` added with exact pins: `playwright==1.64.1`, `openpyxl==3.1.5`,
  `pypdf==6.21.4`.
- `@playwright/mcp` pinned from `@latest` to `0.0.84` in `.vscode/mcp.json`.

#### Test baseline (recorded before any refactor work)

| Run | Command | Result |
|---|---|---|
| 1 - as found | `python -m unittest discover -s tests -v` | **20 passed, 1 error** - `test_vscode_mcp_configures_playwright` raised `KeyError: 'playwright'` because `.vscode/mcp.json` was `{"servers": {}}` |
| 2 - after MCP config restored | same | **20 passed, 1 failure** - old test hardcodes `@playwright/mcp@latest`, conflicts with the required exact pin |

Expected: both defects are addressed in Phase 1 by the rewritten contract tests (adapters must
contain playwright, canonical files must not name a harness). Baseline canonical instruction
payload: **56,947 bytes** (~14.2k tokens) across `AGENTS.md` + 8 `SKILL.md` files.

### Phase 1 - Harness-agnostic layout (2026-10-31)

- Canonical layer: `AGENTS.md` + `agent/skills/**` (8 skills), `agent/TOOLS.md`,
  `agent/MODEL_POLICY.md`. Harness-specific copies are generated, never edited by hand.
- Python moved to `scripts/{runtime,scan,tailoring,maintenance}`; `skills/`, `docs/`, `pipeline/`
  and `setup/` removed. `data/tmp/playwright-mcp/` replaces the root `.playwright-mcp/`.
- `scripts/maintenance/sync_adapters.py` writes 21 adapter files for OpenCode, VS Code/Copilot
  and Claude Code; `--check` is a CI gate. `.vscode/mcp.json`, `.mcp.json` and `opencode.jsonc`
  keep the pinned `@playwright/mcp@0.0.84`.
- Tests rewritten for the new layout: **24/24 pass**; `validate_all.py` green. Session-start
  payload: **56,947 -> 17,526 bytes**.

### Phase 2 - Data slices and lean instructions (2026-10-31)

- New slice scripts so no large file is read whole: `state.py` (`get`/`set`/`keys`/`hot`, hot
  projection capped at 1,024 B), `answers.py` (`find`/`add`/`count`), `tracker.py`
  (`has-applied`/`add`/`update`/`summary`), `companies.py` (`build`/`show`/`list`/`stale`,
  md -> JSON index with a 180-day staleness flag), `mail.py` (`query`, narrow sender+date only),
  `queue.py` (`view`, `queue.md` capped at 2,048 B).
- `sweep.py --next` prints one JSON row and reads `companies.json`; `gen.py`/`build_all.py` now
  read `data/profile/tailoring-base.json` (10.7 KB shared content) plus one
  `<job folder>/tailoring.json` instead of the 209 KB `tailoring-content.json`. Splitter:
  `scripts/maintenance/split_tailoring.py` (35 jobs written, original file untouched).
- `AGENTS.md` reduced to **5,099 B** (12 hard rules preserved; control flow, filters and portal
  detail moved to skills). `application-fill`, `tailoring` and `job-search` split into lean
  `SKILL.md` + on-demand `reference/` files. Every file is inside its budget.
- Tests: **45/45 pass** (`tests/test_data_slices.py` added); `validate_all.py` green.
  Session-start payload **17,526 -> 6,211 bytes** (~1,553 tokens); worst phase 9,818 bytes.

### Phase 3 - Session runtime (2026-10-31)

- `scripts/runtime/boot.py`: one-screen JSON briefing (mode, current job/step, queue head, cursor,
  next approved company, interview blocks, legal blockers, onboarding flags, lock state) capped at
  2,048 B - currently **291 B**. Missing files are reported as `mode: missing`, never fatal, so a
  fresh clone can boot.
- `data/state/run.lock`: single-run lock written by `checkpoint.py set-mode running`, released by
  `set-mode stopped` / `checkpoint.py release`. A dead or >12 h lock is replaced automatically; a
  live foreign lock refuses the start.
- `checkpoint.py save --file <partial.json>` merges a partial checkpoint atomically and validates
  it; repeating the same mode or payload is a no-op (no duplicate timestamps, no duplicate events).
- `data/state/events.jsonl`: append-only event log (`events.py append|tail|count`) with key-based
  dedupe over the recent window. `session-control` now boots from the briefing, checks the lock,
  and uses `checkpoint.py save` after each application.
- Tests: **55/55 pass** (`tests/test_session_runtime.py` added); `validate_all.py` green.
  Session-start payload 6,211 -> **6,502 bytes** (boot briefing included); worst phase 10,109 bytes.

### Phase 4 - Hard-rule gates and credential vault (2026-10-31)

- `scripts/runtime/guard.py` blocks a role unless the session is running with its lock held, the
  company is approved, the title is not managerial, the tracker confirms no duplicate, no matching
  legal blocker exists, and the job folder is present. Duplicate-check failures fail closed.
- `scripts/runtime/presubmit.py` reruns the guard, requires a 0-100 match score and a clean two-pass
  `review.json`, verifies the resume and any uploaded cover-letter PDF, and logs a presubmit event.
  Submit is permitted only when it prints `{"ok":true,"submit":true,...}`.
- `scripts/runtime/creds.py` provides masked `list`/`get`, fill-time `get --reveal`, stdin-only
  `set`, and `new` (generates and stores without printing). Vault writes are atomic; secrets are
  never echoed by `set` or `new`.
- `application-fill` now requires both gates and documented review evidence; `portal-login` uses
  the credential helper. Adapters regenerated. Tests: **74/74 pass** (`test_guard_presubmit.py`);
  `validate_all.py` green. Session-start context remains **6,502 B**; canonical skill text is
  28,548 -> **29,607 B**, with no file over budget.

### Phase 5 - Maintain mode and schema migration (2026-10-31)

- Added `schema_version: 1` to initialized checkpoints and made validation reject missing or
  unsupported schemas. `scripts/runtime/migrate_state.py` plans by default; `--apply` preserves all
  fields, creates a byte-exact sibling backup, and atomically adds the schema marker. It is
  idempotent and tested only on temporary fixtures; personal `data/` was not migrated.
- `session-control` applies migration before validating an existing checkpoint. The fixture-only
  `dry_run.py` exercises the migration and keeps Submit stubbed.
- Added `scripts/maintenance/MAINTAIN.md` with branch/edit/validate/dry-run protocol. README explains
  switching harnesses/models and lists the final tree: `agent/` canonical instructions,
  `scripts/{runtime,scan,tailoring,maintenance}`, `templates/`, `tests/`, and gitignored `data/`.
- Tests: **78/78 pass**; adapter check and `validate_all.py` green. Context before -> after:
  session start **6,502 -> 6,502 B**, skill text **29,607 -> 29,701 B**, worst phase **10,109 B**;
  all budgets remain clear.

### Post-run hardening (2026-10-31)

- The first RUN exposed that helper-process PIDs made the run lock appear stale as soon as each CLI
  exited. Replaced it with a cross-process serialized, 12-hour lease refreshed by checkpoints; added
  a two-process acquisition test. Stop marks the lease released instead of deleting the lock file.
- Recorded the user's hard rule: background discovery uses `fresh_scan.py` only; open the visible
  browser only for a specific candidate as an application attempt. Unsupported boards are recorded
  as unsearched, not browsed or searched through another channel.
- Removed `creds.py --reveal`; reads are always masked. The portal-login instructions now require
  manual entry if safe password transfer is unavailable.
- Tests: **82/82 pass**; adapters and validation gates green. No live application was submitted in
  the first run; the only tracker additions were reviewed skips, and personal `data/` is unchanged
  by this maintenance phase. Context before -> after: session start **6,502 -> 6,486 B**, skill
  text **29,701 -> 29,864 B**, worst phase **10,109 -> 10,093 B**; no budget is exceeded.

### Cross-volume PDF publishing fix (2026-10-31)

- `build_all.py` now publishes verified PDFs through `file_ops.publish_file`: copy into a temporary
  file on the destination volume, atomically replace the final file, then remove the source. This
  avoids Windows cross-drive `os.replace` failures and preserves an existing destination if publish
  fails. The first real Zoox attempt used direct rendering as a workaround; no application data was
  changed by this maintenance fix.
- Added a source/destination-volume test, including failure preservation. Tests: **83/83 pass**;
  `validate_all.py` green. Context is unchanged by the PDF helper: session start **6,873 B**, worst
  phase **10,480 B**, all budgets clear.

### Fresh-PC setup documentation and tracker bootstrap (2026-10-31)

- Reconciled README, SETUP, and PREREQUISITES: documented the Windows/Python 3.12/Node 20 baseline,
  pinned dependencies, harness capability checks, user-configured mail, scanner-only discovery,
  browser/CAPTCHA policy, and the fact that `data/` is not part of a clone.
- Added non-overwriting `tracker.py init` to create the required Applications/Legend workbook,
  headers, status colors, and dropdown; session start now initializes it before reading the summary.
- Tests: **84/84 pass**; all `validate_all.py` gates green. Context before -> after: session start
  **6,873 -> 6,878 B**, skill text **29,864 -> 30,059 B**, worst phase **10,480 -> 10,557 B**;
  `AGENTS.md` is **5,108 B** (budget 5,120 B), with no file over budget.
