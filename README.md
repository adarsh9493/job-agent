# Job Agent

An autonomous job-application workflow designed for any harness that provides the required browser,
shell, file, and mail capabilities. Generated adapters exist for VS Code/Copilot, Claude Code, and
OpenCode; see [agent/TOOLS.md](agent/TOOLS.md). This repository documents and validates a Windows
setup, but every new harness still needs its capabilities checked before a run.

All personal data lives in `data/` and is **gitignored**. A clone does not include a profile, resume,
tracker, portal credentials, or browser profile; each user completes onboarding on their own copy.

## Operating constraints

- Background job discovery uses `scripts/scan/fresh_scan.py` only. The visible browser is opened only
  for a specific scanner candidate as the start of an application attempt, not for broad searching.
  Companies without a scanner adapter remain unsearched for that run.
- A visible CAPTCHA must be solved by the user; the agent never bypasses it. If unresolved, the
  application is recorded as manual-needed.
- `validate_all.py` is offline validation. It does not test the user's browser/mail authentication or
  prove that a live application can be submitted.

## Requirements

See [SETUP.md](SETUP.md) for installation and [PREREQUISITES.md](PREREQUISITES.md) for version
details. Install and authenticate the required tools before the first run.

## How to start

1. Open the repository root in your agent harness (VS Code with Copilot, Claude Code, OpenCode, ...).
2. Confirm skills are discovered and the harness provides `browser`, `shell`, `file-read`,
   `file-write`, and `mail` capabilities. Harness setup details are in [SETUP.md](SETUP.md) and
   [agent/TOOLS.md](agent/TOOLS.md).
3. Say **`start`**.
4. On the first run the agent walks you through **onboarding** (profile, work authorization,
   target roles, locations, answers bank) and builds your target company list.
5. Approve the company list. Applications follow the eligibility rules and mandatory two-pass review
   in [AGENTS.md](AGENTS.md).

## How to stop

- Say **`stop`** — the agent finishes or safely aborts the current form, saves state, and halts.
  The next `start` resumes from the verified checkpoint.
- Say **`I found a job`** — the agent stops permanently, summarizes stats, and asks whether to
  keep the setup for later.

## What you provide (one time)

- Your master resume and master cover letter → `data/master/`
- A user-configured mail tool for narrowly scoped portal OTPs and application responses. Configure
  it in your harness's private environment; never commit mail credentials.
- Portal credentials, if needed, stay under `data/vault/`; reads are always masked. If a password
  cannot be entered safely through the chosen harness, enter it manually.
- Work authorization, locations, salary, and target-company preferences during first-run onboarding.
- The tracker workbook is created on first start and stays local under `data/tracker/`.

## Layout

```
AGENTS.md         Core rules (the only policy file)
CHANGELOG.md      Test state after every maintenance phase
agent/            Canonical instructions - the only place to edit
  skills/           the 8 workflow skills (+ reference/ files loaded on demand)
  TOOLS.md          capability -> harness tool-name map
  MODEL_POLICY.md   light vs heavy model tiers
  mcp.json          canonical MCP servers
scripts/          Executable helpers (no policy text)
  runtime/          boot, state, answers, tracker, queue, sweep, events, creds, mail, guard,
                    presubmit, checkpoint, migration, archive
  scan/             fresh_scan
  tailoring/        gen, build_all, render_pdf, verify_pdf, match_score
  maintenance/      MAINTAIN.md, sync_adapters, context_report, validate_all, dry_run
templates/        resume.html, cover-letter.html (ATS-friendly)
tests/            contract tests + fixtures (never real data)
data/             All personal + generated data (gitignored)
```

Generated adapters - never hand-edited, rebuilt by `scripts/maintenance/sync_adapters.py`:
`.github/skills/`, `.github/copilot-instructions.md`, `.claude/skills/`, `CLAUDE.md`,
`.vscode/mcp.json`, `.mcp.json`, `opencode.jsonc`.

Edit `agent/` and run `python scripts/maintenance/sync_adapters.py`; the tests fail if an adapter
drifts from canonical.

## Switch harness or model

- **Harness:** keep workflow instructions in `agent/skills/` and edit the capability-to-tool map in
  `agent/TOOLS.md` for the new harness. Update its generated adapter through
  `scripts/maintenance/sync_adapters.py`; do not edit generated copies by hand. Verify the harness
  provides the required browser, shell, file-read, file-write, and mail capabilities before a run.
- **Model:** choose the cheapest model that can do the current task and follow
  `agent/MODEL_POLICY.md` for light vs. heavy work. Checkpoints make mid-run model changes safe;
  models may not override hard rules or guess unknown eligibility answers.
- After a switch, run `python scripts/maintenance/validate_all.py`. See
  [`scripts/maintenance/MAINTAIN.md`](scripts/maintenance/MAINTAIN.md) before changing the agent.

## Notes

- Follow the browser-only-for-a-specific-application and scanner-only discovery rules in `AGENTS.md`.
- Portal mail authentication is external to this repository; without it, OTP and response checks
  cannot be automated.
- Use the `start` flow as the supported workflow; Python scripts are helper tools, not a
  standalone application runner.
- Search is strictly limited to eligible automotive ADAS/AD validation roles.
- Before changing workflow instructions or helpers, run
  `python scripts/maintenance/validate_all.py` (tests + adapters + budgets + dry run).
- The session-control skill uses `python scripts/runtime/checkpoint.py init` for first-run state,
  `validate` to check a saved checkpoint, and `set-mode running|stopped` to atomically record
  lifecycle transitions.
