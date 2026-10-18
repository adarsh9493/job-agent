# Setup Guide

Complete setup instructions for the Job Agent — an autonomous job-application agent that runs inside OpenCode.

---

## Quick Start (TL;DR)

```bash
# 1. Clone the repo
git clone <your-fork-url>
cd job-agent

# 2. Install prerequisites (Windows PowerShell)
winget install --id Google.Chrome
node --version     # expect v20+
python --version   # expect 3.11+
git --version
python -m pip install --upgrade playwright
python -m playwright install chromium
python -m pip install openpyxl

# 3. Install OpenCode
npm install -g @opencode/opencode@latest

# 4. Configure MCP servers
opencode mcp add playwright -- npx -y @playwright/mcp@latest
opencode mcp add gmail -- python -m gmail_mcp
opencode mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem <absolute-path-to-job-agent>
opencode mcp add github -- npx -y @modelcontextprotocol/server-github
opencode mcp add context7 -- npx -y @context7/mcp-server
opencode mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking

# 5. Open in OpenCode and start
opencode .
# In OpenCode chat: say "start"
```

---

## Detailed Prerequisites

| Component | Minimum Version | Install Command | Verified |
|-----------|-----------------|-----------------|----------|
| **OS** | Windows 10/11 | — | ✅ |
| **OpenCode** | v2.0+ | `npm install -g @opencode/opencode@latest` | ✅ |
| **Node.js** | v20+ | `winget install OpenJS.NodeJS` | ✅ |
| **Python** | 3.11+ | `winget install Python.Python.3.12` | ✅ |
| **Git** | 2.40+ | `winget install Git.Git` | ✅ |
| **Google Chrome** | Stable | `winget install --id Google.Chrome` | ✅ |
| **Playwright (Python)** | 1.60+ | `python -m pip install --upgrade playwright` | ✅ |
| **Playwright Chromium** | — | `python -m playwright install chromium` | ✅ |
| **openpyxl** | 3.1+ | `python -m pip install openpyxl` | ✅ |

> **Note:** The agent automatically verifies and installs missing pieces on first run. See [PREREQUISITES.md](PREREQUISITES.md) for the full baseline table.

---

## MCP Server Configuration

The agent requires 6 MCP servers. Run these once:

```bash
# Playwright - visible browser for portal login & application submission
opencode mcp add playwright -- npx -y @playwright/mcp@latest

# Gmail - read verification links, OTPs, application confirmations
opencode mcp add gmail -- python -m gmail_mcp

# Filesystem - file access within workspace
opencode mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem "F:\Agentic WorkFlows\job-agent"

# GitHub - version control / repo operations
opencode mcp add github -- npx -y @modelcontextprotocol/server-github

# Context7 - up-to-date library/framework documentation
opencode mcp add context7 -- npx -y @context7/mcp-server

# Sequential Thinking - structured multi-step reasoning
opencode mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

Verify all are connected:
```bash
opencode mcp list
```

---

## First Run — Onboarding

1. **Open the project in OpenCode:**
   ```bash
   opencode .
   ```

2. **Say `start`** in the chat.

3. The agent will walk you through **onboarding** (skill: `onboarding`):
   - Personal details (name, email, phone, location, LinkedIn, portfolio)
   - Work authorization (citizenship, visa status, sponsorship needs)
   - Target roles, locations, salary floor
   - Master resume & cover letter → place in `data/master/`
   - Job email (Gmail MCP must be authenticated)
   - One shared portal password → stored in `data/vault/credentials.txt`
   - Target company list (skill: `company-research`)

4. **Approve the company list** and the **first application**.

5. The agent then runs the autonomous loop: **search → tailor → login → apply → log**.

---

## Directory Layout (What Gets Committed vs. Ignored)

```
job-agent/
├── .gitignore          # Ignores all personal/generated data
├── LICENSE             # MIT License
├── README.md           # Project overview
├── SETUP.md            # This file
├── PREREQUISITES.md    # Verified tool versions
├── AGENTS.md           # Core rules & control flow
├── opencode.jsonc      # Skill registration
├── skills/             # One folder per task (SKILL.md + scripts)
├── templates/          # resume.html, cover-letter.html (ATS-friendly)
└── data/               # ALL PERSONAL + GENERATED DATA (gitignored)
    ├── applications/   # Per-job folders (resume, cover letter, JD, screenshot)
    ├── master/         # Your master resume.docx + master_resume.pdf
    ├── profile/        # profile.json, companies.md, answers-bank.json, prior-applications.md
    ├── state/          # state.json, queue.md, cooling.md, candidates.json, burst.json
    ├── tracker/        # applications.xlsx
    └── vault/          # credentials.txt (portal password)
```

**Never commit the `data/` folder.** It contains your PII, credentials, and application history.

---

## Required User Files (One-Time Setup)

Place these in `data/master/` before first run:

| File | Purpose |
|------|---------|
| `master resume.docx` | Your master resume (source for tailoring) |
| `master_resume.pdf`  | PDF version (used for match scoring) |

The agent will create `data/profile/profile.json` and `data/profile/answers-bank.json` during onboarding.

---

## Gmail Authentication

The Gmail MCP server must be authenticated to your **existing job email**.

1. Run `opencode mcp list` → confirm `gmail` shows "connected"
2. If not, the server will prompt for OAuth on first use
3. Verify with a harmless search:
   ```
   Search my job email for "workday" from the last 7 days
   ```

The agent **only** reads:
- Verification links & OTPs from career portals
- Application confirmations/rejections from portals in use
- Narrow queries: sender domain + recent timestamp

---

## Running the Agent

| Command | Effect |
|---------|--------|
| `start` | Load state, begin search → tailor → login → apply → log loop |
| `stop` | Finish/abort current form, save state, halt (resumes on next `start`) |
| `I found a job` | Stop permanently, summarize stats, ask to keep setup |

**Session budget:** ~12 applications per session, then auto-stop with report.

**Pause between applications:** 30–90 seconds.

**Progress summary:** Every ~5 applications.

---

## How It Works (Architecture)

| Skill | Responsibility |
|-------|----------------|
| `onboarding` | Profile, eligibility, answers bank, target companies |
| `company-research` | Build/expand tiered target company list |
| `job-search` | Search career portals, filter freshness/eligibility, queue candidates |
| `tailoring` | Create ATS-friendly tailored resume + cover letter from master + JD |
| `portal-login` | Create/log in to career portal accounts, handle OTPs, reuse sessions |
| `application-fill` | Fill & submit forms, handle CAPTCHAs, 2-pass review before submit |
| `tracker` | Excel tracker, Gmail response monitoring, summary reports |
| `session-control` | Start/stop/resume, state persistence |

**Core rules (from AGENTS.md):**
- Company career portals only (Workday, Greenhouse, Lever, iCIMS, Taleo, SmartRecruiters, company sites)
- Automotive industry first filter (OEMs, Tier-1/2, AV on-road)
- Tester roles only (validation, verification, integration, HIL/SIL, test automation, reliability)
- Never invent facts on resume/cover letter/application
- Never submit if legal/eligibility answer unknown
- 2-pass review before every submit (truth/eligibility → completeness/accuracy)

---

## Customizing for Yourself

Since this agent is designed to be **shared** (user-agnostic):

1. **Fork this repo** to your GitHub account
2. **Clone your fork** locally
3. **Run setup** (above) — your personal data stays in `data/` (gitignored)
4. **Push only the code** — never `data/`

```bash
git add .gitignore LICENSE README.md SETUP.md PREREQUISITES.md AGENTS.md opencode.jsonc skills/ templates/
git commit -m "Initial commit: Job Agent"
git push origin main
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `opencode mcp list` shows disconnected | Re-run MCP add commands; check Node/Python paths |
| Playwright Chromium not found | `python -m playwright install chromium` |
| Gmail OAuth fails | Ensure Gmail API enabled in Google Cloud Console; check scopes |
| Portals block with CAPTCHA | Agent handles automatically; if stuck, it pauses for you |
| Resume PDF generation fails | Ensure `master_resume.pdf` exists in `data/master/` |
| Match score low | Agent retries tailoring up to 3 passes; check `skills/tailoring/scripts/match_score.py` |

---

## Contributing

This is a personal automation tool shared for learning. PRs welcome for:
- Bug fixes in skills/scripts
- New portal handlers (Workday, Greenhouse, etc.)
- Documentation improvements
- Cross-platform support (macOS/Linux)

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Support

- OpenCode docs: https://opencode.ai/v2/docs
- Issues: GitHub Issues on your fork
- The agent logs everything to the tracker and console — check there first