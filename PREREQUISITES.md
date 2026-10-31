# Prerequisites

The supported workflow runs in GitHub Copilot Chat in VS Code. It needs the interactive browser and
Gmail tools; there is no standalone Python search/apply runner and no first-run dependency installer.

## Required software

| Component | Minimum |
|---|---|
| Windows | 10/11 |
| VS Code | Current stable release |
| GitHub Copilot Chat | Current version with Agent mode and Agent Skills enabled |
| Node.js | 20+ |
| Python | 3.11+ |
| Git | 2.40+ |
| Google Chrome | Stable |
| Playwright Python package | 1.60+ |
| `openpyxl` | 3.1+ |
| `pypdf` | Current version |

Install missing Python packages and the Playwright browser:

```powershell
python -m pip install playwright openpyxl pypdf
python -m playwright install chromium
```

## Required agent tools

- **Playwright MCP** — visible browser access for company career portals, configured in
  `.vscode/mcp.json`.
- **Gmail/MCPEmails** — user-configured email access for narrowly scoped OTPs and application
  responses.

Confirm the skills are listed in **Chat: Configure Skills** and the MCP tools are available in
Copilot Chat before starting. GitHub, Context7, filesystem, and sequential-thinking servers are
optional and are not required for the application flow.

See [SETUP.md](SETUP.md) for first-run steps and [AGENTS.md](AGENTS.md) for the authoritative rules.
