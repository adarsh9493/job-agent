#!/usr/bin/env python
"""Generate every harness adapter from the canonical `agent/` sources.

Adapters are **copies**, never symlinks (Windows). Each generated file starts with a
"GENERATED - do not edit" marker. Canonical files are `AGENTS.md`, `agent/skills/`,
`agent/mcp.json`; everything this script writes is disposable.

    python scripts/maintenance/sync_adapters.py            # write adapters
    python scripts/maintenance/sync_adapters.py --check    # verify, exit 1 on drift
    python scripts/maintenance/sync_adapters.py --verbose  # list every file
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON_SKILLS = ROOT / "agent" / "skills"
CANON_MCP = ROOT / "agent" / "mcp.json"

SKILL_TARGETS = (".github/skills", ".claude/skills")
MARKER = "GENERATED - do not edit"

CLAUDE_MD = f"""<!-- {MARKER}. Source: AGENTS.md + agent/skills/ (scripts/maintenance/sync_adapters.py) -->
@AGENTS.md

Workflow skills: `.claude/skills/`. Tool names for each capability: `agent/TOOLS.md`.
Model tiers: `agent/MODEL_POLICY.md`.
"""

COPILOT_MD = f"""<!-- {MARKER}. Source: AGENTS.md + agent/skills/ (scripts/maintenance/sync_adapters.py) -->
`AGENTS.md` is the authoritative rule set. Read it first, then the matching skill in
`.github/skills/`. Tool names for each capability: `agent/TOOLS.md`. Model tiers:
`agent/MODEL_POLICY.md`. Never restate a rule here - change the canonical file instead.
"""


def canon_skills() -> dict[str, list[Path]]:
    """skill name -> every file in that skill folder, relative to the skill folder."""
    found: dict[str, list[Path]] = {}
    for folder in sorted(p for p in CANON_SKILLS.iterdir() if p.is_dir()):
        found[folder.name] = sorted(
            (f.relative_to(folder) for f in folder.rglob("*") if f.is_file()),
            key=lambda p: p.as_posix(),
        )
    return found


def marked(text: str, source: str) -> str:
    """Add the generated marker without breaking YAML frontmatter."""
    line = f"# {MARKER}. Source: {source}"
    if text.startswith("---"):
        head, _, tail = text.partition("\n")
        return f"{head}\n{line}\n{tail}"
    return f"<!-- {MARKER}. Source: {source} -->\n\n{text}"


def mcp_servers() -> dict:
    return json.loads(CANON_MCP.read_text(encoding="utf-8"))["servers"]


def render() -> dict[Path, str]:
    """Every adapter path -> exact expected text."""
    out: dict[Path, str] = {}
    skills = canon_skills()

    for target in SKILL_TARGETS:
        base = ROOT / target
        for name, files in skills.items():
            for rel in files:
                src = CANON_SKILLS / name / rel
                text = src.read_text(encoding="utf-8")
                out[base / name / rel] = marked(text, f"agent/skills/{name}/{rel.as_posix()}")

    servers = mcp_servers()

    vscode = {n: {"type": "stdio", "command": s["command"], "args": s["args"]}
              for n, s in servers.items()}
    out[ROOT / ".vscode" / "mcp.json"] = json.dumps({"servers": vscode}, indent=2) + "\n"

    portable = {n: {"command": s["command"], "args": s["args"]} for n, s in servers.items()}
    out[ROOT / ".mcp.json"] = json.dumps({"mcpServers": portable}, indent=2) + "\n"

    local = {n: {"type": "local", "command": [s["command"], *s["args"]]}
             for n, s in servers.items()}
    out[ROOT / "opencode.jsonc"] = (
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "$comment": f"{MARKER}. Source: agent/mcp.json + agent/skills/",
                "skills": ["./agent/skills"],
                "mcp": {"servers": local},
            },
            indent=2,
        )
        + "\n"
    )

    out[ROOT / "CLAUDE.md"] = CLAUDE_MD
    out[ROOT / ".github" / "copilot-instructions.md"] = COPILOT_MD
    return out


def prune(expected: dict[Path, str]) -> list[str]:
    """Delete generated skill folders that no longer exist in agent/skills/."""
    removed: list[str] = []
    keep = set(canon_skills())
    for target in SKILL_TARGETS:
        base = ROOT / target
        if not base.is_dir():
            continue
        for folder in base.iterdir():
            if folder.is_dir() and folder.name not in keep:
                shutil.rmtree(folder)
                removed.append(str(folder.relative_to(ROOT)).replace("\\", "/"))
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify adapters, write nothing")
    parser.add_argument("--verbose", action="store_true", help="list every adapter file")
    args = parser.parse_args(argv)

    expected = render()
    drift: list[str] = []
    written: list[str] = []

    for path, text in sorted(expected.items()):
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if current == text:
            continue
        drift.append(rel)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            written.append(rel)

    removed = [] if args.check else prune(expected)

    stale = sorted(
        str(p.relative_to(ROOT)).replace("\\", "/")
        for target in SKILL_TARGETS
        for p in (ROOT / target).rglob("*")
        if p.is_file() and p not in expected
    ) if any((ROOT / t).is_dir() for t in SKILL_TARGETS) else []

    payload = {
        "ok": not drift and not stale,
        "mode": "check" if args.check else "write",
        "adapters": len(expected),
        "changed": len(drift),
        "removed": len(removed),
        "stale": len(stale),
    }
    if args.verbose:
        payload["files"] = sorted(written or drift)
    print(json.dumps(payload, separators=(",", ":")))

    if args.check and (drift or stale):
        for rel in (drift + stale)[:20]:
            print(f"drift: {rel}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
