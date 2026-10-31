# Tool capability map

Canonical instructions (`AGENTS.md`, `agent/skills/`) name **capabilities**, never a harness or a
tool name. This file is the only place that maps a capability to a concrete tool. Adapters for each
harness are generated from `agent/mcp.json` by `scripts/maintenance/sync_adapters.py`.

## Capabilities

| Capability | What the agent may do | Never do |
|---|---|---|
| `browser` | One visible browser page: navigate, click, type, read the accessibility tree or a targeted locator, screenshot for confirmation, close the page | open parallel pages, read a whole-page dump when one locator answers the question |
| `shell` | Run the `scripts/` entry points and `git` in the project root | run ad-hoc scrapers, install packages mid-run, delete `data/` |
| `file-read` | Read `AGENTS.md`, `agent/`, and slices returned by scripts | read `data/state/state.json`, `answers-bank.json`, `applications.xlsx`, `queue.md`, or `logs/events.jsonl` in full |
| `file-write` | Write inside `data/` only, plus generated adapters via the sync script | edit `AGENTS.md`, `agent/`, or `scripts/` during a run |
| `mail` | Narrow queries: portal sender domain + `since`; read only OTPs, verification links, confirmations, rejections | open, summarise, or quote any other message |

## Harness mapping

Tool names are the harness's own; confirm them from the harness's tool list before first use.

| Capability | VS Code / Copilot | Claude Code | OpenCode | Other harnesses |
|---|---|---|---|---|
| `browser` | `playwright` MCP tools (`browser_navigate`, `browser_click`, `browser_type`, `browser_snapshot`, `browser_take_screenshot`, `browser_close`) | `mcp__playwright__*` equivalents | `playwright_*` equivalents | any Playwright MCP server |
| `shell` | terminal / `run_in_terminal` | `Bash` | `bash` | any command runner |
| `file-read` | `read_file` / `list_dir` | `Read` / `Glob` | `read` / `glob` | any file reader |
| `file-write` | `create_file` / `replace_string_in_file` | `Write` / `Edit` | `write` / `edit` | any file writer |
| `mail` | configured mail MCP server tools | same server via `mcp__<server>__*` | same server tools | any IMAP/API mail tool |

## Discovery paths (verified against each harness's docs, 2026-10-31)

| Harness | Skills | Instruction file | MCP config |
|---|---|---|---|
| VS Code / Copilot | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `.github/copilot-instructions.md` | `.vscode/mcp.json` (`servers`) or `.mcp.json` (`mcpServers`) |
| Claude Code | `.claude/skills/` | `CLAUDE.md` | `.mcp.json` (`mcpServers`) |
| OpenCode | `skills` array in config; defaults to `skill/` and `skills/` | `AGENTS.md` | `opencode.jsonc` (`mcp.servers`, `type: local`, array `command`) |

## Missing capability

If a harness has no `browser` or `mail` capability, the run cannot submit applications. Say so and
stop; do not substitute ad-hoc HTTP scraping for the portal.
