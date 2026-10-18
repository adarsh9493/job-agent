# Prerequisites

Everything the Job Agent needs, with the versions verified in this workspace and how a new user
gets each one. The agent checks and installs missing pieces automatically on the first run
(section D of the build prompt).

## Detected environment (baseline)

| Component                    | Version / value                                                        | Status     |
| ---------------------------- | ---------------------------------------------------------------------- | ---------- |
| OS                           | Windows 11 (`Microsoft Windows NT 10.0.26200.0`)                        | ✅         |
| OpenCode                     | `v2.0.24`                                                               | ✅         |
| Node.js                      | `v24.21.0`                                                              | ✅         |
| npm                          | `12.2.0`                                                                | ✅         |
| Python                       | `3.15.0`                                                                | ✅         |
| Git                          | `2.55.0.windows.5`                                                      | ✅         |
| Google Chrome (stable)       | `C:\Program Files\Google\Chrome\Application\chrome.exe`                 | ✅         |
| Playwright (Python)          | `1.63.0`                                                                | ✅         |
| Playwright Chromium          | Chrome for Testing `153.0.8010.12` (revision 1243)                      | ✅         |
| openpyxl (Excel library)     | `3.1.5`                                                                 | ✅         |
| HTML → PDF                   | Playwright Chromium headless `page.pdf()`                               | ✅         |

## MCP servers

All are configured and reported **connected** by `opencode mcp list`:

| Server                | Purpose                                                        |
| --------------------- | -------------------------------------------------------------- |
| `playwright`          | Visible Chrome browser for login and application submission    |
| `gmail`               | Read verification links, OTPs, application confirmations       |
| `filesystem`          | File access within the workspace                               |
| `github`              | Version control / repo operations                              |
| `context7`            | Up-to-date library/framework documentation                     |
| `sequential-thinking`  | Structured multi-step reasoning                                |

## Install / verify commands

Run these if setting up a fresh machine:

```powershell
# Core runtimes (install if missing)
node --version                 # expect v20+
python --version               # expect 3.11+
git --version
winget install --id Google.Chrome

# Playwright + browser
python -m pip install --upgrade playwright
python -m playwright install chromium

# Excel library
python -m pip install openpyxl

# Verify MCP servers
opencode mcp list
```

## Browser strategy (minimize CAPTCHAs)

- Use a **persistent browser profile** so cookies, sessions, and trusted-device signals survive
  between runs.
- Use **real Chrome** (`channel: "chrome"`) with the normal user agent, not a headless/automation
  fingerprint.
- Act with **slow, human-paced, sequential** interactions (one action at a time, natural delays).
- Keep **one account per portal** and reuse the session for other roles at the same company.

## Notes

- The visible browser is used only from portal login through final submission; all other work runs
  in the background.
- The Gmail MCP server must be authenticated to the user's existing job email. Verify with a
  harmless, narrow, job-related search.
