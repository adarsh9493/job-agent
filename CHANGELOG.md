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
