# Fresh-PC setup

The workflow runs inside an agent harness; it is not a standalone job-search/apply program. The
validated local baseline is Windows 10/11 with Python 3.12, Node.js 20+, Git, and a harness that
provides the required browser, shell, file-read, file-write, and mail capabilities. The repository
contains adapters for VS Code/Copilot, Claude Code, and OpenCode, but each harness's tools and mail
authentication must be checked on the new machine. See [agent/TOOLS.md](agent/TOOLS.md).

## Install runtime dependencies

From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
node --version
```

`requirements.txt` contains the pinned Python dependencies. Node.js 20+ supplies `npx`, used by the
pinned `@playwright/mcp@0.0.84` browser server. A system Chrome installation is not used to render
PDFs; Playwright's installed Chromium is used. If using another OS, adapt the venv commands and run
all validation gates before a RUN session.

## Connect the harness

- Open the repository root in the selected harness and confirm it discovers `AGENTS.md` and the
  generated skill adapters. For the documented baseline, install current VS Code with GitHub
  Copilot Chat, enable Agent mode and Agent Skills, and open the repo root as the workspace. The
  workspace browser server is configured in `.vscode/mcp.json`.
- Confirm the harness has a **visible, single-page browser** and the shell/file capabilities listed
  in `agent/TOOLS.md`. Background job discovery is `fresh_scan.py` only; do not use the browser for
  broad searches. If a company has no scanner adapter, it remains unsearched for that run.
- Configure a user-level mail tool for narrow portal OTP/confirmation/rejection queries. Mail
  credentials and server settings are not included here. Validate the connection in the harness;
  without working mail access, OTP/response checks cannot be automated. Never broaden mail queries.
- Run the offline gates before first use:

  ```powershell
  .\.venv\Scripts\python.exe scripts\maintenance\validate_all.py
  ```

  This validates code, adapters, context budgets, and a fixture-only dry run. It does **not** test
  browser/mail authentication or prove a live application can be submitted.

## Add your own personal data

`data/` is gitignored and intentionally absent from a fresh clone. Do not copy another person's
profile or credentials. Add your own:

- `data/master/` — master resume and, if available, master cover letter. Onboarding asks for these;
  the resume is required to proceed.
- Profile details — work authorization/sponsorship, locations, salary floor, legal name, contact,
  education, experience, and approved target companies. The `start` onboarding flow stores them in
  `data/profile/` and asks you to confirm the summary/company list.
- `data/tracker/applications.xlsx` — created safely on first start by
  `python scripts/runtime/tracker.py init`; it will not overwrite an existing workbook.
- `data/vault/` — optional portal credentials and browser profiles. The credential helper always
  masks reads; if the harness cannot enter a password without exposing it, enter it manually.

The first `start` initializes missing session state and performs onboarding when needed. Job files,
tracker, profile, credentials, and run state remain local. Say `stop` to checkpoint; later `start`
resumes. Follow the hard rules in [AGENTS.md](AGENTS.md), especially the two-pass review and manual
handling of visible CAPTCHA challenges.

## Browser and run policy

Use background scanning only to find specific candidates. Open the visible browser for that
candidate's application attempt, inspect the official full JD, then continue to fill only if the role
is eligible. Cookie banners must be dismissed before interacting. Never bypass CAPTCHA; if it cannot
be solved, record `Manual Application Submission Needed` and continue to the next role. See
[`scripts/maintenance/MAINTAIN.md`](scripts/maintenance/MAINTAIN.md) for changing the agent safely.
