# Job Agent

An autonomous, reusable job-application agent that runs inside OpenCode. It researches target
companies, finds fresh job postings on company career portals, tailors your resume and cover
letter to each role, logs in and applies in a visible browser, and tracks everything in an Excel
tracker.

All personal data lives in `data/` and is **gitignored**, so this project can be published to
GitHub for other users without exposing anyone's information.

## Requirements

See [PREREQUISITES.md](PREREQUISITES.md). Everything is installed/verified automatically on the
first run.

## How to start

1. Open this folder in OpenCode.
2. Say **`start`**.
3. On the first run the agent walks you through **onboarding** (profile, work authorization,
   target roles, locations, answers bank) and builds your target company list.
4. Approve the company list and the **first** application. The agent then runs the
   search → tailor → login → apply → log loop.

## How to stop

- Say **`stop`** — the agent finishes or safely aborts the current form, saves state, and halts.
  The next `start` resumes exactly where it left off.
- Say **`I found a job`** — the agent stops permanently, summarizes stats, and asks whether to
  keep the setup for later.

## What you provide (one time)

- Your master resume and master cover letter → `data/master/`
- Your job email (already connected via the Gmail MCP server)
- One shared portal password (or let the agent generate one) → stored in `data/vault/credentials.txt`

## Layout

```
AGENTS.md         Core rules and control flow
README.md         This file
PREREQUISITES.md  Installed tools and versions
opencode.jsonc    Registers skills/ with OpenCode
skills/           One folder per task (SKILL.md)
templates/        resume.html, cover-letter.html (ATS-friendly)
data/             All personal + generated data (gitignored)
```

## Notes

- The visible browser is used from portal login through final submission; everything else runs
  in the background.
- No daily application cap is set by default. The agent reminds you to set one at every stop.
