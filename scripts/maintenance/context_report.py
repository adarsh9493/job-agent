#!/usr/bin/env python
"""Report how many bytes the agent must read, per phase (about 4 bytes per token).

    python scripts/maintenance/context_report.py
    python scripts/maintenance/context_report.py --verbose

Output is one line of JSON. Budgets (enforced by tests):
    AGENTS.md <= 5120 bytes, every SKILL.md <= 5120 bytes, boot payload <= 2048 bytes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "AGENTS.md"
SKILLS = ROOT / "agent" / "skills"

BUDGET_AGENTS = 5120
BUDGET_SKILL = 5120
BUDGET_BOOT = 2048


def size(path: Path) -> int:
    return path.stat().st_size if path.is_file() else 0


def skill_index_bytes() -> int:
    """Name + description frontmatter of every skill - what a harness loads up front."""
    total = 0
    for folder in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        if text.startswith("---"):
            _, _, rest = text.partition("---")
            frontmatter, _, _ = rest.partition("---")
            total += len(frontmatter.encode("utf-8"))
    return total


def boot_bytes() -> int:
    """Size of the briefing the agent reads at session start (scripts/runtime/boot.py)."""
    boot = ROOT / "scripts" / "runtime" / "boot.py"
    if not boot.is_file():
        return 0
    result = subprocess.run(
        [sys.executable, str(boot), "--measure"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return 0
    return len(result.stdout.encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="include every skill")
    args = parser.parse_args(argv)

    skills = {p.parent.name: size(p) for p in sorted(SKILLS.rglob("SKILL.md"))}
    agents = size(AGENTS)
    boot = boot_bytes()

    report = {
        "agents_md": agents,
        "skill_index": skill_index_bytes(),
        "skills": sum(skills.values()),
        "boot": boot,
        "session_start": agents + skill_index_bytes() + boot,
        "worst_phase": agents + max(skills.values(), default=0) + boot,
        "tokens_session_start": round((agents + skill_index_bytes() + boot) / 4),
        "over_budget": sorted(
            [name for name, n in skills.items() if n > BUDGET_SKILL]
            + (["AGENTS.md"] if agents > BUDGET_AGENTS else [])
            + (["boot"] if boot > BUDGET_BOOT else [])
        ),
    }
    if args.verbose:
        report["per_skill"] = dict(sorted(skills.items(), key=lambda kv: -kv[1]))
    print(json.dumps(report, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
