# Prerequisites

The agent requires an interactive harness; the Python scripts are helpers, not a standalone
search/apply runner. The documented and tested local baseline is Windows 10/11, Python 3.12, and
Node.js 20+. Generated adapters are provided for VS Code/Copilot, Claude Code, and OpenCode; each
harness must expose the capabilities in `agent/TOOLS.md` and keep its mail authentication private.

## Required software

| Component | Required baseline |
|---|---|
| OS | Windows 10/11 (other OSes require a local validation pass) |
| Python | 3.12 |
| Python packages | Exact pins in `requirements.txt` |
| Playwright browser | Chromium installed with `python -m playwright install chromium` |
| Node.js | 20+ and `npx` for the pinned `@playwright/mcp@0.0.84` server |
| Git | Required to clone and update the repository |
| Agent harness | Visible browser, shell, file-read, file-write, and mail capabilities |
| Mail access | User-configured mail tool for narrow portal OTP/response queries |

The documented baseline harness is VS Code with GitHub Copilot Chat, Agent mode, and Agent Skills.
Generated adapters also exist for Claude Code and OpenCode; configure and validate their mail and
browser tools in those harnesses before relying on them for applications.

Install from the repository root (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Required harness capabilities

- **Browser:** one visible page for a specific candidate's application attempt; no broad browser
  searches. Background discovery uses `fresh_scan.py` only.
- **Shell / files:** run repository helper scripts and read/write under the allowed paths.
- **Mail:** query only portal sender domains and recent dates for OTPs, confirmations, and rejections.
  No mail server or credentials are bundled with the repository.

Confirm the skills and browser/mail tools are available in the chosen harness. Then run:

```powershell
.\.venv\Scripts\python.exe scripts\maintenance\validate_all.py
```

This gate is offline and fixture-only; it cannot verify the harness's external authentication or a
successful live submission. See [SETUP.md](SETUP.md) for onboarding and [AGENTS.md](AGENTS.md) for
the authoritative safety rules.
