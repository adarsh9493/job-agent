# Setup

The supported entry point is the Copilot Agent workflow in VS Code. Do not run a separate Python
search/apply runner; the portal, legal-eligibility, review, and tracker steps require the agent's
interactive browser and tool context.

## Requirements

- Windows 10/11, Node.js 20+, Python 3.11+, Git, Chrome.
- Current VS Code with GitHub Copilot Chat and Agent mode.
- Python packages: `playwright`, `openpyxl`, `pypdf`; install the matching Playwright browser with
  `python -m playwright install chromium`.
- Playwright MCP for company-portal browsing. The workspace configuration is in `.vscode/mcp.json`.
- A user-configured Gmail/MCPEmails server available to Copilot for narrowly scoped OTPs and
  application responses. Keep authentication in the user environment; never put credentials in the
  repository.

Install the Python dependencies:

```powershell
python -m pip install playwright openpyxl pypdf
python -m playwright install chromium
```

Open the repository root in VS Code. Start the `playwright` server from the MCP Servers view or the
CodeLens in `.vscode/mcp.json`, then confirm its tools are available in Copilot Chat. Configure and
authenticate Gmail/MCPEmails in your VS Code user environment, then confirm the email tools are
available. Use those tools only within the restrictions in `AGENTS.md`.

In **Chat: Configure Skills**, confirm the workflow skills under `agent/skills/` are discovered.
If skills are disabled, enable the `chat.useAgentSkills` setting. Open the repository root as the
workspace so `AGENTS.md` and the workspace MCP configuration are in scope.

## Personal setup

Keep all personal files under the ignored `data/` directory:

- `data/master/` — master resume and, if available, master cover letter.
- `data/profile/` — profile, answers bank, approved companies, legal blockers, and optional local
  tailoring configurations. Personal tailoring content stays here, never in tracked scripts.
- `data/state/` — resumable queue and session state.
- `data/tracker/` — application workbook.
- `data/vault/` — portal credentials and persistent browser profiles.
- `data/applications/current/` and `data/applications/history/` — job-specific files.

Say **`start`** in Copilot Chat. Complete onboarding and approve the company list. Applications
follow the two-pass review and hard rules in `AGENTS.md`.

Say **`stop`** to safely save progress and resume later. Say **`I found a job`** to stop the workflow
permanently and review the session summary.

## Safety and support

- Never commit `data/`; it contains personal information and credentials.
- Use only company career portals. Search only for automotive ADAS/AD validation roles.
- The agent must not submit an application when a legal/eligibility answer is unknown.
- For the authoritative workflow and constraints, see `AGENTS.md` and the matching skill in
  `agent/skills/`. Avoid maintaining a second copy of policy in setup documentation.
