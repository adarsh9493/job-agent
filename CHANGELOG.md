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
