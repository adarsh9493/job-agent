# Job Agent

An autonomous, reusable job-application agent designed exclusively for GitHub Copilot in VS Code. It researches
companies, finds fresh job postings on company career portals, tailors your resume and cover
letter to each role, works through a visible browser, and tracks applications in an Excel workbook.

All personal data lives in `data/` and is **gitignored**, so this project can be published to
GitHub for other users without exposing anyone's information.

## Requirements

See [SETUP.md](SETUP.md) for installation and [PREREQUISITES.md](PREREQUISITES.md) for version
details. Install and authenticate the required tools before the first run.

## How to start

1. Open the repository root in VS Code and start a Copilot Agent session.
2. Confirm the project skills appear in **Chat: Configure Skills** and the Playwright MCP server is
   available in the MCP Servers view. This repository is configured for VS Code; it has no
   OpenCode-specific setup.
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
AGENTS.md         Core rules and control flow
README.md         This file
PREREQUISITES.md  Installed tools and versions
.github/skills/   Copilot-discoverable workflow skills
.vscode/mcp.json  Workspace Playwright MCP configuration
skills/           Python helpers only; no duplicate SKILL.md files
templates/        resume.html, cover-letter.html (ATS-friendly)
data/             All personal + generated data (gitignored)
```

The two `skills` locations have different jobs: `.github/skills/<name>/SKILL.md` contains
Copilot-discoverable workflow instructions; `skills/` contains executable Python helpers, grouped
by workflow area. Keep workflow guidance in the former and implementation in the latter.

## Notes

- The visible browser is used from portal login through final submission; everything else runs
  in the background.
- Use the Copilot Agent `start` flow as the supported workflow; Python scripts are helper tools,
  not a standalone application runner.
- Search is strictly limited to eligible automotive ADAS/AD validation roles.
- Before changing workflow instructions or helpers, run
  `python -m unittest discover -s tests -v` to verify the workflow contract.
- The session-control skill uses `python skills/session_checkpoint.py init` for first-run state,
  `validate` to check a saved checkpoint, and `set-mode running|stopped` to atomically record
  lifecycle transitions.
