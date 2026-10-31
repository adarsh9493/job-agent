# Job Agent

An autonomous, reusable job-application agent that runs in any agent harness with a browser tool and
a mail tool (VS Code/Copilot, Claude Code, OpenCode, or another). It researches companies, finds
fresh job postings on company career portals, tailors your resume and cover letter to each role,
works through a visible browser, and tracks applications in an Excel workbook.

All personal data lives in `data/` and is **gitignored**, so this project can be published to
GitHub for other users without exposing anyone's information.

## Requirements

See [SETUP.md](SETUP.md) for installation and [PREREQUISITES.md](PREREQUISITES.md) for version
details. Install and authenticate the required tools before the first run.

## How to start

1. Open the repository root in your agent harness (VS Code with Copilot, Claude Code, OpenCode, ...).
2. Confirm the workflow skills are discovered and the `playwright` MCP server is connected. Adapters
   for each harness are generated; see [agent/TOOLS.md](agent/TOOLS.md) for the discovery paths.
3. Say **`start`**.
4. On the first run the agent walks you through **onboarding** (profile, work authorization,
   target roles, locations, answers bank) and builds your target company list.
5. Approve the company list. Applications follow the eligibility rules and mandatory two-pass review
   in [AGENTS.md](AGENTS.md).

## How to stop

- Say **`stop`** — the agent finishes or safely aborts the current form, saves state, and halts.
  The next `start` resumes exactly where it left off.
- Say **`I found a job`** — the agent stops permanently, summarizes stats, and asks whether to
  keep the setup for later.

## What you provide (one time)

- Your master resume and master cover letter → `data/master/`
- A Gmail/MCPEmails connection available to Copilot for narrowly scoped portal OTPs and application
  responses; configure it in your VS Code user environment and do not commit credentials.
- One shared portal password (or let the agent generate one) → stored in `data/vault/credentials.txt`

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
  runtime/          boot, state, answers, tracker, sweep, guard, presubmit, checkpoint, migration, archive
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

- The visible browser is used from portal login through final submission; everything else runs
  in the background.
- Use the `start` flow as the supported workflow; Python scripts are helper tools, not a
  standalone application runner.
- Search is strictly limited to eligible automotive ADAS/AD validation roles.
- Before changing workflow instructions or helpers, run
  `python scripts/maintenance/validate_all.py` (tests + adapters + budgets + dry run).
- The session-control skill uses `python scripts/runtime/checkpoint.py init` for first-run state,
  `validate` to check a saved checkpoint, and `set-mode running|stopped` to atomically record
  lifecycle transitions.
